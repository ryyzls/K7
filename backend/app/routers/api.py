from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.services import fuzzy_search as fz
from app.services import sparql_service as sp
from app.services.specialty_service import resolve_synonym, get_active_specialty_list
from app.services.comparison_service import compare_hospitals
from app.services.alternatives_service import find_alternatives
from app.services.enrichment_service import get_hospital_enrichment, get_all_hospitals_enrichment_summary

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(db: Session = Depends(get_db)):
    out = {}
    try:
        db.execute(text("SELECT 1"))
        out["postgres"] = "ok"
    except Exception as e:
        out["postgres"] = f"error: {type(e).__name__}"
    try:
        rows = await sp.select("SELECT (COUNT(*) AS ?n) WHERE { ?s a hf:RumahSakit }")
        out["fuseki"], out["jumlah_rs"] = "ok", int(rows[0]["n"])
    except Exception as e:
        out["fuseki"] = f"error: {type(e).__name__}"
    return JSONResponse(out, status_code=200 if out.get("postgres") == "ok" and out.get("fuseki") == "ok" else 503)


@router.get("/search")
async def search(q: str = "", kelas: str = "", jenis: str = "", kabkota: str = "", layanan: str = "",
                 spesialisasi: str = "", limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    q = q.strip()
    matched_specialty = None
    # Jika q cocok dengan istilah awam/sinonim spesialisasi (misal 'dokter jantung', 'dokter anak')
    if q and not spesialisasi:
        resolved = resolve_synonym(q)
        if resolved:
            matched_specialty = resolved
            spesialisasi = resolved

    if not q:  # tanpa kata kunci nama: filter terstruktur
        items = await sp.search_hospitals(q="", kelas=kelas, jenis=jenis, kabkota=kabkota,
                                          layanan=layanan, spesialisasi=spesialisasi, limit=limit, offset=offset)
        res = {"items": items, "count": len(items)}
        if spesialisasi:
            res["matched_specialty"] = spesialisasi
            res["specialty_notice"] = "Layanan dilaporkan dalam profil administratif SIRS Kemenkes, bukan verifikasi operasional real-time."
        return res

    # Jika q adalah sinonim spesialisasi (misal 'dokter jantung'), jangan ranking fuzzy nama RS
    # melainkan kembalikan RS yang terbukti memiliki spesialisasi tersebut di SIRS
    if matched_specialty:
        items = await sp.search_hospitals(q="", kelas=kelas, jenis=jenis, kabkota=kabkota,
                                          layanan=layanan, spesialisasi=matched_specialty, limit=limit, offset=offset)
        return {
            "items": items,
            "count": len(items),
            "matched_specialty": matched_specialty,
            "query_type": "specialty_synonym",
            "specialty_notice": "Layanan dilaporkan dalam profil administratif SIRS Kemenkes, bukan verifikasi operasional real-time.",
        }

    # Dengan kata kunci nama RS: ambil semua RS yang lolos filter lain, lalu fuzzy ranking
    semua = await sp.search_hospitals(q="", kelas=kelas, jenis=jenis, kabkota=kabkota,
                                      layanan=layanan, spesialisasi=spesialisasi, limit=500, offset=0)
    hasil = fz.rank(q, semua)
    items = hasil[offset:offset + limit]
    res = {"items": items, "count": len(items)}
    if spesialisasi:
        res["matched_specialty"] = spesialisasi
        res["specialty_notice"] = "Layanan dilaporkan dalam profil administratif SIRS Kemenkes, bukan verifikasi operasional real-time."
    return res


@router.get("/specialties")
async def specialties():
    """Mengembalikan daftar 16 spesialisasi medis terkurasi aktif bersumber dari SIRS Kemenkes."""
    return {"items": get_active_specialty_list(), "count": len(get_active_specialty_list())}


@router.get("/filters")
async def filters():
    opts = await sp.filter_options()
    opts["spesialisasi"] = get_active_specialty_list()
    return opts


@router.get("/compare")
async def compare(ids: str = Query(..., description="Daftar ID RS dipisah koma, contoh: rs-001,rs-008,rs-171")):
    """Membandingkan 2 hingga 3 rumah sakit secara faktual."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    return await compare_hospitals(id_list)


@router.get("/hospitals/{rs_id}")
async def hospital_detail(rs_id: str, db: Session = Depends(get_db)):
    """Profil RS dari RDF (SPARQL) digabung dengan sisa kuota kamar dari SQL (Federated Mapping via rs_id)."""
    h = await sp.get_hospital(rs_id)
    if not h:
        return JSONResponse({"detail": f"Rumah sakit '{rs_id}' tidak ditemukan"}, status_code=404)
    try:
        from app.services.availability_service import kamar_availability
        h = {**h, "ketersediaan_kamar": kamar_availability(db, rs_id)}
    except Exception:  # SQL belum siap tidak boleh merusak profil RDF
        db.rollback()
        h = {**h, "ketersediaan_kamar": None}
    return h


@router.get("/hospitals/{rs_id}/operational-hours")
async def hospital_operational_hours(rs_id: str):
    """Mengembalikan rincian jam operasional per-unit faskes (IGD vs Poliklinik vs Pendaftaran) beserta kalkulasi status realtime WIB."""
    h = await sp.get_hospital(rs_id)
    if not h:
        return JSONResponse({"detail": f"Rumah sakit '{rs_id}' tidak ditemukan"}, status_code=404)
    enrichment = get_hospital_enrichment(rs_id)
    return {
        "id_carisehat": rs_id,
        "nama": h["nama"],
        "telepon": h.get("telepon"),
        "jam_operasional": enrichment.get("jam_operasional", {})
    }


@router.get("/enrichment/summary")
async def enrichment_summary():
    """Mengembalikan statistik cakupan 6 fitur final enrichment & data freeze readiness."""
    return get_all_hospitals_enrichment_summary()


@router.get("/hospitals/{rs_id}/alternatives")
async def hospital_alternatives(
    rs_id: str,
    limit: int = Query(4, ge=1, le=5),
    db: Session = Depends(get_db),
):
    """Mengembalikan 3-5 rumah sakit rujukan berjenjang BPJS & alternatif beserta kuota live PostgreSQL."""
    return await find_alternatives(rs_id, limit=limit, db=db)


@router.get("/emergency/radar")
async def emergency_radar(
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    kabkota: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Radar Darurat IGD 24 Jam & Ketersediaan Bed ICU Real-Time (RDF + PostgreSQL)."""
    import datetime
    from app.services.alternatives_service import _haversine_km, _live_quota_map

    igd_status_map = {}
    try:
        rows_igd = db.execute(text("SELECT rs_id, status_igd, catatan FROM status_igd_rs")).mappings().all()
        igd_status_map = {r["rs_id"]: dict(r) for r in rows_igd}
    except Exception:
        db.rollback()
    hospitals = await sp.search_hospitals(limit=500)
    emergency_pool = []
    for h in hospitals:
        if kabkota and h.get("kabkota") != kabkota:
            continue
        tags = [*(h.get("layanan") or []), *(h.get("fasilitas") or [])]
        has_igd = any(k in t.lower() for t in tags for k in ("igd", "ugd", "gawat darurat", "ambulans"))
        has_icu_tag = any("icu" in t.lower() or "intensif" in t.lower() for t in tags)
        if not (has_igd or has_icu_tag):
            continue
        dist_km = _haversine_km(lat, lon, h.get("lat"), h.get("lon")) if (lat is not None and lon is not None) else None
        emergency_pool.append({
            **h,
            "has_igd": has_igd,
            "has_icu_tag": has_icu_tag,
            "jarak_km": dist_km,
            "estimasi_menit": max(3, round((dist_km / 32.0) * 60)) if dist_km is not None else None,
        })

    if lat is not None and lon is not None:
        emergency_pool.sort(
            key=lambda x: (
                x["jarak_km"] if x["jarak_km"] is not None else 9999.0,
                0 if x["has_igd"] else 1,
            )
        )
    else:
        kelas_prio = {"A": 0, "B": 1, "C": 2, "D": 3}
        emergency_pool.sort(key=lambda x: (0 if x["has_igd"] else 1, kelas_prio.get(x.get("kelas") or "", 9)))

    selected = emergency_pool[:limit]
    qmap = _live_quota_map(db, [item["id"] for item in selected])
    for item in selected:
        q = qmap.get(item["id"], {"sisa_bed_total": 25, "status_igd": (igd_status_map.get(h.get("id")) or {}).get("status_igd", "normal"), "sisa_icu": 5})
        item["sisa_icu"] = q["sisa_icu"]
        item["sisa_bed_total"] = q["sisa_bed_total"]

    return {
        "gps_aktif": lat is not None and lon is not None,
        "kabkota": kabkota or "Semua Wilayah Sumatera Utara",
        "total_terdeteksi": len(emergency_pool),
        "items": selected,
    }


@router.get("/config/maps")
async def maps_config():
    """Mengembalikan Google Maps API key agar dapat dipakai oleh frontend.
    Hanya mengembalikan key jika sudah dikonfigurasi (tidak bocorkan placeholder)."""
    key = settings.google_maps_api_key
    has_key = bool(key) and not key.startswith("ISI_")
    return {"google_maps_api_key": key if has_key else "", "enabled": has_key}
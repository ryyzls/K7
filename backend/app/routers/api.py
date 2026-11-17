from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.services import sparql_service as sp

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
                 limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    items = await sp.search_hospitals(q=q, kelas=kelas, jenis=jenis, kabkota=kabkota,
                                      layanan=layanan, limit=limit, offset=offset)
    return {"items": items, "count": len(items)}


@router.get("/filters")
async def filters():
    return await sp.filter_options()


@router.get("/config/maps")
async def maps_config():
    """Mengembalikan Google Maps API key agar dapat dipakai oleh frontend.
    Hanya mengembalikan key jika sudah dikonfigurasi (tidak bocorkan placeholder)."""
    key = settings.google_maps_api_key
    has_key = bool(key) and not key.startswith("ISI_")
    return {"google_maps_api_key": key if has_key else "", "enabled": has_key}

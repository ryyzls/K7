#!/usr/bin/env python3
"""Cari koordinat tiap RS -> data/koordinat.csv. Hanya pustaka standar Python, butuh internet.

    python scripts/geocode.py             # lanjut dari yang sudah ada (aman dihentikan, Ctrl+C)
    python scripts/geocode.py --perbaiki  # ulangi hanya baris yang belum akurat (sumber kabkota / kosong)
    python scripts/geocode.py --ulang     # mulai dari nol

Urutan strategi per RS (berhenti di yang pertama berhasil), dan nilai kolom `sumber`:
  osm      nama RS dicocokkan dengan semua amenity=hospital OSM di Sumut (Overpass API). PALING AKURAT.
  nama     Nominatim mencari nama RS (+ variasi "Rumah Sakit <nama inti>")
  jalan    Nominatim mencari nama jalan dari alamat (titik di jalan, selisih bisa ratusan meter)
  kabkota  titik pusat kab/kota. PERKIRAAN KASAR: jangan dipakai sebagai lokasi RS; lengkapi manual.
Hasil di luar kotak Sumatera Utara ditolak; pencocokan OSM yang terlalu jauh dari kab/kota RS ditolak.

Aturan Nominatim: maksimal 1 permintaan/detik (sudah diatur). Data (c) kontributor OpenStreetMap, ODbL:
cantumkan atribusinya. Setelah selesai, periksa data/koordinat.csv, lalu:
    python scripts/csv_ke_rdf.py --koordinat data/koordinat.csv
"""
import argparse
import csv
import difflib
import json
import math
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"]
UA = "CariSehat-tugas-kuliah/0.1 (proyek mahasiswa, Web Semantik)"
BBOX = (0.9, 4.4, 97.0, 100.6)  # lat_min, lat_max, lon_min, lon_max (kasar, Sumatera Utara + Nias)
JEDA = 1.1
AMBANG_OSM = 0.78      # skor kemiripan nama minimal
JARAK_MAKS_KM = 70     # pencocokan OSM harus dalam radius ini dari titik pusat kab/kota
STOP = {"rs", "rsu", "rsud", "rsup", "rsia", "rsk", "rumah", "sakit", "umum", "daerah", "khusus", "dr", "drs", "h"}
AKURAT = {"osm", "nama"}  # "jalan" hanya titik di jalan: diulang oleh --perbaiki


def spasi(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def norm(s):
    return [t for t in re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).split() if t not in STOP]


def skor(a, b):
    """Kemiripan nama 0..1. Ejaan mirip tapi beda kata (Delia vs Deli, Metta vs Mitra) sengaja TIDAK lolos."""
    ta, tb = norm(a), norm(b)
    if not ta or not tb:
        return 0.0
    sa, sb = set(ta), set(tb)
    r = difflib.SequenceMatcher(None, "".join(ta), "".join(tb)).ratio()  # tanpa spasi: Gunung Sitoli = Gunungsitoli
    j = len(sa & sb) / len(sa | sb)
    kecil = min(len(sa), len(sb))
    ada = sa & sb
    isi = 0.9 if (kecil >= 2 or (kecil == 1 and max(map(len, ada), default=0) >= 6)) and len(ada) == kecil else 0.0
    return max(r if r >= 0.92 else 0.0, j, isi)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def http(req, timeout=30):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:  # jaringan putus, 429, dst.
        print("   gagal:", type(e).__name__, e)
        return None


def cari(q):
    time.sleep(JEDA)
    qs = urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "id"})
    req = urllib.request.Request(f"{NOMINATIM}?{qs}", headers={"User-Agent": UA, "Accept-Language": "id"})
    hasil = http(req, 25)
    if hasil is None:  # gagal jaringan/timeout (bukan "tidak ada hasil"): coba sekali lagi
        time.sleep(3)
        hasil = http(req, 40)
    if not hasil:
        return None
    lat, lon = float(hasil[0]["lat"]), float(hasil[0]["lon"])
    if not (BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lon <= BBOX[3]):
        return None
    return lat, lon


def dari_elemen(j):
    out = []
    for e in j.get("elements", []):
        t = e.get("tags", {})
        nama = t.get("name") or t.get("name:id") or t.get("official_name")
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if nama and lat and lon:
            out.append([nama, float(lat), float(lon)])
    return out


def muat_osm(path):
    """Semua amenity=hospital di Sumut: daftar (nama, lat, lon), di-cache ke data/osm_hospital.json.
    Bila server Overpass semua gagal, simpan hasil query manual (lihat README) ke file yang sama:
    format mentah Overpass ({"elements": [...]}) juga diterima."""
    if path.exists():
        j = json.loads(path.read_text(encoding="utf-8"))
        return dari_elemen(j) if isinstance(j, dict) else j
    q = '[out:json][timeout:120];area["ISO3166-2"="ID-SU"]->.a;nwr["amenity"="hospital"](area.a);out center tags;'
    data = urllib.parse.urlencode({"data": q}).encode()
    for url in OVERPASS:
        for percobaan in (1, 2):
            print(f"Mengunduh daftar RS dari OSM: {url.split('/')[2]} (percobaan {percobaan}) ...")
            j = http(urllib.request.Request(url, data=data, headers={"User-Agent": UA}), 180)
            if j and j.get("elements") is not None:
                out = dari_elemen(j)
                path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
                print(f"  {len(out)} RS bernama di OSM")
                return out
            time.sleep(8)
    print("Semua server Overpass gagal; lanjut tanpa pencocokan OSM (hasil kurang akurat).")
    return []


def cocok_osm(nama, pusat, osm, terpakai):
    """Pilih entri OSM dengan nama paling mirip; kalau seri, yang terdekat ke titik pusat kab/kota."""
    kandidat = []
    for i, (n, la, lo) in enumerate(osm):
        if i in terpakai:
            continue
        s = skor(nama, n)
        if s < AMBANG_OSM or (not pusat and s < 0.95):  # tanpa titik pusat tak bisa cek jarak: minta lebih yakin
            continue
        d = km(pusat, (la, lo)) if pusat else 0
        if pusat and d > JARAK_MAKS_KM:
            continue
        kandidat.append((s, -d, i))
    if not kandidat:
        return None
    best = max(k[0] for k in kandidat)
    i = max((k for k in kandidat if k[0] >= best - 0.03), key=lambda k: k[1])[2]
    return i


def jalan_dari(alamat):
    return spasi(re.split(r",|\bNo\b|\bNomor\b|\bKel\b|\bKec\b|\bDesa\b|\bKm\b|\bKM\b", alamat, flags=re.I)[0])


def inti(nama):
    return spasi(re.sub(r"^(rs\s+umum\s+daerah|rs\s+umum|rsud|rsu|rsia|rs\s+khusus|rs)\s+", "", nama, flags=re.I))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "data/rumah_sakit_sumut.csv"))
    ap.add_argument("--out", default=str(ROOT / "data/koordinat.csv"))
    ap.add_argument("--osm", default=str(ROOT / "data/osm_hospital.json"))
    ap.add_argument("--ulang", action="store_true")
    ap.add_argument("--perbaiki", action="store_true")
    a = ap.parse_args()

    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = pathlib.Path(a.out)
    selesai = {}
    if out.exists() and not a.ulang:
        with open(out, encoding="utf-8", newline="") as f:
            selesai = {r["kode"]: r for r in csv.DictReader(f)}
        for v in selesai.values():  # sumber "alamat" (skrip versi lama) = pencarian nama RS
            if v["sumber"] == "alamat":
                v["sumber"] = "nama"
        if a.perbaiki:
            selesai = {k: v for k, v in selesai.items() if v["sumber"] in AKURAT}

    def simpan():
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["kode", "nama", "lat", "lon", "sumber"])
            w.writeheader()
            w.writerows(sorted(selesai.values(), key=lambda r: r["kode"]))

    osm = muat_osm(pathlib.Path(a.osm))
    terpakai = set()
    pusat = {}

    def titik_kab(kab):
        if kab not in pusat:
            print(f"  titik pusat {kab} ...")
            pusat[kab] = cari(f"{kab}, Sumatera Utara")
        return pusat[kab]

    try:
        for i, r in enumerate(rows, 1):
            kode = f"rs-{i:03d}"
            if kode in selesai:
                continue
            nama, alamat, kab = spasi(r["Rumah Sakit"]), spasi(r["Alamat"]), spasi(r["Kab/Kota"])
            wilayah = f"{kab}, Sumatera Utara"
            hasil, sumber = None, ""

            ti = titik_kab(kab)
            if osm:
                idx = cocok_osm(nama, ti, osm, terpakai)
                if idx is not None:
                    terpakai.add(idx)
                    hasil, sumber = (osm[idx][1], osm[idx][2]), "osm"
            if not hasil:
                hasil, sumber = cari(f"{nama}, {wilayah}"), "nama"
            if not hasil and inti(nama) != nama:
                hasil, sumber = cari(f"Rumah Sakit {inti(nama)}, {wilayah}"), "nama"
            if not hasil and jalan_dari(alamat):
                hasil, sumber = cari(f"{jalan_dari(alamat)}, {wilayah}"), "jalan"
            if not hasil and ti:
                hasil, sumber = ti, "kabkota"
            if not hasil:
                sumber = ""
            print(f"[{i:3d}/{len(rows)}] {nama[:45]:45s} -> {sumber or 'TIDAK KETEMU'}")
            selesai[kode] = {"kode": kode, "nama": nama,
                             "lat": f"{hasil[0]:.6f}" if hasil else "", "lon": f"{hasil[1]:.6f}" if hasil else "",
                             "sumber": sumber}
            if i % 10 == 0:
                simpan()
    except KeyboardInterrupt:
        print("\nDihentikan; hasil sementara disimpan. Jalankan lagi untuk melanjutkan.")
    simpan()
    hitung = {}
    for v in selesai.values():
        hitung[v["sumber"] or "kosong"] = hitung.get(v["sumber"] or "kosong", 0) + 1
    print("Ringkasan:", ", ".join(f"{k}={v}" for k, v in sorted(hitung.items())), f"(dari {len(rows)} RS) -> {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Ubah data/rumah_sakit_sumut.csv menjadi semantic/rdf/hospitals-sumut.ttl.

Hanya memakai pustaka standar Python (tanpa pip).

    python scripts/csv_ke_rdf.py                 # tanpa koordinat
    python scripts/csv_ke_rdf.py --koordinat data/koordinat.csv

File koordinat (opsional, dibuat scripts/geocode.py):  kode,lat,lon,sumber
  sumber = "alamat" (hasil cari alamat/nama RS) atau "kabkota" (titik pusat wilayah, perkiraan kasar)

Aturan pemetaan (catat di paper bagian metodologi):
  - kode RS   : rs-001, rs-002, ... sesuai urutan baris CSV (URI v0: {BASE}/rs/rs-NNN)
  - jenis     : "RSU" -> Umum; selain itu -> Khusus (jenis rinci disimpan di hf:spesialisasi)
  - kelas     : "D PRATAMA" -> D + hf:pratama true
  - layanan   : HANYA diturunkan dari jenis RS khusus (mis. RSIA -> Anak, Bersalin).
                RS Umum tidak diberi layanan karena CSV tidak memuat datanya.
  - telepon   : dibersihkan; hanya nomor pertama bila ada beberapa
"""
import argparse
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

SPESIALISASI = {  # kode jenis di CSV -> (label spesialisasi, layanan turunan)
    "RSU": (None, []),
    "RSIA": ("Ibu dan Anak", ["Anak", "Bersalin"]),
    "RSK BEDAH": ("Bedah", ["Bedah"]),
    "RSK GINJAL": ("Ginjal", ["Ginjal"]),
    "RSK GM": ("Gigi dan Mulut", ["Gigi dan Mulut"]),
    "RSK JIWA": ("Jiwa", ["Jiwa"]),
    "RSK MATA": ("Mata", ["Mata"]),
    "RSK PARU": ("Paru", ["Paru"]),
}


def spasi(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def rapikan_huruf(s: str, batas: float = 0.8) -> str:
    """Jika hampir semua huruf kapital, ubah ke huruf judul (singkatan/angka romawi dipulihkan)."""
    huruf = [c for c in s if c.isalpha()]
    if huruf and sum(c.isupper() for c in huruf) / len(huruf) > batas:
        s = s.title()
        s = re.sub(r"\b(Rs|Rsu|Rsud|Rsup|Rsia|Tni|Al|Au|Ad|Pln|Ptp|Km|Rt|Rw|Mh|Kl|Hkbp|Usu)\b",
                   lambda m: m.group(1).upper(), s)
        s = re.sub(r"\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii|Xiii)\b", lambda m: m.group(1).upper(), s)
    return s


def telepon(s: str) -> str:
    s = (s or "").split("/")[0]
    s = s.replace("_", "").strip(" -,.;")
    return spasi(s)


def lit(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def label_kabkota(nama: str) -> tuple[str, str]:
    """-> (slug, label) mengikuti gaya contoh: 'Kota Medan', 'Kab. Karo'."""
    nama = spasi(nama)
    if nama.startswith("Kota "):
        return slug(nama), nama
    return "kab-" + slug(nama), "Kab. " + nama


def baca_koordinat(path):
    out = {}
    if not path:
        return out
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("lat") and r.get("lon"):
                out[r["kode"]] = (r["lat"], r["lon"], r.get("sumber", ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "data/rumah_sakit_sumut.csv"))
    ap.add_argument("--koordinat", default=None)
    ap.add_argument("--out", default=str(ROOT / "semantic/rdf/hospitals-sumut.ttl"))
    a = ap.parse_args()

    koord = baca_koordinat(a.koordinat)
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    kabkota, layanan, baris = {}, set(), []
    for i, r in enumerate(rows, 1):
        kode = f"rs-{i:03d}"
        nama = rapikan_huruf(spasi(r["Rumah Sakit"]), batas=0.99)
        alamat = rapikan_huruf(spasi(r["Alamat"]).rstrip(" ,."))
        ks, kl = label_kabkota(r["Kab/Kota"])
        kabkota[ks] = kl

        kode_jenis = spasi(r["Jenis"]).upper()
        if kode_jenis not in SPESIALISASI:
            sys.exit(f"Jenis tidak dikenal di baris {i}: {r['Jenis']!r}")
        spes, lay = SPESIALISASI[kode_jenis]
        jenis = "Umum" if kode_jenis == "RSU" else "Khusus"

        kelas_raw = spasi(r["Kelas"]).upper()
        kelas, pratama = kelas_raw[:1], "PRATAMA" in kelas_raw
        if kelas not in "ABCD" or not kelas:
            sys.exit(f"Kelas tidak dikenal di baris {i}: {r['Kelas']!r}")

        p = [f"rs:{kode} a hf:RumahSakit", f"schema:name {lit(nama)}",
             f"hf:jenis {lit(jenis)}", f"hf:kelas {lit(kelas)}", f"hf:alamat {lit(alamat)}",
             f"hf:pemilik {lit(spasi(r['Pemilik']))}", f"hf:beradaDiKabupatenKota kk:{ks}"]
        if spes:
            p.append(f"hf:spesialisasi {lit(spes)}")
        if pratama:
            p.append('hf:pratama "true"^^xsd:boolean')
        tel = telepon(r["Telepon"])
        if tel:
            p.append(f"schema:telephone {lit(tel)}")
        if kode in koord:
            lat, lon, sumber = koord[kode]
            p.append(f'geo:lat "{lat}"^^xsd:decimal')
            p.append(f'geo:long "{lon}"^^xsd:decimal')
            if sumber:
                p.append(f"hf:sumberKoordinat {lit(sumber)}")
        if lay:
            layanan.update(lay)
            p.append("hf:menyediakanLayanan " + ", ".join(f"lay:{slug(x)}" for x in lay))
        baris.append(" ;\n  ".join(p) + " .")

    out = ["# Dibuat otomatis oleh scripts/csv_ke_rdf.py dari data/rumah_sakit_sumut.csv. JANGAN diedit manual;",
           "# ubah CSV atau skripnya lalu jalankan ulang. Skema/kelas/properti ada di ontologi.ttl.",
           "@prefix hf: <http://carisehat.id/ontology/> .",
           "@prefix schema: <https://schema.org/> .",
           "@prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> .",
           "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
           "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
           "@prefix rs: <http://localhost:8000/rs/> .",
           "@prefix kk: <http://localhost:8000/kabkota/> .",
           "@prefix prov: <http://localhost:8000/provinsi/> .",
           "@prefix lay: <http://localhost:8000/layanan/> .",
           "", 'prov:sumut a hf:Provinsi ; rdfs:label "Sumatera Utara" .', ""]
    for ks in sorted(kabkota):
        out.append(f"kk:{ks} a hf:KabupatenKota ; rdfs:label {lit(kabkota[ks])} ; hf:bagianDariProvinsi prov:sumut .")
    out.append("")
    for x in sorted(layanan):
        out.append(f"lay:{slug(x)} a hf:Layanan ; rdfs:label {lit(x)} .")
    out.append("")
    out += baris
    pathlib.Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} RS, {len(kabkota)} kab/kota, {len(layanan)} layanan, "
          f"{sum(1 for i in range(1, len(rows) + 1) if f'rs-{i:03d}' in koord)} punya koordinat -> {a.out}")


if __name__ == "__main__":
    main()

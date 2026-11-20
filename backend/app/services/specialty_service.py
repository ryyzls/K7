"""Layanan pencarian spesialisasi medis berbasis data SIRS Kemenkes terkurasi.

Modul ini menyediakan:
1. Daftar spesialisasi klinis aktif yang lolos review semantik dari AMAN_SEBAGAI_PENCARIAN.
2. Mapping sinonim eksplisit dan deterministik (misal 'dokter jantung' -> 'Jantung dan Pembuluh Darah').
3. Helper query SPARQL yang aman ke named graph SIRS.
4. Pemisahan status 'tercatat di SIRS' vs 'ketersediaan operasional real-time'.
5. Fallback lokal saat Fuseki offline.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace, URIRef, Literal

from app.config import settings
from app.services import sirs

CS = Namespace("http://carisehat.id/ontology/sirs/")

# ---------------------------------------------------------------------------
# 1. Daftar 16 Spesialisasi Klinis Standar (Permenkes 3/2020) yang Diaktifkan
#    Diekstrak dari 153 label AMAN_SEBAGAI_PENCARIAN (review_239_label_klinis.csv)
# ---------------------------------------------------------------------------
ACTIVE_CLINICAL_SPECIALTIES: dict[str, dict[str, Any]] = {
    "Kesehatan anak": {
        "label": "Kesehatan anak",
        "display_name": "Spesialis Anak (Pediatri)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan medis spesialisasi kesehatan bayi, anak, dan remaja terlapor di SIRS.",
        "frekuensi_rs": 190,
    },
    "Penyakit dalam": {
        "label": "Penyakit dalam",
        "display_name": "Spesialis Penyakit Dalam (Internis)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan medis penyakit dalam dewasa terlapor di SIRS.",
        "frekuensi_rs": 188,
    },
    "Bedah": {
        "label": "Bedah",
        "display_name": "Spesialis Bedah Umum",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan bedah umum dan operatif terlapor di SIRS.",
        "frekuensi_rs": 188,
    },
    "Obstetri dan ginekologi": {
        "label": "Obstetri dan ginekologi",
        "display_name": "Spesialis Kebidanan & Kandungan (Obgyn)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan kehamilan, persalinan, dan kesehatan reproduksi wanita terlapor di SIRS.",
        "frekuensi_rs": 186,
    },
    "Anestesi": {
        "label": "Anestesi",
        "display_name": "Spesialis Anestesiologi & Terapi Intensif",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan anestesiologi dan penanganan perioperatif terlapor di SIRS.",
        "frekuensi_rs": 186,
    },
    "Paru": {
        "label": "Paru",
        "display_name": "Spesialis Paru (Pulmonologi)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan pernapasan dan paru terlapor di SIRS.",
        "frekuensi_rs": 164,
    },
    "Pelayanan medik gigi mulut": {
        "label": "Pelayanan medik gigi mulut",
        "display_name": "Pelayanan Gigi & Mulut",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan kesehatan gigi dan mulut terlapor di SIRS.",
        "frekuensi_rs": 142,
    },
    "Saraf": {
        "label": "Saraf",
        "display_name": "Spesialis Saraf (Neurologi)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan neurologi dan sistem saraf terlapor di SIRS.",
        "frekuensi_rs": 135,
    },
    "Telinga Hidung Tenggorok Kepala Leher": {
        "label": "Telinga Hidung Tenggorok Kepala Leher",
        "display_name": "Spesialis THT-KL",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan telinga, hidung, tenggorok, bedah kepala leher terlapor di SIRS.",
        "frekuensi_rs": 132,
    },
    "Mata": {
        "label": "Mata",
        "display_name": "Spesialis Mata (Oftalmologi)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan kesehatan penglihatan dan mata terlapor di SIRS.",
        "frekuensi_rs": 116,
    },
    "Jantung dan Pembuluh Darah": {
        "label": "Jantung dan Pembuluh Darah",
        "display_name": "Spesialis Jantung & Pembuluh Darah (Kardiologi)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan kardiovaskular dan jantung terlapor di SIRS.",
        "frekuensi_rs": 106,
    },
    "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA": {
        "label": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
        "display_name": "Spesialis Kedokteran Jiwa (Psikiatri)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan kesehatan jiwa dan psikiatri terlapor di SIRS.",
        "frekuensi_rs": 87,
    },
    "Kulit dan Kelamin": {
        "label": "Kulit dan Kelamin",
        "display_name": "Spesialis Kulit & Kelamin (Dermatologi)",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan dermatologi dan venereologi terlapor di SIRS.",
        "frekuensi_rs": 87,
    },
    "Rehabilitasi Medik": {
        "label": "Rehabilitasi Medik",
        "display_name": "Kedokteran Fisik & Rehabilitasi",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan fisioterapi dan pemulihan fisik terlapor di SIRS.",
        "frekuensi_rs": 87,
    },
    "Orthopedi": {
        "label": "Orthopedi",
        "display_name": "Spesialis Bedah Ortopedi & Traumatologi",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan bedah tulang, sendi, dan traumatologi terlapor di SIRS.",
        "frekuensi_rs": 62,
    },
    "Urologi": {
        "label": "Urologi",
        "display_name": "Spesialis Urologi",
        "kategori": "Spesialisasi Klinis Standar (Permenkes 3/2020)",
        "deskripsi": "Pelayanan saluran kemih dan urogenital terlapor di SIRS.",
        "frekuensi_rs": 47,
    },
}

# Layanan darurat dan diagnostik penting yang sudah tervalidasi sebelumnya
ACTIVE_DIAGNOSTIC_EMERGENCY: dict[str, dict[str, Any]] = {
    sirs.EMERGENCY: {
        "label": sirs.EMERGENCY,
        "display_name": "UGD / IGD 24 Jam",
        "kategori": "Gawat Darurat Terlapor",
        "deskripsi": "Pelayanan gawat darurat umum 24 jam & 7 hari seminggu.",
        "frekuensi_rs": 194,
    },
    "Radiologi": {
        "label": "Radiologi",
        "display_name": "Radiologi & Rontgen",
        "kategori": "Diagnostik & Pemeriksaan",
        "deskripsi": "Pemeriksaan radiodiagnostik dan pencitraan medis.",
        "frekuensi_rs": 184,
    },
    "Patologi Klinik": {
        "label": "Patologi Klinik",
        "display_name": "Patologi Klinik / Laboratorium",
        "kategori": "Diagnostik & Pemeriksaan",
        "deskripsi": "Pemeriksaan spesimen darah dan cairan tubuh.",
        "frekuensi_rs": 169,
    },
}

ALL_ACTIVE_SPECIALTIES = {**ACTIVE_CLINICAL_SPECIALTIES, **ACTIVE_DIAGNOSTIC_EMERGENCY}

# ---------------------------------------------------------------------------
# 2. Mapping Istilah Eksplisit & Sinonim Awam -> Label Resmi SIRS
# ---------------------------------------------------------------------------
SYNONYM_MAP: dict[str, str] = {
    # Jantung
    "dokter jantung": "Jantung dan Pembuluh Darah",
    "spesialis jantung": "Jantung dan Pembuluh Darah",
    "jantung": "Jantung dan Pembuluh Darah",
    "kardiologi": "Jantung dan Pembuluh Darah",
    "kardiovaskuler": "Jantung dan Pembuluh Darah",
    "kardiovaskular": "Jantung dan Pembuluh Darah",
    "poli jantung": "Jantung dan Pembuluh Darah",
    # Anak
    "dokter anak": "Kesehatan anak",
    "spesialis anak": "Kesehatan anak",
    "anak": "Kesehatan anak",
    "pediatri": "Kesehatan anak",
    "pediatrik": "Kesehatan anak",
    "poli anak": "Kesehatan anak",
    "kesehatan anak": "Kesehatan anak",
    # Kandungan
    "dokter kandungan": "Obstetri dan ginekologi",
    "spesialis kandungan": "Obstetri dan ginekologi",
    "dokter obgyn": "Obstetri dan ginekologi",
    "kandungan": "Obstetri dan ginekologi",
    "kebidanan": "Obstetri dan ginekologi",
    "kebidanan dan kandungan": "Obstetri dan ginekologi",
    "obgyn": "Obstetri dan ginekologi",
    "spog": "Obstetri dan ginekologi",
    "obstetri": "Obstetri dan ginekologi",
    "ginekologi": "Obstetri dan ginekologi",
    "obstetri dan ginekologi": "Obstetri dan ginekologi",
    "poli kandungan": "Obstetri dan ginekologi",
    # Mata
    "dokter mata": "Mata",
    "spesialis mata": "Mata",
    "mata": "Mata",
    "oftalmologi": "Mata",
    "oftalmologis": "Mata",
    "poli mata": "Mata",
    # Penyakit Dalam
    "dokter penyakit dalam": "Penyakit dalam",
    "spesialis penyakit dalam": "Penyakit dalam",
    "penyakit dalam": "Penyakit dalam",
    "internis": "Penyakit dalam",
    "dokter internis": "Penyakit dalam",
    "poli penyakit dalam": "Penyakit dalam",
    # Bedah
    "dokter bedah": "Bedah",
    "spesialis bedah": "Bedah",
    "bedah": "Bedah",
    "bedah umum": "Bedah",
    "poli bedah": "Bedah",
    # Saraf
    "dokter saraf": "Saraf",
    "spesialis saraf": "Saraf",
    "saraf": "Saraf",
    "neurologi": "Saraf",
    "neurolog": "Saraf",
    "poli saraf": "Saraf",
    # Paru
    "dokter paru": "Paru",
    "spesialis paru": "Paru",
    "paru": "Paru",
    "pulmonologi": "Paru",
    "pulmonologis": "Paru",
    "poli paru": "Paru",
    # THT
    "dokter tht": "Telinga Hidung Tenggorok Kepala Leher",
    "spesialis tht": "Telinga Hidung Tenggorok Kepala Leher",
    "tht": "Telinga Hidung Tenggorok Kepala Leher",
    "tht-kl": "Telinga Hidung Tenggorok Kepala Leher",
    "tht kl": "Telinga Hidung Tenggorok Kepala Leher",
    "telinga hidung tenggorok": "Telinga Hidung Tenggorok Kepala Leher",
    "telinga hidung tenggorok kepala leher": "Telinga Hidung Tenggorok Kepala Leher",
    "poli tht": "Telinga Hidung Tenggorok Kepala Leher",
    # Kulit & Kelamin
    "dokter kulit": "Kulit dan Kelamin",
    "spesialis kulit": "Kulit dan Kelamin",
    "kulit dan kelamin": "Kulit dan Kelamin",
    "kulit kelamin": "Kulit dan Kelamin",
    "dermatologi": "Kulit dan Kelamin",
    "spkk": "Kulit dan Kelamin",
    "poli kulit": "Kulit dan Kelamin",
    # Ortopedi
    "dokter tulang": "Orthopedi",
    "dokter ortopedi": "Orthopedi",
    "spesialis ortopedi": "Orthopedi",
    "ortopedi": "Orthopedi",
    "orthopedi": "Orthopedi",
    "bedah tulang": "Orthopedi",
    "bedah ortopedi": "Orthopedi",
    "traumatologi": "Orthopedi",
    "poli ortopedi": "Orthopedi",
    # Urologi
    "dokter urologi": "Urologi",
    "spesialis urologi": "Urologi",
    "urologi": "Urologi",
    "urolog": "Urologi",
    "saluran kemih": "Urologi",
    "poli urologi": "Urologi",
    # Jiwa / Psikiatri
    "dokter jiwa": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "spesialis jiwa": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "psikiater": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "kejiwaan": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "psikiatri": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "kesehatan jiwa": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    "poli jiwa": "Kedokteran Jiwa / Psikiatri/ Psikogeriatri/ NAPZA",
    # Gigi
    "dokter gigi": "Pelayanan medik gigi mulut",
    "spesialis gigi": "Pelayanan medik gigi mulut",
    "gigi": "Pelayanan medik gigi mulut",
    "gigi dan mulut": "Pelayanan medik gigi mulut",
    "poli gigi": "Pelayanan medik gigi mulut",
    # Rehabilitasi Medik
    "rehabilitasi medik": "Rehabilitasi Medik",
    "rehab medik": "Rehabilitasi Medik",
    "fisioterapi": "Rehabilitasi Medik",
    "terapi fisik": "Rehabilitasi Medik",
    # Anestesi
    "anestesi": "Anestesi",
    "anestesiologi": "Anestesi",
    "bius": "Anestesi",
    # Gawat Darurat
    "igd": sirs.EMERGENCY,
    "ugd": sirs.EMERGENCY,
    "gawat darurat": sirs.EMERGENCY,
    "darurat": sirs.EMERGENCY,
    "darurat 24 jam": sirs.EMERGENCY,
    "emergency": sirs.EMERGENCY,
    # Radiologi
    "radiologi": "Radiologi",
    "rontgen": "Radiologi",
    "x-ray": "Radiologi",
    "xray": "Radiologi",
    # Patologi Klinik
    "patologi klinik": "Patologi Klinik",
    "patologi": "Patologi Klinik",
    "lab patologi": "Patologi Klinik",
}


def normalize_term(term: str) -> str:
    """Membersihkan whitespace dan karakter non-alfanumerik dari istilah pencarian."""
    t = term.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def resolve_synonym(query: str) -> str | None:
    """Mencari mapping sinonim umum ke label resmi SIRS.

    Mengembalikan label SIRS persis (misal 'Jantung dan Pembuluh Darah')
    atau None jika tidak ditemukan kecocokan istilah eksplisit.
    """
    clean = normalize_term(query)
    # 1. Exact match di SYNONYM_MAP
    if clean in SYNONYM_MAP:
        return SYNONYM_MAP[clean]

    # 2. Check apakah query persis sama dengan salah satu label aktif (case-insensitive)
    for lbl in ALL_ACTIVE_SPECIALTIES:
        if clean == lbl.lower():
            return lbl

    # 3. Check jika kata kunci awam terkandung sebagai frase utuh
    for syn, target_lbl in SYNONYM_MAP.items():
        if f" {syn} " in f" {clean} ":
            return target_lbl

    return None


def get_active_specialty_list() -> list[dict[str, Any]]:
    """Mengembalikan daftar seluruh spesialisasi dan layanan aktif dengan metadata."""
    out = []
    for lbl, meta in ALL_ACTIVE_SPECIALTIES.items():
        syns = [k for k, v in SYNONYM_MAP.items() if v == lbl]
        out.append({
            "label_sirs": lbl,
            "display_name": meta["display_name"],
            "kategori": meta["kategori"],
            "deskripsi": meta["deskripsi"],
            "frekuensi_rs": meta["frekuensi_rs"],
            "sinonim_populer": syns[:5],
            "status_kebijakan": "REVIEWED_ACTIVE",
            "catatan_status": "Tercatat di laporan profil SIRS; bukan bukti ketersediaan real-time.",
        })
    return sorted(out, key=lambda x: x["frekuensi_rs"], reverse=True)


def sirs_specialty_pattern(label: str, rs_var: str = "?rs", obs_var: str = "?obs") -> str:
    """Menghasilkan snippet SPARQL aman untuk filter spesialisasi di named graph SIRS.

    Query ini memeriksa keberadaan catatan pelayanan dengan label exact pada named graph.
    """
    escaped = label.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    return (
        f"GRAPH <{sirs.GRAPH_URI}> {{ "
        f"{rs_var} <{CS.catatanPelayanan}> {obs_var} . "
        f'{obs_var} <{CS.labelPelayanan}> "{escaped}" . '
        f"}}"
    )


@lru_cache(maxsize=1)
def load_all_sirs_observations() -> dict[str, list[dict[str, Any]]]:
    """Memuat seluruh observasi dari services-reviewed.ttl sebagai fallback lokal.

    Struktur return: {hospital_id: [observation_dict, ...]}
    """
    path = Path(settings.rdf_dir).parent / "sirs/services-reviewed.ttl"
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / "semantic/sirs/services-reviewed.ttl"
    if not path.exists():
        return {}
    g = Graph().parse(path)
    result: dict[str, list[dict[str, Any]]] = {}
    for obs in g.subjects(CS.labelPelayanan, None):
        uri = g.value(obs, CS.untukRumahSakit)
        if not uri:
            continue
        ident = str(uri).rsplit("/", 1)[-1]
        lbl = str(g.value(obs, CS.labelPelayanan))
        item = {
            "record_uri": str(obs),
            "label": lbl,
            "category": str(g.value(obs, CS.kategoriKurasi)),
            "source_url": str(g.value(obs, CS.sumberProfil)),
            "retrieved_at": str(g.value(obs, CS.tanggalPengambilan)),
            "source_status": str(g.value(obs, CS.statusPublikasi)),
            "category_status": str(g.value(obs, CS.statusKurasi)),
            "is_active_specialty": lbl in ALL_ACTIVE_SPECIALTIES,
            "verification_status": "reported_not_operationally_verified",
        }
        result.setdefault(ident, []).append(item)
    return result


def get_hospital_specialties(rs_id: str) -> list[dict[str, Any]]:
    """Mengambil seluruh spesialisasi terlapor SIRS untuk suatu rumah sakit (lengkap provenance)."""
    records = load_all_sirs_observations().get(rs_id, [])
    # Filter hanya spesialisasi aktif atau diagnostik terkurasi
    active_records = [r for r in records if r["label"] in ALL_ACTIVE_SPECIALTIES]
    return active_records

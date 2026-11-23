"""Auto-seeder idempoten untuk skema MSBD CariSehat (Poliklinik, Jadwal, Pasien Demo, Ulasan)."""
from __future__ import annotations

import logging
from datetime import date, time, timedelta

from sqlalchemy import text

from app.database.connection import engine
from app.routers.auth_pasien import _hash_password
from app.services import hospital_repo

log = logging.getLogger("carisehat.seed_msbd")

DOKTER_SAMPLES = [
    ("dr. Andi Pratama, Sp.PD", time(8, 0), time(12, 0)),
    ("dr. Maya Sari Lubis, Sp.A", time(13, 0), time(16, 30)),
    ("dr. Hendra Gunawan, Sp.JP", time(9, 0), time(13, 0)),
    ("dr. Rina Nasution, Sp.OG", time(10, 0), time(14, 0)),
]

DEMO_USERS = [
    ("pasien_demo", "pasien.demo@carisehat.id", "Budi Santoso", "081260001101", "Demo1234!"),
    ("rizal_medan", "rizal@carisehat.id", "Fahri Arizal", "081260001102", "Demo1234!"),
    ("siti_aminah", "siti.aminah@carisehat.id", "Siti Aminah Siregar", "081260001103", "Demo1234!"),
]

ULASAN_SAMPLES = [
    (0, 0, 5, "Pelayanan pendaftaran poliklinik cepat, nomor antrean jelas, dan dokter sangat komunikatif."),
    (1, 0, 4, "Fasilitas ruang tunggu rawat jalan bersih serta informasi jadwal dokter cukup akurat."),
    (0, 1, 5, "Proses reservasi online sangat membantu mengurangi waktu antre di loket rumah sakit."),
    (2, 1, 4, "Perawat ramah dan penanganan di poli spesialis berjalan tertib sesuai nomor tiket."),
    (1, 2, 5, "Lokasi mudah dijangkau dan informasi layanan spesialis sesuai dengan profil RS."),
    (2, 3, 4, "Pelayanan cukup baik, antrean poliklinik terpantau rapi dari pagi hingga siang."),
]


def seed_msbd_data() -> dict[str, int]:
    """Isi data awal MSBD secara idempoten dari repositori RDF ke PostgreSQL."""
    hospitals = hospital_repo.get_all_hospitals()
    if not hospitals:
        log.warning("Data rumah sakit RDF kosong; auto-seed MSBD dilewati.")
        return {"poliklinik": 0, "jadwal": 0, "users": 0, "ulasan": 0, "favorit": 0}

    poli_inserted = 0
    jadwal_inserted = 0
    users_inserted = 0
    ulasan_inserted = 0
    favorit_inserted = 0

    with engine.begin() as conn:
        # 1. Seed master poliklinik dari layanan/spesialisasi RDF setiap RS
        for rs in hospitals:
            rs_id = rs.get("id")
            if not rs_id:
                continue

            raw_layanan = rs.get("layanan") or ["Poli Umum"]
            seen_spec: set[str] = set()
            unique_specs: list[str] = []
            for item in raw_layanan:
                spec = str(item).strip()[:120]
                key = spec.lower()
                if spec and key not in seen_spec:
                    seen_spec.add(key)
                    unique_specs.append(spec)
                if len(unique_specs) >= 4:
                    break

            if not unique_specs:
                unique_specs = ["Poli Umum"]

            kuota_harian = 30 if rs.get("kelas") in ("A", "B") else 20

            for idx, spec in enumerate(unique_specs, start=1):
                kode_poli = f"POL-{idx:02d}"
                nama_poli = (
                    spec
                    if spec.lower().startswith(("poli", "pelayanan", "klinik"))
                    else f"Poliklinik {spec}"
                )[:120]
                lokasi = f"Gedung Rawat Jalan Lt. {(idx - 1) // 2 + 1}, Ruang {100 + idx}"

                res = conn.execute(
                    text("""
                        INSERT INTO poliklinik (
                            rs_id, kode_poli, nama_poli, spesialisasi,
                            lokasi_ruangan, jam_operasional, kuota_harian, aktif
                        )
                        VALUES (
                            :rs_id, :kode_poli, :nama_poli, :spesialisasi,
                            :lokasi, 'Senin-Sabtu, 08:00-16:00 WIB', :kuota, TRUE
                        )
                        ON CONFLICT (rs_id, spesialisasi) DO NOTHING
                        RETURNING id
                    """),
                    {
                        "rs_id": rs_id,
                        "kode_poli": kode_poli,
                        "nama_poli": nama_poli,
                        "spesialisasi": spec,
                        "lokasi": lokasi,
                        "kuota": kuota_harian,
                    },
                ).scalar_one_or_none()
                if res is not None:
                    poli_inserted += 1

        # 2. Seed jadwal dokter untuk 40 RS pertama & seluruh RS di Kota Medan
        target_rs_ids = {rs["id"] for rs in hospitals[:40] if rs.get("id")}
        for rs in hospitals:
            if "medan" in str(rs.get("kabkota", "")).lower() and rs.get("id"):
                target_rs_ids.add(rs["id"])

        target_polis = conn.execute(
            text("""
                SELECT id, rs_id, spesialisasi
                FROM poliklinik
                WHERE aktif = TRUE AND rs_id = ANY(:rs_ids)
                ORDER BY rs_id, id
            """),
            {"rs_ids": list(target_rs_ids)},
        ).all()

        per_rs_count: dict[str, int] = {}
        for poli_id, rs_id, spesialisasi in target_polis:
            cnt = per_rs_count.get(rs_id, 0)
            if cnt >= 2:
                continue
            per_rs_count[rs_id] = cnt + 1

            exists = conn.execute(
                text("SELECT 1 FROM jadwal_konsultasi WHERE poliklinik_id = :pid LIMIT 1"),
                {"pid": poli_id},
            ).scalar_one_or_none()
            if exists:
                continue

            dokter, jam_mulai, jam_selesai = DOKTER_SAMPLES[poli_id % len(DOKTER_SAMPLES)]
            for hari in (1, 3, 5):  # Senin, Rabu, Jumat
                conn.execute(
                    text("""
                        INSERT INTO jadwal_konsultasi (
                            rs_id, poliklinik_id, nama_dokter, spesialisasi,
                            hari, jam_mulai, jam_selesai, kuota_per_sesi, aktif
                        )
                        VALUES (
                            :rs_id, :poliklinik_id, :nama_dokter, :spesialisasi,
                            :hari, :jam_mulai, :jam_selesai, 15, TRUE
                        )
                    """),
                    {
                        "rs_id": rs_id,
                        "poliklinik_id": poli_id,
                        "nama_dokter": dokter,
                        "spesialisasi": spesialisasi,
                        "hari": hari,
                        "jam_mulai": jam_mulai,
                        "jam_selesai": jam_selesai,
                    },
                )
                jadwal_inserted += 1

        # 3. Seed akun pasien demo
        for uname, email, nama, telp, raw_pwd in DEMO_USERS:
            uid = conn.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, nama_lengkap, no_telp, aktif)
                    VALUES (:u, :e, :p, :n, :t, TRUE)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id
                """),
                {
                    "u": uname,
                    "e": email,
                    "p": _hash_password(raw_pwd),
                    "n": nama,
                    "t": telp,
                },
            ).scalar_one_or_none()
            if uid is not None:
                users_inserted += 1

        user_ids = conn.execute(
            text("SELECT id FROM users WHERE username = ANY(:unames) ORDER BY id"),
            {"unames": [u[0] for u in DEMO_USERS]},
        ).scalars().all()

        top_rs_ids = [rs["id"] for rs in hospitals[:6] if rs.get("id")]

        # 4. Seed favorit & ulasan awal
        if user_ids and top_rs_ids:
            for u_idx, uid in enumerate(user_ids):
                for offset in range(2):
                    rs_target = top_rs_ids[(u_idx + offset) % len(top_rs_ids)]
                    fav = conn.execute(
                        text("""
                            INSERT INTO favorit_rs (user_id, rs_id, catatan)
                            VALUES (:uid, :rs_id, 'Rumah sakit rujukan pilihan')
                            ON CONFLICT (user_id, rs_id) DO NOTHING
                            RETURNING user_id
                        """),
                        {"uid": uid, "rs_id": rs_target},
                    ).scalar_one_or_none()
                    if fav is not None:
                        favorit_inserted += 1

            for u_idx, rs_idx, rating, komentar in ULASAN_SAMPLES:
                if u_idx < len(user_ids) and rs_idx < len(top_rs_ids):
                    rev = conn.execute(
                        text("""
                            INSERT INTO ulasan_rs (
                                user_id, rs_id, rating, komentar, status_moderasi, dimoderasi_oleh
                            )
                            VALUES (:uid, :rs_id, :rating, :komentar, 'disetujui', 'system_seed')
                            ON CONFLICT (user_id, rs_id) DO NOTHING
                            RETURNING id
                        """),
                        {
                            "uid": user_ids[u_idx],
                            "rs_id": top_rs_ids[rs_idx],
                            "rating": rating,
                            "komentar": komentar,
                        },
                    ).scalar_one_or_none()
                    if rev is not None:
                        ulasan_inserted += 1

            # 5. Seed 1 contoh reservasi poliklinik via stored function jika tabel masih kosong
            total_res = conn.execute(text("SELECT COUNT(*) FROM reservasi_konsultasi")).scalar_one()
            if total_res == 0:
                sample_jadwal = conn.execute(
                    text("SELECT id, hari FROM jadwal_konsultasi WHERE aktif = TRUE ORDER BY id LIMIT 1")
                ).first()
                if sample_jadwal:
                    jid, target_hari = sample_jadwal
                    besok = date.today() + timedelta(days=1)
                    while besok.isoweekday() != target_hari:
                        besok += timedelta(days=1)
                    conn.execute(
                        text("""
                            SELECT * FROM sp_buat_reservasi_poliklinik(
                                CAST(:kode AS text), :jid, :uid,
                                CAST(:nama AS text), CAST(:telp AS text),
                                :tgl, CAST(:keluhan AS text), CAST(:idem AS text)
                            )
                        """),
                        {
                            "kode": "RSV-SEED-001",
                            "jid": jid,
                            "uid": user_ids[0],
                            "nama": "Budi Santoso",
                            "telp": "081260001101",
                            "tgl": besok,
                            "keluhan": "Kontrol rutin tekanan darah dan konsultasi poli spesialis",
                            "idem": "seed-initial-reservasi-001",
                        },
                    )

    summary = {
        "poliklinik": poli_inserted,
        "jadwal": jadwal_inserted,
        "users": users_inserted,
        "ulasan": ulasan_inserted,
        "favorit": favorit_inserted,
    }
    log.info("Auto-seed MSBD selesai: %s", summary)
    return summary


"""Router Admin CariSehat (Tubes MSBD): autentikasi, RBAC, dan CRUD lengkap.

Setiap endpoint ubah-data berjalan dalam satu transaksi (commit/rollback eksplisit) dan
memanggil set_actor() agar trigger audit_log mencatat pelaku. Semua SQL memakai bind
parameter; body divalidasi Pydantic. Atribut deskriptif RS tidak pernah disimpan di SQL:
nama/kabupaten diambil dari RDF lewat rs_id.
"""
import datetime
import secrets
import string
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.services.admin_auth import (
    current_admin, hash_password, hash_token, require_perm, set_actor, verify_password,
)
from app.services.availability_service import ROOM_TYPES, hospital_name

router = APIRouter(prefix="/api/admin", tags=["Admin"])
ui_router = APIRouter()

RoomType = Literal["VIP", "Kelas I", "Kelas II", "Kelas III", "ICU"]
BookingStatus = Literal["menunggu", "dikonfirmasi", "dibatalkan"]
ReservasiStatus = Literal["menunggu", "dikonfirmasi", "selesai", "dibatalkan"]
RS_ID = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")

_PGCODE_STATUS = {"CS409": 409, "CS404": 404, "CS422": 422}
_CONSTRAINT_MSG = {
    "uq_booking_pasien_aktif": "Pasien yang sama sudah punya booking aktif untuk kamar & tanggal tersebut",
    "admin_users_username_key": "Username sudah dipakai",
    "reservasi_konsultasi_jadwal_id_fkey": "Jadwal masih memiliki reservasi; nonaktifkan jadwal alih-alih menghapus",
    "uq_reservasi_pasien_aktif": "Nomor telepon ini sudah punya reservasi aktif pada sesi tersebut",
    "booking_idempotency_booking_id_fkey": "Booking masih direferensikan ledger idempotency",
}
_DUMMY_HASH: str | None = None


# ─── Utilitas ────────────────────────────────────────────────────────────────

@contextmanager
def tx(db: Session):
    """Transaksi: commit bila sukses, rollback + terjemahkan error DB ke HTTP bila gagal."""
    try:
        yield
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        c = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
        raise HTTPException(409, _CONSTRAINT_MSG.get(c, "Data melanggar aturan integritas database")) from None
    except DBAPIError as exc:
        db.rollback()
        orig = getattr(exc, "orig", None)
        code = getattr(orig, "pgcode", "") or ""
        msg = getattr(getattr(orig, "diag", None), "message_primary", "") or ""
        if code in _PGCODE_STATUS:
            raise HTTPException(_PGCODE_STATUS[code], msg or "Ditolak oleh aturan database") from None
        raise HTTPException(503, "Database tidak tersedia; coba lagi nanti") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Database tidak tersedia; coba lagi nanti") from None


def _like(q: str) -> str:
    esc = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{esc}%"


def _need_rs(rs_id: str) -> str:
    name = hospital_name(rs_id)
    if not name:
        raise HTTPException(422, f"rs_id '{rs_id}' tidak ada di dataset RDF")
    return name


def _with_names(rows, key: str = "kode_rs") -> list[dict]:
    cache: dict[str, str] = {}
    out = []
    for r in rows:
        d = dict(r)
        rid = d.get(key)
        if rid not in cache:
            cache[rid] = hospital_name(rid) or rid
        d["nama_rs"] = cache[rid]
        out.append(d)
    return out


def _gen(prefix: str) -> str:
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"{prefix}-{datetime.date.today():%Y%m%d}-{suffix}"


# ─── Skema ───────────────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class BookingIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    kode_rs: str = RS_ID
    nama_pasien: str = Field(min_length=1, max_length=100)
    no_telp: str = Field(min_length=1, max_length=20)
    tanggal_masuk: datetime.date
    tanggal_keluar: datetime.date | None = None
    jenis_kamar: RoomType
    catatan: str | None = Field(default=None, max_length=2000)
    status: BookingStatus = "menunggu"

    @model_validator(mode="after")
    def _tgl(self):
        if self.tanggal_keluar and self.tanggal_keluar < self.tanggal_masuk:
            raise ValueError("tanggal_keluar harus >= tanggal_masuk")
        if self.tanggal_keluar and (self.tanggal_keluar - self.tanggal_masuk).days > 365:
            raise ValueError("lama rawat maksimal 365 hari")
        return self


class BookingPatch(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    kode_rs: str | None = Field(default=None, min_length=1, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    nama_pasien: str | None = Field(default=None, min_length=1, max_length=100)
    no_telp: str | None = Field(default=None, min_length=1, max_length=20)
    tanggal_masuk: datetime.date | None = None
    tanggal_keluar: datetime.date | None = None
    jenis_kamar: RoomType | None = None
    catatan: str | None = Field(default=None, max_length=2000)
    status: BookingStatus | None = None


class KuotaIn(BaseModel):
    rs_id: str = RS_ID
    jenis_kamar: RoomType
    kapasitas: int = Field(ge=0, le=1000)


class JadwalIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    rs_id: str = RS_ID
    nama_dokter: str = Field(min_length=2, max_length=120)
    spesialisasi: str = Field(min_length=2, max_length=80)
    hari: int = Field(ge=1, le=7)
    jam_mulai: datetime.time
    jam_selesai: datetime.time
    kuota_per_sesi: int = Field(default=10, ge=1, le=500)
    aktif: bool = True

    @model_validator(mode="after")
    def _jam(self):
        if self.jam_selesai <= self.jam_mulai:
            raise ValueError("jam_selesai harus setelah jam_mulai")
        return self


class ReservasiPatch(BaseModel):
    status: ReservasiStatus


class UserIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(pattern=r"^[A-Za-z0-9_.-]{3,50}$")
    nama_lengkap: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role_kode: str = Field(min_length=1, max_length=30)


class UserPatch(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nama_lengkap: str | None = Field(default=None, min_length=2, max_length=100)
    role_kode: str | None = Field(default=None, min_length=1, max_length=30)
    aktif: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


# ─── UI ──────────────────────────────────────────────────────────────────────

@ui_router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
@ui_router.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
def admin_page():
    html = (Path(__file__).resolve().parents[1] / "templates" / "admin.html").read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})


# ─── Auth ────────────────────────────────────────────────────────────────────

def _user_payload(user: dict) -> dict:
    return {"id": user["id"], "username": user["username"], "nama_lengkap": user["nama_lengkap"],
            "role_kode": user["role_kode"], "permissions": sorted(user["permissions"])}


@router.post("/login", summary="Login admin, mengembalikan token Bearer")
def login(body: LoginIn, db: Session = Depends(get_db)):
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password("dummy-password")
    with tx(db):
        row = db.execute(
            text("SELECT id, username, nama_lengkap, role_kode, password_hash, aktif, failed_attempts, "
                 "(locked_until IS NOT NULL AND locked_until > now()) AS locked "
                 "FROM admin_users WHERE lower(username) = lower(:u)"), {"u": body.username}).mappings().first()
        if row and row["locked"]:
            raise HTTPException(429, f"Akun dikunci sementara {settings.admin_lock_minutes} menit karena terlalu banyak percobaan gagal")
        ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH)
        if not (row and row["aktif"] and ok):
            if row:
                db.execute(text("SELECT set_config('app.aktor', :a, true)"), {"a": row["username"]})
                db.execute(
                    text("UPDATE admin_users SET failed_attempts = failed_attempts + 1, "
                         "locked_until = CASE WHEN failed_attempts + 1 >= :mx THEN now() + make_interval(mins => :mn) ELSE locked_until END "
                         "WHERE id = :id"),
                    {"id": row["id"], "mx": settings.admin_max_failed_logins, "mn": settings.admin_lock_minutes})
                db.commit()
            raise HTTPException(401, "Username atau password salah")
        token = secrets.token_urlsafe(32)
        db.execute(text("SELECT set_config('app.aktor', :a, true)"), {"a": row["username"]})
        db.execute(text("DELETE FROM admin_sessions WHERE expires_at < now()"))
        db.execute(
            text("INSERT INTO admin_sessions (token_hash, user_id, expires_at) "
                 "VALUES (:h, :u, now() + make_interval(hours => :hrs))"),
            {"h": hash_token(token), "u": row["id"], "hrs": settings.admin_session_hours})
        db.execute(text("UPDATE admin_users SET failed_attempts = 0, locked_until = NULL, last_login = now() WHERE id = :id"),
                   {"id": row["id"]})
        perms = db.execute(text("SELECT permission FROM role_permissions WHERE role_kode = :r"),
                           {"r": row["role_kode"]}).scalars().all()
    return {"token": token, "expires_in": settings.admin_session_hours * 3600,
            "user": {"id": row["id"], "username": row["username"], "nama_lengkap": row["nama_lengkap"],
                     "role_kode": row["role_kode"], "permissions": sorted(perms)}}


@router.post("/logout", summary="Akhiri sesi admin")
def logout(authorization: str = Header(default=""), user: dict = Depends(current_admin), db: Session = Depends(get_db)):
    token = authorization.partition(" ")[2].strip()
    with tx(db):
        db.execute(text("DELETE FROM admin_sessions WHERE token_hash = :h"), {"h": hash_token(token)})
    return {"message": "Berhasil keluar"}


@router.get("/me", summary="Profil & hak akses admin yang sedang login")
def me(user: dict = Depends(current_admin)):
    return _user_payload(user)


@router.get("/hospitals", summary="Daftar RS dari RDF (untuk dropdown); rs_id = kunci federasi")
def hospitals(user: dict = Depends(current_admin)):
    from app.services import hospital_repo
    items = hospital_repo.get_all_hospitals()
    return [{"id": h["id"], "nama": h["nama"], "kabkota": h.get("kabkota"), "kelas": h.get("kelas")}
            for h in sorted(items, key=lambda x: x["id"])]


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/dashboard", summary="Statistik dari view SQL + jumlah RS dari RDF")
def dashboard(user: dict = Depends(require_perm("dashboard.view")), db: Session = Depends(get_db)):
    stats = dict(db.execute(text("SELECT * FROM v_statistik_dashboard")).mappings().one())
    top = _with_names(db.execute(text("SELECT * FROM v_ringkasan_booking_per_rs ORDER BY total DESC, rs_id LIMIT 5")).mappings().all(), "rs_id")
    by_jenis = [dict(r) for r in db.execute(text(
        "SELECT jenis_kamar, COUNT(*) AS total FROM booking_kamar WHERE status <> 'dibatalkan' "
        "GROUP BY jenis_kamar ORDER BY total DESC")).mappings().all()]
    recent = _with_names(db.execute(text(
        "SELECT id, kode_booking, kode_rs, nama_pasien, jenis_kamar, status, created_at "
        "FROM booking_kamar ORDER BY created_at DESC, id DESC LIMIT 6")).mappings().all())
    okupansi = _with_names(db.execute(text(
        "SELECT * FROM v_okupansi_kamar ORDER BY sisa_hari_ini, rs_id LIMIT 6")).mappings().all(), "rs_id")
    try:
        from app.services import hospital_repo
        total_rs = len(hospital_repo.get_all_hospitals())
    except Exception:
        total_rs = None
    return {"stats": stats, "total_rs_rdf": total_rs, "top_rs": top, "by_jenis": by_jenis,
            "recent_booking": recent, "okupansi": okupansi}


# ─── Booking CRUD ────────────────────────────────────────────────────────────

_BOOKING_COLS = ("b.id, b.kode_booking, b.kode_rs, b.nama_pasien, b.no_telp, b.tanggal_masuk, "
                 "b.tanggal_keluar, b.jenis_kamar, b.catatan, b.status, b.created_at, b.updated_at")


@router.get("/bookings", summary="Daftar booking (filter, cari, paginasi)")
def list_bookings(status: str = "", kode_rs: str = "", q: str = "", limit: int = Query(20, ge=1, le=200),
                  offset: int = Query(0, ge=0), user: dict = Depends(require_perm("booking.read")),
                  db: Session = Depends(get_db)):
    p = {"status": status, "rs": kode_rs, "q": q, "ql": _like(q), "limit": limit, "offset": offset}
    where = ("WHERE (:status = '' OR b.status = :status) AND (:rs = '' OR b.kode_rs = :rs) "
             "AND (:q = '' OR b.nama_pasien ILIKE :ql OR b.kode_booking ILIKE :ql OR b.no_telp ILIKE :ql)")
    total = db.execute(text("SELECT COUNT(*) FROM booking_kamar b " + where), p).scalar_one()
    rows = db.execute(text(f"SELECT {_BOOKING_COLS} FROM booking_kamar b {where} "
                           "ORDER BY b.created_at DESC, b.id DESC LIMIT :limit OFFSET :offset"), p).mappings().all()
    return {"total": total, "items": _with_names(rows)}


@router.get("/bookings/{bid}")
def get_booking(bid: int, user: dict = Depends(require_perm("booking.read")), db: Session = Depends(get_db)):
    row = db.execute(text(f"SELECT {_BOOKING_COLS} FROM booking_kamar b WHERE b.id = :id"), {"id": bid}).mappings().first()
    if not row:
        raise HTTPException(404, "Booking tidak ditemukan")
    return _with_names([row])[0]


@router.post("/bookings", status_code=201, summary="Buat booking (lewat sp_buat_booking: cek kuota atomik)")
def create_booking(body: BookingIn, user: dict = Depends(require_perm("booking.write")), db: Session = Depends(get_db)):
    _need_rs(body.kode_rs)
    with tx(db):
        set_actor(db, user)
        new_id = None
        for _ in range(5):
            try:
                with db.begin_nested():
                    new_id = db.execute(
                        text("SELECT sp_buat_booking(:kode,:rs,:pasien,:telp,:masuk,:keluar,:jenis,:catatan)"),
                        dict(kode=_gen("BK"), rs=body.kode_rs, pasien=body.nama_pasien, telp=body.no_telp,
                             masuk=body.tanggal_masuk, keluar=body.tanggal_keluar, jenis=body.jenis_kamar,
                             catatan=body.catatan)).scalar_one()
                break
            except IntegrityError as exc:
                c = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
                if "kode_booking" not in c:
                    raise
        if new_id is None:
            raise HTTPException(409, "Gagal membuat kode booking unik; coba lagi")
        if body.status != "menunggu":
            db.execute(text("UPDATE booking_kamar SET status = :s WHERE id = :id"), {"s": body.status, "id": new_id})
    return get_booking(new_id, user, db)


@router.put("/bookings/{bid}", summary="Ubah booking; kuota dicek ulang bila kamar/tanggal berubah")
def update_booking(bid: int, body: BookingPatch, user: dict = Depends(require_perm("booking.write")),
                   db: Session = Depends(get_db)):
    changes = body.model_dump(exclude_unset=True)
    if "kode_rs" in changes:
        _need_rs(changes["kode_rs"])
    with tx(db):
        set_actor(db, user)
        cur = db.execute(text("SELECT * FROM booking_kamar WHERE id = :id FOR UPDATE"), {"id": bid}).mappings().first()
        if not cur:
            raise HTTPException(404, "Booking tidak ditemukan")
        new = {**dict(cur), **changes}
        if new["tanggal_keluar"] and new["tanggal_keluar"] < new["tanggal_masuk"]:
            raise HTTPException(422, "tanggal_keluar harus >= tanggal_masuk")
        affects = any(k in changes for k in ("kode_rs", "jenis_kamar", "tanggal_masuk", "tanggal_keluar"))
        if new["status"] != "dibatalkan" and affects:
            db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"),
                       {"k": f"booking:{new['kode_rs']}:{new['jenis_kamar']}"})
            sisa = db.execute(text("SELECT fn_sisa_kamar(:rs,:j,:m,:k,:ex)"),
                              {"rs": new["kode_rs"], "j": new["jenis_kamar"], "m": new["tanggal_masuk"],
                               "k": new["tanggal_keluar"], "ex": bid}).scalar_one()
            if sisa <= 0:
                raise HTTPException(409, f"Kamar {new['jenis_kamar']} penuh pada periode yang dipilih")
        db.execute(
            text("UPDATE booking_kamar SET kode_rs=:kode_rs, nama_pasien=:nama_pasien, no_telp=:no_telp, "
                 "tanggal_masuk=:tanggal_masuk, tanggal_keluar=:tanggal_keluar, jenis_kamar=:jenis_kamar, "
                 "catatan=:catatan, status=:status WHERE id=:id"),
            {k: new[k] for k in ("kode_rs", "nama_pasien", "no_telp", "tanggal_masuk", "tanggal_keluar",
                                 "jenis_kamar", "catatan", "status")} | {"id": bid})
    return get_booking(bid, user, db)


@router.delete("/bookings/{bid}", summary="Hapus permanen booking (khusus superadmin)")
def delete_booking(bid: int, user: dict = Depends(require_perm("booking.delete")), db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        db.execute(text("DELETE FROM booking_idempotency WHERE booking_id = :id"), {"id": bid})
        n = db.execute(text("DELETE FROM booking_kamar WHERE id = :id"), {"id": bid}).rowcount
        if not n:
            raise HTTPException(404, "Booking tidak ditemukan")
    return {"message": "Booking dihapus", "id": bid}


# ─── Kuota kamar ─────────────────────────────────────────────────────────────

@router.get("/kuota", summary="Kuota kamar per RS + okupansi hari ini (view v_okupansi_kamar)")
def list_kuota(rs_id: str = "", user: dict = Depends(require_perm("kuota.read")), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT rs_id, jenis_kamar, kapasitas, terisi_hari_ini, sisa_hari_ini FROM v_okupansi_kamar "
                           "WHERE (:rs = '' OR rs_id = :rs) ORDER BY rs_id, jenis_kamar"), {"rs": rs_id}).mappings().all()
    return {"default_kapasitas": 5, "items": _with_names(rows, "rs_id")}


@router.post("/kuota", summary="Tambah/ubah kapasitas kamar (upsert)")
def upsert_kuota(body: KuotaIn, user: dict = Depends(require_perm("kuota.write")), db: Session = Depends(get_db)):
    _need_rs(body.rs_id)
    with tx(db):
        set_actor(db, user)
        db.execute(text("INSERT INTO kuota_kamar (rs_id, jenis_kamar, kapasitas) VALUES (:rs,:j,:k) "
                        "ON CONFLICT (rs_id, jenis_kamar) DO UPDATE SET kapasitas = EXCLUDED.kapasitas"),
                   {"rs": body.rs_id, "j": body.jenis_kamar, "k": body.kapasitas})
    return {"message": "Kuota disimpan", **body.model_dump()}


@router.delete("/kuota/{rs_id}/{jenis_kamar}", summary="Hapus pengaturan kuota (kembali ke default)")
def delete_kuota(rs_id: str, jenis_kamar: str, user: dict = Depends(require_perm("kuota.write")),
                 db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        n = db.execute(text("DELETE FROM kuota_kamar WHERE rs_id = :rs AND jenis_kamar = :j"),
                       {"rs": rs_id, "j": jenis_kamar}).rowcount
        if not n:
            raise HTTPException(404, "Pengaturan kuota tidak ditemukan")
    return {"message": "Kuota dihapus (memakai default)"}


# ─── Jadwal konsultasi ───────────────────────────────────────────────────────

_JADWAL_SQL = ("SELECT id, rs_id, nama_dokter, spesialisasi, hari, to_char(jam_mulai,'HH24:MI') AS jam_mulai, "
               "to_char(jam_selesai,'HH24:MI') AS jam_selesai, kuota_per_sesi, aktif FROM jadwal_konsultasi ")


@router.get("/jadwal", summary="Daftar jadwal konsultasi dokter")
def list_jadwal(rs_id: str = "", user: dict = Depends(require_perm("jadwal.read")), db: Session = Depends(get_db)):
    rows = db.execute(text(_JADWAL_SQL + "WHERE (:rs = '' OR rs_id = :rs) ORDER BY rs_id, hari, jam_mulai"),
                      {"rs": rs_id}).mappings().all()
    return {"items": _with_names(rows, "rs_id")}


@router.post("/jadwal", status_code=201)
def create_jadwal(body: JadwalIn, user: dict = Depends(require_perm("jadwal.write")), db: Session = Depends(get_db)):
    _need_rs(body.rs_id)
    with tx(db):
        set_actor(db, user)
        new_id = db.execute(
            text("INSERT INTO jadwal_konsultasi (rs_id,nama_dokter,spesialisasi,hari,jam_mulai,jam_selesai,kuota_per_sesi,aktif) "
                 "VALUES (:rs_id,:nama_dokter,:spesialisasi,:hari,:jam_mulai,:jam_selesai,:kuota_per_sesi,:aktif) RETURNING id"),
            body.model_dump()).scalar_one()
    return {"message": "Jadwal dibuat", "id": new_id}


@router.put("/jadwal/{jid}")
def update_jadwal(jid: int, body: JadwalIn, user: dict = Depends(require_perm("jadwal.write")),
                  db: Session = Depends(get_db)):
    _need_rs(body.rs_id)
    with tx(db):
        set_actor(db, user)
        n = db.execute(
            text("UPDATE jadwal_konsultasi SET rs_id=:rs_id, nama_dokter=:nama_dokter, spesialisasi=:spesialisasi, "
                 "hari=:hari, jam_mulai=:jam_mulai, jam_selesai=:jam_selesai, kuota_per_sesi=:kuota_per_sesi, "
                 "aktif=:aktif WHERE id=:id"), body.model_dump() | {"id": jid}).rowcount
        if not n:
            raise HTTPException(404, "Jadwal tidak ditemukan")
    return {"message": "Jadwal diperbarui", "id": jid}


@router.delete("/jadwal/{jid}")
def delete_jadwal(jid: int, user: dict = Depends(require_perm("jadwal.write")), db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        n = db.execute(text("DELETE FROM jadwal_konsultasi WHERE id = :id"), {"id": jid}).rowcount
        if not n:
            raise HTTPException(404, "Jadwal tidak ditemukan")
    return {"message": "Jadwal dihapus", "id": jid}


# ─── Reservasi konsultasi ────────────────────────────────────────────────────

@router.get("/reservasi", summary="Daftar reservasi konsultasi")
def list_reservasi(status: str = "", q: str = "", limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0),
                   user: dict = Depends(require_perm("reservasi.read")), db: Session = Depends(get_db)):
    p = {"status": status, "q": q, "ql": _like(q), "limit": limit, "offset": offset}
    where = ("WHERE (:status = '' OR r.status = :status) AND "
             "(:q = '' OR r.nama_pasien ILIKE :ql OR r.kode_reservasi ILIKE :ql OR r.no_telp ILIKE :ql)")
    total = db.execute(text("SELECT COUNT(*) FROM reservasi_konsultasi r " + where), p).scalar_one()
    rows = db.execute(text(
        "SELECT r.id, r.kode_reservasi, r.rs_id, r.nama_pasien, r.no_telp, r.tanggal, r.keluhan, r.status, "
        "r.created_at, j.nama_dokter, j.spesialisasi, to_char(j.jam_mulai,'HH24:MI') AS jam_mulai, "
        "to_char(j.jam_selesai,'HH24:MI') AS jam_selesai "
        "FROM reservasi_konsultasi r JOIN jadwal_konsultasi j ON j.id = r.jadwal_id " + where +
        " ORDER BY r.created_at DESC, r.id DESC LIMIT :limit OFFSET :offset"), p).mappings().all()
    return {"total": total, "items": _with_names(rows, "rs_id")}


@router.put("/reservasi/{rid}")
def update_reservasi(rid: int, body: ReservasiPatch, user: dict = Depends(require_perm("reservasi.write")),
                     db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        n = db.execute(text("UPDATE reservasi_konsultasi SET status = :s WHERE id = :id"),
                       {"s": body.status, "id": rid}).rowcount
        if not n:
            raise HTTPException(404, "Reservasi tidak ditemukan")
    return {"message": "Status diperbarui", "id": rid, "status": body.status}


@router.delete("/reservasi/{rid}")
def delete_reservasi(rid: int, user: dict = Depends(require_perm("reservasi.write")), db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        n = db.execute(text("DELETE FROM reservasi_konsultasi WHERE id = :id"), {"id": rid}).rowcount
        if not n:
            raise HTTPException(404, "Reservasi tidak ditemukan")
    return {"message": "Reservasi dihapus", "id": rid}


# ─── Pengguna & hak akses ────────────────────────────────────────────────────

@router.get("/roles", summary="Role beserta permission-nya")
def list_roles(user: dict = Depends(require_perm("user.manage")), db: Session = Depends(get_db)):
    roles = db.execute(text("SELECT kode, deskripsi FROM roles ORDER BY kode")).mappings().all()
    perms = db.execute(text("SELECT role_kode, permission FROM role_permissions ORDER BY permission")).mappings().all()
    return [{**dict(r), "permissions": [p["permission"] for p in perms if p["role_kode"] == r["kode"]]} for r in roles]


_USER_COLS = "id, username, nama_lengkap, role_kode, aktif, last_login, created_at"


@router.get("/users")
def list_users(user: dict = Depends(require_perm("user.manage")), db: Session = Depends(get_db)):
    return {"items": [dict(r) for r in db.execute(text(f"SELECT {_USER_COLS} FROM admin_users ORDER BY id")).mappings().all()]}


def _check_role(db: Session, role: str):
    if not db.execute(text("SELECT 1 FROM roles WHERE kode = :r"), {"r": role}).first():
        raise HTTPException(422, f"Role '{role}' tidak dikenal")


def _other_superadmins(db: Session, exclude_id: int) -> int:
    return db.execute(text("SELECT COUNT(*) FROM admin_users WHERE role_kode='superadmin' AND aktif AND id <> :id"),
                      {"id": exclude_id}).scalar_one()


@router.post("/users", status_code=201)
def create_user(body: UserIn, user: dict = Depends(require_perm("user.manage")), db: Session = Depends(get_db)):
    with tx(db):
        set_actor(db, user)
        _check_role(db, body.role_kode)
        new_id = db.execute(
            text("INSERT INTO admin_users (username, password_hash, nama_lengkap, role_kode) "
                 "VALUES (:u,:p,:n,:r) RETURNING id"),
            {"u": body.username, "p": hash_password(body.password), "n": body.nama_lengkap, "r": body.role_kode}).scalar_one()
    return {"message": "Pengguna dibuat", "id": new_id}


@router.put("/users/{uid}")
def update_user(uid: int, body: UserPatch, user: dict = Depends(require_perm("user.manage")),
                db: Session = Depends(get_db)):
    ch = body.model_dump(exclude_unset=True)
    with tx(db):
        set_actor(db, user)
        cur = db.execute(text("SELECT id, role_kode, aktif FROM admin_users WHERE id = :id FOR UPDATE"), {"id": uid}).mappings().first()
        if not cur:
            raise HTTPException(404, "Pengguna tidak ditemukan")
        if "role_kode" in ch:
            _check_role(db, ch["role_kode"])
        new_role = ch.get("role_kode", cur["role_kode"])
        new_aktif = ch.get("aktif", cur["aktif"])
        if uid == user["id"] and (not new_aktif or new_role != "superadmin"):
            raise HTTPException(400, "Anda tidak dapat menonaktifkan atau menurunkan role akun sendiri")
        if cur["role_kode"] == "superadmin" and cur["aktif"] and (new_role != "superadmin" or not new_aktif) \
                and _other_superadmins(db, uid) == 0:
            raise HTTPException(400, "Minimal harus ada satu superadmin aktif")
        if "nama_lengkap" in ch:
            db.execute(text("UPDATE admin_users SET nama_lengkap = :v WHERE id = :id"), {"v": ch["nama_lengkap"], "id": uid})
        db.execute(text("UPDATE admin_users SET role_kode = :r, aktif = :a WHERE id = :id"),
                   {"r": new_role, "a": new_aktif, "id": uid})
        if ch.get("password"):
            db.execute(text("UPDATE admin_users SET password_hash = :p, failed_attempts = 0, locked_until = NULL WHERE id = :id"),
                       {"p": hash_password(ch["password"]), "id": uid})
        if uid != user["id"] and (ch.get("password") or "aktif" in ch or "role_kode" in ch):
            db.execute(text("DELETE FROM admin_sessions WHERE user_id = :id"), {"id": uid})  # paksa login ulang
    return {"message": "Pengguna diperbarui", "id": uid}


@router.delete("/users/{uid}")
def delete_user(uid: int, user: dict = Depends(require_perm("user.manage")), db: Session = Depends(get_db)):
    if uid == user["id"]:
        raise HTTPException(400, "Anda tidak dapat menghapus akun sendiri")
    with tx(db):
        set_actor(db, user)
        cur = db.execute(text("SELECT role_kode, aktif FROM admin_users WHERE id = :id FOR UPDATE"), {"id": uid}).mappings().first()
        if not cur:
            raise HTTPException(404, "Pengguna tidak ditemukan")
        if cur["role_kode"] == "superadmin" and cur["aktif"] and _other_superadmins(db, uid) == 0:
            raise HTTPException(400, "Minimal harus ada satu superadmin aktif")
        db.execute(text("DELETE FROM admin_users WHERE id = :id"), {"id": uid})
    return {"message": "Pengguna dihapus", "id": uid}


# ─── Audit log ───────────────────────────────────────────────────────────────

@router.get("/audit", summary="Audit log perubahan data (diisi trigger database)")
def list_audit(tabel: str = "", aktor: str = "", limit: int = Query(30, ge=1, le=200), offset: int = Query(0, ge=0),
               user: dict = Depends(require_perm("audit.read")), db: Session = Depends(get_db)):
    p = {"t": tabel, "a": aktor, "limit": limit, "offset": offset}
    where = "WHERE (:t = '' OR tabel = :t) AND (:a = '' OR aktor = :a)"
    total = db.execute(text("SELECT COUNT(*) FROM audit_log " + where), p).scalar_one()
    rows = db.execute(text("SELECT id, waktu, aktor, aksi, tabel, record_id, data_lama, data_baru FROM audit_log " + where +
                           " ORDER BY id DESC LIMIT :limit OFFSET :offset"), p).mappings().all()
    return {"total": total, "items": [dict(r) for r in rows]}

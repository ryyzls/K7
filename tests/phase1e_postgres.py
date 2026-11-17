"""Explicit opt-in runner via docker exec stdin. Never discovered by unittest.
Host prepends MIGRATION_UP/DOWN strings; no production DDL or patient output.
"""
import datetime
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database.connection import engine, get_db
from app.main import app
from app.config import settings

def fingerprint():
    with engine.connect() as c:
        c.execute(text('SET TRANSACTION READ ONLY'))
        rows = c.execute(text('SELECT row_to_json(b)::text FROM booking_kamar b ORDER BY id')).scalars().all()
        digest = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
        c.rollback()
        return len(rows), digest

before = fingerprint()
e = create_engine(engine.url.set(database='carisehat_test_phase1d'))
with e.connect() as c:
    assert c.execute(text('SELECT current_database()')).scalar() == 'carisehat_test_phase1d'
assert len(inspect(e).get_check_constraints('booking_kamar')) == 2
def migrate(sql):
    raw = e.raw_connection()
    try:
        raw.cursor().execute(sql)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()

if not inspect(e).has_table('booking_idempotency'):
    migrate(MIGRATION_UP)
    migrate(MIGRATION_DOWN)
    migrate(MIGRATION_UP)
    print('PASS migration 002 up/down/up; migration 001 constraints present')
else:
    assert set(inspect(e).get_pk_constraint('booking_idempotency')['constrained_columns']) == {'scope', 'key_hash'}
    print('SKIPPED migration drill on existing ledger; preserved prior synthetic operations')
Session = sessionmaker(bind=e)
def test_db():
    with Session() as s:
        yield s
app.dependency_overrides[get_db] = test_db
settings.booking_access_key = 'phase1e-synthetic-operator'
settings.gemini_api_key = ''
p = dict(kode_rs='rs-001', nama_rs='UNTRUSTED', nama_pasien='SYNTHETIC PHASE1E', no_telp='000', tanggal_masuk=str(datetime.date.today()), jenis_kamar='VIP')
key = uuid.uuid4().hex
def send(k, payload=p):
    c = TestClient(app)
    try:
        return c.post('/api/booking', json=payload, headers={'Idempotency-Key':k})
    finally:
        c.close()

barrier = Barrier(8)
def concurrent(_):
    barrier.wait()
    return send(key)
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(concurrent, range(8)))
assert all(r.status_code == 201 for r in results), [r.status_code for r in results]
ids = {r.json()['id'] for r in results}
assert len(ids) == 1
assert results[0].json()['nama_rs'] == 'Og Hospital'
print('PASS 8 concurrent identical requests -> one canonical booking')
assert send(key, dict(p, catatan='different')).status_code == 409
assert send('short').status_code == 422
assert send('x'*129).status_code == 422
assert send('bad key with spaces').status_code == 422
print('PASS changed payload 409 and key validation 422')
e.dispose()  # New physical connections: no memory cache participates.
assert send(key).json()['id'] in ids
print('PASS replay across connection pool restart')
existing = results[0].json()['kode_booking']
with patch('app.routers.booking._generate_kode', side_effect=[existing, 'BK-T-'+uuid.uuid4().hex[:15]]):
    assert send(uuid.uuid4().hex).status_code == 201
retry_key = uuid.uuid4().hex
with patch('app.routers.booking._generate_kode', return_value=existing):
    assert send(retry_key).status_code == 409
assert send(retry_key).status_code == 201
print('PASS code collision retry, exhaustion rollback and reservation recovery')
original_commit = Session.class_.commit
def lost_response(s):
    original_commit(s)
    from sqlalchemy.exc import OperationalError
    raise OperationalError('synthetic lost acknowledgement', {}, Exception('synthetic'))
lost_key = uuid.uuid4().hex
with patch.object(Session.class_, 'commit', lost_response):
    assert send(lost_key).status_code == 503
recovered = send(lost_key)
assert recovered.status_code == 201
with e.connect() as c:
    n = c.execute(text('SELECT count(*) FROM booking_idempotency WHERE key_hash=:h'), {'h':hashlib.sha256(lost_key.encode()).hexdigest()}).scalar()
    assert n == 1
print('PASS commit success / response failure retry recovers one operation')
c = TestClient(app)
url = '/api/booking/'+existing
assert c.get(url).status_code == 403
assert c.delete(url).status_code == 403
assert c.delete(url, headers={'X-Booking-Key':settings.booking_access_key}).status_code == 200
assert send(key).json()['id'] in ids
assert send(key).json()['status'] == 'dibatalkan'
assert c.post('/api/booking', json=p).status_code == 201
print('PASS operator gate, cancellation, replay retains identity, legacy no-key')
assert fingerprint() == before
print('PASS production count and private in-memory row digest unchanged; count', before[0])

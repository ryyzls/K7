"""Run from root: python -m unittest discover -s tests -p 'test_*.py'. No live DB."""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import datetime
import unittest
from unittest.mock import Mock
from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from app.routers.booking import BookingCreate, buat_booking, require_booking_access
from app.routers.chat import ChatPayload
from app.services.sparql_service import lit, build_search_query

class ValidationTests(unittest.TestCase):
    def payload(self):
        return dict(kode_rs="rs-001", nama_rs="RS O'Connor", nama_pasien="Demo", no_telp="0812", tanggal_masuk=datetime.date.today(), jenis_kamar="VIP")
    def test_booking_valid(self):
        self.assertEqual(BookingCreate(**self.payload()).nama_rs, "RS O'Connor")
    def test_booking_dates(self):
        p=self.payload(); p['tanggal_keluar']=datetime.date.today()-datetime.timedelta(days=1)
        with self.assertRaises(ValidationError): BookingCreate(**p)
    def test_booking_lengths(self):
        for field,length in [('kode_rs',20),('nama_rs',200),('nama_pasien',100),('no_telp',20)]:
            p=self.payload();p[field]='x'*(length+1)
            with self.assertRaises(ValidationError): BookingCreate(**p)
    def test_chat_invalid(self):
        with self.assertRaises(ValidationError): ChatPayload(messages=[{'text':123}])
        self.assertEqual(ChatPayload(text='').text,'')
    def test_query_escape(self):
        self.assertIn('FILTER',build_search_query(q='RS "Demo"'))
        self.assertEqual(lit('a\nb'), '\"a b\"')
    def test_database_failure_rolls_back(self):
        db=Mock(); db.flush.side_effect=OperationalError('query',{},Exception('offline'))
        with self.assertRaises(HTTPException) as ctx: buat_booking(BookingCreate(**self.payload()),db)
        self.assertEqual(ctx.exception.status_code,503);db.rollback.assert_called_once()
    def test_booking_access_denied(self):
        with self.assertRaises(HTTPException) as ctx: require_booking_access('')
        self.assertEqual(ctx.exception.status_code,403)

if __name__=='__main__': unittest.main()

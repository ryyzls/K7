from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

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
    return out


@router.get("/search")
async def search(q: str = "", kelas: str = "", jenis: str = "", kabkota: str = "", layanan: str = "",
                 limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    items = await sp.search_hospitals(q=q, kelas=kelas, jenis=jenis, kabkota=kabkota,
                                      layanan=layanan, limit=limit, offset=offset)
    return {"items": items, "count": len(items)}


@router.get("/filters")
async def filters():
    return await sp.filter_options()

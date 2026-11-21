import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database.connection import engine
from app.database import models  # noqa: F401 — trigger ORM model registration
from app.routers import api, booking, chat, semantic
from app.services.rdf_loader import load_all

log = logging.getLogger("carisehat")


class SPAStaticFiles(StaticFiles):
    """StaticFiles yang mengembalikan index.html untuk rute SPA (mis. /pencarian)."""

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or "." in Path(path).name:
                raise
            return await super().get_response("index.html", scope)
        if response.status_code == 404 and "." not in Path(path).name:
            return await super().get_response("index.html", scope)
        return response


async def _boot():
    n = await load_all()
    log.info("RDF dimuat otomatis: %s file", n)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tabel baru (booking_kamar) tanpa perlu rebuild volume PostgreSQL
    models.Base.metadata.create_all(engine)
    task = asyncio.create_task(_boot()) if settings.auto_load_rdf else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="CariSehat", lifespan=lifespan)


@app.exception_handler(httpx.HTTPError)
async def fuseki_error(request: Request, exc: httpx.HTTPError):
    return JSONResponse({"detail": "Fuseki tidak dapat dihubungi atau query gagal"}, status_code=502)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse({"detail": "Database tidak tersedia; coba lagi nanti"}, status_code=503)


app.include_router(api.router)
app.include_router(booking.router)
app.include_router(chat.router)
app.include_router(semantic.router)
frontend_path = Path(settings.frontend_dir)
public_images = frontend_path / "public" / "images"
if public_images.exists():
    app.mount("/images", StaticFiles(directory=str(public_images), follow_symlink=True), name="public-images")
dist_path = frontend_path / "dist"
serve_dir = str(dist_path) if (dist_path / "index.html").exists() else str(frontend_path)
if Path(serve_dir).exists():  # harus terakhir: melayani "/" dan file statis
    app.mount("/", SPAStaticFiles(directory=serve_dir, html=True, follow_symlink=True), name="frontend")


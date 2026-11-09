import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import api, semantic
from app.services.rdf_loader import load_all

log = logging.getLogger("carisehat")


async def _boot():
    n = await load_all()
    log.info("RDF dimuat otomatis: %s file", n)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_boot()) if settings.auto_load_rdf else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="CariSehat", lifespan=lifespan)


@app.exception_handler(httpx.HTTPError)
async def fuseki_error(request: Request, exc: httpx.HTTPError):
    return JSONResponse({"detail": "Fuseki tidak dapat dihubungi atau query gagal"}, status_code=502)


app.include_router(api.router)
app.include_router(semantic.router)
if Path(settings.frontend_dir).exists():  # harus terakhir: melayani "/" dan file statis
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")

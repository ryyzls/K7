"""Halaman RDFa + OGP, unduhan RDF, dan SPARQL playground (YASGUI) via proxy read-only."""
from pathlib import Path
from urllib.parse import parse_qs

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services import sparql_service as sp
from app.services.sparql_guard import validate_sparql_query, enforce_result_limit

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
FMT = {"rdf": "application/rdf+xml", "ttl": "text/turtle"}

PROXY_TIMEOUT = 10  # detik


@router.get("/rs/{rs_id}.{fmt}")
async def rs_rdf(rs_id: str, fmt: str):
    if fmt not in FMT:
        raise HTTPException(404)
    try:
        uri = sp.rs_uri(rs_id)
    except ValueError:
        raise HTTPException(404)
    return Response(await sp.construct(uri, FMT[fmt]), media_type=FMT[fmt])


@router.get("/rs/{rs_id}", response_class=HTMLResponse)
async def rs_page(request: Request, rs_id: str):
    try:
        h = await sp.get_hospital(rs_id)
    except ValueError:
        h = None
    if not h:
        raise HTTPException(404, "Rumah sakit tidak ditemukan")
    alternatives = []
    try:
        from app.services.alternatives_service import find_alternatives
        alt_res = await find_alternatives(rs_id, limit=4)
        alternatives = alt_res.get("alternatives", [])
    except Exception:
        alternatives = []
    return templates.TemplateResponse(request, "rs_detail.html", {
        "h": h,
        "base": settings.base_uri,
        "onto": settings.onto_ns,
        "alternatives": alternatives,
    })


@router.get("/data/hospitals.rdf")
async def dump_rdf():
    return Response(await sp.construct(None, FMT["rdf"]), media_type=FMT["rdf"])


@router.get("/sparql", response_class=HTMLResponse)
async def sparql_page(request: Request):
    return templates.TemplateResponse(request, "sparql.html", {})


@router.api_route("/sparql/query", methods=["GET", "POST"])
async def sparql_proxy(request: Request):
    """Proxy SPARQL read-only ke Fuseki dengan SPARQL Guard keamanan."""
    if request.method == "GET":
        query = request.query_params.get("query", "")
    else:
        # Batasi ukuran request payload sebelum decode (dengan atau tanpa Content-Length)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
            except ValueError:
                raise HTTPException(400, "Content-Length tidak valid")
            if size < 0:
                raise HTTPException(400, "Content-Length tidak valid")
            if size > 100 * 1024:
                raise HTTPException(413, "Ukuran request payload terlalu besar (maks 100 KB)")
        body_bytes = bytearray()
        async for chunk in request.stream():
            body_bytes.extend(chunk)
            if len(body_bytes) > 100 * 1024:
                raise HTTPException(413, "Ukuran request payload terlalu besar (maks 100 KB)")
        body = body_bytes.decode("utf-8", errors="replace")
        ctype = request.headers.get("content-type", "")
        query = body if ctype.startswith("application/sparql-query") else parse_qs(body).get("query", [""])[0]

    if not query:
        raise HTTPException(400, "parameter query kosong")

    # --- SPARQL Guard: validasi keamanan (AST parser + tokenizer) ---
    error = validate_sparql_query(query)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # --- Enforce result limit (maks 1000 baris) ---
    query = enforce_result_limit(query)

    # --- Teruskan ke Fuseki dengan timeout ketat ---
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as c:
            r = await c.post(
                f"{settings.fuseki_url}/query",
                data={"query": query},
                headers={"Accept": request.headers.get("accept", "application/sparql-results+json")},
            )
        return Response(r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))
    except httpx.TimeoutException:
        raise HTTPException(504, "Query SPARQL melebihi batas waktu (timeout 10 detik)")
    except httpx.ConnectError:
        raise HTTPException(503, "Layanan basis data semantik (Fuseki) tidak dapat dijangkau")

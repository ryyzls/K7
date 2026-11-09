"""Halaman RDFa + OGP, unduhan RDF, dan SPARQL playground (YASGUI) via proxy read-only."""
from pathlib import Path
from urllib.parse import parse_qs

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services import sparql_service as sp

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
FMT = {"rdf": "application/rdf+xml", "ttl": "text/turtle"}


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
    return templates.TemplateResponse(request, "rs_detail.html", {"h": h, "base": settings.base_uri, "onto": settings.onto_ns})


@router.get("/data/hospitals.rdf")
async def dump_rdf():
    return Response(await sp.construct(None, FMT["rdf"]), media_type=FMT["rdf"])


@router.get("/sparql", response_class=HTMLResponse)
async def sparql_page(request: Request):
    return templates.TemplateResponse(request, "sparql.html", {})


@router.api_route("/sparql/query", methods=["GET", "POST"])
async def sparql_proxy(request: Request):
    """Teruskan hanya ke endpoint /query Fuseki (read-only; update ditolak Fuseki)."""
    if request.method == "GET":
        query = request.query_params.get("query", "")
    else:
        body = (await request.body()).decode()
        ctype = request.headers.get("content-type", "")
        query = body if ctype.startswith("application/sparql-query") else parse_qs(body).get("query", [""])[0]
    if not query:
        raise HTTPException(400, "parameter query kosong")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{settings.fuseki_url}/query", data={"query": query},
                         headers={"Accept": request.headers.get("accept", "application/sparql-results+json")})
    return Response(r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))

"""Memuat file RDF (semantic/rdf/*.ttl|*.rdf) ke Fuseki. Otomatis saat start jika dataset kosong.
Muat ulang paksa:  docker compose exec backend python -m app.services.rdf_loader --force"""
import asyncio
import pathlib
import sys

import httpx

from app.config import settings

TYPES = {".ttl": "text/turtle", ".rdf": "application/rdf+xml"}
JSON = {"Accept": "application/sparql-results+json"}


async def _wait(c: httpx.AsyncClient, tries: int = 30) -> bool:
    for _ in range(tries):
        try:
            if (await c.post(f"{settings.fuseki_url}/query", data={"query": "ASK {}"}, headers=JSON)).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        await asyncio.sleep(2)
    return False


async def load_all(force: bool = False) -> int:
    files = [f for f in sorted(pathlib.Path(settings.rdf_dir).glob("*")) if f.suffix in TYPES]
    async with httpx.AsyncClient(timeout=120) as c:
        if not await _wait(c):
            print("Fuseki tidak merespons; pemuatan RDF dilewati")
            return 0
        if force:
            await c.post(f"{settings.fuseki_url}/update", data={"update": "CLEAR DEFAULT"})
        else:
            r = await c.post(f"{settings.fuseki_url}/query", data={"query": "ASK { ?s ?p ?o }"}, headers=JSON)
            if r.json().get("boolean"):
                return 0
        for f in files:
            r = await c.post(f"{settings.fuseki_url}/data", content=f.read_bytes(), headers={"Content-Type": TYPES[f.suffix]})
            r.raise_for_status()
    return len(files)


if __name__ == "__main__":
    print("file dimuat:", asyncio.run(load_all(force="--force" in sys.argv)))

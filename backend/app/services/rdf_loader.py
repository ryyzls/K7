"""Memuat file RDF (semantic/rdf/*.ttl|*.rdf) ke Fuseki. Otomatis saat start jika dataset kosong.
Muat ulang paksa:  docker compose exec backend python -m app.services.rdf_loader --force"""
import asyncio
import pathlib
import sys

import httpx
from rdflib import Graph

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
    root = pathlib.Path(settings.rdf_dir).parent
    named = {
        'http://carisehat.id/graph/sirs/2026-11-19': root / 'sirs/services-reviewed.ttl',
        'http://carisehat.id/graph/enrichment/2026-11-20': root / 'named_graphs/carisehat-enrichment-freeze.ttl',
        'http://carisehat.id/graph/search/facilities/2026-11-25': root / 'search/facilities-evidence.ttl',
        'http://carisehat.id/graph/search/concepts/2026-11-25': root / 'search/search-concepts.ttl',
    }
    # Parse all inputs before any write; do not leave a partially loaded deployment.
    default = Graph()
    for f in files:
        default.parse(f, format='turtle' if f.suffix == '.ttl' else 'xml')
    if not files:
        raise RuntimeError('Dataset RDF default tidak ditemukan')
    for path in named.values():
        Graph().parse(path, format='turtle')
    loaded = 0
    async with httpx.AsyncClient(timeout=120) as c:
        if not await _wait(c):
            print("Fuseki tidak merespons; pemuatan RDF dilewati")
            return 0
        r = await c.post(f"{settings.fuseki_url}/query", data={"query": "ASK { ?s ?p ?o }"}, headers=JSON)
        r.raise_for_status()
        if force or not r.json().get('boolean'):
            # A single Graph Store PUT is atomic; never CLEAR before an upload.
            r = await c.put(f"{settings.fuseki_url}/data", params={'default': ''},
                            content=default.serialize(format='turtle').encode(), headers={'Content-Type': 'text/turtle'})
            r.raise_for_status()
            loaded += len(files)
        for uri, path in named.items():
            r = await c.post(f"{settings.fuseki_url}/query", data={'query': f'ASK {{ GRAPH <{uri}> {{ ?s ?p ?o }} }}'}, headers=JSON)
            r.raise_for_status()
            # Existing named graphs require an explicit backed-up rollout, even with --force.
            if r.json().get('boolean'):
                continue
            r = await c.put(f"{settings.fuseki_url}/data", params={'graph': uri},
                            content=path.read_bytes(), headers={'Content-Type': 'text/turtle'})
            r.raise_for_status()
            loaded += 1
    return loaded


if __name__ == "__main__":
    print("file dimuat:", asyncio.run(load_all(force="--force" in sys.argv)))

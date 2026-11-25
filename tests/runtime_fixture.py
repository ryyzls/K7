"""Isolated runtime: SQLite memory + RDFLib, NOT PostgreSQL/Fuseki."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.update(DATABASE_URL="sqlite://", AUTO_LOAD_RDF="false", FRONTEND_DIR=str(ROOT / "frontend"), GEMINI_API_KEY="", BOOKING_ACCESS_KEY="test-operator-only", GOOGLE_MAPS_API_KEY="")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from rdflib import Dataset, URIRef
from app.config import settings
if hasattr(settings, "gemini_api_key"):
    settings.gemini_api_key = ""
settings.booking_access_key = "test-operator-only"
settings.auto_load_rdf = False
from app.main import app
from app.database.connection import Base, get_db
from app.services import sparql_service as sp
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
def db():
    with Session() as session:
        yield session
app.dependency_overrides[get_db] = db
# Lifespan still executes the real application initialization against SQLite only.
graph = Dataset()
for path in (ROOT / "semantic/rdf").glob("*.ttl"):
    graph.default_graph.parse(path, format="turtle")
from app.services.sirs import GRAPH_URI
graph.graph(URIRef(GRAPH_URI)).parse(ROOT / 'semantic/sirs/services-reviewed.ttl', format='turtle')
graph.graph(URIRef('http://carisehat.id/graph/enrichment/2026-11-20')).parse(ROOT / 'semantic/named_graphs/carisehat-enrichment-freeze.ttl', format='turtle')
graph.graph(URIRef('http://carisehat.id/graph/search/facilities/2026-11-25')).parse(ROOT / 'semantic/search/facilities-evidence.ttl', format='turtle')
graph.graph(URIRef('http://carisehat.id/graph/search/concepts/2026-11-25')).parse(ROOT / 'semantic/search/search-concepts.ttl', format='turtle')
async def select(query):
    return [{str(k): str(v) for k,v in row.asdict().items()} for row in graph.query(sp.PREFIXES + query)]
async def construct(uri, accept):
    return graph.query(sp.PREFIXES + sp.build_construct_query(uri)).graph.serialize(format="xml" if accept == "application/rdf+xml" else "turtle")
sp.select = select
sp.construct = construct
# Local protocol adapter for public SPARQL proxy tests. This is RDFLib, not Jena.
from fastapi import APIRouter, Request, Response
from urllib.parse import parse_qs
fixture_router = APIRouter()
@fixture_router.post('/_fixture-fuseki/query')
async def fixture_query(request: Request):
    query = parse_qs((await request.body()).decode()).get('query', [''])[0]
    result = graph.query(query)
    if result.type in ('SELECT', 'ASK'):
        return Response(result.serialize(format='json'), media_type='application/sparql-results+json')
    accept = request.headers.get('accept', '')
    return Response(result.graph.serialize(format='xml' if 'rdf+xml' in accept else 'turtle'),
                    media_type='application/rdf+xml' if 'rdf+xml' in accept else 'text/turtle')
app.router.routes[0:0] = fixture_router.routes
settings.fuseki_url = 'http://127.0.0.1:8765/_fixture-fuseki'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)

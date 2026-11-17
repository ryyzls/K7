"""Isolated runtime: SQLite memory + RDFLib, NOT PostgreSQL/Fuseki."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.update(DATABASE_URL="sqlite://", AUTO_LOAD_RDF="false", FRONTEND_DIR=str(ROOT / "frontend"), GEMINI_API_KEY="", BOOKING_ACCESS_KEY="test-operator-only", GOOGLE_MAPS_API_KEY="")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from rdflib import Graph
from app.config import settings
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
graph = Graph()
for path in (ROOT / "semantic/rdf").glob("*.ttl"):
    graph.parse(path, format="turtle")
async def select(query):
    return [{str(k): str(v) for k,v in row.asdict().items()} for row in graph.query(sp.PREFIXES + query)]
async def construct(uri, accept):
    query = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ <{uri}> }} ?s ?p ?o }}" if uri else "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    return graph.query(query).graph.serialize(format="xml" if accept == "application/rdf+xml" else "turtle")
sp.select = select
sp.construct = construct
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)

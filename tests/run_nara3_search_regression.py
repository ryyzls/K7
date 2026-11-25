"""Run the unchanged 210 search scenarios through ASGI + existing RDF graphs.
Output paths differ so earlier live-Fuseki evidence is preserved.
"""
import sys,json,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import runtime_fixture as fixture
from fastapi.testclient import TestClient
import httpx
source=(ROOT/'tests/test_hybrid_search_200.py').read_text(encoding='utf8').replace('search_test_results_200','NARA_3_SEARCH_REGRESSION')
ns={'__name__':'isolated_search_regression','__file__':str(ROOT/'tests/test_hybrid_search_200.py')}
exec(compile(source,str(ROOT/'tests/test_hybrid_search_200.py'),'exec'),ns)
def post(url, data, **kwargs):
    # Only the ground-truth schedule SELECT is redirected to the same existing RDF dataset.
    assert url=='http://127.0.0.1:3030/hospital/query'
    return httpx.Response(200,content=fixture.graph.query(data['query']).serialize(format='json'))
client=TestClient(fixture.app)
ns['httpx']=types.SimpleNamespace(post=post,Client=lambda **kwargs:client)
summary,failed=ns['run_suite']()
(ROOT/'docs/NARA_3_SEARCH_REGRESSION_SUMMARY.json').write_text(json.dumps({'environment':'ASGI/RDFLib; original 210 scenarios','summary':summary,'failures':failed},indent=2),encoding='utf8')

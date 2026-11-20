"""Exercise reversible Graph Store operations using HTTP mock, never production."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from rdflib import Graph, URIRef
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import deploy_sirs_graph as migration


class MigrationTests(unittest.TestCase):
    def test_deploy_rollback_and_drift_guard(self):
        default = b'<urn:old> <urn:predicate> <urn:preserved> .'
        state = {'named':None}
        candidate = Graph().parse(data='<urn:new> <urn:predicate> <urn:value> .',format='turtle')
        def handler(request):
            if 'default' in request.url.params:
                self.assertEqual(request.method,'GET')
                return httpx.Response(200,content=default)
            self.assertEqual(request.url.params['graph'],migration.GRAPH)
            if request.method=='GET':
                return httpx.Response(404 if state['named'] is None else 200,content=state['named'] or b'')
            if request.method=='PUT':
                state['named']=request.content
                return httpx.Response(201)
            if request.method=='DELETE':
                state['named']=None
                return httpx.Response(204)
            raise AssertionError(request.method)
        original_client=httpx.Client
        def client(**kwargs):
            return original_client(transport=httpx.MockTransport(handler),**kwargs)
        with tempfile.TemporaryDirectory() as tmp, patch.object(migration,'prepare',return_value=(candidate,{})), patch.object(migration.httpx,'Client',side_effect=client):
            migration.deploy('http://isolated.test/hospital',tmp)
            self.assertEqual((Path(tmp)/'default-before.ttl').read_bytes(),default)
            state['named'] += b'\n<urn:other> <urn:predicate> <urn:value> .'
            with self.assertRaisesRegex(AssertionError,'Graph changed'):
                migration.deploy('http://isolated.test/hospital',tmp,rollback=True)
            state['named']=(Path(tmp)/'deployed.ttl').read_bytes()
            migration.deploy('http://isolated.test/hospital',tmp,rollback=True)
            self.assertIsNone(state['named'])


if __name__=='__main__':
    unittest.main()

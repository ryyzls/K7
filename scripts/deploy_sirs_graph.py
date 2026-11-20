"""Explicit named-graph deployment/rollback. Never clears the default graph."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx
from rdflib import Graph
from rdflib.compare import isomorphic
from integrate_sirs import ROOT, GRAPH, prepare


def deploy(base, backup_dir, rollback=False):
    backup_dir = Path(backup_dir)
    manifest_path = backup_dir / 'migration.json'
    with httpx.Client(timeout=120) as client:
        def read(params):
            response = client.get(base+'/data',params=params,headers={'Accept':'text/turtle'})
            return response
        def default_graph():
            response = read({'default':''}); response.raise_for_status()
            return response.content, Graph().parse(data=response.text,format='turtle')
        if rollback:
            manifest = json.loads(manifest_path.read_text())
            assert manifest['graph'] == GRAPH and manifest['base'] == base
            current = read({'graph':GRAPH})
            current.raise_for_status()
            prepared = Graph().parse(backup_dir/'deployed.ttl')
            assert isomorphic(prepared,Graph().parse(data=current.text,format='turtle')), 'Graph changed; refusing rollback'
            _, before = default_graph()
            response = client.delete(base+'/data',params={'graph':GRAPH})
            response.raise_for_status()
            _, after = default_graph()
            assert isomorphic(before,after), 'Default graph changed'
            print('ROLLBACK PASS: only newly created SIRS graph removed; default unchanged')
            return
        graph, report = prepare()
        assert not manifest_path.exists(), 'Use a new backup directory'
        existing = read({'graph':GRAPH})
        assert existing.status_code == 404, 'Target graph exists or access failed; refusing overwrite'
        raw, before = default_graph()
        backup_dir.mkdir(parents=True,exist_ok=True)
        (backup_dir/'default-before.ttl').write_bytes(raw)
        assert isomorphic(before,Graph().parse(backup_dir/'default-before.ttl'))
        deployed = graph.serialize(format='turtle').encode()
        (backup_dir/'deployed.ttl').write_bytes(deployed)
        manifest = {'base':base,'graph':GRAPH,'created_at':datetime.now(timezone.utc).isoformat(),
                    'default_triples':len(before),'default_sha256':hashlib.sha256(raw).hexdigest(),
                    'deployed_triples':len(graph),'previous_graph':'absent','status':'BACKED_UP'}
        manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        response = client.put(base+'/data',params={'graph':GRAPH},content=deployed,headers={'Content-Type':'text/turtle'})
        response.raise_for_status()
        result = read({'graph':GRAPH}); result.raise_for_status()
        assert isomorphic(graph,Graph().parse(data=result.text,format='turtle'))
        _, after = default_graph()
        assert isomorphic(before,after), 'Default graph changed'
        manifest['status']='VERIFIED'
        manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:3030/hospital')
    parser.add_argument('--backup-dir',required=True)
    parser.add_argument('--rollback',action='store_true')
    args=parser.parse_args()
    deploy(args.base,args.backup_dir,args.rollback)

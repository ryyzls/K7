"""Add search evidence to a dedicated graph. Never clears or replaces an existing graph."""
import argparse
from pathlib import Path
import httpx
from rdflib import Graph
from rdflib.compare import isomorphic
URI='http://carisehat.id/graph/search/facilities/2026-11-25'
def main():
 p=argparse.ArgumentParser();p.add_argument('--endpoint',default='http://127.0.0.1:3030/hospital');p.add_argument('--apply',action='store_true');a=p.parse_args()
 src=Path(__file__).resolve().parents[1]/'semantic/search/facilities-evidence.ttl';g=Graph().parse(src)
 with httpx.Client(timeout=30) as c:
  r=c.post(a.endpoint+'/query',data={'query':f'CONSTRUCT {{?s ?p ?o}} WHERE {{GRAPH <{URI}> {{?s ?p ?o}}}}'},headers={'Accept':'text/turtle'});r.raise_for_status();existing=Graph().parse(data=r.text,format='turtle')
  if len(existing):
   if not isomorphic(g,existing):raise SystemExit('STOP: existing graph differs; no overwrite allowed')
   print('Already installed; no mutation');return
  if not a.apply:print('Validated',len(g),'triples; use --apply to install new graph');return
  r=c.post(a.endpoint+'/data',params={'graph':URI},content=src.read_bytes(),headers={'Content-Type':'text/turtle'});r.raise_for_status();print('Installed new graph',URI,len(g),'triples',r.status_code)
if __name__=='__main__':main()

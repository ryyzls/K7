import rdflib

g = rdflib.Graph()
g.parse('semantic/rdf/hospitals-sumut.ttl', format='turtle')

target_ids = ['rs-171', 'rs-170', 'rs-172', 'rs-001', 'rs-008', 'rs-007']
for rs_id in target_ids:
    subj = rdflib.URIRef(f"http://localhost:8000/rs/{rs_id}")
    print(f"\n--- {rs_id} ---")
    for p, o in g.predicate_objects(subj):
        p_name = str(p).split('/')[-1].split('#')[-1]
        print(f"  {p_name}: {o}")

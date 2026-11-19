import re
import difflib
import rdflib
from rdflib import RDF, Namespace

g = rdflib.Graph()
g.parse('C:/K7/semantic/rdf/hospitals-sumut.ttl', format='turtle')
HF = Namespace('http://carisehat.id/ontology/')
SCHEMA = Namespace('https://schema.org/')

all_rs = []
for s in g.subjects(RDF.type, HF.RumahSakit):
    rs_id = str(s).rsplit('/', 1)[-1]
    name = str(g.value(s, SCHEMA.name))
    alamat = str(g.value(s, HF.alamat) or '')
    kabkota_node = g.value(s, HF.beradaDiKabupatenKota)
    kabkota = str(g.value(kabkota_node, rdflib.RDFS.label) or '') if kabkota_node else ''
    all_rs.append({'id': rs_id, 'nama': name, 'alamat': alamat, 'kabkota': kabkota})

print(f'Loaded {len(all_rs)} hospitals.')

import asyncio
import httpx

async def test_sparql():
    q = """PREFIX cs: <http://carisehat.id/ontology/sirs/>
PREFIX hf: <http://carisehat.id/ontology/>
PREFIX schema: <https://schema.org/>

SELECT ?rs ?kodeKemenkes ?direktur ?kepemilikan ?statusIgd24Jam ?email
WHERE {
  GRAPH <http://carisehat.id/graph/enrichment/2026-11-20> {
    ?rs cs:kodeRegistrasiKemenkes ?kodeKemenkes .
    OPTIONAL { ?rs schema:director ?direktur }
    OPTIONAL { ?rs hf:kepemilikanSirs ?kepemilikan }
    OPTIONAL { ?rs hf:statusIgd24Jam ?statusIgd24Jam }
    OPTIONAL { ?rs schema:email ?email }
  }
}
LIMIT 5
"""
    async with httpx.AsyncClient() as c:
        r = await c.post("http://localhost:3030/hospital/query", data={"query": q}, headers={"Accept": "application/sparql-results+json"})
        print("Status:", r.status_code)
        for b in r.json()["results"]["bindings"]:
            print({k: v["value"] for k, v in b.items()})

asyncio.run(test_sparql())

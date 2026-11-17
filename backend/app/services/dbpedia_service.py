"""Layanan integrasi DBpedia SPARQL Endpoint (External Linked Data).
Memenuhi syarat Tugas Besar Web Semantik: integrasi dataset lokal dengan dataset eksternal.
"""
import logging
import re
import httpx

log = logging.getLogger("carisehat.dbpedia")

DBPEDIA_SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

# Pemetaan nama kabupaten/kota ke entitas DBpedia resmi
DBPEDIA_CITY_MAPPING = {
    "kota medan": "Medan",
    "medan": "Medan",
    "kota pematang siantar": "Pematangsiantar",
    "kota padang sidempuan": "Padang_Sidempuan",
    "kota tanjung balai": "Tanjungbalai",
    "kab. toba samosir": "Toba_Regency",
    "kota binjai": "Binjai",
    "binjai": "Binjai",
    "kota pematangsiantar": "Pematangsiantar",
    "pematangsiantar": "Pematangsiantar",
    "kota tebing tinggi": "Tebing_Tinggi",
    "tebing tinggi": "Tebing_Tinggi",
    "kota tanjungbalai": "Tanjungbalai",
    "tanjungbalai": "Tanjungbalai",
    "kota sibolga": "Sibolga",
    "sibolga": "Sibolga",
    "kota padangsidimpuan": "Padang_Sidempuan",
    "padangsidimpuan": "Padang_Sidempuan",
    "kota gunungsitoli": "Gunungsitoli",
    "gunungsitoli": "Gunungsitoli",
    "deli serdang": "Deli_Serdang_Regency",
    "kab. deli serdang": "Deli_Serdang_Regency",
    "karo": "Karo_Regency",
    "kab. karo": "Karo_Regency",
    "simalungun": "Simalungun_Regency",
    "kab. simalungun": "Simalungun_Regency",
    "asahan": "Asahan_Regency",
    "kab. asahan": "Asahan_Regency",
    "tapanuli utara": "North_Tapanuli_Regency",
    "kab. tapanuli utara": "North_Tapanuli_Regency",
    "toba": "Toba_Regency",
    "sumatera utara": "North_Sumatra"
}


async def get_dbpedia_info(nama_wilayah: str) -> dict:
    """Ambil ringkasan wilayah, populasi, dan gambar dari DBpedia SPARQL."""
    clean_name = nama_wilayah.lower().strip()
    resource_name = DBPEDIA_CITY_MAPPING.get(clean_name)
    
    if not resource_name:
        # Fallback jika belum di-mapping
        formatted = nama_wilayah.replace("Kota ", "").replace("Kab. ", "").strip().replace(" ", "_")
        resource_name = f"{formatted}_Regency"

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", resource_name):
        return {"status": "unavailable", "dbpedia_resource": None}

    query = f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?abstract ?thumb ?population WHERE {{
      OPTIONAL {{ dbr:{resource_name} dbo:abstract ?abstract . FILTER(lang(?abstract) = 'id' || lang(?abstract) = 'en') }}
      OPTIONAL {{ dbr:{resource_name} dbo:thumbnail ?thumb }}
      OPTIONAL {{ dbr:{resource_name} dbo:populationTotal ?population }}
    }} LIMIT 1
    """

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                DBPEDIA_SPARQL_ENDPOINT,
                params={"query": query, "format": "application/sparql-results+json"}
            )
            if resp.status_code == 200:
                bindings = resp.json().get("results", {}).get("bindings", [])
                if bindings and any(bindings[0].get(k) for k in ("abstract", "thumb", "population")):
                    b = bindings[0]
                    return {
                        "status": "ok",
                        "dbpedia_resource": f"http://dbpedia.org/resource/{resource_name}",
                        "abstract": b.get("abstract", {}).get("value"),
                        "thumbnail": b.get("thumb", {}).get("value"),
                        "population": b.get("population", {}).get("value")
                    }
    except Exception as e:
        log.warning("Gagal query DBpedia untuk %s: %s", nama_wilayah, e)

    return {"status": "unavailable", "dbpedia_resource": None}

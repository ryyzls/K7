#!/usr/bin/env python3
"""Deploy or rollback the Enrichment Freeze named graph in Apache Jena Fuseki.

Target Named Graph: http://carisehat.id/graph/enrichment/2026-11-20
Preserves default graph and SIRS graph.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx
from rdflib import Graph
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import settings

GRAPH_URI = "http://carisehat.id/graph/enrichment/2026-11-20"
TTL_PATH = ROOT / "semantic" / "named_graphs" / "carisehat-enrichment-freeze.ttl"
BACKUP_DIR = ROOT / "semantic" / "backups" / "enrichment_freeze_20261120"


def deploy(rollback=False):
    base = settings.fuseki_url
    manifest_path = BACKUP_DIR / "deployment_manifest.json"

    with httpx.Client(timeout=120) as client:
        def read(params):
            return client.get(f"{base}/data", params=params, headers={"Accept": "text/turtle"})

        def get_default_graph():
            res = read({"default": ""})
            res.raise_for_status()
            return res.content, Graph().parse(data=res.text, format="turtle")

        if rollback:
            if not manifest_path.exists():
                raise FileNotFoundError(f"Manifest not found: {manifest_path}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            print(f"Rolling back named graph: {manifest['graph']}")

            _, before = get_default_graph()
            res = client.delete(f"{base}/data", params={"graph": GRAPH_URI})
            res.raise_for_status()
            _, after = get_default_graph()
            assert isomorphic(before, after), "Default graph was modified during rollback!"
            print(f"ROLLBACK SUCCESS: {GRAPH_URI} removed, default graph unchanged.")
            return

        # DEPLOY
        print(f"Deploying {TTL_PATH} to named graph {GRAPH_URI} at {base}...")
        raw_default, default_before = get_default_graph()

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        (BACKUP_DIR / "default-before.ttl").write_bytes(raw_default)

        graph_to_deploy = Graph().parse(str(TTL_PATH), format="turtle")
        deployed_bytes = graph_to_deploy.serialize(format="turtle").encode("utf-8")
        (BACKUP_DIR / "deployed.ttl").write_bytes(deployed_bytes)

        manifest = {
            "base": base,
            "graph": GRAPH_URI,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "default_triples": len(default_before),
            "default_sha256": hashlib.sha256(raw_default).hexdigest(),
            "deployed_triples": len(graph_to_deploy),
            "source_file": str(TTL_PATH),
            "status": "BACKED_UP"
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # PUT named graph
        put_res = client.put(
            f"{base}/data",
            params={"graph": GRAPH_URI},
            content=deployed_bytes,
            headers={"Content-Type": "text/turtle; charset=utf-8"}
        )
        put_res.raise_for_status()

        # Verify deployment
        verify_res = read({"graph": GRAPH_URI})
        verify_res.raise_for_status()
        deployed_in_fuseki = Graph().parse(data=verify_res.text, format="turtle")
        assert len(deployed_in_fuseki) == len(graph_to_deploy), f"Triple count mismatch: {len(deployed_in_fuseki)} != {len(graph_to_deploy)}"

        # Verify default graph untouched
        _, default_after = get_default_graph()
        assert isomorphic(default_before, default_after), "Default graph was modified during deployment!"

        manifest["status"] = "VERIFIED"
        manifest["verified_fuseki_triples"] = len(deployed_in_fuseki)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        print("DEPLOYMENT SUCCESS!")
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true", help="Rollback named graph")
    args = parser.parse_args()
    deploy(rollback=args.rollback)

"""Held-out V3 suite (54 independent scenarios) for NARA 3.0 finalization."""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from test_nara3 import oracle_ids  # noqa: E402
from app.services.chatbot.engine import process  # noqa: E402


def verify_subset(r, allowed):
    actual = {h["id"] for h in r.get("hospitals", [])}
    return bool(actual) and actual <= allowed and r.get("total") == len(allowed)


CASES = [
    # 1. Double typos & informal (5)
    ("V3-01", "typo", "Herminah Medann", lambda r, s: [h["id"] for h in r["hospitals"]] == ["rs-125"]),
    ("V3-02", "typo", "Adam Maliik", lambda r, s: [h["id"] for h in r["hospitals"]] == ["rs-171"]),
    ("V3-03", "typo", "rs klas b d medan", lambda r, s: verify_subset(r, oracle_ids("Kota Medan", {"B"}))),
    ("V3-04", "typo", "poli jantng di siantarr", lambda r, s: verify_subset(r, oracle_ids("Kota Pematang Siantar", service="Jantung dan Pembuluh Darah"))),
    ("V3-05", "typo", "rs d binjai yg ada picu", lambda r, s: verify_subset(r, oracle_ids("Kota Binjai", facility="PICU"))),

    # 2. Very short queries (5)
    ("V3-06", "short", "IGD", lambda r, s: bool(r["hospitals"]) and r["kind"] == "hospital_list"),
    ("V3-07", "short", "NICU", lambda r, s: verify_subset(r, oracle_ids(facility="NICU"))),
    ("V3-08", "short", "saraf", lambda r, s: verify_subset(r, oracle_ids(service="Saraf"))),
    ("V3-09", "short", "PICU", lambda r, s: verify_subset(r, oracle_ids(facility="PICU"))),
    ("V3-10", "short", "CT Scan", lambda r, s: verify_subset(r, oracle_ids(facility="CT Scan"))),

    # 3. Long natural sentences (4)
    ("V3-11", "long", "Saya orang tua yang perlu cari RS kelas B di kota Medan dengan NICU",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", {"B"}, facility="NICU"))),
    ("V3-12", "long", "Tolong rekomendasikan rumah sakit di Kota Binjai yang memiliki layanan mata",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai", service="Mata"))),
    ("V3-13", "long", "Mohon bantuannya mencarikan rumah sakit kelas C di Deli Serdang dengan fasilitas ICU",
     lambda r, s: verify_subset(r, oracle_ids("Kab. Deli Serdang", {"C"}, facility="ICU"))),
    ("V3-14", "long", "Saya sedang mencari informasi rumah sakit umum di Kota Pematang Siantar yang memiliki CT Scan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Pematang Siantar", facility="CT Scan"))),

    # 4. Sinonim medis (5)
    ("V3-15", "synonym", "RS dengan dokter kandungan di Medan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", service="Obstetri dan Ginekologi"))),
    ("V3-16", "synonym", "RS untuk bersalin di Binjai",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai", service="Obstetri dan Ginekologi"))),
    ("V3-17", "synonym", "Cari RS cuci darah di Medan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", facility="Hemodialisis"))),
    ("V3-18", "synonym", "RS dengan dokter saraf di Siantar",
     lambda r, s: verify_subset(r, oracle_ids("Kota Pematang Siantar", service="Saraf"))),
    ("V3-19", "synonym", "Poli THT di Medan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", service="Telinga Hidung Tenggorok - Bedah Kepala Leher"))),

    # 5. Negation & exclusion (4)
    ("V3-20", "negation", "RS di Medan bukan kelas A",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan") - oracle_ids(classes={"A"}))),
    ("V3-21", "negation", "RS di Binjai selain kelas C",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai") - oracle_ids(classes={"C"}))),
    ("V3-22", "negation", "RS tanpa ICU di Binjai",
     lambda r, s: r["kind"] == "clarification" and not r["hospitals"]),
    ("V3-23", "negation", "RS tanpa CT Scan di Medan",
     lambda r, s: r["kind"] == "clarification" and not r["hospitals"]),

    # 6. Boolean OR & AND (4)
    ("V3-24", "boolean", "RS dengan layanan mata atau saraf di Medan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", service="Mata") | oracle_ids("Kota Medan", service="Saraf"))),
    ("V3-25", "boolean", "RS kelas A atau kelas B di Binjai",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai", {"A", "B"}))),
    ("V3-26", "boolean", "RS di Medan dengan ICU dan NICU",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", facility="ICU") & oracle_ids("Kota Medan", facility="NICU"))),
    ("V3-27", "boolean", "RS di Medan dengan HCU atau PICU",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", facility="HCU") | oracle_ids("Kota Medan", facility="PICU"))),

    # 7. Multi-intent & Compare 3 (4)
    ("V3-28", "multi_intent", "Cari RS kelas B di Medan dan tunjukkan yang punya ICU",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", {"B"}, facility="ICU"))),
    ("V3-29", "compare", "Bandingkan Adam Malik, Hermina Medan, dan Columbia Asia Medan",
     lambda r, s: r["kind"] == "comparison" and len(r["hospitals"]) == 3),
    ("V3-30", "compare", "Bandingkan Pirngadi dan Murni Teguh",
     lambda r, s: r["kind"] == "comparison" and len(r["hospitals"]) == 2),
    ("V3-31", "multi_intent", "Tampilkan 3 RS kelas B di Medan dengan CT Scan",
     lambda r, s: len(r["hospitals"]) == 3 and {h["id"] for h in r["hospitals"]} <= oracle_ids("Kota Medan", {"B"}, facility="CT Scan")),

    # 8. Attribute specific (4)
    ("V3-32", "attribute", "Jam buka RS Adam Malik?",
     lambda r, s: r["kind"] == "hours" and [h["id"] for h in r["hospitals"]] == ["rs-171"]),
    ("V3-33", "attribute", "Nomor telepon RS Hermina Medan?",
     lambda r, s: r["kind"] == "contact" and [h["id"] for h in r["hospitals"]] == ["rs-125"]),
    ("V3-34", "attribute", "Alamat RSUD Dr Pirngadi?",
     lambda r, s: r["kind"] == "detail" and [h["id"] for h in r["hospitals"]] == ["rs-083"]),
    ("V3-35", "attribute", "Apakah RS Adam Malik terima BPJS?",
     lambda r, s: r["kind"] == "detail" and [h["id"] for h in r["hospitals"]] == ["rs-171"]),

    # 9. Context correction & Multi-turn (5)
    ("V3-36", "context", ["Cari RS di Binjai", "eh maksud saya di Siantar"],
     lambda r, s: verify_subset(r, oracle_ids("Kota Pematang Siantar"))),
    ("V3-37", "context", ["Cari RS kelas B di Medan", "Tambah ICU"],
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", {"B"}, facility="ICU"))),
    ("V3-38", "context", ["Cari RS di Medan dengan NICU", "Hapus NICU"],
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan"))),
    ("V3-39", "context", ["Cari RS di Medan", "Reset"],
     lambda r, s: r["kind"] == "text" and not r["hospitals"] and r["state"] == {}),
    ("V3-40", "context", ["Cari RS di Binjai", "Yang pertama tadi", "Emailnya?"],
     lambda r, s: r["kind"] == "contact" and [h["id"] for h in r["hospitals"]] == s["last_hospital_ids"]),

    # 10. Preferences & Conditionals (4)
    ("V3-41", "preference", "Cari RS di Medan, kalau bisa kelas A",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan")) and bool(r["state"]["plan"].get("preferences"))),
    ("V3-42", "preference", "Cari RS di Binjai, utamakan ICU",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai")) and bool(r["state"]["plan"].get("preferences"))),
    ("V3-43", "preference", "Cari RS kelas B di Medan, lebih bagus kalau ada CT Scan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Medan", {"B"})) and bool(r["state"]["plan"].get("preferences"))),
    ("V3-44", "conditional", "Kalau ada RS kelas B di Binjai, tampilkan",
     lambda r, s: verify_subset(r, oracle_ids("Kota Binjai", {"B"}))),

    # 11. Hypothetical & Safety (6)
    ("V3-45", "safety_non_emergency", "Jika seseorang sesak napas apa yang dilakukan?",
     lambda r, s: not r["is_emergency"]),
    ("V3-46", "safety_non_emergency", "Misalnya ada yang nyeri dada, apakah itu darurat?",
     lambda r, s: not r["is_emergency"]),
    ("V3-47", "safety_non_emergency", "Dulu saya pernah sesak napas tapi sudah sembuh",
     lambda r, s: not r["is_emergency"]),
    ("V3-48", "safety_emergency", "Tolong ibu saya sesak napas berat sekarang",
     lambda r, s: r["is_emergency"]),
    ("V3-49", "safety_emergency", "Ada pasien kejang dan tidak sadarkan diri",
     lambda r, s: r["is_emergency"]),
    ("V3-50", "safety_emergency", "Saya mengalami nyeri dada hebat sekarang",
     lambda r, s: r["is_emergency"]),

    # 12. Security, Scope & Clarification (4)
    ("V3-51", "security", "SELECT ?s ?p WHERE { ?s ?p ?o }",
     lambda r, s: r["kind"] == "clarification" and not r["hospitals"]),
    ("V3-52", "security", "<img src=x onerror=alert(1)>",
     lambda r, s: r["kind"] == "clarification" and not r["hospitals"]),
    ("V3-53", "scope", "Cari RS di Bandung dengan ICU",
     lambda r, s: r["state"].get("last_intent") == "OUT_OF_SCOPE" and not r["hospitals"]),
    ("V3-54", "clarification", "RS dengan rating terbaik di Medan",
     lambda r, s: r["kind"] == "clarification" and not r["hospitals"]),
]


async def main():
    rows = []
    for cid, cat, inp, check in CASES:
        turns = inp if isinstance(inp, list) else [inp]
        state, prior, r = None, None, None
        for q in turns:
            prior = state
            r = await process(q, state=state)
            state = r["state"]
        ok = False
        try:
            ok = bool(check(r, prior))
        except Exception as exc:
            r = {"kind": "exception", "text": str(exc)}
        rows.append({
            "id": cid,
            "category": cat,
            "prompt": " -> ".join(turns),
            "passed": ok,
            "kind": r.get("kind"),
            "intent": (r.get("state") or {}).get("last_intent"),
            "text_preview": (r.get("text") or "")[:120],
        })
    passed = sum(x["passed"] for x in rows)
    out = {"total": len(rows), "passed": passed, "pass_rate": round(100 * passed / len(rows), 2), "results": rows}
    (ROOT / "docs/NARA_3_HELDOUT_V3_RESULTS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf8")
    print(f"V3: {passed} / {len(rows)} ({out['pass_rate']}%)", flush=True)
    for x in rows:
        if not x["passed"]:
            print(f"  FAIL {x['id']} [{x['category']}] {x['prompt']} => kind={x['kind']} intent={x['intent']} text={x['text_preview']}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

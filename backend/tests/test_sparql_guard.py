"""Test suite untuk SPARQL Guard keamanan CariSehat.

Menguji bahwa:
- Query SELECT/ASK/CONSTRUCT/DESCRIBE valid → tidak diblokir (None)
- Operasi berbahaya → diblokir (mengembalikan pesan error)
- Query terlalu besar → diblokir
- Query kosong/invalid → diblokir dengan pesan jelas
- enforce_result_limit berfungsi dengan benar
"""

import sys
import os

# Tambahkan path backend agar import bisa berjalan tanpa instalasi
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.sparql_guard import validate_sparql_query, enforce_result_limit, MAX_QUERY_BYTES, MAX_RESULTS

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def assert_pass(query: str, label: str):
    err = validate_sparql_query(query)
    if err is not None:
        print(f"  FAIL [{label}]: diblokir padahal seharusnya PASS. Error: {err}")
        return False
    print(f"  PASS [{label}]")
    return True


def assert_blocked(query: str, label: str):
    err = validate_sparql_query(query)
    if err is None:
        print(f"  FAIL [{label}]: TIDAK diblokir padahal seharusnya REJECTED")
        return False
    print(f"  PASS (BLOCKED) [{label}]: {err[:80]}")
    return True


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_01_select_valid():
    """TC01: SELECT valid → PASS"""
    q = """
    PREFIX hf: <http://example.org/ont/>
    SELECT ?rs ?nama WHERE {
      ?rs a hf:RumahSakit ;
          hf:nama ?nama .
    } LIMIT 10
    """
    return assert_pass(q, "TC01 SELECT valid")


def test_02_ask_valid():
    """TC02: ASK valid → PASS"""
    q = """
    ASK {
      <http://example.org/rs/001> a <http://example.org/ont/RumahSakit> .
    }
    """
    return assert_pass(q, "TC02 ASK valid")


def test_03_construct_valid():
    """TC03: CONSTRUCT valid → PASS"""
    q = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 50
    """
    return assert_pass(q, "TC03 CONSTRUCT valid")


def test_04_describe_valid():
    """TC04: DESCRIBE valid → PASS"""
    q = "DESCRIBE <http://example.org/rs/001>"
    return assert_pass(q, "TC04 DESCRIBE valid")


def test_05_insert_data_rejected():
    """TC05: INSERT DATA {...} → REJECTED"""
    q = """
    INSERT DATA {
      <http://example.org/rs/HACK> a <http://example.org/ont/RumahSakit> .
    }
    """
    return assert_blocked(q, "TC05 INSERT DATA")


def test_06_delete_where_rejected():
    """TC06: DELETE WHERE {...} → REJECTED"""
    q = """
    DELETE WHERE {
      ?rs ?p ?o .
    }
    """
    return assert_blocked(q, "TC06 DELETE WHERE")


def test_07_service_localhost_rejected():
    """TC07: SERVICE <http://localhost:3030/> {...} → REJECTED"""
    q = """
    SELECT ?x WHERE {
      SERVICE <http://localhost:3030/sparql> {
        ?x ?p ?o .
      }
    }
    """
    return assert_blocked(q, "TC07 SERVICE localhost")


def test_08_service_external_rejected():
    """TC08: SERVICE clause eksternal (dbpedia) → REJECTED (semua SERVICE diblokir)"""
    q = """
    SELECT ?label WHERE {
      SERVICE <http://dbpedia.org/sparql> {
        <http://dbpedia.org/resource/Medan> rdfs:label ?label .
      }
    }
    """
    return assert_blocked(q, "TC08 SERVICE eksternal")


def test_09_query_too_large():
    """TC09: Query sangat besar (>50KB) → REJECTED"""
    # Buat query lebih dari 50KB
    padding = "# " + "A" * 100 + "\n"
    q = "SELECT ?x WHERE { ?x ?p ?o }\n" + padding * 520  # ~52KB
    assert len(q.encode()) > MAX_QUERY_BYTES, "Padding tidak cukup besar untuk test"
    return assert_blocked(q, "TC09 Query >50KB")


def test_10_empty_query():
    """TC10: Query kosong → REJECTED dengan pesan jelas"""
    return assert_blocked("", "TC10 Query kosong")


def test_11_whitespace_only():
    """TC11: Query hanya whitespace → REJECTED"""
    return assert_blocked("   \n\t   ", "TC11 Query whitespace")


def test_12_load_rejected():
    """TC12: LOAD <url> → REJECTED"""
    q = "LOAD <http://example.org/data.rdf>"
    return assert_blocked(q, "TC12 LOAD")


def test_13_drop_rejected():
    """TC13: DROP GRAPH → REJECTED"""
    q = "DROP GRAPH <http://example.org/graph>"
    return assert_blocked(q, "TC13 DROP GRAPH")


def test_14_clear_rejected():
    """TC14: CLEAR ALL → REJECTED"""
    q = "CLEAR ALL"
    return assert_blocked(q, "TC14 CLEAR ALL")


def test_15_create_graph_rejected():
    """TC15: CREATE GRAPH → REJECTED"""
    q = "CREATE GRAPH <http://example.org/newgraph>"
    return assert_blocked(q, "TC15 CREATE GRAPH")


def test_16_insert_in_comment_pass():
    """TC16: INSERT dalam komentar saja → PASS (bukan operasi sungguhan)"""
    q = """
    # Ini query untuk mencari data, bukan INSERT
    SELECT ?rs ?nama WHERE {
      ?rs ?p ?o .
    } LIMIT 5
    """
    return assert_pass(q, "TC16 INSERT dalam komentar")


def test_17_insert_in_string_pass():
    """TC17: INSERT dalam string literal → PASS"""
    q = '''
    SELECT ?rs WHERE {
      ?rs <http://example.org/desc> "This is not an INSERT operation" .
    }
    '''
    return assert_pass(q, "TC17 INSERT dalam string literal")


def test_18_multistatement_insert_rejected():
    """TC18: SELECT valid diikuti INSERT (multi-statement) → REJECTED"""
    q = """SELECT ?x WHERE { ?x ?p ?o } ;
INSERT DATA { <http://hack.com/> a <http://hack.com/Evil> }"""
    return assert_blocked(q, "TC18 Multi-statement SELECT;INSERT")


def test_19_enforce_limit_no_limit():
    """TC19: enforce_result_limit tambahkan LIMIT jika tidak ada"""
    q = "SELECT ?x WHERE { ?x ?p ?o }"
    result = enforce_result_limit(q)
    assert f"LIMIT {MAX_RESULTS}" in result, f"LIMIT tidak ditambahkan: {result}"
    print(f"  PASS [TC19 enforce_result_limit tanpa LIMIT]")
    return True


def test_20_enforce_limit_too_high():
    """TC20: enforce_result_limit turunkan LIMIT jika terlalu tinggi"""
    q = f"SELECT ?x WHERE {{ ?x ?p ?o }} LIMIT {MAX_RESULTS + 5000}"
    result = enforce_result_limit(q)
    assert f"LIMIT {MAX_RESULTS}" in result, f"LIMIT tidak diturunkan: {result}"
    print(f"  PASS [TC20 enforce_result_limit turunkan LIMIT]")
    return True


def test_21_enforce_limit_ok():
    """TC21: enforce_result_limit biarkan LIMIT wajar"""
    q = "SELECT ?x WHERE { ?x ?p ?o } LIMIT 10"
    result = enforce_result_limit(q)
    assert "LIMIT 10" in result, f"LIMIT 10 diubah padahal OK: {result}"
    print(f"  PASS [TC21 enforce_result_limit LIMIT wajar]")
    return True


def test_22_service_internal_ip_rejected():
    """TC22: SERVICE dengan IP internal (192.168.x.x) → REJECTED"""
    q = """
    SELECT ?x WHERE {
      SERVICE <http://192.168.1.100:8080/sparql> {
        ?x ?p ?o .
      }
    }
    """
    return assert_blocked(q, "TC22 SERVICE IP internal")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

ALL_TESTS = [
    test_01_select_valid,
    test_02_ask_valid,
    test_03_construct_valid,
    test_04_describe_valid,
    test_05_insert_data_rejected,
    test_06_delete_where_rejected,
    test_07_service_localhost_rejected,
    test_08_service_external_rejected,
    test_09_query_too_large,
    test_10_empty_query,
    test_11_whitespace_only,
    test_12_load_rejected,
    test_13_drop_rejected,
    test_14_clear_rejected,
    test_15_create_graph_rejected,
    test_16_insert_in_comment_pass,
    test_17_insert_in_string_pass,
    test_18_multistatement_insert_rejected,
    test_19_enforce_limit_no_limit,
    test_20_enforce_limit_too_high,
    test_21_enforce_limit_ok,
    test_22_service_internal_ip_rejected,
]


def run_all():
    passed = 0
    failed = 0
    print("=" * 60)
    print("SPARQL Guard Test Suite - CariSehat")
    print("=" * 60)
    for test_fn in ALL_TESTS:
        try:
            ok = test_fn()
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR [{test_fn.__name__}]: {e}")
            failed += 1
    print("=" * 60)
    print(f"TOTAL: {passed + failed} test | {passed} PASS | {failed} FAIL")
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    p, f = run_all()
    sys.exit(0 if f == 0 else 1)

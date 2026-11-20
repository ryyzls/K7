"""SPARQL Security Guard untuk CariSehat.

Memvalidasi query SPARQL sebelum diteruskan ke Fuseki.
Menggabungkan dua lapisan pertahanan (Defense-in-Depth):
1. SPARQL AST Parser (rdflib.plugins.sparql.parser / W3C SPARQL 1.1 Grammar)
   sebagai verifikator utama struktur sintaks query, membedakan operasi nyata
   dari teks dalam komentar atau string literal.
2. Tokenizer & lexical skeleton analyzer berbasis regex standar untuk deteksi
   multi-statement, validasi IRI internal (SSRF), dan batas ukuran.

Whitelist: SELECT, ASK, CONSTRUCT, DESCRIBE
Blocklist: INSERT, DELETE, LOAD, CLEAR, DROP, CREATE, COPY, MOVE, ADD, WITH,
           SERVICE (semua federated query / SSRF protection)

Batasan:
  - Max query size : 50 KB
  - Max results    : 1000 baris (diterapkan via enforce_result_limit)
  - Timeout proxy  : 10 detik (diterapkan di semantic router)
"""

from __future__ import annotations

import re
from typing import Optional

# Coba import parser SPARQL 1.1 W3C resmi dari RDFLib
try:
    import rdflib.plugins.sparql.parser as sparql_parser
    from rdflib.plugins.sparql.parserutils import CompValue
    from pyparsing import ParseException
    HAS_SPARQL_PARSER = True
except ImportError:
    HAS_SPARQL_PARSER = False
    CompValue = object
    ParseException = Exception

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

MAX_QUERY_BYTES = 50 * 1024  # 50 KB

# Token-tipe query yang diizinkan (read-only)
ALLOWED_QUERY_TYPES: frozenset[str] = frozenset({"SELECT", "ASK", "CONSTRUCT", "DESCRIBE"})

# Operasi SPARQL Update / DDL yang diblokir
BLOCKED_OPERATIONS: frozenset[str] = frozenset({
    "INSERT",
    "DELETE",
    "LOAD",
    "CLEAR",
    "DROP",
    "CREATE",
    "COPY",
    "MOVE",
    "ADD",
    "WITH",  # WITH ... DELETE/INSERT pattern
})

# Kata kunci yang memerlukan pemeriksaan konteks ekstra
CONTEXT_KEYWORDS: frozenset[str] = frozenset({"SERVICE"})

# Pattern comment SPARQL: single-line (#)
_COMMENT_RE = re.compile(r"#[^\n]*")

# Pattern string literal: """...""", '''...''', "...", '...'
_STRING_TRIPLE_DOUBLE = re.compile(r'"""(?:[^\\]|\\.)*?"""', re.DOTALL)
_STRING_TRIPLE_SINGLE = re.compile(r"'''(?:[^\\]|\\.)*?'''", re.DOTALL)
_STRING_DOUBLE = re.compile(r'"(?:[^"\\]|\\.)*"')
_STRING_SINGLE = re.compile(r"'(?:[^'\\]|\\.)*'")

# URI (IRI) reference: <...>
_IRI_RE = re.compile(r"<[^>]*>")

# Tokenizer: identifier SPARQL
_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Deteksi URI lokal/internal yang diblokir dalam SERVICE / query (SSRF Prevention)
_LOCAL_IRI_RE = re.compile(
    r"<\s*(https?://)?"
    r"(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|::1|10\.\d+\.\d+\.\d+|"
    r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+|"
    r"\[::1\]|fuseki|carisehat|internal|host\.docker\.internal)"
    r"[:/\s>]",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# AST Traversal Helpers (RDFLib SPARQL 1.1 Parser)
# ---------------------------------------------------------------------------

def _ast_contains_service(obj: object) -> bool:
    """Periksa secara rekursif apakah AST SPARQL mengandung node ServiceGraphPattern."""
    if isinstance(obj, CompValue):
        if "Service" in getattr(obj, "name", ""):
            return True
        for k in obj:
            if _ast_contains_service(obj[k]):
                return True
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, dict)):
        for item in obj:
            if _ast_contains_service(item):
                return True
    return False


# ---------------------------------------------------------------------------
# Lexical Skeleton Helpers (Fallback & Defense-in-Depth)
# ---------------------------------------------------------------------------

def _strip_literals_and_comments(query: str) -> str:
    """Hapus string literal dan komentar dari query agar token scan aman.

    Urutan kritis:
    1. Ganti IRI <...> dengan placeholder agar '#' di dalam IRI tidak dikira komentar
    2. Hapus string literal (triple dulu, baru single)
    3. Hapus komentar single-line (#...)
    """
    q = _IRI_RE.sub(" __IRI__ ", query)
    q = _STRING_TRIPLE_DOUBLE.sub(" ", q)
    q = _STRING_TRIPLE_SINGLE.sub(" ", q)
    q = _STRING_DOUBLE.sub(" ", q)
    q = _STRING_SINGLE.sub(" ", q)
    q = _COMMENT_RE.sub(" ", q)
    return q


def _extract_tokens(skeleton: str) -> list[str]:
    """Ekstrak semua token kata dari skeleton query (uppercase)."""
    return [m.group().upper() for m in _WORD_RE.finditer(skeleton)]


_PREFIX_DECL_RE = re.compile(
    r"\b(PREFIX|BASE)\b\s*[A-Za-z0-9_-]*\s*:?\s*(?:<[^>]*>|__IRI__)",
    re.IGNORECASE,
)


def _strip_prefix_declarations(skeleton: str) -> str:
    """Hapus deklarasi PREFIX dan BASE dari skeleton agar tidak dikacaukan dengan token query."""
    return _PREFIX_DECL_RE.sub(" ", skeleton)


def _extract_iris(query: str) -> list[str]:
    """Ekstrak semua IRI <...> dari teks query mentah."""
    return [m.group() for m in _IRI_RE.finditer(query)]


# ---------------------------------------------------------------------------
# Fungsi Utama Validasi
# ---------------------------------------------------------------------------

def validate_sparql_query(query: str) -> Optional[str]:
    """Validasi query SPARQL untuk memastikan keamanan read-only dan mencegah SSRF.

    Args:
        query: String query SPARQL mentah dari pengguna.

    Returns:
        None jika aman, pesan error (str) jika ditolak.
    """
    # 1. Periksa query kosong
    if not query or not query.strip():
        return "Query SPARQL tidak boleh kosong."

    # 2. Periksa batas ukuran query (max 50 KB)
    if len(query.encode("utf-8")) > MAX_QUERY_BYTES:
        return (
            f"Query terlalu besar (maks {MAX_QUERY_BYTES // 1024} KB). "
            "Sederhanakan query Anda."
        )

    # 3. Periksa IRI internal / SSRF sebelum eksekusi
    iris = _extract_iris(query)
    for iri in iris:
        if _LOCAL_IRI_RE.search(iri):
            return (
                f"Query mengandung IRI yang mengarah ke jaringan internal: {iri[:80]}. "
                "Akses ke endpoint internal tidak diizinkan."
            )

    # 4. Strip literal dan komentar untuk analisis skeleton
    skeleton = _strip_literals_and_comments(query)
    skeleton_no_prefix = _strip_prefix_declarations(skeleton)
    tokens = _extract_tokens(skeleton_no_prefix)

    if not tokens:
        return "Query SPARQL tidak mengandung token yang valid."

    # 5. Deteksi multi-statement (SELECT ... ; INSERT ...)
    if ";" in skeleton:
        parts = skeleton.split(";")
        for part in parts[1:]:
            part_tokens = set(_extract_tokens(part))
            if part_tokens & (BLOCKED_OPERATIONS | CONTEXT_KEYWORDS):
                bad = sorted(part_tokens & (BLOCKED_OPERATIONS | CONTEXT_KEYWORDS))
                return (
                    f"Query multi-statement mengandung operasi terlarang: {', '.join(bad)}. "
                    "Hanya single-statement read-only query yang diizinkan."
                )

    # 6. Evaluasi token pertama (tipe query)
    query_type = tokens[0]
    if query_type not in ALLOWED_QUERY_TYPES:
        if query_type in BLOCKED_OPERATIONS or query_type in CONTEXT_KEYWORDS:
            return (
                f"Operasi '{query_type}' tidak diizinkan. "
                "Hanya SELECT, ASK, CONSTRUCT, dan DESCRIBE yang diperbolehkan."
            )
        return (
            f"Tipe query '{query_type}' tidak dikenal atau tidak diizinkan. "
            "Hanya SELECT, ASK, CONSTRUCT, dan DESCRIBE yang diperbolehkan."
        )

    # 7. Scan semua token skeleton untuk operasi mutasi terlarang
    token_set = set(tokens)
    blocked_found = token_set & BLOCKED_OPERATIONS
    if blocked_found:
        found = sorted(blocked_found)
        return (
            f"Query mengandung operasi terlarang: {', '.join(found)}. "
            "Hanya operasi read-only yang diizinkan."
        )

    # 8. Blokir semua klausa SERVICE (SSRF & federated query prevention)
    if "SERVICE" in token_set:
        return (
            "Klausa SERVICE tidak diizinkan demi keamanan. "
            "Federated SPARQL queries diblokir."
        )

    # 9. Verifikasi mendalam via W3C SPARQL AST Parser (RDFLib)
    if HAS_SPARQL_PARSER:
        try:
            parsed = sparql_parser.parseQuery(query)
            # Pastikan AST tidak mengandung SERVICE
            if _ast_contains_service(parsed):
                return (
                    "Klausa SERVICE tidak diizinkan demi keamanan. "
                    "Federated SPARQL queries diblokir."
                )
        except ParseException:
            # Jika gagal di parseQuery, uji apakah ini merupakan update SPARQL yang lolos
            try:
                sparql_parser.parseUpdate(query)
                return (
                    "Operasi update RDF terdeteksi oleh parser dan tidak diizinkan. "
                    "Hanya operasi read-only yang diperbolehkan."
                )
            except Exception:
                # Query memiliki sintaks error menurut standar SPARQL 1.1
                pass

    return None  # Query aman


# ---------------------------------------------------------------------------
# Response Limit Helper
# ---------------------------------------------------------------------------

MAX_RESULTS = 1000

_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)", re.IGNORECASE)


def enforce_result_limit(query: str, max_results: int = MAX_RESULTS) -> str:
    """Pastikan query SELECT memiliki LIMIT <= max_results.

    Jika tidak ada LIMIT, tambahkan. Jika LIMIT lebih besar, turunkan.
    Untuk ASK/CONSTRUCT/DESCRIBE, kembalikan apa adanya.
    """
    skeleton = _strip_literals_and_comments(query)
    tokens = _extract_tokens(skeleton)
    meaningful = [t for t in tokens if t not in ("PREFIX", "BASE")]
    if not meaningful or meaningful[0] != "SELECT":
        return query  # hanya enforce pada SELECT

    match = _LIMIT_RE.search(query)
    if match:
        current_limit = int(match.group(1))
        if current_limit > max_results:
            return _LIMIT_RE.sub(f"LIMIT {max_results}", query, count=1)
        return query
    else:
        return query.rstrip() + f"\nLIMIT {max_results}"

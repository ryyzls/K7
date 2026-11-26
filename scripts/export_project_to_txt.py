#!/usr/bin/env python3
"""
Export seluruh codebase proyek CariSehat (K7) ke file .txt terstruktur agar mudah
dibaca dan dipahami secara menyeluruh oleh AI (ChatGPT, Claude, Gemini, dll.).

Fitur utama:
- Zero external dependency (cukup Python 3 standar).
- Aman: otomatis mengecualikan file rahasia (.env), binary/media, node_modules, .git, dll.
- Menyertakan Pohon Direktori (Directory Tree) + statistik ringkas di bagian awal.
- Mode 'ai' (default): 100% seluruh kode sumber (backend, frontend, SQL/MSBD, fuseki,
  ontologi/semantik, docker) dimuat UTUH; file dataset raksasa (.ttl/.rdf/.csv/.json > 60 KB)
  diambil sampel awalnya agar AI paham skemanya tanpa kehabisan kuota token.
- Mode 'full': memuat semua file teks tanpa pemotongan.
- Mendukung pemecahan otomatis (--split-mb) bila perlu upload beberapa file ke AI.

Contoh pemakaian (jalankan dari folder root K7):
  python scripts/export_project_to_txt.py
  python scripts/export_project_to_txt.py --output carisehat_ai_context.txt
  python scripts/export_project_to_txt.py --mode full --split-mb 2
  python scripts/export_project_to_txt.py --include-scripts --include-tests
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

# Folder yang selalu diabaikan (build, dependency, git, media, cache)
ALWAYS_IGNORE_DIRS = {
    ".git",
    ".github",
    ".agents",
    ".vscode",
    ".idea",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    "backups",
    "scratch",
}

# Folder besar/tambahan yang diabaikan pada mode 'ai' kecuali diminta eksplisit
OPTIONAL_DIRS_IN_AI_MODE = {
    "data",
    "tests",
    "scripts",
}

# Nama file yang selalu diabaikan (rahasia, lockfile, legacy sangat besar)
ALWAYS_IGNORE_FILES = {
    ".env",
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
    "skills-lock.json",
    "index.legacy.html",
}

# Ekstensi biner / media yang selalu dilewati
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".wav", ".ogg", ".webm", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".db", ".sqlite",
}

# Ekstensi teks yang diizinkan
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs",
    ".html", ".css", ".scss",
    ".sql", ".ttl", ".rdf", ".owl", ".rq", ".sparql", ".n3", ".nt",
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".md", ".txt", ".sh", ".ps1", ".env.example", ".csv",
}

# Nama file tanpa ekstensi yang tetap disertakan
ALLOW_NO_EXT_NAMES = {
    "Dockerfile",
    "Makefile",
    ".gitignore",
    ".gitattributes",
    ".env.example",
}

# Ekstensi dataset yang dipotong pintar pada mode 'ai' bila ukurannya besar
DATA_EXTENSIONS = {".ttl", ".rdf", ".owl", ".json", ".csv", ".xml", ".nt", ".n3"}


def is_text_candidate(path: Path) -> bool:
    name = path.name
    if name in ALWAYS_IGNORE_FILES:
        return False
    if name in ALLOW_NO_EXT_NAMES:
        return True
    ext = path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return False
    if ext in TEXT_EXTENSIONS:
        return True
    return False


def collect_files(
    root: Path,
    mode: str,
    include_data: bool,
    include_scripts: bool,
    include_tests: bool,
    include_docs: bool,
    output_paths_to_skip: set[Path],
) -> list[Path]:
    collected: list[Path] = []

    skip_top_dirs: set[str] = set()
    if mode == "ai":
        if not include_data:
            skip_top_dirs.add("data")
        if not include_scripts:
            skip_top_dirs.add("scripts")
        if not include_tests:
            skip_top_dirs.add("tests")
        if not include_docs:
            skip_top_dirs.add("docs")

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)

        # Pruning direktori
        pruned: list[str] = []
        for d in sorted(dirnames):
            if d in ALWAYS_IGNORE_DIRS:
                continue
            if rel_dir == Path(".") and d in skip_top_dirs:
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if fpath.resolve() in output_paths_to_skip:
                continue
            if not is_text_candidate(fpath):
                continue
            collected.append(fpath)

    return collected


def build_tree(root: Path, files: list[Path]) -> str:
    tree: dict = {}
    for f in files:
        parts = f.relative_to(root).parts
        node = tree
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = None

    lines: list[str] = [f"{root.name}/"]

    def _walk(node: dict, prefix: str = "") -> None:
        keys = sorted(node.keys(), key=lambda k: (node[k] is None, k.lower()))
        for idx, key in enumerate(keys):
            is_last = idx == len(keys) - 1
            branch = "└── " if is_last else "├── "
            if node[key] is None:
                lines.append(f"{prefix}{branch}{key}")
            else:
                lines.append(f"{prefix}{branch}{key}/")
                ext = "    " if is_last else "│   "
                _walk(node[key], prefix + ext)

    _walk(tree)
    return "\n".join(lines)


def read_file_content(
    fpath: Path,
    mode: str,
    max_data_kb: int,
    sample_lines: int,
) -> tuple[str, bool, int]:
    """Mengembalikan (teks, is_truncated, total_lines)."""
    size_bytes = fpath.stat().st_size
    ext = fpath.suffix.lower()

    try:
        raw_text = fpath.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            raw_text = fpath.read_text(encoding="latin-1")
        except Exception as exc:
            return f"[Gagal membaca file: {exc}]\n", False, 0

    lines = raw_text.splitlines()
    total_lines = len(lines)

    # Pada mode 'ai', potong file dataset yang terlalu besar agar tidak memboroskan token
    if mode == "ai" and ext in DATA_EXTENSIONS and size_bytes > max_data_kb * 1024:
        head = "\n".join(lines[:sample_lines])
        notice = (
            f"\n\n... [DIPOTONG OTOMATIS OLEH MODE 'ai': menampilkan {min(sample_lines, total_lines)} "
            f"dari {total_lines:,} baris | ukuran asli {size_bytes / 1024:.1f} KB. "
            f"Jalankan dengan --mode full bila ingin memuat seluruh isi file ini.] ...\n"
        )
        return head + notice, True, total_lines

    if not raw_text.endswith("\n"):
        raw_text += "\n"
    return raw_text, False, total_lines


def write_outputs(
    header: str,
    sections: list[str],
    output_path: Path,
    split_mb: float,
) -> list[Path]:
    if split_mb <= 0:
        full_text = header + "".join(sections)
        output_path.write_text(full_text, encoding="utf-8")
        return [output_path]

    max_bytes = int(split_mb * 1024 * 1024)
    written: list[Path] = []
    stem = output_path.stem
    suffix = output_path.suffix or ".txt"
    parent = output_path.parent

    part_idx = 1
    current_buf = [header]
    current_size = len(header.encode("utf-8"))

    for sec in sections:
        sec_bytes = len(sec.encode("utf-8"))
        if current_size + sec_bytes > max_bytes and len(current_buf) > 1:
            part_file = parent / f"{stem}_part{part_idx}{suffix}"
            part_file.write_text("".join(current_buf), encoding="utf-8")
            written.append(part_file)
            part_idx += 1
            part_header = (
                f"=== LANJUTAN EXPORT PROYEK CARISEHAT (PART {part_idx}) ===\n\n"
            )
            current_buf = [part_header, sec]
            current_size = len(part_header.encode("utf-8")) + sec_bytes
        else:
            current_buf.append(sec)
            current_size += sec_bytes

    if current_buf:
        part_file = parent / f"{stem}_part{part_idx}{suffix}"
        part_file.write_text("".join(current_buf), encoding="utf-8")
        written.append(part_file)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gabungkan seluruh codebase proyek CariSehat (K7) ke dalam file .txt untuk AI."
    )
    parser.add_argument(
        "--output", "-o",
        default="CariSehat_Full_Context.txt",
        help="Nama file output .txt di root proyek (default: CariSehat_Full_Context.txt)",
    )
    parser.add_argument(
        "--mode",
        choices=["ai", "full"],
        default="ai",
        help="'ai' (default): kode utuh + sampel dataset besar; 'full': semua file teks utuh tanpa potong.",
    )
    parser.add_argument(
        "--max-data-kb",
        type=int,
        default=60,
        help="Batas ukuran (KB) file dataset (.ttl/.rdf/.csv/.json) sebelum diambil sampel di mode 'ai' (default: 60).",
    )
    parser.add_argument(
        "--sample-lines",
        type=int,
        default=120,
        help="Jumlah baris sampel untuk file dataset besar di mode 'ai' (default: 120).",
    )
    parser.add_argument(
        "--split-mb",
        type=float,
        default=0,
        help="Pecah file output otomatis per N MB (misal: --split-mb 1.5). Default 0 = 1 file utuh.",
    )
    parser.add_argument("--include-data", action="store_true", help="Sertakan folder data/ pada mode 'ai'.")
    parser.add_argument("--include-scripts", action="store_true", help="Sertakan folder scripts/ pada mode 'ai'.")
    parser.add_argument("--include-tests", action="store_true", help="Sertakan folder tests/ pada mode 'ai'.")
    parser.add_argument("--include-docs", action="store_true", help="Sertakan folder docs/ pada mode 'ai'.")

    args = parser.parse_args()

    # Root proyek = satu tingkat di atas folder scripts/
    root = Path(__file__).resolve().parent.parent
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = root / out_path

    # Hindari membaca file output sendiri jika sudah ada sebelumnya
    skip_outputs = {out_path.resolve()}
    for old_part in out_path.parent.glob(f"{out_path.stem}_part*{out_path.suffix}"):
        skip_outputs.add(old_part.resolve())

    files = collect_files(
        root=root,
        mode=args.mode,
        include_data=args.include_data,
        include_scripts=args.include_scripts,
        include_tests=args.include_tests,
        include_docs=args.include_docs,
        output_paths_to_skip=skip_outputs,
    )

    sections: list[str] = []
    truncated_count = 0
    total_lines_all = 0

    for fpath in files:
        rel = fpath.relative_to(root).as_posix()
        size_kb = fpath.stat().st_size / 1024
        content, is_trunc, line_count = read_file_content(
            fpath, args.mode, args.max_data_kb, args.sample_lines
        )
        if is_trunc:
            truncated_count += 1
        total_lines_all += line_count

        bar = "=" * 80
        status = "SAMPEL" if is_trunc else "UTUH"
        sec = (
            f"\n{bar}\n"
            f"FILE: {rel}  |  UKURAN: {size_kb:.1f} KB  |  BARIS: {line_count:,}  |  MODE: {status}\n"
            f"{bar}\n"
            f"{content}"
        )
        sections.append(sec)

    tree_str = build_tree(root, files)
    est_chars = sum(len(s) for s in sections) + len(tree_str)
    est_tokens = est_chars // 4

    header = (
        "================================================================================\n"
        "CARISEHAT (K7) — PROJECT CONTEXT EXPORT UNTUK AI\n"
        "================================================================================\n"
        f"Mode Export     : {args.mode}\n"
        f"Jumlah File     : {len(files)} file ({truncated_count} file dataset besar diambil sampel)\n"
        f"Total Baris Asli: {total_lines_all:,} baris\n"
        f"Estimasi Token  : ~{est_tokens:,} token\n"
        "Catatan Keamanan: File .env (rahasia), node_modules, .git, dan media/biner dikecualikan.\n"
        "\n"
        "--- STRUKTUR DIREKTORI PROYEK ---\n"
        f"{tree_str}\n"
        "\n"
        "--- ISI FILE KODE & KONFIGURASI ---\n"
    )

    written_files = write_outputs(header, sections, out_path, args.split_mb)

    print("Export selesai!")
    print(f"  Mode           : {args.mode}")
    print(f"  Total file     : {len(files)} ({truncated_count} dataset disampel)")
    print(f"  Estimasi token : ~{est_tokens:,} token")
    for wf in written_files:
        sz_kb = wf.stat().st_size / 1024
        print(f"  Output         : {wf} ({sz_kb:.1f} KB)")


if __name__ == "__main__":
    main()

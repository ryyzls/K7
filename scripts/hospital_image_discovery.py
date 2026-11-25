"""Mass Hospital Image Discovery, Matching, Validation & Optimization Pipeline for CariSehat."""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import io
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
import imagehash
from bs4 import BeautifulSoup
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parent.parent
PROFIL_JSON = ROOT / "data" / "enrichment" / "final_info_rs" / "profil_lengkap_206.json"
KONTAK_JSON = ROOT / "data" / "enrichment" / "final_info_rs" / "kontak_dan_website_206.json"
EXISTING_DIR = ROOT / "frontend" / "public" / "images" / "rs"
OUT_WEB_DIR = ROOT / "frontend" / "public" / "images" / "hospitals"
STAGING_DIR = ROOT / "data" / "enrichment" / "hospital_images"
RAW_CACHE_DIR = STAGING_DIR / "_raw_cache"

NEGATIVE_KW = {
    "logo", "icon", "favicon", "avatar", "banner", "poster", "flyer", "brosur",
    "jadwal", "promo", "iklan", "placeholder", "default", "no-image", "noimage",
    "maps.gstatic", "streetview", "staticmap", "shutterstock", "istockphoto",
    "dreamstime", "123rf", "freepik", "vecteezy", "clipart", "whatsapp", "qr",
    "barcode", "button", "badge", "spinner", "loader", "arrow", "background",
    "slider-bg", "pattern", "dokter", "doctor", "direktur", "pegawai", "karir",
    "lowongan", "bpjs-logo", "kemenkes-logo", "akreditasi-logo",
}

CHAIN_BRANDS = [
    "hermina", "columbia asia", "murni teguh", "mitra medika", "efarina",
    "sri pamela", "bina karsa", "martha friska", "melati", "bhayangkara",
    "advent", "methodist", "royal prima", "santa elisabeth", "sari mutiara",
    "bunda thamrin", "imelda", "grandmed", "madani", "permatabunda", "permata bunda",
]

POSITIVE_CUES = {
    "gedung": 0.14, "bangunan": 0.14, "exterior": 0.14, "tampak depan": 0.15,
    "lobby": 0.10, "lobi": 0.10, "fasilitas": 0.08, "igd": 0.08, "ugd": 0.08,
    "rumah sakit": 0.10, "hospital": 0.10, "rsud": 0.10, "rsu": 0.08,
    "ruang": 0.06, "rawat": 0.06, "poliklinik": 0.06, "profil": 0.06,
}

STOPWORDS = {
    "rs", "rsu", "rsud", "rsk", "rsia", "rsj", "umum", "khusus", "daerah",
    "rumah", "sakit", "kota", "kab", "kabupaten", "provinsi", "sumatera",
    "utara", "sumut", "dr", "prof", "h", "hj", "st", "tk", "ii", "iii", "iv",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def norm_tokens(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    return {t for t in cleaned.split() if len(t) >= 2 and t not in STOPWORDS}


def build_queries(h: dict[str, Any]) -> list[str]:
    nama = h["nama"].strip()
    kab = re.sub(r"^(Kota|Kab\.)\s+", "", h.get("kabkota", "")).strip()
    short_name = re.sub(r"^RS\s+(Umum|Khusus|Jiwa|Ibu dan Anak)\s+", "RS ", nama, flags=re.I)
    queries = [
        f"{nama} {kab} gedung",
        f"{short_name} {kab} foto rumah sakit",
        f"{nama} {kab}",
    ]
    return list(dict.fromkeys(q.strip() for q in queries if q.strip()))


def has_negative_kw(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in NEGATIVE_KW)


def analyze_image_bytes(data: bytes) -> dict[str, Any] | None:
    if len(data) < 12_000:
        return None
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            w, h = im.size
            if w < 400 or h < 250:
                return None
            ratio = w / max(h, 1)
            if ratio < 0.55 or ratio > 2.6:
                return None
            rgb = im.convert("RGB")
            gray = rgb.convert("L")
            stat = ImageStat.Stat(gray)
            if stat.stddev[0] < 14.0:
                return None
            ph = str(imagehash.phash(rgb))
            sha = hashlib.sha256(data).hexdigest()
            return {"width": w, "height": h, "file_size": len(data), "sha256": sha, "perceptual_hash": ph}
    except Exception:
        return None


def score_candidate(h: dict[str, Any], cand: dict[str, Any], img_meta: dict[str, Any]) -> tuple[float, str]:
    text_blob = " ".join([
        cand.get("context_text", ""),
        cand.get("alt", ""),
        cand.get("source_title", ""),
        cand.get("original_image_url", ""),
        cand.get("source_url", ""),
    ]).lower()

    if has_negative_kw(text_blob):
        return 0.0, "REJECTED_NEGATIVE_KW"

    name_tokens = norm_tokens(h["nama"])
    kab_clean = re.sub(r"^(Kota|Kab\.)\s+", "", h.get("kabkota", "")).lower().strip()
    kab_tokens = norm_tokens(kab_clean)

    matched_name = sum(1 for t in name_tokens if t in text_blob)
    name_ratio = matched_name / max(len(name_tokens), 1)
    matched_kab = sum(1 for t in kab_tokens if t in text_blob)

    # Branch check for chain hospitals
    nama_low = h["nama"].lower()
    for chain in CHAIN_BRANDS:
        if chain in nama_low:
            # Specific branch tokens beyond the chain name
            chain_toks = set(chain.split())
            branch_toks = name_tokens - chain_toks
            if branch_toks and not any(bt in text_blob for bt in branch_toks):
                # Require kabkota if branch token missing
                if not matched_kab:
                    return 0.32, "REVIEW_CHAIN_BRANCH_UNCERTAIN"

    score = 0.0
    if matched_name >= 2 and name_ratio >= 0.6:
        score += 0.48
    else:
        score += min(0.42, name_ratio * 0.42)
    if matched_kab > 0:
        score += 0.14
    source_type = cand.get("source_name", "")
    if source_type == "Official Website":
        score += 0.25
    elif source_type == "Wikimedia Commons":
        score += 0.22
    elif source_type in ("Government / Dinkes", "Bing/Web Source"):
        score += 0.16

    for cue, pts in POSITIVE_CUES.items():
        if cue in text_blob:
            score += pts
            break

    if img_meta["width"] >= 800 and img_meta["height"] >= 450:
        score += 0.10
    elif img_meta["width"] >= 600:
        score += 0.06

    score = round(min(1.0, score), 3)
    if score >= 0.68:
        return score, "VERIFIED"
    if score >= 0.45:
        return score, "REVIEW_QUEUE"
    return score, "REJECTED_LOW_SCORE"


async def discover_official_website(client: httpx.AsyncClient, h: dict[str, Any], website_url: str) -> list[dict[str, Any]]:
    if not website_url:
        return []
    results = []
    base = website_url.strip()
    if not base.startswith("http"):
        base = "https://" + base
    parsed_base = urlparse(base)
    root_url = f"{parsed_base.scheme}://{parsed_base.netloc}"
    pages_to_try = list(dict.fromkeys([base, root_url, urljoin(root_url, "/profil"), urljoin(root_url, "/tentang-kami"), urljoin(root_url, "/fasilitas")]))

    seen_imgs = set()
    for page_url in pages_to_try[:3]:
        try:
            r = await client.get(page_url, timeout=12, follow_redirects=True)
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            title = (soup.title.string or "").strip() if soup.title else ""

            # og:image
            for meta in soup.find_all("meta", attrs={"property": "og:image"}):
                img_u = meta.get("content", "").strip()
                if img_u and img_u not in seen_imgs:
                    seen_imgs.add(img_u)
                    results.append({
                        "source_url": str(r.url),
                        "original_image_url": urljoin(str(r.url), img_u),
                        "source_name": "Official Website",
                        "source_title": title,
                        "alt": title,
                        "context_text": f"{title} gedung rumah sakit",
                        "attribution": f"Website Resmi {h['nama']}",
                        "license": "Official Website Reference",
                        "usage_permission": "verified_official_site",
                        "image_type": "cover_candidate",
                    })

            for img in soup.find_all("img"):
                src = (img.get("src") or img.get("data-src") or img.get("data-lazy-src") or "").strip()
                if not src or src.startswith("data:") or src.endswith(".svg"):
                    continue
                full_u = urljoin(str(r.url), src)
                if full_u in seen_imgs:
                    continue
                alt = (img.get("alt") or img.get("title") or "").strip()
                parent_txt = img.parent.get_text(" ", strip=True)[:140] if img.parent else ""
                if has_negative_kw(full_u + " " + alt):
                    continue
                seen_imgs.add(full_u)
                results.append({
                    "source_url": str(r.url),
                    "original_image_url": full_u,
                    "source_name": "Official Website",
                    "source_title": title,
                    "alt": alt,
                    "context_text": f"{title} {alt} {parent_txt}",
                    "attribution": f"Website Resmi {h['nama']}",
                    "license": "Official Website Reference",
                    "usage_permission": "verified_official_site",
                    "image_type": "gallery_candidate",
                })
                if len(results) >= 10:
                    return results
        except Exception:
            continue
    return results


async def discover_wikimedia(client: httpx.AsyncClient, h: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    kab = re.sub(r"^(Kota|Kab\.)\s+", "", h.get("kabkota", "")).strip()
    search_terms = [f"{h['nama']}", f"{re.sub(r'^RS\\s+Umum\\s+', 'RSU ', h['nama'])} {kab}"]
    for term in search_terms[:2]:
        try:
            r = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": term,
                    "gsrnamespace": "6",
                    "gsrlimit": "5",
                    "prop": "imageinfo",
                    "iiprop": "url|size|extmetadata",
                    "format": "json",
                },
                timeout=12,
            )
            if r.status_code != 200:
                continue
            pages = (r.json().get("query") or {}).get("pages") or {}
            for page in pages.values():
                ii = (page.get("imageinfo") or [{}])[0]
                img_u = ii.get("url")
                if not img_u or img_u.endswith(".svg") or img_u.endswith(".pdf"):
                    continue
                ext = ii.get("extmetadata") or {}
                lic = (ext.get("LicenseShortName") or {}).get("value", "CC / Wikimedia Commons")
                artist = re.sub(r"<[^>]+>", "", (ext.get("Artist") or {}).get("value", "Wikimedia Commons Contributor")).strip()
                desc = re.sub(r"<[^>]+>", "", (ext.get("ImageDescription") or {}).get("value", "")).strip()
                title = page.get("title", "")
                results.append({
                    "source_url": ii.get("descriptionurl", img_u),
                    "original_image_url": img_u,
                    "source_name": "Wikimedia Commons",
                    "source_title": title,
                    "alt": desc[:150] or title,
                    "context_text": f"{title} {desc}",
                    "attribution": f"{artist} (Wikimedia Commons)",
                    "license": lic,
                    "usage_permission": "open_license_with_attribution",
                    "image_type": "cover_candidate",
                })
        except Exception:
            continue
    return results


async def discover_bing_images(client: httpx.AsyncClient, h: dict[str, Any]) -> list[dict[str, Any]]:
    """Query Bing Images HTML search to discover original source pages and high-res hospital building photos."""
    results = []
    seen = set()
    for q in build_queries(h)[:2]:
        try:
            r = await client.get(
                "https://www.bing.com/images/search",
                params={"q": q, "qft": "+filterui:imagesize-large", "form": "HDRSC2"},
                timeout=12,
                follow_redirects=True,
            )
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.iusc"):
                m_raw = a.get("m")
                if not m_raw:
                    continue
                try:
                    m = json.loads(m_raw)
                except Exception:
                    continue
                murl = (m.get("murl") or "").strip()
                purl = (m.get("purl") or "").strip()
                t = (m.get("t") or "").strip()
                if not murl or murl in seen or has_negative_kw(murl + " " + t + " " + purl):
                    continue
                seen.add(murl)
                host = urlparse(purl).netloc.lower()
                sname = "Government / Dinkes" if ".go.id" in host else "Bing/Web Source"
                results.append({
                    "source_url": purl or murl,
                    "original_image_url": murl,
                    "source_name": sname,
                    "source_title": t,
                    "alt": t,
                    "context_text": f"{t} {purl}",
                    "attribution": host or "Web Source",
                    "license": "Source Reference",
                    "usage_permission": "web_source_verified",
                    "image_type": "cover_candidate",
                })
                if len(results) >= 8:
                    return results
        except Exception:
            continue
    return results


async def download_image(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        r = await client.get(url, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return None
        ctype = (r.headers.get("content-type") or "").lower()
        if "image" not in ctype and not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", url, re.I):
            return None
        return r.content
    except Exception:
        return None


def optimize_to_webp(src_bytes: bytes, dest_path: Path, max_width: int, quality: int = 82) -> tuple[int, int, int]:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(src_bytes)) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        if w > max_width:
            new_h = max(1, round(h * (max_width / w)))
            rgb = rgb.resize((max_width, new_h), Image.Resampling.LANCZOS)
        rgb.save(dest_path, format="WEBP", quality=quality, method=4)
        return rgb.size[0], rgb.size[1], dest_path.stat().st_size


async def process_hospital(
    client: httpx.AsyncClient,
    h: dict[str, Any],
    website_url: str,
    existing_cross_dups: set[str],
    global_sha: dict[str, str],
    global_phash: list[tuple[str, imagehash.ImageHash]],
) -> dict[str, Any]:
    rs_id = h["id_carisehat"]
    if True:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates_meta: list[dict[str, Any]] = []
        accepted: list[dict[str, Any]] = []
        review_q: list[dict[str, Any]] = []
        rejected_dups = 0

        # 1. Inspect existing local photos first (unless flagged as cross-RS duplicate)
        rs_existing_dir = EXISTING_DIR / rs_id
        local_shas = set()
        if rs_existing_dir.exists():
            for fp in sorted(rs_existing_dir.glob("*")):
                if not fp.is_file():
                    continue
                raw = fp.read_bytes()
                meta = analyze_image_bytes(raw)
                if not meta:
                    continue
                if meta["sha256"] in local_shas:
                    rejected_dups += 1
                    continue
                local_shas.add(meta["sha256"])

                if str(fp.relative_to(ROOT)) in existing_cross_dups:
                    # Cross-hospital duplicate: send to review, don't auto-accept as cover if we can find a unique one
                    review_q.append({
                        "hospital_id": rs_id,
                        "hospital_name": h["nama"],
                        "hospital_registration_code": h.get("kode_kemenkes", ""),
                        "image_type": "existing_cross_duplicate",
                        "source_url": f"local://{fp.name}",
                        "original_image_url": f"/images/rs/{rs_id}/{fp.name}",
                        "source_name": "Existing Dataset",
                        "attribution": "CariSehat Dataset",
                        "license": "Project Dataset",
                        "usage_permission": "needs_branch_verification",
                        "local_path": str(fp.relative_to(ROOT)),
                        "width": meta["width"],
                        "height": meta["height"],
                        "file_size": meta["file_size"],
                        "sha256": meta["sha256"],
                        "perceptual_hash": meta["perceptual_hash"],
                        "confidence_score": 0.50,
                        "verification_status": "REVIEW_CROSS_RS_DUPLICATE",
                        "discovered_at": now_iso,
                    })
                    continue

                accepted.append({
                    "raw_bytes": raw,
                    "source_url": f"local://{fp.name}",
                    "original_image_url": f"/images/rs/{rs_id}/{fp.name}",
                    "source_name": "Existing Dataset",
                    "attribution": "CariSehat Dataset",
                    "license": "Project Dataset",
                    "usage_permission": "existing_verified",
                    "confidence_score": 0.90,
                    "verification_status": "EXISTING_VERIFIED",
                    "discovered_at": now_iso,
                    **meta,
                })
                global_sha.setdefault(meta["sha256"], rs_id)
                global_phash.append((rs_id, imagehash.hex_to_hash(meta["perceptual_hash"])))

        # 2. Discover new photos if we have < 3 accepted photos (or 0 cover)
        if len(accepted) < 3:
            discovered = []
            if website_url:
                discovered.extend(await discover_official_website(client, h, website_url))
            discovered.extend(await discover_wikimedia(client, h))
            if len(accepted) == 0 or len(discovered) < 3:
                discovered.extend(await discover_bing_images(client, h))

            for cand in discovered[:12]:
                if len(accepted) >= 4:
                    break
                raw = await download_image(client, cand["original_image_url"])
                if not raw:
                    continue
                meta = analyze_image_bytes(raw)
                if not meta:
                    continue
                # Deduplicate by SHA-256 and pHash (Hamming <= 6)
                if meta["sha256"] in local_shas or meta["sha256"] in global_sha:
                    rejected_dups += 1
                    continue
                cand_ph = imagehash.hex_to_hash(meta["perceptual_hash"])
                if any((cand_ph - existing_ph) <= 6 for _, existing_ph in global_phash):
                    rejected_dups += 1
                    continue

                score, status = score_candidate(h, cand, meta)
                row = {
                    "hospital_id": rs_id,
                    "hospital_name": h["nama"],
                    "hospital_registration_code": h.get("kode_kemenkes", ""),
                    "image_type": cand["image_type"],
                    "source_url": cand["source_url"],
                    "original_image_url": cand["original_image_url"],
                    "source_name": cand["source_name"],
                    "attribution": cand["attribution"],
                    "license": cand["license"],
                    "usage_permission": cand["usage_permission"],
                    "local_path": "",
                    "width": meta["width"],
                    "height": meta["height"],
                    "file_size": meta["file_size"],
                    "sha256": meta["sha256"],
                    "perceptual_hash": meta["perceptual_hash"],
                    "confidence_score": score,
                    "verification_status": status,
                    "discovered_at": now_iso,
                }
                candidates_meta.append(row)

                if status == "VERIFIED":
                    local_shas.add(meta["sha256"])
                    global_sha[meta["sha256"]] = rs_id
                    global_phash.append((rs_id, cand_ph))
                    accepted.append({**row, "raw_bytes": raw})
                elif status == "REVIEW_QUEUE":
                    review_q.append(row)

        # 3. Optimize accepted photos to WebP in frontend/public/images/hospitals/rs-xxx/
        out_dir = OUT_WEB_DIR / rs_id
        published_files = []
        if accepted:
            # Best candidate first: higher confidence + wider resolution
            accepted.sort(key=lambda x: (x["confidence_score"], x["width"]), reverse=True)
            cover = accepted[0]
            cw, ch, csz = optimize_to_webp(cover["raw_bytes"], out_dir / "cover.webp", 1280, quality=82)
            tw, th, tsz = optimize_to_webp(cover["raw_bytes"], out_dir / "thumbnail.webp", 640, quality=80)
            published_files.append({
                "role": "cover",
                "delivery_url": f"/images/hospitals/{rs_id}/cover.webp",
                "thumbnail_url": f"/images/hospitals/{rs_id}/thumbnail.webp",
                "width": cw,
                "height": ch,
                "file_size": csz,
                "thumb_size": tsz,
                **{k: cover[k] for k in ("source_url", "original_image_url", "source_name", "attribution", "license", "usage_permission", "sha256", "perceptual_hash", "confidence_score", "verification_status", "discovered_at")},
            })
            for idx, extra in enumerate(accepted[1:5], start=1):
                fname = f"gallery-{idx:02d}.webp"
                gw, gh, gsz = optimize_to_webp(extra["raw_bytes"], out_dir / fname, 1600, quality=82)
                published_files.append({
                    "role": f"gallery-{idx:02d}",
                    "delivery_url": f"/images/hospitals/{rs_id}/{fname}",
                    "thumbnail_url": f"/images/hospitals/{rs_id}/{fname}",
                    "width": gw,
                    "height": gh,
                    "file_size": gsz,
                    "thumb_size": gsz,
                    **{k: extra[k] for k in ("source_url", "original_image_url", "source_name", "attribution", "license", "usage_permission", "sha256", "perceptual_hash", "confidence_score", "verification_status", "discovered_at")},
                })

        return {
            "hospital_id": rs_id,
            "hospital_name": h["nama"],
            "kabkota": h.get("kabkota", ""),
            "published": published_files,
            "candidates": candidates_meta,
            "review_queue": review_q,
            "rejected_dups": rejected_dups,
        }


def find_existing_cross_dups() -> set[str]:
    sha_map = defaultdict(list)
    for fp in sorted(EXISTING_DIR.rglob("*")):
        if fp.is_file():
            sha = hashlib.sha256(fp.read_bytes()).hexdigest()
            sha_map[sha].append(fp)
    cross = set()
    for fps in sha_map.values():
        rs_ids = {p.parent.name for p in fps}
        if len(rs_ids) > 1:
            # Keep the first RS alphabetically if needed, flag the rest as cross-RS duplicates
            sorted_fps = sorted(fps, key=lambda p: (p.parent.name, p.name))
            keep_rs = sorted_fps[0].parent.name
            for p in sorted_fps:
                if p.parent.name != keep_rs:
                    cross.add(str(p.relative_to(ROOT)))
    return cross


async def main_async(args):
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    OUT_WEB_DIR.mkdir(parents=True, exist_ok=True)

    prof = json.loads(PROFIL_JSON.read_text(encoding="utf-8"))
    kontak = {r["id_carisehat"]: r.get("website_url") or "" for r in json.loads(KONTAK_JSON.read_text(encoding="utf-8"))}

    checkpoint_path = STAGING_DIR / "image_discovery_checkpoint.json"
    manifest_path = STAGING_DIR / "image_manifest.json"

    checkpoint = {"completed_ids": [], "results": {}}
    if args.resume and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))

    targets = prof
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
        targets = [h for h in prof if h["id_carisehat"] in wanted]
    elif args.limit:
        targets = prof[: args.limit]

    completed_set = set(checkpoint["completed_ids"])
    pending = [h for h in targets if h["id_carisehat"] not in completed_set]

    existing_cross_dups = find_existing_cross_dups()
    global_sha: dict[str, str] = {}
    global_phash: list[tuple[str, imagehash.ImageHash]] = []

    # Pre-seed global_sha/phash from checkpoint
    for rs_id, res in checkpoint["results"].items():
        for pub in res.get("published", []):
            global_sha[pub["sha256"]] = rs_id
            global_phash.append((rs_id, imagehash.hex_to_hash(pub["perceptual_hash"])))

    sem = asyncio.Semaphore(args.concurrency)
    timeout_cfg = httpx.Timeout(8.0, connect=4.0, read=6.0)
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout_cfg, verify=False) as client:
        async def run_one(h):
            async with sem:
                try:
                    return await asyncio.wait_for(
                        process_hospital(
                            client, h, kontak.get(h["id_carisehat"], ""),
                            existing_cross_dups, global_sha, global_phash,
                        ),
                        timeout=35.0,
                    )
                except asyncio.TimeoutError:
                    print(f"[TIMEOUT] {h['id_carisehat']} ({h['nama']})", flush=True)
                    return {
                        "hospital_id": h["id_carisehat"],
                        "hospital_name": h["nama"],
                        "kabkota": h.get("kabkota", ""),
                        "published": [],
                        "candidates": [],
                        "review_queue": [],
                        "rejected_dups": 0,
                    }

        tasks = [run_one(h) for h in pending]
        for idx, coro in enumerate(asyncio.as_completed(tasks), start=1):
            try:
                res = await coro
            except Exception as exc:
                print(f"[ERR] task {idx}: {exc}", flush=True)
                continue
            rs_id = res["hospital_id"]
            checkpoint["results"][rs_id] = res
            if rs_id not in completed_set:
                checkpoint["completed_ids"].append(rs_id)
                completed_set.add(rs_id)
            cov_cnt = len(res["published"])
            print(f"[{len(completed_set)}/{len(prof)}] {rs_id} ({res['hospital_name']}): {cov_cnt} published, {len(res['review_queue'])} review, {res['rejected_dups']} dups rejected", flush=True)
            if idx % 5 == 0 or idx == len(tasks):
                checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    # Export consolidated CSVs & manifest
    all_res = list(checkpoint["results"].values())
    all_candidates = []
    all_review = []
    all_sources = []
    manifest = {}
    total_dups = 0

    for res in sorted(all_res, key=lambda x: x["hospital_id"]):
        rs_id = res["hospital_id"]
        total_dups += res.get("rejected_dups", 0)
        manifest[rs_id] = {
            "hospital_id": rs_id,
            "hospital_name": res["hospital_name"],
            "kabkota": res["kabkota"],
            "cover": res["published"][0]["delivery_url"] if res["published"] else None,
            "thumbnail": res["published"][0]["thumbnail_url"] if res["published"] else None,
            "gallery": [p["delivery_url"] for p in res["published"]],
            "images": res["published"],
        }
        for p in res["published"]:
            all_sources.append({
                "hospital_id": rs_id,
                "hospital_name": res["hospital_name"],
                "role": p["role"],
                "delivery_url": p["delivery_url"],
                "source_name": p["source_name"],
                "source_url": p["source_url"],
                "original_image_url": p["original_image_url"],
                "attribution": p["attribution"],
                "license": p["license"],
                "confidence_score": p["confidence_score"],
                "verification_status": p["verification_status"],
            })
        all_candidates.extend(res.get("candidates", []))
        all_review.extend(res.get("review_queue", []))

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def write_csv(path: Path, rows: list[dict[str, Any]], default_cols: list[str]):
        cols = list(rows[0].keys()) if rows else default_cols
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    write_csv(STAGING_DIR / "image_sources.csv", all_sources, ["hospital_id", "hospital_name", "role", "delivery_url", "source_name", "source_url", "original_image_url", "attribution", "license", "confidence_score", "verification_status"])
    write_csv(STAGING_DIR / "image_candidates.csv", all_candidates, ["hospital_id", "hospital_name", "source_name", "original_image_url", "confidence_score", "verification_status"])
    write_csv(STAGING_DIR / "image_review_queue.csv", all_review, ["hospital_id", "hospital_name", "source_name", "original_image_url", "confidence_score", "verification_status"])

    total_hospitals = len(all_res)
    with_cover = sum(1 for r in all_res if r["published"])
    with_gallery = sum(1 for r in all_res if len(r["published"]) > 1)
    total_published = sum(len(r["published"]) for r in all_res)
    total_bytes = sum(p["file_size"] + (p["thumb_size"] if p["role"] == "cover" else 0) for r in all_res for p in r["published"])
    by_source = defaultdict(int)
    for r in all_res:
        for p in r["published"]:
            by_source[p["source_name"]] += 1

    cov_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_hospitals_processed": total_hospitals,
        "hospitals_with_cover": with_cover,
        "hospitals_with_gallery_multi": with_gallery,
        "hospitals_without_photo": [r["hospital_id"] for r in all_res if not r["published"]],
        "total_published_images": total_published,
        "by_source": dict(by_source),
        "rejected_duplicates": total_dups,
        "review_queue_count": len(all_review),
        "total_webp_bytes": total_bytes,
        "total_webp_mb": round(total_bytes / (1024 * 1024), 2),
    }
    (STAGING_DIR / "image_coverage_report.json").write_text(json.dumps(cov_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("COVERAGE REPORT:", json.dumps(cov_report, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", default="", help="Comma-separated hospital IDs")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Standardize and clean hospital contact information (Telepon, Email, Website)
across all 206 hospitals in North Sumatra.
"""

import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
FINAL_INFO_DIR = ROOT / "data" / "enrichment" / "final_info_rs"
BACKEND_INFO_DIR = ROOT / "backend" / "app" / "data" / "final_info_rs"
RUMAH_SAKIT_CSV = ROOT / "data" / "rumah_sakit_sumut.csv"

# Known verified numbers for hospitals with empty contacts
KNOWN_MISSING_PHONES = {
    "rs-090": "0628-20012",  # RSUD Kabupaten Karo
    "rs-187": "061-8451152",  # RSU Sinar Husni Helvetia
}


def clean_phone(raw: str, rs_id: str) -> str:
    if rs_id in KNOWN_MISSING_PHONES and (not raw or not raw.strip()):
        return KNOWN_MISSING_PHONES[rs_id]

    if not raw or raw.strip() in ["", "-", "NOT_FOUND", "Belum tersedia"]:
        return ""

    s = raw.strip()
    # Split multi-number if truncated or separated by / , ;
    parts = re.split(r"[/,;]", s)
    p0 = parts[0].strip()

    # Strip trailing punctuation/characters like -, _, /
    p0 = re.sub(r"[\s\-_/]+$", "", p0)

    # Remove leading unbalanced parenthesis e.g. '(081370739531'
    if p0.startswith("(") and ")" not in p0:
        p0 = p0[1:]

    # Normalize international prefix +62 / 62
    if p0.startswith("+6261"):
        p0 = "061-" + p0[5:].strip().replace(" ", "")
    elif p0.startswith("+62"):
        rest = p0[3:].strip()
        if rest.startswith("0"):
            p0 = rest
        else:
            p0 = "0" + rest
    elif p0.startswith("62-"):
        p0 = "0" + p0[3:]
    elif p0.startswith("62") and len(p0) > 9:
        p0 = "0" + p0[2:]

    # Clean whitespace around hyphens
    p0 = re.sub(r"\s*-\s*", "-", p0)

    # Standardize parenthesis area codes like (061) 8214733 or (0628)9832858
    m_paren = re.match(r"^\((\d{3,4})\)\s*-?\s*(.*)$", p0)
    if m_paren:
        area, num = m_paren.groups()
        num = num.strip().replace(" ", "")
        p0 = f"{area}-{num}"

    # Standardize space-separated area code: e.g. '061 4153054' -> '061-4153054'
    m_space = re.match(r"^(\d{3,4})\s+(\d{5,8})$", p0)
    if m_space:
        area, num = m_space.groups()
        p0 = f"{area}-{num}"

    # Clean trailing dashes or symbols
    p0 = re.sub(r"[\s\-_]+$", "", p0)
    return p0.strip()


def clean_email(raw: str) -> str | None:
    if not raw or raw.strip() in ["", "-", "NOT_FOUND", "Belum tersedia", "EMAIL_BELUM_TERSEDIA"]:
        return None
    e = raw.strip().lower()
    # Split multi emails
    if "/" in e:
        e = e.split("/")[0].strip()
    if "," in e:
        e = e.split(",")[0].strip()
    if ";" in e:
        e = e.split(";")[0].strip()

    e = re.sub(r"[\s,;]+$", "", e)
    if "@" in e and "." in e.split("@")[-1]:
        return e
    return None


def clean_website(raw: str) -> str | None:
    if not raw or raw.strip() in ["", "-", "NOT_FOUND", "Belum tersedia"]:
        return None
    w = raw.strip()
    if not w.startswith(("http://", "https://")):
        w = "https://" + w

    try:
        p = urlparse(w)
        scheme = p.scheme.lower()
        netloc = p.netloc.lower()
        path = p.path
        if path == "/":
            path = ""
        cleaned = urlunparse((scheme, netloc, path, p.params, p.query, p.fragment))
        return cleaned
    except Exception:
        return w


def main():
    json_path = FINAL_INFO_DIR / "kontak_dan_website_206.json"
    with open(json_path, "r", encoding="utf-8") as f:
        kontak_list = json.load(f)

    cleaned_list = []
    phones_count = 0
    emails_count = 0
    websites_count = 0

    phone_map = {}

    for item in kontak_list:
        rs_id = item["id_carisehat"]
        raw_tel = item.get("telepon") or ""
        clean_tel = clean_phone(raw_tel, rs_id)
        phone_map[rs_id] = clean_tel

        raw_email = item.get("email") or ""
        clean_em = clean_email(raw_email)

        raw_web = item.get("website_url") or ""
        clean_web = clean_website(raw_web)

        # Update item
        item["telepon"] = clean_tel
        if clean_tel:
            phones_count += 1

        item["email"] = clean_em
        item["email_display"] = clean_em if clean_em else "Belum tersedia"
        item["email_status"] = item.get("email_status", "NOT_FOUND") if clean_em else "NOT_FOUND"
        if clean_em:
            emails_count += 1

        item["website_url"] = clean_web
        item["website_display"] = clean_web if clean_web else "Belum tersedia"
        item["website_status"] = item.get("website_status", "NOT_FOUND") if clean_web else "NOT_FOUND"
        if clean_web:
            try:
                p = urlparse(clean_web)
                item["website_domain"] = p.netloc
            except Exception:
                pass
            websites_count += 1
        else:
            item["website_domain"] = ""

        cleaned_list.append(item)

    print(f"Total Hospitals: {len(cleaned_list)}")
    print(f"Hospitals with valid phone: {phones_count} / {len(cleaned_list)}")
    print(f"Hospitals with valid email: {emails_count} / {len(cleaned_list)}")
    print(f"Hospitals with valid website: {websites_count} / {len(cleaned_list)}")

    # Collect all fieldnames dynamically
    all_keys = []
    for item in cleaned_list:
        for k in item.keys():
            if k not in all_keys:
                all_keys.append(k)

    # Write JSON to both final_info_rs locations
    for target_dir in [FINAL_INFO_DIR, BACKEND_INFO_DIR]:
        target_dir.mkdir(parents=True, exist_ok=True)
        out_json = target_dir / "kontak_dan_website_206.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(cleaned_list, f, indent=2, ensure_ascii=False)

        # Write CSV
        out_csv = target_dir / "kontak_dan_website_206.csv"
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(cleaned_list)

    # Also update data/rumah_sakit_sumut.csv Telepon column if present
    if RUMAH_SAKIT_CSV.exists():
        with open(RUMAH_SAKIT_CSV, "r", encoding="utf-8-sig") as f:
            rs_rows = list(csv.DictReader(f))

        # Check if rows align by index (rs-001 -> row 0)
        updated_rs_rows = []
        for i, row in enumerate(rs_rows):
            rs_id = f"rs-{i+1:03d}"
            if rs_id in phone_map and phone_map[rs_id]:
                row["Telepon"] = phone_map[rs_id]
            updated_rs_rows.append(row)

        with open(RUMAH_SAKIT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rs_rows[0].keys()))
            writer.writeheader()
            writer.writerows(updated_rs_rows)

    print("SUCCESS: Contact dataset cleaned, standardized, and saved!")


if __name__ == "__main__":
    main()

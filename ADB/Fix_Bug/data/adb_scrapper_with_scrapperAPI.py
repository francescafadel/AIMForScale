"""
ADB Project Description Extractor — via ScraperAPI
====================================================
Run test (5 projects):
    python adb_scrapper_with_scrapperAPI.py --test 5

Full run:
    python adb_scrapper_with_scrapperAPI.py
"""

import argparse
import csv
import random
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Settings ──────────────────────────────────────────────────────────────────

CSV_FILE        = Path("/Users/francesca/Desktop/AIMForScale/ADB/Fix_Bug/data/Final ADB Corpus - Unique.csv")
API_KEY         = "ee48012eab0863c9c7d54f036972c5a8"

DELAY_SECONDS   = (1.0, 2.5)
REQUEST_TIMEOUT = 60
MAX_RETRIES     = 3


# ── Fetch one project description ─────────────────────────────────────────────

def fetch_description(session, project_url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            scraper_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={project_url}&render=false"
            resp = session.get(scraper_url, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = 15 * attempt
                print(f"    ⚠ Rate limited — waiting {wait}s...")
                time.sleep(wait)
                continue

            if not resp.ok:
                print(f"    ✗ HTTP {resp.status_code} (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(5 * attempt)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Strategy 1: <dt>Description</dt> → grab entire <dd> content
            # This is PRIMARY — gets the full multi-paragraph description
            for dt in soup.find_all("dt"):
                if dt.get_text(strip=True).lower() == "description":
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        text = " ".join(dd.get_text(" ", strip=True).split())
                        if len(text) > 30:
                            return text

            # Strategy 2: <meta name="description"> — FALLBACK only
            # Shorter (first paragraph only) but always present
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content", "").strip():
                content = meta["content"].strip()
                if len(content) > 30:
                    return content

            print(f"    ⚠ Page loaded but no description found (attempt {attempt}/{MAX_RETRIES})")

        except requests.exceptions.Timeout:
            print(f"    ✗ Timeout (attempt {attempt}/{MAX_RETRIES})")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:80]}")
            return ""

        if attempt < MAX_RETRIES:
            time.sleep(5 * attempt)

    return ""


# ── CSV helpers ───────────────────────────────────────────────────────────────

def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f))

def save_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

def find_header(rows):
    for i, row in enumerate(rows):
        if "Project Link" in row or (row and row[0] == "Project ID"):
            return i
    raise ValueError("Header row not found.")

def find_col(header, name):
    for i, c in enumerate(header):
        if c.strip() == name:
            return i
    raise ValueError(f"Column '{name}' not found.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(test_size=None):
    if not CSV_FILE.exists():
        print(f"ERROR: CSV not found at {CSV_FILE}")
        return

    rows       = load_csv(CSV_FILE)
    header_idx = find_header(rows)
    header     = rows[header_idx]
    link_col   = find_col(header, "Project Link")
    desc_col   = find_col(header, "Description")

    # Collect unique projects that still need a description
    seen_ids   = set()
    to_process = []

    data_rows = rows[header_idx + 1:]
    if test_size:
        data_rows = data_rows[:test_size]

    for i, row in enumerate(data_rows, start=header_idx + 1):
        if len(row) <= link_col or not row[link_col].strip():
            continue
        url = row[link_col].strip()
        pid = row[0].strip() if row else ""

        # Skip already filled
        existing = row[desc_col].strip() if len(row) > desc_col else ""
        if existing:
            continue

        # Skip duplicates
        if pid and pid in seen_ids:
            continue
        if pid:
            seen_ids.add(pid)

        to_process.append((i, url))

    total = len(to_process)
    print(f"Found {total} projects needing descriptions.\n")

    session   = requests.Session()
    succeeded = 0

    for count, (row_idx, url) in enumerate(to_process, start=1):
        print(f"[{count}/{total}] {url}")

        desc = fetch_description(session, url)

        while len(rows[row_idx]) <= desc_col:
            rows[row_idx].append("")
        rows[row_idx][desc_col] = desc

        if desc:
            succeeded += 1
            preview = desc[:150] + ("..." if len(desc) > 150 else "")
            print(f"    ✓ ({len(desc)} chars) {preview}")

        # Save after every row — never lose progress
        save_csv(rows, CSV_FILE)

        if count < total:
            time.sleep(random.uniform(*DELAY_SECONDS))

    print(f"\n{'='*60}")
    print(f"Done! {succeeded}/{total} descriptions filled.")
    print(f"Saved to: {CSV_FILE.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, metavar="N",
                        help="Only process first N projects")
    args = parser.parse_args()
    main(test_size=args.test)
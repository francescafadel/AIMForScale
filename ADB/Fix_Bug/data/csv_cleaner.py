"""
CSV Deduplicator
=================
Reads the ADB CSV and keeps only one row per unique Project ID.
Saves a new clean CSV so the scraper only processes unique projects.

Run:
    python csv_cleaner.py
"""

import csv
from pathlib import Path

# ── Edit these paths ──────────────────────────────────────────────────────────

INPUT_CSV  = Path("/Users/bipu/Desktop/AIMForScale/ADB/Fix_Bug/data/Final ADB Corpus - Sheet1_with_urls.csv")
OUTPUT_CSV = Path("/Users/bipu/Desktop/AIMForScale/ADB/Fix_Bug/data/Final ADB Corpus - Unique.csv")

# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not INPUT_CSV.exists():
        print(f"ERROR: File not found at {INPUT_CSV}")
        return

    # Load all rows
    with open(INPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.reader(f))

    # Find header row
    header_idx = None
    for i, row in enumerate(rows):
        if row and (row[0] == "Project ID" or "Project Link" in row):
            header_idx = i
            break

    if header_idx is None:
        print("ERROR: Could not find header row.")
        return

    header    = rows[header_idx]
    data_rows = rows[header_idx + 1:]

    # Project ID is the first column
    pid_col = 0

    # Deduplicate — keep first occurrence of each Project ID
    seen     = set()
    unique   = []
    skipped  = 0

    for row in data_rows:
        pid = row[pid_col].strip() if row else ""
        if not pid:
            continue   # skip completely empty rows
        if pid in seen:
            skipped += 1
            continue
        seen.add(pid)
        unique.append(row)

    # Write clean CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Write any rows before the header (e.g. title rows) as-is
        for row in rows[:header_idx]:
            writer.writerow(row)
        writer.writerow(header)
        writer.writerows(unique)

    print(f"Original rows : {len(data_rows)}")
    print(f"Duplicates    : {skipped}")
    print(f"Unique rows   : {len(unique)}")
    print(f"\nClean CSV saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
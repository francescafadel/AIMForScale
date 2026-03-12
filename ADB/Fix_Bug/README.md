# Fix_Bug

This folder contains copies of the documents your coder should use to debug and fix the ADB description extraction scraper. Files are organized by type and labeled below.

## Must read / use

| File | Purpose |
|------|---------|
| `data/Final ADB Corpus - Sheet1_with_urls.csv` | CSV with Project IDs, Project Link column (hyperlinks to ADB project pages), and Description column to fill. |
| `scripts/adb_description_extractor.py` | Main Playwright script: navigates to each link, opens Project Data Sheet, extracts Description. |
| `docs/ISSUES_ANALYSIS.md` | Documented issues (Cloudflare, tab click, selectors, timing) and proposed fixes. |

## Strongly recommended

| File | Purpose |
|------|---------|
| `docs/TEST_RESULTS.md` | Test run outcomes, success rates, and sample failed URLs. |
| `scripts/scrape_adb_descriptions.py` | Alternative scraper implementation (pandas-based). |
| `tests/test_single_url.py` | Single-URL test script for quick debugging. |
| `docs/USAGE.md` | How to run the extractor and tests. |
| `requirements.txt` | Python dependencies (pandas, playwright). |

## Folder layout

- `data/` – Input CSV with project links.
- `scripts/` – Main and alternative extraction scripts.
- `docs/` – Issues, test results, and usage.
- `tests/` – Single-URL test script.

Run scripts from the `Fix_Bug` directory (or set paths as needed). See `docs/USAGE.md` for commands.

The copy of `adb_description_extractor.py` in `scripts/` is already configured to read and write the CSV in `data/Final ADB Corpus - Sheet1_with_urls.csv`. Header detection works for both "Project ID" in the first column and for CSVs where "Project Link" appears in the first row (e.g. Sheet1_with_urls); in the latter case the first row is treated as the header, so the very first data row in that file is not processed.

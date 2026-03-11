# ADB Project Description Extraction

Automated tool to extract project descriptions from Asian Development Bank (ADB) project pages.

## Features

- **Direct Navigation**: Bypasses clicking by navigating directly to `/pds` URLs
- **Force Click Strategy**: Aggressive clicking with `force=True` to bypass overlays
- **Multiple Extraction Methods**: Handles different page structures (table rows, dt/dd elements)
- **Duplicate Handling**: Automatically skips duplicate project IDs
- **Cloudflare Bypass**: Handles Cloudflare protection with appropriate waits
- **Rate Limiting**: Polite delays between requests

## Project Structure

```
ADB/Project Description Extraction/
├── scripts/
│   ├── adb_description_extractor.py  # Main extraction script (Path-based paths)
│   ├── extract_descriptions_test_3_fixed.py  # Same logic, paths for data/
│   └── scrape_adb_descriptions.py   # Alternative scraper
├── tests/
│   ├── extract_descriptions_test_5.py
│   ├── extract_descriptions_test_batch.py
│   ├── scrape_adb_descriptions_test.py
│   └── test_single_url.py
├── data/
│   └── [CSV and Numbers files]
├── docs/
│   ├── ISSUES_ANALYSIS.md
│   ├── TEST_RESULTS.md
│   └── USAGE.md
├── utils/
│   └── add_description_column_header.py
├── requirements.txt
├── README.md
├── PROJECT_README.md          # Original project README
├── push_adb_to_github.py      # Copy this folder into AIMForScale repo
├── DIAGNOSE_AND_PUSH.py       # Diagnose paths + copy + git status
├── setup_repo.py              # Organize files into this structure
├── HOW_TO_PUSH_TO_GITHUB.md   # Instructions to push to GitHub
└── COPY_PASTE_COMMANDS.txt    # Terminal commands (no Python)
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browser:
```bash
playwright install chromium
```

## Usage

### Test Run (First 5 URLs)
```bash
cd scripts
python adb_description_extractor.py
```

### Configuration

Edit the configuration in `scripts/adb_description_extractor.py`:

```python
TEST_SIZE = 5  # Change to process more URLs
INPUT_CSV = DATA_DIR / "Copy of Final ADB Corpus - Link Extraction File.csv"
OUTPUT_CSV = DATA_DIR / "Copy of Final ADB Corpus - Link Extraction File.csv"
```

## Extraction Strategies

1. **Direct Navigation**: If URL ends with `/main`, navigates directly to `/pds`
2. **Force Click**: Uses `force=True` to click "Project Data Sheet" tab even if overlapped
3. **Table Row Extraction**: Looks for `<tr>` elements with "Description" label
4. **Definition List Extraction**: Extracts from `<dt>/<dd>` HTML structure

## Notes

- The script automatically skips duplicate project IDs
- Rate limiting: 1-2 second delays between requests
- Handles Cloudflare protection automatically
- Saves progress after each batch

---

## What each document contains

Use this section to find where a file lives and what it is for.

### Scripts (`scripts/`)

| File | Description |
|------|-------------|
| **adb_description_extractor.py** | Main extraction script. Reads project URLs from the working CSV, navigates to each ADB project page (or directly to `/pds`), clicks “Project Data Sheet” if needed, extracts the Description text, and writes it into the Description column. Supports test-size limits and duplicate-ID skipping. |
| **scrape_adb_descriptions.py** | Alternative scraper with a different navigation/wait strategy. Can be used if the main script has issues on certain pages. |

### Tests (`tests/`)

| File | Description |
|------|-------------|
| **extract_descriptions_test_5.py** | Runs the extraction logic on the first 5 URLs (or a small batch) to verify the pipeline without a full run. |
| **extract_descriptions_test_batch.py** | Batch-oriented test script for running extraction on a configurable number of rows. |
| **scrape_adb_descriptions_test.py** | Test harness for the alternative scraper (`scrape_adb_descriptions.py`). |
| **test_single_url.py** | Single-URL test; opens one project page (e.g. in headed browser) for debugging clicks and description extraction. |

### Data (`data/`)

| File | Description |
|------|-------------|
| **Copy of Final ADB Corpus - Link Extraction File.csv** | Working CSV used by the main extractor: project IDs, metadata, a “Project Link” column (URLs), and a “Description” column that the script fills. Input and output for the pipeline. |
| **Final ADB Corpus - Link Extraction File.csv** | Source corpus exported from the Numbers “Link Extraction File”; may include intro rows. Used to create or compare with the “Copy of…” working file. |
| **Final ADB Corpus - Sheet1_with_urls.csv** | Earlier corpus with project IDs and a column of project page URLs. |
| **Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv** | Corpus with URLs and extracted descriptions (e.g. from a previous full run). |
| **Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv** | Test-run output: same structure as above but only for the rows used in a test (e.g. first 5). |
| **ADB Working document.csv** | Deduplicated working corpus; can be used as an alternative input after removing duplicate project rows. |
| **Final ADB Corpus - Link Extraction File .numbers** | Original Numbers workbook for the link-extraction corpus. |
| **Final ADB Corpus, Insert to Cursor.numbers** | Numbers workbook used for preparing or curating the corpus (e.g. for Cursor). |

### Documentation (`docs/`)

| File | Description |
|------|-------------|
| **ISSUES_ANALYSIS.md** | Notes on extraction failures (e.g. domcontentloaded vs load, click timing, Cloudflare) and the fixes applied (e.g. direct `/pds` navigation, force click). |
| **TEST_RESULTS.md** | Summary of test runs: success rate, sample extractions, and known limitations. |
| **USAGE.md** | Step-by-step instructions for installing dependencies, running the scraper, and interpreting progress output. |

### Utils (`utils/`)

| File | Description |
|------|-------------|
| **add_description_column_header.py** | Adds a “Description” column to the working CSV and pads rows so every row has the same number of columns. Run once before the first extraction if your CSV does not yet have a Description column. |

### Root of Project Description Extraction

| File | Description |
|------|-------------|
| **requirements.txt** | Python dependencies (e.g. `playwright`). Install with `pip install -r requirements.txt`; then run `playwright install chromium`. |
| **README.md** | This file: overview, structure, installation, usage, and what each document contains. |

---

## Documentation (quick links)

- **ISSUES_ANALYSIS.md** (`docs/`): Detailed analysis of extraction issues and fixes.
- **TEST_RESULTS.md** (`docs/`): Test run results and statistics.
- **USAGE.md** (`docs/`): How to run the scraper and interpret output.

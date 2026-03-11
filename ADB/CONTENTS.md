# ADB folder — complete file list (all code and data we created)

This file lists every script, data file, and document that belongs to the ADB work. Use it to check that nothing is missing when you push to GitHub.

---

## Scripts (Python code)

| Path | Purpose |
|------|---------|
| `Project Description Extraction/scripts/adb_description_extractor.py` | Main extractor: direct /pds navigation, force click, table + dt/dd extraction, duplicate-ID skip. |
| `Project Description Extraction/scripts/scrape_adb_descriptions.py` | Alternative scraper. |
| `Project Description Extraction/utils/add_description_column_header.py` | Adds the Description column to the working CSV. |

## Test scripts

| Path | Purpose |
|------|---------|
| `Project Description Extraction/tests/extract_descriptions_test_5.py` | Test on first 5 URLs. |
| `Project Description Extraction/tests/extract_descriptions_test_batch.py` | Batch test script. |
| `Project Description Extraction/tests/scrape_adb_descriptions_test.py` | Test for alternative scraper. |
| `Project Description Extraction/tests/test_single_url.py` | Single-URL debug test. |

## Data (CSVs)

| Path | Purpose |
|------|---------|
| `Project Description Extraction/data/Copy of Final ADB Corpus - Link Extraction File.csv` | Main working CSV (Project Link + Description columns). |
| `Project Description Extraction/data/Final ADB Corpus - Link Extraction File.csv` | Source corpus. |
| `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls.csv` | Corpus with URLs. |
| `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv` | Corpus with URLs and descriptions. |
| `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv` | Test-run output. |
| `Project Description Extraction/data/ADB Working document.csv` | Deduplicated working corpus. |

## Documentation

| Path | Purpose |
|------|---------|
| `Project Description Extraction/docs/ISSUES_ANALYSIS.md` | Extraction issues and fixes. |
| `Project Description Extraction/docs/TEST_RESULTS.md` | Test run results. |
| `Project Description Extraction/docs/USAGE.md` | How to run the scraper. |

## Config and READMEs

| Path | Purpose |
|------|---------|
| `Project Description Extraction/requirements.txt` | Python dependencies. |
| `README.md` | ADB folder overview (this repo). |
| `ADB Links/README.md` | What goes in ADB Links. |
| `Project Description Extraction/README.md` | Setup, usage, and what each file contains. |

---

If you do not see these files under `ADB/` on GitHub, copy the entire **ADB** folder from your local **ADB Project Description Extraction** project into your **AIMForScale** repo and push.

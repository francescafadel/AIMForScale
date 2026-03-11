# ADB (Asian Development Bank)

This folder contains materials related to the **Asian Development Bank (ADB)** for the AIMForScale project. It is organized into two main areas: **ADB Links** (project corpus and URL generation) and **Project Description Extraction** (automated scraping of project descriptions from ADB project pages).

---

## Contents of this folder (what you should see)

| Name | Description |
|------|-------------|
| **README.md** | This file. Overview of the ADB folder and where everything is. |
| **CONTENTS.md** | **Full list of every file we created** — all scripts, data, and docs. Use this to confirm you see all the code. |
| **ADB Links/** | Corpus CSVs and script to add project URLs. Contains `README.md` describing what goes here. |
| **Project Description Extraction/** | Full pipeline: scripts, tests, data, docs, utils. Open its `README.md` for per-file descriptions. |

If you do not see **ADB Links** or **Project Description Extraction** as subfolders, they may not have been pushed to GitHub yet—see “Adding this ADB folder to your GitHub repo” below.

---

## Complete list of code and files (everything we created)

Use this list to confirm all the code and data from our work are present. Every file should exist under `ADB/` when you push to GitHub.

**Scripts (Python code we wrote)**  
- `Project Description Extraction/scripts/adb_description_extractor.py` — main extractor (direct /pds navigation, force click, table + dt/dd extraction)  
- `Project Description Extraction/scripts/scrape_adb_descriptions.py` — alternative scraper  
- `Project Description Extraction/utils/add_description_column_header.py` — adds Description column to CSV  

**Test scripts**  
- `Project Description Extraction/tests/extract_descriptions_test_5.py`  
- `Project Description Extraction/tests/extract_descriptions_test_batch.py`  
- `Project Description Extraction/tests/scrape_adb_descriptions_test.py`  
- `Project Description Extraction/tests/test_single_url.py`  

**Data (CSVs used and produced by the pipeline)**  
- `Project Description Extraction/data/Copy of Final ADB Corpus - Link Extraction File.csv` — main working CSV (URLs + Description column)  
- `Project Description Extraction/data/Final ADB Corpus - Link Extraction File.csv`  
- `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls.csv`  
- `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv`  
- `Project Description Extraction/data/Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv`  
- `Project Description Extraction/data/ADB Working document.csv`  

**Documentation**  
- `Project Description Extraction/docs/ISSUES_ANALYSIS.md` — extraction issues and fixes  
- `Project Description Extraction/docs/TEST_RESULTS.md` — test run results  
- `Project Description Extraction/docs/USAGE.md` — how to run the scraper  

**Config**  
- `Project Description Extraction/requirements.txt` — Python dependencies  

**READMEs**  
- `README.md` — this file  
- `ADB Links/README.md` — what goes in ADB Links  
- `Project Description Extraction/README.md` — setup, usage, and what each file contains  

If any of these are missing in your clone or on GitHub, copy the full **ADB** folder from your local **ADB Project Description Extraction** project into **AIMForScale** and push again (see below).

---

## Where everything is

```
ADB/
├── README.md                          ← You are here. Overview of the ADB folder.
├── ADB Links/                         ← Corpus and URLs
│   └── README.md                      (what to put here: CSVs, add_adb_urls.py)
└── Project Description Extraction/    ← Description scraping pipeline
    ├── README.md                      ← How to run the extractor; what each file does
    ├── requirements.txt               ← Python dependencies
    ├── scripts/                       ← Main and alternative scrapers
    ├── tests/                         ← Test scripts (small batches, single URL)
    ├── data/                          ← Input/output CSVs and Numbers files
    ├── docs/                          ← Analysis, results, usage notes
    └── utils/                         ← Helper scripts (e.g. add Description column)
```

---

## What each part contains

### `ADB Links/`

| Item | Description |
|------|-------------|
| **Final ADB Corpus - Sheet1.csv** | Base CSV corpus of ADB projects (project IDs and metadata). |
| **Final ADB Corpus - Sheet1_with_urls.csv** | Same corpus with an added column of project page URLs (`https://www.adb.org/projects/{Project ID}/main`). |
| **add_adb_urls.py** | Python script that generates the URL column from the Project ID column. |

Use this subfolder when you need the list of ADB projects and their links; the extractor pipeline reads from similar corpora in **Project Description Extraction/data/**.

---

### `Project Description Extraction/`

Automated pipeline to visit each ADB project page, open the “Project Data Sheet” view, and extract the **Description** text into a CSV column.

| Location | Contents |
|----------|----------|
| **README.md** | Setup, usage, and a **per-file description** of every script, data file, and document in this subfolder. |
| **requirements.txt** | Python dependencies (e.g. `playwright`). Install with `pip install -r requirements.txt` and run `playwright install chromium`. |
| **scripts/** | Main extraction script and alternative scraper. See **Project Description Extraction/README.md** for what each script does. |
| **tests/** | Test scripts (e.g. first 5 URLs, single URL, batch tests) to validate the pipeline before a full run. |
| **data/** | Input CSVs (e.g. “Final ADB Corpus - Link Extraction File”, “Copy of…”), output CSVs with a Description column, and any Numbers exports. See the subfolder README for a list of each file. |
| **docs/** | ISSUES_ANALYSIS.md (extraction issues and fixes), TEST_RESULTS.md (run results), USAGE.md (how to run the scraper). |
| **utils/** | Helper scripts (e.g. adding the “Description” column header to the working CSV). |

For **detailed descriptions of every document and script** in Project Description Extraction, open **Project Description Extraction/README.md**.

---

## Quick start (Project Description Extraction)

1. **Install dependencies** (from the repo root or from `ADB/Project Description Extraction/`):
   ```bash
   pip install -r "ADB/Project Description Extraction/requirements.txt"
   playwright install chromium
   ```
2. **Run a small test** (from `ADB/Project Description Extraction/`):
   ```bash
   cd "ADB/Project Description Extraction/scripts"
   python adb_description_extractor.py
   ```
   By default this processes a few URLs and writes descriptions into the CSV in `data/`.

3. **Full run**: Adjust `TEST_SIZE` (or equivalent) in the main script to process the full corpus; see **Project Description Extraction/README.md** and **docs/USAGE.md**.

---

## Connection to AIMForScale

This **ADB** folder is part of the **AIMForScale** repository:

- **Repository:** [https://github.com/francescafadel/AIMForScale](https://github.com/francescafadel/AIMForScale)
- **Clone:** `git clone https://github.com/francescafadel/AIMForScale.git`
- After cloning, the ADB materials are under `AIMForScale/ADB/`. The **Project Description Extraction** code and data live in `AIMForScale/ADB/Project Description Extraction/`.

For repository-wide structure and usage, see the main **AIMForScale README.md** in the repo root.

### Adding this ADB folder to your GitHub repo

If you have the ADB folder locally and want it inside [AIMForScale](https://github.com/francescafadel/AIMForScale):

1. **Clone the repo** (if you don’t already have it):
   ```bash
   git clone https://github.com/francescafadel/AIMForScale.git
   cd AIMForScale
   ```
2. **Copy this ADB folder** into the repo so you have `AIMForScale/ADB/` (with `README.md`, `Project Description Extraction/`, and optionally `ADB Links/`).
3. **Commit and push:**
   ```bash
   git add ADB/
   git commit -m "Add ADB folder: Project Description Extraction and README"
   git push origin main
   ```

If the repo already has an `ADB/` or `ADB/ADB Links/` folder, add or replace contents as needed (e.g. add `Project Description Extraction/` and this `README.md`) so the structure matches the “Where everything is” section above.

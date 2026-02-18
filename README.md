# AIMForScale

A data collection and keyword-analysis toolkit for international development project documents from three International Financial Institutions (IFIs): the **World Bank**, the **Inter-American Development Bank (IDB)**, and the **African Development Bank (AfDB)**. The repository stores downloaded project appraisal documents (PADs), project information documents (PIDs), loan proposals, and project abstracts, and provides scripts for downloading, organizing, and scanning those documents for agriculture- and climate-related keywords.

---

## Repository Structure

```
AIMForScale/
├── ADB/
│   └── ADB Links/
├── IDB/
│   ├── IDB documents/
│   ├── analysis/
│   ├── docs/
│   ├── src/
│   └── unsuccessful_attempts/
├── World Bank Documents PAD/
│   └── PID/
│       ├── PAD/PID/
│       ├── Pivot Tables/
│       ├── archive/
│       ├── data/
│       └── ChatGPT Prompt/
└── keyword-search/
    ├── archive/
    ├── config/
    ├── data/
    │   ├── input/
    │   └── processed/
    ├── scripts/
    └── updated/
```

---

## Folder Descriptions

### `ADB/`

Contains materials related to the African Development Bank.

| Subfolder / File | Description |
|---|---|
| `ADB Links/` | A CSV corpus listing AfDB projects (`Final ADB Corpus - Sheet1.csv`), a version with appended document URLs (`Final ADB Corpus - Sheet1_with_urls.csv`), and the Python script (`add_adb_urls.py`) used to generate those URLs. |

---

### `IDB/`

Contains materials related to the Inter-American Development Bank.

| Subfolder / File | Description |
|---|---|
| `IDB documents/` | Downloaded PDF documents (project abstracts, loan proposals, and related files) organized into country-level subfolders. Covers 20 countries/regions: Argentina, Belize, Bolivia, Brazil, Chile, Colombia, Costa Rica, Dominican Republic, Ecuador, El Salvador, Guatemala, Guyana, Haiti, Honduras, Mexico, Paraguay, Peru, Regional, Suriname, and Uruguay. |
| `analysis/` | Script (`analyze_download_results.py`) for evaluating the completeness of downloaded documents. |
| `docs/` | Summaries and logs generated during the document download process, including download summaries, availability analyses, and a research overview (`IDB_Research_Summary.md`). |
| `src/` | The working download script (`ssl_fixed_document_downloader.py`) used to retrieve IDB documents. |
| `unsuccessful_attempts/` | Archive of earlier download scripts that were iterated on before arriving at the working version in `src/`. Kept for reference. |

---

### `World Bank Documents PAD/`

Contains materials related to the World Bank. Everything is nested under a `PID/` subfolder.

| Subfolder / File | Description |
|---|---|
| `PID/PAD/PID/` | Downloaded PAD and PID documents organized by country. Each country folder contains a `PAD/` subfolder with Project Appraisal Documents and a `PID/` subfolder with Project Information Documents. Covers 118 countries and regions (e.g., Republic of India, Federal Republic of Nigeria, Western and Central Africa). |
| `PID/Pivot Tables/` | Pivot table outputs and the script (`make_pivots.py`) that generates them. Includes intervention and outcome category pivots (`intervention_category_pivot.csv`, `outcome_primary_category_pivot.csv`, `outcome_primary_subcategory_pivot.csv`) and a category dictionary (`category_dictionary.csv`). |
| `PID/data/` | Source CSV files used for downloading and analysis, including keyword lists and project abstract datasets (`World Bank 2020-2025 Key Words.csv`, `World Bank With Abstracts pt.2.csv`, etc.). |
| `PID/archive/` | Archived or deprecated files from earlier stages of the workflow. |
| `PID/ChatGPT Prompt/` | Prompt templates used with ChatGPT for document analysis tasks. |
| `PID/wb_downloader.py` | Python script for downloading World Bank PAD/PID documents. |
| `PID/reorganize_by_country.py` | Python script that reorganizes downloaded documents into country-level folders. |
| `PID/requirements.txt` | Python dependencies for the World Bank scripts. |

---

### `keyword-search/`

A cross-IFI keyword scanning pipeline. Takes project corpora from the World Bank, IDB, and AfDB and flags documents containing agriculture- and climate-related keywords.

| Subfolder / File | Description |
|---|---|
| `config/` | Keyword lists used by the scanners (`keywords.txt`, `new_ifi_keywords.txt`). |
| `data/input/` | Raw input CSV files for each IFI corpus (World Bank, IDB, AfDB) before keyword scanning. |
| `data/processed/` | Output CSV files with keyword match columns appended to each input corpus. |
| `scripts/` | Python scanning scripts: `csv_keyword_scanner.py` (scans CSV text fields), `new_ifi_scanner.py` (updated scanner for all IFIs), `pdf_keyword_scanner_improved.py` (scans PDF files directly), and `test_keyword_robustness.py` (tests for keyword matching accuracy). |
| `archive/` | Older versions of processed corpora and intermediate files. |
| `updated/` | Final cleaned corpora for all three IFIs (`Final AfDB Cleaned Corpus.csv`, `Final IDB Cleaned Corpus.csv`, `Final World Bank Cleaned Corpus.csv`) along with the keyword list used. |
| `requirements.txt` | Python dependencies for the keyword-search scripts. |
| `setup_guide.md` | Setup instructions for running the keyword-search pipeline. |

---

## Usage

### Prerequisites

- Python 3.8+
- Install dependencies for each component from its respective `requirements.txt`:

```bash
pip install -r keyword-search/requirements.txt
pip install -r IDB/requirements.txt
pip install -r "World Bank Documents PAD/PID/requirements.txt"
```

### Running the Keyword Search Pipeline

1. Place raw corpus CSVs in `keyword-search/data/input/`.
2. Configure keyword lists in `keyword-search/config/keywords.txt` (one keyword per line).
3. Run the scanner:

```bash
python keyword-search/scripts/csv_keyword_scanner.py
```

4. Find the results in `keyword-search/data/processed/`.

### Downloading World Bank Documents

```bash
python "World Bank Documents PAD/PID/wb_downloader.py"
```

Documents are saved into country-level folders under `World Bank Documents PAD/PID/PAD/PID/`.

### Downloading IDB Documents

```bash
python IDB/src/ssl_fixed_document_downloader.py
```

Documents are saved into country-level folders under `IDB/IDB documents/`.

### Generating Pivot Tables (World Bank)

```bash
python "World Bank Documents PAD/PID/Pivot Tables/make_pivots.py"
```

Output CSVs are written to the `Pivot Tables/` folder.

---

## Language

Python 100%


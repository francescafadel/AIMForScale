# IDB Document Downloader

Automated downloader for Inter-American Development Bank (IDB) project documents. This tool processes a dataset of IDB agriculture and rural development projects and downloads publicly available English documents.

---

## Overview

This project downloads three specific types of English documents from IDB project pages:
- **Loan Proposal Documents** -- documents containing "loan", "proposal", or "loan proposal" in the title
- **Project Proposal Documents** -- documents containing "project proposal" or "proposal document" in the title
- **Project Abstract Documents** -- documents containing "abstract", "synthesis", or "tc abstract" in the title

Key criteria:
- **Language**: Only English documents are downloaded (Spanish documents are identified but skipped)
- **Accessibility**: Only publicly accessible documents are downloaded (no authentication required)
- **Coverage**: All 565 projects in the dataset are processed

---

## Folder Structure

```
IDB/
├── src/
│   └── ssl_fixed_document_downloader.py
├── analysis/
│   └── analyze_download_results.py
├── docs/
├── IDB documents/
├── unsuccessful_attempts/
├── organize_documents.py
├── requirements.txt
└── README.md
```

| Subfolder / File | Description |
|---|---|
| `src/` | The working download script (`ssl_fixed_document_downloader.py`) used to retrieve IDB documents. |
| `analysis/` | Script (`analyze_download_results.py`) for evaluating the completeness of downloaded documents. |
| `docs/` | Summaries and logs generated during the document download process, including download summaries, availability analyses, and a research overview (`IDB_Research_Summary.md`). |
| `IDB documents/` | Downloaded PDF documents (project abstracts, loan proposals, and related files) organized into 20 country-level subfolders: Argentina, Belize, Bolivia, Brazil, Chile, Colombia, Costa Rica, Dominican Republic, Ecuador, El Salvador, Guatemala, Guyana, Haiti, Honduras, Mexico, Paraguay, Peru, Regional, Suriname, and Uruguay. |
| `unsuccessful_attempts/` | Archive of earlier download scripts that were iterated on before arriving at the working version in `src/`. Kept for reference. |
| `organize_documents.py` | Script that reorganizes downloaded documents into country-level folders. |
| `requirements.txt` | Python dependencies for the IDB scripts. |

---

## Usage

### Prerequisites

- Python 3.7+
- Required packages (see `requirements.txt`)
- `curl` command-line tool (for SSL bypass)

### Installation

```bash
pip install -r requirements.txt
```

### Running the Downloader

1. Navigate to the IDB directory:

```bash
cd IDB
```

2. Run the main downloader:

```bash
python src/ssl_fixed_document_downloader.py
```

The script will:
- Access each project page on the IDB website
- Download English documents of the requested types
- Organize downloads by country in the `IDB documents/` folder

### Running the Analysis

```bash
python analysis/analyze_download_results.py
```

---

## Results

- **Total Projects Processed**: 565
- **Projects with Documents**: 81 (14.3%)
- **Total Documents Downloaded**: 107
- **English Documents**: 79
- **Success Rate**: 100% for documents found

### Document Types Found

- Loan Proposal Documents: 17 projects
- Project Proposal Documents: 0 projects
- Project Abstract Documents: 65 projects

### Top Countries by Documents

1. Bolivia: 24 documents
2. Peru: 17 documents
3. Regional: 11 documents
4. Brazil: 9 documents
5. Colombia: 8 documents

---

## Technical Details

### SSL Bypass Solution

The IDB document server has SSL certificate issues. The script uses multiple fallback methods:
1. `curl` with `--insecure` flag (primary method)
2. `wget` with `--no-check-certificate`
3. `requests` with SSL verification disabled

### Document Classification

Documents are classified by matching keywords in their titles:
- **Loan Proposal**: "loan", "proposal", "loan proposal"
- **Project Proposal**: "project proposal", "proposal document"
- **Project Abstract**: "abstract", "synthesis", "tc abstract"

### Language Filtering

Only English documents are downloaded. Spanish documents are identified but skipped.

---

## Notes

- Documents are organized by country in the `IDB documents/` folder
- All downloads are publicly accessible documents only
- The main working script is `src/ssl_fixed_document_downloader.py`
- Previous unsuccessful attempts are archived in `unsuccessful_attempts/` for reference
- Large download files are excluded from git (see `.gitignore`)

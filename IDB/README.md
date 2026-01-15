# IDB Document Downloader

Automated downloader for Inter-American Development Bank (IDB) project documents. This tool processes a dataset of IDB agriculture and rural development projects and downloads publicly available English documents.

## 📋 Overview

This project downloads three specific types of English documents from IDB project pages:
- **Loan Proposal Documents**
- **Project Proposal Documents**
- **Project Abstract Documents**

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Required packages (see `requirements.txt`)
- `curl` command-line tool (for SSL bypass)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

1. Navigate to the IDB directory:
```bash
cd IDB
```

2. Place your project data CSV file in the `data/` directory
3. Run the main downloader:

```bash
python src/ssl_fixed_document_downloader.py
```

The script will:
- Load projects from `data/IDB Corpus Key Words.csv`
- Access each project page on the IDB website
- Download English documents of the requested types
- Organize downloads by country in the `downloads/` folder
- Generate a tracking CSV in `data/ssl_fixed_document_tracking.csv`

### Analysis

To analyze the download results:

```bash
cd IDB
python analysis/analyze_download_results.py
```

## 📁 Project Structure

```
.
├── src/                          # Main working scripts
│   └── ssl_fixed_document_downloader.py
├── analysis/                     # Analysis scripts
│   └── analyze_download_results.py
├── data/                         # Data files (CSV, tracking)
│   ├── IDB Corpus Key Words.csv
│   └── ssl_fixed_document_tracking.csv
├── docs/                         # Documentation
├── downloads/                    # Downloaded documents (by country)
├── unsuccessful_attempts/        # Previous failed attempts (archived)
├── requirements.txt
└── README.md
```

## 📊 Results

- **Total Projects Processed**: 565
- **Projects with Documents**: 81 (14.3%)
- **Total Documents Downloaded**: 107
- **English Documents**: 79
- **Success Rate**: 100% for documents found

### Document Types Found:
- Loan Proposal Documents: 17 projects
- Project Proposal Documents: 0 projects
- Project Abstract Documents: 65 projects

### Top Countries by Documents:
1. Bolivia: 24 documents
2. Peru: 17 documents
3. Regional: 11 documents
4. Brazil: 9 documents
5. Colombia: 8 documents

## 🔧 Technical Details

### SSL Bypass Solution

The IDB document server has SSL certificate issues. The script uses multiple fallback methods:
1. **curl** with `--insecure` flag (primary method)
2. **wget** with `--no-check-certificate`
3. **requests** with SSL verification disabled

### Document Classification

Documents are classified by matching keywords in their titles:
- **Loan Proposal**: "loan", "proposal", "loan proposal"
- **Project Proposal**: "project proposal", "proposal document"
- **Project Abstract**: "abstract", "synthesis", "tc abstract"

### Language Filtering

Only English documents are downloaded. Spanish documents are identified but skipped.

## 📝 Notes

- Documents are organized by country in the `downloads/` folder
- The tracking CSV provides detailed information about which projects have which document types
- Some documents may be categorized as "Unknown" country due to incomplete country code mapping
- All downloads are publicly accessible documents only

## ⚠️ Important

- The main working script is `src/ssl_fixed_document_downloader.py` - **do not modify this file**
- Previous unsuccessful attempts are archived in `unsuccessful_attempts/` for reference
- Large download files are excluded from git (see `.gitignore`)

## 📄 License

[Add your license here]

## 👤 Author

[Add your name/info here]


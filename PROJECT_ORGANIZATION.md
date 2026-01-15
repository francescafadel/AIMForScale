# Project Organization

This document describes the reorganized structure of the World Bank Document Downloader project.

## Directory Structure

```
World Bank Documents/
├── wb_downloader.py          # Main Python application
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── CLEANUP_REPORT.md         # Cleanup documentation
├── PROJECT_ORGANIZATION.md   # This file
│
├── data/                      # Input CSV files
│   ├── World Bank 2020-2025 Key Words.csv
│   ├── World Bank With Key Words pt.1.csv
│   ├── World Bank With Abstracts pt.2.csv
│   └── World Bank pt2 clean.csv
│
├── test_runs/                 # Test files and test results
│   ├── README.md
│   ├── test_*.csv
│   ├── test_downloader.py
│   ├── sample_projects.csv
│   └── test_downloads_real/  # Actual test download results
│
├── results/                   # All download results
│   └── full_downloads/        # Consolidated results directory
│       ├── full_downloads/    # Results from dataset 1
│       ├── full_downloads_pt2/ # Results from dataset 2
│       ├── manifest.csv       # Download tracking
│       └── summary.csv        # Project statistics
│
└── archive/                   # Archived files (currently empty)
    └── README.md
```

## Organization Principles

1. **Code**: Main application files in root directory
2. **Data**: All input CSV files in `data/` directory
3. **Test Runs**: All test files and test results in `test_runs/` directory
4. **Results**: All download results consolidated in `results/full_downloads/`
5. **Archive**: Reserved for archived files

## What's Ignored by Git

- `results/full_downloads/` - Large download directories (can be regenerated)
- `test_runs/` - Test files and test results
- System files (`.DS_Store`, etc.)
- Python cache files

## GitHub Repository

This project is now connected to: **https://github.com/francescafadel/AIMForScale.git**

The repository also contains a `keyword-search/` directory with related keyword scanning tools for World Bank, IDB, and AfDB documents.


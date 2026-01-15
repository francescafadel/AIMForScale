# Quick Setup Guide

## Prerequisites

1. **Python 3.7+** - Make sure Python 3 is installed on your system
2. **Java Runtime Environment (JRE)** - Required for tabula-py to extract tables from PDFs
   - macOS: `brew install java`
   - Ubuntu: `sudo apt-get install default-jre`
   - Windows: Download from Oracle's website

## Installation Steps

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Test the installation:**
   ```bash
   python3 test_keyword_matching.py
   ```
   This should run successfully and create a `sample_results.csv` file.

## Usage

1. **Place your PDF file** in the same directory as the script
2. **Run the script:**
   ```bash
   python3 pdf_keyword_scanner.py your_file.pdf
   ```

## Example Output

The script will create a CSV file with the original data plus two new columns:
- `Keywords Found in Project Name` - List of keywords found in project names
- `Keywords Found in Project Description` - List of keywords found in project descriptions

## Troubleshooting

- **"No module named 'PyPDF2'"** - Run `pip3 install -r requirements.txt`
- **"Java not found"** - Install Java Runtime Environment
- **"No tables found"** - Make sure your PDF contains tables with "Project Name" and "Project Description" columns
- **"No required columns found"** - Check that your PDF table has exactly these column names (case-insensitive)

## Keywords List

The script searches for these 41 keywords:
- animal, beef, butter, cheese, cream, dairy
- deforestation, disease, drought
- egg, eggs, efficiency, export
- feed, flock, fodder, forage
- genetics, goat, grains, grazing
- health, herd, import
- lamb, livestock
- manure, market, meat, milk, mutton
- pasture, pork, poultry, protein
- resilience
- supplements
- vet
- waste
- yogurt
- zoonotic 
# PDF Keyword Scanner

This script reads a PDF file containing "Project Name" and "Project Description" columns, scans them for specific keywords, and creates two new columns with the found keywords.

## Features

- Reads PDF files and extracts table data
- Performs case-sensitive keyword matching
- Creates two new columns: "Keywords Found in Project Name" and "Keywords Found in Project Description"
- Saves results to a CSV file
- Provides summary statistics

## Keywords

The script searches for the following livestock-related keywords:
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

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Java installed (required for tabula-py):
   - On macOS: `brew install java`
   - On Ubuntu: `sudo apt-get install default-jre`
   - On Windows: Download from Oracle's website

## Usage

1. Place your PDF file in the same directory as the script
2. Run the script with your PDF file as an argument:

```bash
python pdf_keyword_scanner.py your_file.pdf
```

## Output

The script will:
1. Extract tables from the PDF
2. Find the table with "Project Name" and "Project Description" columns
3. Scan both columns for keywords
4. Create a new CSV file with the original data plus two new columns:
   - "Keywords Found in Project Name"
   - "Keywords Found in Project Description"
5. Display summary statistics

## Example

If your input file is `projects.pdf`, the output will be saved as `projects_with_keywords.csv`.

## Notes

- Keyword matching is case-sensitive
- Only whole words are matched (not partial matches)
- If no keywords are found, the column will contain an empty list
- The script will show available columns if the required columns are not found 
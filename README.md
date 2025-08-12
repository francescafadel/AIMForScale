# World Bank PDF Keyword Scanner

This script reads a PDF file containing World Bank project data, scans for livestock-related keywords across multiple columns, and creates comprehensive keyword analysis with rock-solid accuracy and alignment.

## Features

- **Rock-solid PDF extraction** with proper multi-line cell handling
- **Case-insensitive keyword matching** with Unicode normalization
- **Three-column search**: Project Name, Project Description, and Implementing Agency
- **Duplicate elimination** and perfect row alignment
- **Comprehensive output** with union column showing all keywords found
- **Debug functionality** to verify detection accuracy
- **Robust error handling** and validation

## Keywords

The script searches for 41 livestock-related keywords:
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
2. Run the improved script:

```bash
python3 pdf_keyword_scanner_improved.py "your_file.pdf"
```

## Output

The script will:
1. Extract all columns from the PDF table
2. Search for keywords in Project Name, Project Description, and Implementing Agency
3. Create a CSV file with original data plus keyword columns:
   - "Keywords Found in Project Name"
   - "Keywords Found in Project Description" 
   - "Keywords Found in Implementing Agency"
   - "Keywords Found (Any Column)" - union of all three
4. Display comprehensive summary statistics
5. Provide debug output for verification

## Key Improvements

- **Perfect alignment**: No duplicate rows, consistent column structure
- **Multi-line handling**: Properly merges cells with line breaks
- **Unicode robust**: Handles special characters and non-breaking spaces
- **Semantic column matching**: Finds columns regardless of exact header formatting
- **Validation**: Checks Project ID presence and data integrity

## Example

If your input file is `Final World Bank Corpus - Sheet1.pdf`, the output will be saved as `Final World Bank Corpus - Sheet1_with_keywords_improved.csv`.

## Files

- `pdf_keyword_scanner_improved.py` - Main script with all improvements
- `keywords.txt` - 41 livestock-related keywords
- `requirements.txt` - Python dependencies
- `setup_guide.md` - Quick setup instructions
- `test_keyword_matching.py` - Test script for verification

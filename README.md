# AIMForScale Word Search

A comprehensive Python tool for extracting and analyzing livestock-related keywords from PDF documents and CSV files from various International Financial Institutions (IFIs), including World Bank, African Development Bank (AfDB), and Inter-American Development Bank (IDB) projects.

## Features

- **Enhanced PDF extraction** with proper multi-line cell handling
- **Robust keyword matching** with case-insensitive, accent-normalized, separator-tolerant detection
- **Multi-column search**: Project Name, Project Description, Implementing Agency, and Abstract
- **CSV processing capability** for existing CSV files
- **189 specialized livestock keywords** covering technical and modern livestock development terms
- **Perfect alignment** with duplicate elimination and validation
- **Comprehensive output** with union column showing all keywords found
- **Debug functionality** to verify detection accuracy
- **Test suite** for validating keyword detection robustness
- **Robust error handling** and validation

## Repository Structure

```
World Bank/
├── data/
│   ├── input/          # Original CSV files
│   ├── processed/      # Intermediate files with keywords
│   └── output/         # Final cleaned corpora
├── scripts/            # Python processing scripts
├── config/             # Configuration files (keywords)
├── updated/            # Latest updated keyword list
└── archive/            # Old/duplicate files
```

## Keywords

The script searches for 189 specialized livestock-related keywords including technical terms like:
- Animal management: anthelmintics, artificial insemination, castration, dehorning, embryo transfer
- Infrastructure: biogas digester, cattle crush, chute, corral, dip tank
- Genetics: cloning, CRISPR, genomic selection, genetic improvement
- Feed & nutrition: aquafeed, haylage, silage, total mixed ration, prebiotics, probiotics
- Modern practices: precision livestock farming, in-vitro fertilization
- And many more specialized livestock development terms

See `updated/keywords.txt` for the complete list.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### For CSV Files:
1. Place your CSV file in the `data/input/` directory
2. Run the CSV scanner:

```bash
# Process all columns
python3 scripts/csv_keyword_scanner.py "data/input/your_file.csv"

# Process specific columns only
python3 scripts/csv_keyword_scanner.py "data/input/your_file.csv" "Project Name" "Description" "Agency"
```

The script automatically uses the updated keyword list from `updated/keywords.txt`.

## Output

The script will:
1. Search for keywords in all specified columns (or all columns if none specified)
2. Create a CSV file with original data plus keyword columns:
   - "Keywords Found in [Column Name]" for each column searched
   - "Keywords Found (Any Column)" - union of all matches
3. Display comprehensive summary statistics
4. Save results to the same directory as the input file

## Final Cleaned Corpora

- `data/output/Final IDB Cleaned Corpus.csv` - 110 IDB projects with livestock keywords
- `data/output/Final World Bank Cleaned Corpus.csv` - 203 World Bank projects with livestock keywords
- `data/output/Final AfDB Cleaned Corpus.csv` - 430 AfDB projects with livestock keywords

## Files

- `scripts/csv_keyword_scanner.py` - Main CSV file processing script
- `scripts/pdf_keyword_scanner_improved.py` - PDF processing script
- `updated/keywords.txt` - Latest keyword list (189 keywords)
- `config/keywords.txt` - Original keyword list (for reference)
- `requirements.txt` - Python dependencies
- `setup_guide.md` - Quick setup instructions

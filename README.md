# Key Word Search

A comprehensive Python tool for extracting and analyzing livestock-related keywords from PDF documents and CSV files from various International Financial Institutions (IFIs), including World Bank and African Development Bank (AfDB) projects.

## Features

- **Enhanced PDF extraction** with proper multi-line cell handling
- **Robust keyword matching** with case-insensitive, accent-normalized, separator-tolerant detection
- **Multi-column search**: Project Name, Project Description, Implementing Agency, and Abstract
- **CSV processing capability** for existing CSV files
- **150+ comprehensive livestock keywords** covering all aspects of livestock development
- **Perfect alignment** with duplicate elimination and validation
- **Comprehensive output** with union column showing all keywords found
- **Debug functionality** to verify detection accuracy
- **Test suite** for validating keyword detection robustness
- **Robust error handling** and validation

## Keywords

The script searches for 150+ comprehensive livestock-related keywords including:

**Core Livestock Terms:**
African swine fever, alpaca, alpacas, animal health, animal husbandry, ass, asses, association, average daily gain, barn, beef, beef cattle, biosecurity, boar, boars, breeding, buffalo, buffalos, bull, bulls, butchery, calf, calves, camel, camels, caprine, carbon sequestration, cattle, chicken, chickens, climate smart livestock, climate-smart livestock, commercialization, community based breeding, cooperative, cooperative credit, cow, cows, CRISPR, crossbreeding, curd, dairy, dairy cattle, deworming, disease surveillance, donkey, donkeys, draft power, duck, ducks, egg, eggs, embryo, gene editing, enteric fermentation, ewe, ewes, extension agent, extension services, extensive grazing, farm management, farmer training, farming, feed, feed additives, feed conversion efficiency, feed conversion ratio, feed efficiency, feedlot, fertility, flock management, fodder, food and mouth disease, foot-and-mouth disease, forage, geese, gender roles, genetic, genetics, GHG emissions, goat, goat meat, goats, goose, grant, grazing, grazing land, greenhouse gas, hay, hen, hens, herd health, herd management, herding, herdsmen, herdswomen, horse, horses, household income, immunization, industrial, intensive systems, kid, kids, lactation, lamb, lambs, leather, livelihoods, livestock, llama, llamas, manure, manure management, market access, mastitis, meat, methane, methane capture, milk, microfinance, mixed farming, mule, mules, mutton, Newcastle disease, nutrient cycling, output, overgrazing, parasite control, pastoral, pastoralist, pasture, pasture degradation, pig, pigs, policy, pork, poultry, processing, production system, productivity, ram, ranch, rangeland, rational grazing, regenerative agriculture, reproduction, rooster, roosters, rotational grazing, ruminant, ruminant nutrition, selective breeding, semi-intensive systems, sheep, silvopastoral, slaughterhouse, smallholder, stallion, stallions, stocking density, subsidy, supplements, sustainable intensification, swine, turkey, turkeys, vaccination, value-added processing, value chain, vet, veterinary, waste management, water buffalo, weaning, whey, women in livestock, wool, yield, zero grazing, zero-grazing, zoonosis, zoonotic

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

### For PDF Files:
1. Place your PDF file in the same directory as the script
2. Run the improved script:

```bash
python3 pdf_keyword_scanner_improved.py "your_file.pdf"
```

### For CSV Files:
1. Place your CSV file in the same directory as the script
2. Run the CSV scanner:

```bash
# Process all columns
python3 csv_keyword_scanner.py "your_file.csv"

# Process specific columns only
python3 csv_keyword_scanner.py "your_file.csv" "Project Name" "Description" "Agency"
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

- `pdf_keyword_scanner_improved.py` - Enhanced PDF processing script for World Bank data
- `csv_keyword_scanner.py` - CSV file processing script for any IFI data
- `keywords.txt` - 150+ comprehensive livestock-related keywords
- `test_keyword_robustness.py` - Comprehensive test suite for keyword validation
- `requirements.txt` - Python dependencies
- `setup_guide.md` - Quick setup instructions
- `new_ifi_scanner.py` - Alternative scanner for other IFIs
- `new_ifi_keywords.txt` - Keywords for other IFIs

## Processed Data Files

- `World Bank With Abstracts pt.1_with_keywords.csv` - World Bank projects with keyword analysis
- `World Bank With Abstracts pt.2_with_keywords.csv` - World Bank projects with keyword analysis  
- `afdb_full_extraction_with_keywords.csv` - African Development Bank projects with keyword analysis
- `Final IDB Corpus   - Sheet1_with_keywords.csv` - Inter-American Development Bank projects with keyword analysis

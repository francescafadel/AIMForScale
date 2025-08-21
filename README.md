# World Bank PDF Keyword Scanner

This script reads a PDF file containing World Bank project data, scans for livestock-related keywords across multiple columns, and creates comprehensive keyword analysis with rock-solid accuracy and alignment.

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
- animal, animals, livestock, cattle, dairy, beef, poultry, sheep, goats, pigs, swine
- cow, cows, bull, bulls, calf, calves, heifer, heifers, steer, steers
- chicken, chickens, hen, hens, rooster, roosters, turkey, turkeys, duck, ducks, goose, geese
- goat, goats, kid, kids, ewe, ewes, ram, rams, lamb, lambs
- pig, pigs, boar, boars, sow, sows, piglet, piglets
- horse, horses, mare, mares, stallion, stallions, foal, foals
- donkey, donkeys, mule, mules, ass, asses
- camel, camels, llama, llamas, alpaca, alpacas, buffalo, buffalos

**Livestock Products:**
- milk, dairy, cheese, butter, cream, yogurt
- meat, beef, pork, mutton, lamb, goat meat
- egg, eggs, leather, wool, manure

**Livestock Management:**
- herd, herd health, herd management, flock, flock management
- breeding, selective breeding, crossbreeding, genetics, genetic
- animal health, animal husbandry, veterinary, vet
- feed, feed additives, feed conversion ratio, feed efficiency, fodder, forage
- grazing, grazing land, pasture, pasture degradation, rangeland
- biosecurity, disease surveillance, vaccination, immunization, deworming
- parasite control, mastitis, Newcastle disease, African swine fever

**Agricultural Systems:**
- smallholder, smallholders, farming, mixed farming
- climate smart livestock, climate-smart livestock
- sustainable intensification, regenerative agriculture
- silvopastoral, community based breeding
- women in livestock, gender roles

**Value Chain & Markets:**
- value chain, market access, commercialization, processing
- productivity, production system, output, yield
- livelihoods, household income, cooperative, association
- extension agent, extension services, farmer training

**Environmental & Health:**
- zoonosis, zoonotic, waste management, manure management
- GHG emissions, greenhouse gas, methane, overgrazing
- deforestation, water buffalo, water buffalo

**And many more specialized terms...**

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

- `pdf_keyword_scanner_improved.py` - Enhanced PDF processing script
- `csv_keyword_scanner.py` - CSV file processing script
- `keywords.txt` - 150+ comprehensive livestock-related keywords
- `test_keyword_robustness.py` - Comprehensive test suite for keyword validation
- `requirements.txt` - Python dependencies
- `setup_guide.md` - Quick setup instructions
- `new_ifi_scanner.py` - Alternative scanner for other IFIs
- `new_ifi_keywords.txt` - Keywords for other IFIs

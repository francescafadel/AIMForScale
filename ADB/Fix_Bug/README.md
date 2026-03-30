# ADB Project Description Scraper -- Fix_Bug

Extracts project descriptions from ADB project pages and writes them into a CSV file.

---

## Files

| File | Description |
|------|-------------|
| `csv_cleaner.py` | Removes duplicate rows from the original corpus. Run this once before scraping (done already so DO NOT run it again -- overwrites the descriptions). |
| `test_single_url.py` | Tests a single URL to confirm your API key and extraction logic work. |
| `adb_scrapper_with_scrapperAPI.py` | Main scraper. Fetches descriptions for all projects in the CSV. |

---

## Setup

**1. Install dependencies:**
```bash
pip install requests beautifulsoup4
```

**2. Update the CSV path** in `adb_scrapper_with_scrapperAPI.py`:
```python
CSV_FILE = Path("/your/path/to/Final ADB Corpus - Unique.csv")
```

**3. Add your ScraperAPI key** (get one free at [scraperapi.com](https://www.scraperapi.com)):
```python
API_KEY = "your_api_key_here"
```

---

## How to Run

```bash
# 1. Test on 5 projects first
python adb_scrapper_with_scrapperAPI.py --test 5

# 2. Full run
python adb_scrapper_with_scrapperAPI.py
```

The script skips rows that already have a description and saves after every row — safe to stop and restart anytime.
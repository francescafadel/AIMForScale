# ADB Project Scraper (original project README)

This script automatically extracts project descriptions from ADB (Asian Development Bank) project pages.

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright browser

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright will use for scraping.

## Usage

Simply run the script:

```bash
python scrape_adb_descriptions.py
```

The script will:
1. Load `Final ADB Corpus - Sheet1_with_urls.csv`
2. Navigate to each project URL
3. Click the "Project Data Sheet" link
4. Extract the Description field
5. Save results to `Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv`

## Features

- ✅ **Automatic URL detection** - Finds the URL column automatically
- ✅ **Robust error handling** - Continues even if some URLs fail
- ✅ **Rate limiting** - Adds polite delays between requests (0.5-1.5s)
- ✅ **Headless browser** - Runs invisibly in the background
- ✅ **Progress tracking** - Shows detailed progress for each URL
- ✅ **Clean output** - Removes extra whitespace and newlines from descriptions

## Configuration

You can modify these settings at the top of `scrape_adb_descriptions.py`:

```python
DEFAULT_TIMEOUT = 30000  # Timeout for page loads (milliseconds)
MIN_DELAY = 0.5         # Minimum delay between requests (seconds)
MAX_DELAY = 1.5         # Maximum delay between requests (seconds)
```

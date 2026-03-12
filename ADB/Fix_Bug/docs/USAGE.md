# How to Run the ADB Description Scraper

## Quick Start

### 1. Install Dependencies (one-time setup)

```bash
pip install pandas playwright
playwright install
```

### 2. Run the Scraper

```bash
cd "/Users/francesca/Desktop/ADB Project Description Extraction"
python scrape_adb_descriptions.py
```

That's it! The script will:
- Load your CSV file
- Auto-detect the URL column
- Scrape all 7,330 project descriptions
- Save results to a new CSV file

## What Happens During Execution

### Progress Output
You'll see real-time progress like this:
```
[1/7330] Processing row 1
  → Navigating to https://www.adb.org/projects/48116-001/main
  → Clicked 'Project Data Sheet'
  ✓ Found description (785 chars)
  ⏱  Waiting 1.07s before next request...

[2/7330] Processing row 2
  → Navigating to https://www.adb.org/projects/48061-002/main
  ⚠ Warning: Could not click Project Data Sheet. Using current page.
  ✓ Found description (1843 chars)
  ⏱  Waiting 0.85s before next request...
```

### Output File
- **Filename:** `Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv`
- **Location:** Same folder as the input CSV
- **Columns:** All original columns + new `Description` column

## Key Features

### 🛡️ Robust Error Handling
- **Never crashes** - continues even if individual URLs fail
- **Graceful fallbacks** - uses current page if "Project Data Sheet" tab not found
- **Detailed logging** - shows exactly what happened for each URL

### 🎯 Smart Navigation
- Waits for `networkidle` (page fully loaded)
- Tries multiple selectors for "Project Data Sheet":
  - `a:has-text("Project Data Sheet")`
  - `button:has-text("Project Data Sheet")`
  - Case variations (PROJECT DATA SHEET)
- Scrolls element into view before clicking

### 🔍 Flexible Extraction
- Searches all table rows for "Description" label
- Works with different table structures (th/td combinations)
- Cleans up whitespace automatically
- Returns empty string (not crash) if description not found

### ⏱️ Polite Rate Limiting
- Random delay: 0.5 - 1.5 seconds between requests
- Prevents server overload
- Reduces risk of IP blocking

## Expected Runtime

For 7,330 URLs with 0.5-1.5s delays:
- **Minimum:** ~1 hour (if all succeed quickly)
- **Expected:** 2-3 hours (accounting for page load times)
- **Maximum:** 4+ hours (if many timeouts/retries)

## Troubleshooting

### "Could not detect a URL column"
- Check that your CSV has a column named "ADB URL" or
- Ensure URLs start with `https://www.adb.org/projects/`

### Script runs but no descriptions extracted
- Check internet connectivity
- Try a few URLs manually in your browser
- The ADB website structure may have changed

### Script stops unexpectedly
- Check terminal for error messages
- Partially completed results are NOT saved
- You'll need to re-run from the beginning

### Want to test first?
Modify the script to only process first N rows:
```python
# In scrape_all_descriptions function, after the for loop starts:
for idx, row in df.iterrows():
    if idx >= 10:  # Stop after 10 rows
        break
    # ... rest of code
```

## Understanding the Output

### Success Indicators
- `✓ Found description (X chars)` - Successfully extracted
- `→ Clicked 'Project Data Sheet'` - Tab was clicked
- Numbers in parentheses show description length

### Warning Indicators
- `⚠ Warning: Could not click Project Data Sheet` - Tab not found, using main page
- `⚠ Warning: No description found` - Page loaded but no Description field

### Error Indicators
- `✗ Error scraping URL` - Complete failure for this URL
- `⊘ Skipping empty URL` - No URL in that row

## Final Summary

After completion, you'll see:
```
===============================================================================
SUMMARY
===============================================================================
URL column used: ADB URL
Total rows: 7330
Rows with non-empty descriptions: 1234

📋 Preview of extracted descriptions:

Row 1:
  URL: https://www.adb.org/projects/48116-001/main
  Description: In 2012, the Government of the People's Republic of China...

Row 5:
  URL: https://www.adb.org/projects/48061-002/main
  Description: The proposed TA is in line with ADB's Interim Country...
```

## Support

If you encounter issues:
1. Check the console output for specific error messages
2. Verify a few URLs work manually in a browser
3. Consider running on a smaller subset first (modify script)
4. Check that Playwright browser was installed: `playwright install`

---

**Ready to run?** Just execute:
```bash
python scrape_adb_descriptions.py
```

The script will handle everything else automatically! ✨




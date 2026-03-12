# Tests folder contents

This folder holds test and debug scripts for the ADB description extraction pipeline, plus a summary of test results. Below is what each file contains.

---

**extract_descriptions_test_5.py**  
Runs the extraction logic on a small set of URLs (e.g. first 3 or 5) from the working CSV. Uses networkidle for page load and multiple selectors to find and click the Project Data Sheet tab. Writes results to the same CSV path. Use this to verify the pipeline works on a few URLs before a full run.

**extract_descriptions_test_batch.py**  
Batch test script that processes a configurable number of URLs (default 20) from the working CSV. Navigates to each URL, clicks Project Data Sheet, and extracts the description. Saves output to the same CSV. Use this for a larger test run than test_5 without processing the full corpus.

**scrape_adb_descriptions_test.py**  
Test version of the pandas-based scraper (scrape_adb_descriptions.py). Processes only the first few URLs (e.g. 5) and writes to a test output CSV (e.g. Sheet1_with_urls_and_descriptions_TEST.csv). Same dependencies and flow as the full scraper but limited in scope for quick validation.

**test_single_url.py**  
Single-URL debug script. Opens one fixed project URL (e.g. 29600-013) in a visible browser (headless=False), attempts to click Project Data Sheet, and tries to extract the description from table rows. Keeps the browser open briefly for manual inspection. Use this to debug click or extraction issues on one page.

**TEST_RESULTS.md**  
Summary of test runs: date, script and dataset used, number of URLs tested, success rate, example extracted description, what works, known limitations, and suggested next steps. See this file for historical test outcomes and guidance.

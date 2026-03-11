"""
ADB Project Description Extractor (standalone version)

Same logic as adb_description_extractor.py but with paths relative to the
"Project Description Extraction" folder. Run from that folder so the CSV paths resolve:
  cd "Project Description Extraction"
  python scripts/extract_descriptions_test_3_fixed.py

Extracts project descriptions from ADB project pages using multiple strategies:
1. Direct navigation to /pds URL (bypasses clicking)
2. Force-click on "Project Data Sheet" tab
3. Multiple extraction strategies for different page structures
"""

import asyncio
import csv
import os
import random
from playwright.async_api import async_playwright

# Paths relative to Project Description Extraction folder
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")

INPUT_CSV = os.path.join(DATA_DIR, "Copy of Final ADB Corpus - Link Extraction File.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "Copy of Final ADB Corpus - Link Extraction File.csv")
TEST_SIZE = 5

# Browser settings
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)

# Timeouts (milliseconds)
NAVIGATION_TIMEOUT = 60000
CLOUDFLARE_WAIT_TIMEOUT = 5000
ELEMENT_WAIT_TIMEOUT = 15000
DESCRIPTION_WAIT_TIMEOUT = 10000

# Rate limiting (seconds)
MIN_DELAY = 1.0
MAX_DELAY = 2.0


async def wait_for_cloudflare(page):
    """Wait for Cloudflare challenge to complete if present."""
    try:
        await page.wait_for_selector('text="Just a moment"', timeout=CLOUDFLARE_WAIT_TIMEOUT, state='hidden')
    except Exception:
        pass
    # Give additional time for JavaScript to complete
    await page.wait_for_timeout(5000)


async def navigate_to_pds_page(page, url):
    """
    Navigate directly to PDS page if URL ends with /main.
    Returns True if successful, False otherwise.
    """
    if not url.endswith('/main'):
        return False
    
    try:
        pds_url = url.replace('/main', '/pds')
        await page.goto(pds_url, timeout=NAVIGATION_TIMEOUT, wait_until='load')
        await page.wait_for_selector('body')
        await wait_for_cloudflare(page)
        print(f"  → Direct navigation to PDS page")
        return True
    except Exception:
        return False


async def click_pds_tab(page):
    """
    Attempt to click the "Project Data Sheet" tab using force click.
    Returns True if successful, False otherwise.
    """
    selectors = [
        "a:has-text('Project Data Sheet'), a:has-text('PDS')",
        "button:has-text('Project Data Sheet'), button:has-text('PDS')"
    ]
    
    for selector in selectors:
        try:
            pds_tab = page.locator(selector).first
            await pds_tab.wait_for(state="attached", timeout=ELEMENT_WAIT_TIMEOUT)
            await pds_tab.click(force=True)
            print(f"  → Force-clicked 'Project Data Sheet'")
            return True
        except Exception:
            continue
    
    return False


async def wait_for_description_content(page):
    """Wait for Description content to appear in the DOM."""
    try:
        await page.locator("tr >> text=Description").wait_for(state="attached", timeout=DESCRIPTION_WAIT_TIMEOUT)
    except Exception:
        # If Description doesn't appear, wait a bit more for JS to render
        await page.wait_for_timeout(3000)
        try:
            await page.locator("tr >> text=Description").wait_for(state="attached", timeout=DESCRIPTION_WAIT_TIMEOUT)
        except Exception:
            pass


async def extract_description_table_row(page):
    """
    Strategy 1: Extract description from table row with 'Description' label.
    Returns description text if found, empty string otherwise.
    """
    try:
        desc_row = page.locator("tr:has-text('Description')")
        count = await desc_row.count()
        if count > 0:
            description_text = await desc_row.locator("td").last.inner_text()
            description_text = " ".join(description_text.split())
            if description_text:
                print(f"  ✓ Found description ({len(description_text)} chars)")
                return description_text
    except Exception:
        pass
    return ""


async def extract_description_dt_dd(page):
    """
    Strategy 2: Extract description from dt/dd HTML structure.
    Returns description text if found, empty string otherwise.
    """
    try:
        dt_elements = await page.query_selector_all('dt')
        for dt in dt_elements:
            label_text = await dt.inner_text()
            if label_text and label_text.strip().lower() == 'description':
                # Found the Description label, get the next sibling dd
                dd = await dt.evaluate_handle('(element) => element.nextElementSibling')
                if dd:
                    desc_text = await dd.inner_text()
                    description_text = desc_text.strip()
                    description_text = ' '.join(description_text.split())
                    if description_text and len(description_text) > 50:  # Filter out short labels
                        print(f"  ✓ Found description in dt/dd ({len(description_text)} chars)")
                        return description_text
    except Exception:
        pass
    return ""


async def extract_description(context, url):
    """
    Extract description from a project URL using multiple strategies.
    
    Args:
        context: Playwright browser context
        url: The project URL to visit
    
    Returns:
        str: The extracted description text, or empty string if extraction failed
    """
    page = await context.new_page()
    
    try:
        pds_clicked = False
        
        # Priority 1: Direct Navigation Shortcut
        if await navigate_to_pds_page(page, url):
            pds_clicked = True
        else:
            # Navigate to the provided URL
            await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until='load')
            await page.wait_for_selector('body')
            await wait_for_cloudflare(page)
        
        # Priority 2: Robust Selector & Force Click (Fallback)
        if not pds_clicked:
            pds_clicked = await click_pds_tab(page)
            if not pds_clicked:
                print(f"  ⚠ Could not click Project Data Sheet - will try to extract from current page")
        
        # Synchronization: Wait for Description content to appear
        if pds_clicked:
            await wait_for_description_content(page)
        
        # Extraction Strategies
        description_text = await extract_description_table_row(page)
        
        if not description_text:
            description_text = await extract_description_dt_dd(page)
        
        await page.close()
        return description_text
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:150]}")
        try:
            await page.close()
        except:
            pass
        return ""


async def load_csv_data():
    """Load CSV file and return rows, header index, and column indices."""
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    
    # Find header row
    header_idx = next(i for i, r in enumerate(rows) if len(r) > 0 and r[0] == "Project ID")
    
    # Find column indices
    link_col = next(i for i, c in enumerate(rows[header_idx]) if c == "Project Link")
    desc_col = next(i for i, c in enumerate(rows[header_idx]) if c == "Description")
    project_id_col = 0  # Project ID is in first column
    
    return rows, header_idx, link_col, desc_col, project_id_col


def get_unique_urls(rows, header_idx, link_col, project_id_col, test_size):
    """
    Get unique URLs to process, skipping duplicates.
    Returns list of (row_index, url) tuples.
    """
    seen_ids = set()
    urls = []
    
    for i in range(header_idx + 1, min(header_idx + 1 + test_size, len(rows))):
        if len(rows[i]) > link_col:
            # Get project ID to check for duplicates
            project_id = rows[i][project_id_col].strip() if len(rows[i]) > project_id_col else ""
            url = rows[i][link_col].strip()
            
            # Skip if duplicate project ID
            if project_id and project_id in seen_ids:
                print(f"Skipping duplicate project ID: {project_id}")
                continue
            
            if url.startswith("https://www.adb.org/projects/"):
                seen_ids.add(project_id)
                urls.append((i, url))
    
    return urls


def save_results(rows, output_file):
    """Save processed rows to CSV file."""
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)


async def main():
    """Main execution function."""
    # Load CSV data
    rows, header_idx, link_col, desc_col, project_id_col = load_csv_data()
    
    # Get unique URLs to process
    urls = get_unique_urls(rows, header_idx, link_col, project_id_col, TEST_SIZE)
    
    print(f"Processing {len(urls)} unique URLs...\n")
    
    # Process with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        
        successful = 0
        for idx, (row_idx, url) in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] {url}")
            desc = await extract_description(context, url)
            
            # Ensure row has enough columns
            while len(rows[row_idx]) <= desc_col:
                rows[row_idx].append("")
            
            # Update description
            rows[row_idx][desc_col] = desc
            if desc:
                successful += 1
            
            # Rate limiting between requests
            if idx < len(urls):
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                await asyncio.sleep(delay)
        
        await browser.close()
    
    # Save results
    save_results(rows, OUTPUT_CSV)
    
    print(f"\n✓ Complete! {successful}/{len(urls)} descriptions extracted")


if __name__ == "__main__":
    asyncio.run(main())

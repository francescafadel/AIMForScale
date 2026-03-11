"""
ADB Project Description Extractor - Test 5 URLs

Extracts descriptions from first 5 URLs to test the approach.
"""

import asyncio
import csv
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

INPUT_CSV = "Copy of Final ADB Corpus - Link Extraction File.csv"
OUTPUT_CSV = "Copy of Final ADB Corpus - Link Extraction File.csv"
TEST_SIZE = 3  # Process first 3 URLs


async def extract_description(context, url):
    """Extract description from a project URL."""
    page = await context.new_page()
    try:
        print(f"  → Navigating to {url}")
        # Use networkidle like the working scraper - this waits for all network activity
        await page.goto(url, timeout=60000, wait_until='networkidle')
        await page.wait_for_timeout(4000)
        
        # Click Project Data Sheet - using the same approach as working scraper
        pds_clicked = False
        selectors = [
            'a:has-text("Project Data Sheet")',
            'button:has-text("Project Data Sheet")',
            'a:has-text("PROJECT DATA SHEET")',
            'button:has-text("PROJECT DATA SHEET")',
            'text="Project Data Sheet"',
        ]
        
        # Debug: Check what's on the page
        print(f"  → Checking for Project Data Sheet link...")
        for sel in selectors:
            try:
                locator = page.locator(sel)
                count = await locator.count()
                print(f"    Selector '{sel}': {count} found")
                if count > 0:
                    # Wait for element to be visible
                    await locator.first.wait_for(state='visible', timeout=10000)
                    # Scroll into view
                    await locator.first.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    # Click
                    await locator.first.click()
                    # Wait for page to load after click
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    pds_clicked = True
                    print(f"  → Clicked 'Project Data Sheet' using '{sel}'")
                    break
            except Exception as e:
                print(f"    Selector '{sel}' failed: {str(e)[:80]}")
                continue
        
        if not pds_clicked:
            print(f"  ⚠ Could not click Project Data Sheet")
        
        # Extract description from table - using same approach as working scraper
        description = ""
        
        # Strategy 1: Look for table row with "Description" label
        try:
            rows = page.locator("tr")
            row_count = await rows.count()
            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    label_cell = row.locator("th, td").first
                    label_raw = await label_cell.inner_text()
                    label = label_raw.strip().lower()
                    
                    if label == "description":
                        cells = row.locator("td")
                        if await cells.count() > 0:
                            description = await cells.last.inner_text()
                            description = " ".join(description.split())
                            if description:
                                print(f"  ✓ Found description ({len(description)} chars)")
                                break
                except Exception:
                    continue
        except Exception:
            pass
        
        # Strategy 2: Try get_by_text approach
        if not description:
            try:
                label_candidates = page.get_by_text("Description", exact=True)
                if await label_candidates.count() > 0:
                    label = label_candidates.first
                    # Try to get next sibling element
                    sibling = label.locator("xpath=../following-sibling::*[1]")
                    if await sibling.count() > 0:
                        description = await sibling.inner_text()
                        description = " ".join(description.split())
                        if description:
                            print(f"  ✓ Found description via sibling ({len(description)} chars)")
            except Exception:
                pass
        
        await page.close()
        return description
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:150]}")
        try:
            await page.close()
        except:
            pass
        return ""


async def main():
    # Read CSV
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    
    # Find header
    header_idx = next(i for i, r in enumerate(rows) if len(r) > 0 and r[0] == "Project ID")
    
    # Find columns
    link_col = next(i for i, c in enumerate(rows[header_idx]) if c == "Project Link")
    desc_col = next(i for i, c in enumerate(rows[header_idx]) if c == "Description")
    
    # Get URLs to process
    urls = []
    for i in range(header_idx + 1, min(header_idx + 1 + TEST_SIZE, len(rows))):
        if len(rows[i]) > link_col:
            url = rows[i][link_col].strip()
            if url.startswith("https://www.adb.org/projects/"):
                urls.append((i, url))
    
    print(f"Processing {len(urls)} URLs...\n")
    
    # Process with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        successful = 0
        for idx, (row_idx, url) in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] {url}")
            desc = await extract_description(context, url)
            if desc:
                while len(rows[row_idx]) <= desc_col:
                    rows[row_idx].append("")
                rows[row_idx][desc_col] = desc
                successful += 1
            else:
                while len(rows[row_idx]) <= desc_col:
                    rows[row_idx].append("")
                rows[row_idx][desc_col] = ""
            
            if idx < len(urls):
                delay = random.uniform(1.0, 2.0)
                await asyncio.sleep(delay)
        
        await browser.close()
    
    # Save
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(rows)
    
    print(f"\n✓ Complete! {successful}/{len(urls)} descriptions extracted")


if __name__ == "__main__":
    asyncio.run(main())


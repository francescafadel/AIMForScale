"""
ADB Project Description Scraper - TEST VERSION

This is a test version that only processes the first 5 non-empty URLs.
Use this to verify the scraper works before running on the full dataset.

Prerequisites:
    pip install pandas playwright
    playwright install chromium

Usage:
    python scrape_adb_descriptions_test.py
"""

import asyncio
import random
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re


# Configuration
INPUT_CSV = "Final ADB Corpus - Sheet1_with_urls.csv"
OUTPUT_CSV = "Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv"
DEFAULT_TIMEOUT = 30000  # 30 seconds
MIN_DELAY = 0.5  # Minimum delay between requests (seconds)
MAX_DELAY = 1.5  # Maximum delay between requests (seconds)
TEST_LIMIT = 5  # Only process first 5 URLs for testing


def detect_url_column(df):
    """
    Detect which column contains ADB project URLs.
    
    Priority:
    1. If 'ADB URL' column exists, use it
    2. Otherwise, find the column where most non-null entries start with 
       'https://www.adb.org/projects/'
    
    Returns:
        str: Name of the URL column, or None if not found
    """
    # First, check for exact match
    if 'ADB URL' in df.columns:
        print(f"✓ Found 'ADB URL' column")
        return 'ADB URL'
    
    # Check for case-insensitive match
    for col in df.columns:
        if col.strip().lower() == 'adb url':
            print(f"✓ Found '{col}' column (case-insensitive match)")
            return col
    
    # Search for column with most ADB URLs
    adb_url_prefix = 'https://www.adb.org/projects/'
    best_column = None
    best_match_count = 0
    
    for col in df.columns:
        if df[col].dtype == 'object':  # Only check string columns
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                match_count = sum(
                    str(val).startswith(adb_url_prefix) 
                    for val in non_null_values
                )
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_column = col
    
    if best_column and best_match_count > 0:
        print(f"✓ Detected URL column: '{best_column}' "
              f"({best_match_count} URLs found)")
        return best_column
    
    print("✗ Could not detect a URL column")
    return None


async def extract_description(context, url):
    """
    Navigate to a project URL, click 'Project Data Sheet', and extract the Description.
    Uses a fresh page for each request to avoid state issues.
    
    Args:
        context: Playwright browser context
        url: The project URL to visit
    
    Returns:
        str: The extracted description text, or empty string if extraction failed
    """
    # Create a fresh page for this URL
    page = await context.new_page()
    
    try:
        # Navigate to the project page
        print(f"  → Navigating to {url}")
        await page.goto(url, timeout=DEFAULT_TIMEOUT, wait_until='domcontentloaded')
        
        # Wait for page to fully load and any JS to execute
        await page.wait_for_timeout(4000)
        
        # Try to find and click "Project Data Sheet" link/button
        project_data_sheet_clicked = False
        
        # Strategy 1: Click using text selector
        try:
            # Wait for the element to be visible
            await page.wait_for_selector('text="Project Data Sheet"', timeout=10000)
            await page.click('text="Project Data Sheet"')
            project_data_sheet_clicked = True
            print(f"  → Clicked 'Project Data Sheet'")
            await page.wait_for_timeout(2500)  # Wait for content to load
        except Exception as e:
            pass  # Try next strategy
        
        # Strategy 2: Try finding it via link with has-text
        if not project_data_sheet_clicked:
            try:
                await page.wait_for_selector('a:has-text("Project Data Sheet")', timeout=10000)
                await page.click('a:has-text("Project Data Sheet")')
                project_data_sheet_clicked = True
                print(f"  → Clicked 'Project Data Sheet' link")
                await page.wait_for_timeout(2500)
            except Exception as e:
                pass  # Try next strategy
        
        if not project_data_sheet_clicked:
            print(f"  ✗ Could not find 'Project Data Sheet' element")
            await page.close()
            return ""
        
        # Now extract the description
        # The description might be in dt/dd elements or in table rows
        description = ""
        
        # Strategy 1: Look for dt/dd (definition list) structure
        try:
            # Get all dt elements
            dt_elements = await page.query_selector_all('dt')
            for dt in dt_elements:
                label_text = await dt.inner_text()
                if label_text and label_text.strip().lower() == 'description':
                    # Found the Description label, get the next sibling dd
                    dd = await dt.evaluate_handle('(element) => element.nextElementSibling')
                    if dd:
                        desc_text = await dd.inner_text()
                        description = desc_text.strip()
                        description = re.sub(r'\s+', ' ', description)
                        print(f"  ✓ Found description in dt/dd ({len(description)} chars)")
                        break
        except Exception as e:
            print(f"  ⚠  Error in dt/dd extraction: {str(e)[:100]}")
        
        # Strategy 2: Look for table row with "Description" label
        if not description:
            try:
                rows = await page.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) >= 2:
                        first_cell_text = await cells[0].inner_text()
                        if first_cell_text and first_cell_text.strip().lower() == 'description':
                            desc_text = await cells[1].inner_text()
                            description = desc_text.strip()
                            description = re.sub(r'\s+', ' ', description)
                            print(f"  ✓ Found description in table ({len(description)} chars)")
                            break
            except Exception as e:
                print(f"  ⚠  Error in table extraction: {str(e)[:100]}")
        
        if not description:
            print(f"  ✗ Could not find Description field")
        
        await page.close()
        return description
        
    except PlaywrightTimeoutError:
        print(f"  ✗ Timeout while loading {url}")
        await page.close()
        return ""
    except Exception as e:
        print(f"  ✗ Error processing {url}: {str(e)[:150]}")
        try:
            await page.close()
        except:
            pass
        return ""


async def scrape_descriptions(df, url_column):
    """
    Scrape descriptions for URLs in the DataFrame (TEST VERSION - limited rows).
    
    Args:
        df: pandas DataFrame
        url_column: Name of the column containing URLs
    
    Returns:
        list: List of description strings (same length as df)
    """
    descriptions = [''] * len(df)  # Initialize with empty strings
    
    async with async_playwright() as p:
        # Launch browser in headless mode
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Find first N UNIQUE non-empty URLs
        urls_processed = 0
        successful_extractions = 0
        seen_urls = set()  # Track URLs we've already processed
        
        print(f"\n📊 TEST MODE: Processing first {TEST_LIMIT} unique non-empty URLs...\n")
        
        for idx, row in df.iterrows():
            if urls_processed >= TEST_LIMIT:
                break
                
            url = row[url_column]
            
            # Skip empty/null URLs
            if pd.isna(url) or not url or str(url).strip() == "":
                continue
            
            # Skip duplicate URLs in test mode
            url_str = str(url).strip()
            if url_str in seen_urls:
                continue
            
            seen_urls.add(url_str)
            urls_processed += 1
            print(f"[{urls_processed}/{TEST_LIMIT}] Processing row {idx + 1}")
            
            # Extract description (using fresh page each time)
            description = await extract_description(context, str(url).strip())
            descriptions[idx] = description
            
            if description:
                successful_extractions += 1
            
            # Politeness delay
            if urls_processed < TEST_LIMIT:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"  ⏱  Waiting {delay:.2f}s before next request...\n")
                await asyncio.sleep(delay)
        
        await browser.close()
        print(f"\n✅ Test scraping complete!")
        print(f"   Successfully extracted: {successful_extractions}/{urls_processed} descriptions")
    
    return descriptions


async def main():
    """Main execution function."""
    print("=" * 70)
    print("ADB Project Description Scraper - TEST VERSION")
    print(f"(Will only process first {TEST_LIMIT} non-empty URLs)")
    print("=" * 70)
    
    # Load the CSV
    print(f"\n📂 Loading CSV: {INPUT_CSV}")
    try:
        df = pd.read_csv(INPUT_CSV, encoding='utf-8')
        print(f"   ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    except FileNotFoundError:
        print(f"   ✗ Error: File '{INPUT_CSV}' not found!")
        return
    except Exception as e:
        print(f"   ✗ Error loading CSV: {str(e)}")
        return
    
    # Detect URL column
    print(f"\n🔍 Detecting URL column...")
    url_column = detect_url_column(df)
    
    if not url_column:
        print("\n❌ Could not detect a URL column. Please ensure your CSV has:")
        print("   - A column named 'ADB URL', or")
        print("   - A column with URLs starting with 'https://www.adb.org/projects/'")
        return
    
    # Scrape descriptions
    descriptions = await scrape_descriptions(df, url_column)
    
    # Add descriptions to DataFrame
    print(f"\n💾 Adding 'Description' column to DataFrame...")
    df['Description'] = descriptions
    
    # Save the updated CSV
    print(f"   Saving to: {OUTPUT_CSV}")
    try:
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"   ✓ Saved successfully!")
    except Exception as e:
        print(f"   ✗ Error saving CSV: {str(e)}")
        return
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"URL column used: {url_column}")
    print(f"Total rows in dataset: {len(df)}")
    
    non_empty_descriptions = df['Description'].apply(lambda x: bool(x and str(x).strip())).sum()
    print(f"Rows with non-empty descriptions: {non_empty_descriptions}")
    
    # Show sample of results (only rows that were processed)
    print(f"\n📋 Extracted descriptions:\n")
    processed_rows = df[df['Description'].notna() & (df['Description'] != '')]
    
    if len(processed_rows) == 0:
        # Show rows that were attempted even if empty
        attempted_rows = df[df[url_column].notna() & (df[url_column] != '')].head(TEST_LIMIT)
        for idx, row in attempted_rows.iterrows():
            url = row[url_column]
            desc = row['Description']
            print(f"Row {idx + 1}:")
            print(f"  URL: {url}")
            print(f"  Description: (empty or failed)")
            print()
    else:
        for idx, row in processed_rows.iterrows():
            url = row[url_column]
            desc = row['Description']
            print(f"Row {idx + 1}:")
            print(f"  URL: {url}")
            if desc and str(desc).strip():
                # Truncate long descriptions for display
                desc_preview = str(desc)[:200] + "..." if len(str(desc)) > 200 else str(desc)
                print(f"  Description: {desc_preview}")
            else:
                print(f"  Description: (empty)")
            print()
    
    print("=" * 70)
    print("✨ Test complete!")
    print("\nIf the test looks good, run the full version:")
    print("  python scrape_adb_descriptions.py")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

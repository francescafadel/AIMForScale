"""
ADB Project Description Scraper

Scrapes project descriptions from ADB project pages and adds them to the CSV.

Prerequisites:
    pip install pandas playwright
    playwright install

Usage:
    python scrape_adb_descriptions.py
"""

import asyncio
import random
import pandas as pd
from playwright.async_api import async_playwright
import sys


INPUT_CSV = "Final ADB Corpus - Sheet1_with_urls.csv"
OUTPUT_CSV = "Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv"


def detect_url_column(df):
    """
    Detect which column contains ADB project URLs.
    
    Returns:
        str: Name of the URL column, or None if not found
    """
    # Check for exact match
    if 'ADB URL' in df.columns:
        return 'ADB URL'
    
    # Check for case-insensitive match
    for col in df.columns:
        if col.strip().lower() == 'adb url':
            return col
    
    # Find column with most URLs starting with https://www.adb.org/projects/
    adb_url_prefix = 'https://www.adb.org/projects/'
    best_column = None
    best_match_count = 0
    
    for col in df.columns:
        if df[col].dtype == 'object':
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                match_count = sum(
                    str(val).startswith(adb_url_prefix) 
                    for val in non_null_values
                )
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_column = col
    
    return best_column


async def extract_description(context, url):
    """
    Extract description from an ADB project page using multiple strategies.
    
    Args:
        context: Playwright browser context
        url: Project URL
    
    Returns:
        str: Extracted description or empty string
    """
    page = await context.new_page()
    
    try:
        # Navigate to project page
        await page.goto(url, timeout=60000, wait_until='networkidle')
        await page.wait_for_timeout(4000)
        
        # Try to click "Project Data Sheet" tab if it exists
        pds_clicked = False
        selectors = [
            'a:has-text("Project Data Sheet")',
            'button:has-text("Project Data Sheet")',
            'a:has-text("PROJECT DATA SHEET")',
            'button:has-text("PROJECT DATA SHEET")'
        ]
        
        for sel in selectors:
            try:
                locator = page.locator(sel)
                if await locator.count() > 0:
                    await locator.first.wait_for(state='visible', timeout=10000)
                    await locator.first.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await locator.first.click()
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    pds_clicked = True
                    break
            except Exception:
                continue
        
        if not pds_clicked:
            print(f"[WARN] Could not click Project Data Sheet for {url}; staying on Overview page.")
        
        description_text = ""
        
        # Strategy 1: "Description" table row (Project Data Sheet style)
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
                            description_text = await cells.last.inner_text()
                            description_text = " ".join(description_text.split())
                            if description_text:
                                await page.close()
                                return description_text
                except Exception:
                    continue
        except Exception:
            pass
        
        # Strategy 2: Label "Description" + following sibling text
        if not description_text:
            try:
                label_candidates = page.get_by_text("Description", exact=True)
                if await label_candidates.count() > 0:
                    label = label_candidates.first
                    # Try to get next sibling element
                    sibling = label.locator("xpath=../following-sibling::*[1]")
                    if await sibling.count() > 0:
                        description_text = await sibling.inner_text()
                        description_text = " ".join(description_text.split())
                        if description_text:
                            await page.close()
                            return description_text
            except Exception:
                pass
        
        # Strategy 3: Overview paragraph fallback
        if not description_text:
            try:
                # Try main container
                containers = [
                    page.locator("main"),
                    page.locator("article"),
                    page.locator("div.region-content"),
                    page.locator("div.content"),
                    page.locator("body")
                ]
                
                for container in containers:
                    if await container.count() > 0:
                        paragraphs = container.locator("p")
                        p_count = await paragraphs.count()
                        
                        for i in range(p_count):
                            try:
                                p = paragraphs.nth(i)
                                text = await p.inner_text()
                                text = text.strip()
                                
                                # Look for substantial paragraph (>150 chars)
                                if len(text) > 150:
                                    description_text = " ".join(text.split())
                                    if description_text:
                                        await page.close()
                                        return description_text
                            except Exception:
                                continue
                        
                        # If we found a container but no substantial paragraph, break
                        if await container.count() > 0:
                            break
            except Exception:
                pass
        
        await page.close()
        return description_text
        
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        try:
            await page.close()
        except:
            pass
        return ""


async def main():
    """Main execution function."""
    print("=" * 80)
    print("ADB Project Description Scraper")
    print("=" * 80)
    
    # Load CSV
    print(f"\nLoading CSV: {INPUT_CSV}")
    try:
        df = pd.read_csv(INPUT_CSV, encoding='utf-8')
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    # Detect URL column
    url_column = detect_url_column(df)
    if not url_column:
        print("Error: Could not detect URL column")
        sys.exit(1)
    
    print(f"Using URL column: {url_column}")
    
    # Initialize descriptions list
    descriptions = []
    
    # Launch browser
    async with async_playwright() as p:
        print("\nLaunching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        
        total_urls = len(df)
        successful_extractions = 0
        
        print(f"\nProcessing {total_urls} URLs...\n")
        
        # Process all rows
        for idx, row in df.iterrows():
            url = row[url_column]
            
            print(f"[{idx + 1}/{total_urls}] Row {idx + 1}")
            
            # Skip null/empty URLs
            if pd.isna(url) or not url or str(url).strip() == "":
                descriptions.append("")
                continue
            
            # Extract description
            try:
                description = await extract_description(context, str(url).strip())
                descriptions.append(description)
                
                if description:
                    successful_extractions += 1
                    print(f"  ✓ Extracted description ({len(description)} chars)")
                else:
                    print(f"  ⊘ No description found")
                    
            except Exception as e:
                print(f"  [ERROR] {url}: {e}")
                descriptions.append("")
            
            # Rate limiting
            if idx < total_urls - 1:
                delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)
        
        await browser.close()
        
        print(f"\nProcessing complete!")
        print(f"Successfully extracted: {successful_extractions}/{total_urls} descriptions")
    
    # Add descriptions column
    df['Description'] = descriptions
    
    # Save to CSV
    print(f"\nSaving to: {OUTPUT_CSV}")
    try:
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print("Saved successfully!")
    except Exception as e:
        print(f"Error saving CSV: {e}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"URL column used: {url_column}")
    print(f"Total rows: {len(df)}")
    
    non_empty_descriptions = df['Description'].apply(
        lambda x: bool(x and str(x).strip())
    ).sum()
    print(f"Rows with non-empty descriptions: {non_empty_descriptions}")
    
    print(f"\nPreview:\n")
    print(df[[url_column, 'Description']].head())
    
    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

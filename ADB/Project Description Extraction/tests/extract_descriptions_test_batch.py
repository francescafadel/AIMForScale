"""
ADB Project Description Extractor - Test Batch

Extracts descriptions from ADB project pages for a test batch of URLs.
Processes first 20 URLs to verify the approach works.

Prerequisites:
    pip install pandas playwright
    playwright install
"""

import asyncio
import csv
import random
import time
from playwright.async_api import async_playwright

INPUT_CSV = "Copy of Final ADB Corpus - Link Extraction File.csv"
OUTPUT_CSV = "Copy of Final ADB Corpus - Link Extraction File.csv"
TEST_BATCH_SIZE = 20  # Process first 20 URLs as test


async def extract_description(page, url):
    """
    Navigate to a project URL, click 'Project Data Sheet', and extract the Description.
    
    Args:
        page: Playwright page object
        url: The project URL to visit
    
    Returns:
        str: The extracted description text, or empty string if extraction failed
    """
    try:
        print(f"  → Navigating to {url}")
        await page.goto(url, timeout=60000, wait_until='domcontentloaded')
        
        # Wait for page to fully load
        await page.wait_for_timeout(3000)
        
        # Try to click "Project Data Sheet" link/button
        project_data_sheet_clicked = False
        
        # Strategy 1: Click using text selector
        try:
            await page.wait_for_selector('text="Project Data Sheet"', timeout=10000)
            await page.click('text="Project Data Sheet"')
            project_data_sheet_clicked = True
            print(f"  → Clicked 'Project Data Sheet'")
            await page.wait_for_timeout(3000)  # Wait for content to load
        except Exception as e:
            pass  # Try next strategy
        
        # Strategy 2: Try finding it via link with has-text
        if not project_data_sheet_clicked:
            try:
                await page.wait_for_selector('a:has-text("Project Data Sheet")', timeout=10000)
                await page.click('a:has-text("Project Data Sheet")')
                project_data_sheet_clicked = True
                print(f"  → Clicked 'Project Data Sheet' link")
                await page.wait_for_timeout(3000)
            except Exception as e:
                pass
        
        if not project_data_sheet_clicked:
            print(f"  ✗ Could not find 'Project Data Sheet' element")
            return ""
        
        # Now extract the description
        description = ""
        
        # Strategy 1: Look for table row with "Description" label
        try:
            rows = await page.query_selector_all('tr')
            for row in rows:
                cells = await row.query_selector_all('td, th')
                if len(cells) >= 2:
                    first_cell_text = await cells[0].inner_text()
                    if first_cell_text and first_cell_text.strip().lower() == 'description':
                        desc_text = await cells[1].inner_text()
                        description = desc_text.strip()
                        # Clean up whitespace
                        description = ' '.join(description.split())
                        print(f"  ✓ Found description in table ({len(description)} chars)")
                        break
        except Exception as e:
            print(f"  ⚠  Error in table extraction: {str(e)[:100]}")
        
        # Strategy 2: Look for dt/dd (definition list) structure
        if not description:
            try:
                dt_elements = await page.query_selector_all('dt')
                for dt in dt_elements:
                    label_text = await dt.inner_text()
                    if label_text and label_text.strip().lower() == 'description':
                        # Found the Description label, get the next sibling dd
                        dd = await dt.evaluate_handle('(element) => element.nextElementSibling')
                        if dd:
                            desc_text = await dd.inner_text()
                            description = desc_text.strip()
                            description = ' '.join(description.split())
                            print(f"  ✓ Found description in dt/dd ({len(description)} chars)")
                            break
            except Exception as e:
                print(f"  ⚠  Error in dt/dd extraction: {str(e)[:100]}")
        
        if not description:
            print(f"  ✗ Could not find Description field")
        
        return description
        
    except Exception as e:
        print(f"  ✗ Error processing {url}: {str(e)[:150]}")
        return ""


async def process_test_batch():
    """
    Process a test batch of URLs from the CSV file.
    """
    # Read the CSV file
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Find the header row
    header_row_index = None
    for i, row in enumerate(rows):
        if len(row) > 0 and row[0].strip() == "Project ID":
            header_row_index = i
            break
    
    if header_row_index is None:
        print("Error: Could not find header row with 'Project ID'")
        return
    
    # Add "Description" column if it doesn't exist
    if "Description" not in rows[header_row_index]:
        rows[header_row_index].append("Description")
        description_col_index = len(rows[header_row_index]) - 1
    else:
        description_col_index = rows[header_row_index].index("Description")
    
    # Find the Project Link column
    project_link_col_index = None
    for i, col in enumerate(rows[header_row_index]):
        if col.strip() == "Project Link":
            project_link_col_index = i
            break
    
    if project_link_col_index is None:
        print("Error: Could not find 'Project Link' column")
        return
    
    # Get URLs to process (test batch)
    urls_to_process = []
    for i in range(header_row_index + 1, min(header_row_index + 1 + TEST_BATCH_SIZE, len(rows))):
        if len(rows[i]) > project_link_col_index:
            url = rows[i][project_link_col_index].strip()
            if url and url.startswith("https://www.adb.org/projects/"):
                urls_to_process.append((i, url))
    
    print(f"Found {len(urls_to_process)} URLs to process in test batch")
    
    # Process URLs with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        processed = 0
        successful = 0
        
        for row_index, url in urls_to_process:
            processed += 1
            print(f"\n[{processed}/{len(urls_to_process)}] Processing: {url}")
            
            description = await extract_description(page, url)
            
            if description:
                # Ensure the row has enough columns
                while len(rows[row_index]) <= description_col_index:
                    rows[row_index].append("")
                
                rows[row_index][description_col_index] = description
                successful += 1
                print(f"  ✓ Successfully extracted description")
            else:
                # Ensure the row has enough columns
                while len(rows[row_index]) <= description_col_index:
                    rows[row_index].append("")
                
                rows[row_index][description_col_index] = ""
                print(f"  ✗ Failed to extract description")
            
            # Rate limiting - be polite to the server
            if processed < len(urls_to_process):
                delay = random.uniform(1.0, 2.5)
                print(f"  → Waiting {delay:.1f}s before next request...")
                await asyncio.sleep(delay)
        
        await browser.close()
    
    # Write the updated CSV file
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"\n{'='*60}")
    print(f"Test batch complete!")
    print(f"Processed: {processed} URLs")
    print(f"Successful: {successful} descriptions extracted")
    print(f"Failed: {processed - successful}")
    print(f"Results saved to: {OUTPUT_CSV}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(process_test_batch())

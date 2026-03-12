"""
Quick test to extract description from a single URL
"""
import asyncio
from playwright.async_api import async_playwright

async def test_extract():
    url = "https://www.adb.org/projects/29600-013/main"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"Navigating to {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Try to click Project Data Sheet
            try:
                await page.click('text="Project Data Sheet"')
                print("Clicked Project Data Sheet")
                await page.wait_for_timeout(3000)
            except:
                print("Could not click Project Data Sheet")
            
            # Try to find description
            try:
                rows = await page.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) >= 2:
                        first_text = await cells[0].inner_text()
                        if first_text and 'description' in first_text.lower():
                            desc = await cells[1].inner_text()
                            print(f"Found description: {desc[:200]}...")
                            break
            except Exception as e:
                print(f"Error: {e}")
            
            await page.wait_for_timeout(5000)  # Keep browser open for inspection
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_extract())


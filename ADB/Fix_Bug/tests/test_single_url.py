"""
Quick single URL test using ScraperAPI -- this one uses the meta tag -- description lies in the <dd></dd> description tag. (updated full working code under adb_scrapper_with_scrapperAPI.py)
"""

import requests
from bs4 import BeautifulSoup

API_KEY     = "4ce855c35a657eb52b13db560d24d56c"
PROJECT_URL = "https://www.adb.org/projects/48409-001/main"

def fetch_description(url):
    print(f"Fetching: {url}\n")

    # Build URL directly instead of using params dict
    scraper_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=false"

    resp = requests.get(scraper_url, timeout=60)

    print(f"Status code: {resp.status_code}")

    if not resp.ok:
        print(f"Failed — HTTP {resp.status_code}")
        print(resp.text[:200])
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    # Strategy 1: meta tag
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content", "").strip():
        print(f"\n✓ Found via meta tag:")
        print("-" * 60)
        print(meta["content"].strip())
        print("-" * 60)
        return

    # Strategy 2: dt/dd
    for dt in soup.find_all("dt"):
        if dt.get_text(strip=True).lower() == "description":
            dd = dt.find_next_sibling("dd")
            if dd:
                text = " ".join(dd.get_text(" ", strip=True).split())
                if len(text) > 30:
                    print(f"\n✓ Found via dt/dd:")
                    print("-" * 60)
                    print(text)
                    print("-" * 60)
                    return

    print("✗ No description found in the page")

if __name__ == "__main__":
    fetch_description(PROJECT_URL)
#!/usr/bin/env python3
"""
Debug Single Project
===================
Test a single project to understand why pages are not loading correctly.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def debug_project(project_number):
    """Debug a single project to understand the issue."""
    
    # Setup Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"Testing project: {project_number}")
        
        # First visit main site
        print("1. Visiting main IDB site...")
        driver.get("https://www.iadb.org/en")
        time.sleep(3)
        print(f"   Main page title: {driver.title}")
        
        # Now visit project page
        url = f"https://www.iadb.org/en/project/{project_number}"
        print(f"2. Visiting project page: {url}")
        driver.get(url)
        time.sleep(5)
        
        print(f"   Project page title: {driver.title}")
        print(f"   Current URL: {driver.current_url}")
        
        # Check page content
        page_source = driver.page_source
        print(f"   Page source length: {len(page_source)}")
        
        # Check for specific content
        if "Project not found" in page_source:
            print("   ❌ 'Project not found' detected in page source")
        elif "404" in page_source:
            print("   ❌ '404' detected in page source")
        else:
            print("   ✅ No 'Project not found' or '404' detected")
        
        # Look for project-specific content
        if project_number in page_source:
            print(f"   ✅ Project number '{project_number}' found in page source")
        else:
            print(f"   ❌ Project number '{project_number}' NOT found in page source")
        
        # Check for document cards
        document_cards = driver.find_elements(By.TAG_NAME, "idb-document-card")
        print(f"   Found {len(document_cards)} document cards")
        
        # Check for Preparation Phase
        prep_phase = driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
        print(f"   Found {len(prep_phase)} Preparation Phase elements")
        
        # Save page source for inspection
        with open(f"debug_{project_number}_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print(f"   Page source saved to debug_{project_number}_page.html")
        
        return len(document_cards) > 0
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        driver.quit()

def main():
    # Test a few projects that we know should work
    test_projects = ["PE-L1187", "CO-M1089", "RG-T4752"]
    
    for project in test_projects:
        print(f"\n{'='*60}")
        success = debug_project(project)
        print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()

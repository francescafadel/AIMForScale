#!/usr/bin/env python3
"""
Test Single Project
==================
Test document extraction from a single project to understand the structure.
"""

import pandas as pd
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import urllib.request
import ssl

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

class TestSingleProject:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Use system ChromeDriver if available
            try:
                service = Service("chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                # Fallback to webdriver-manager
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("✓ Chrome WebDriver setup successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup WebDriver: {e}")
            return False
    
    def test_project(self, project_number="PE-L1187"):
        """Test document extraction from a single project."""
        print(f"Testing project: {project_number}")
        
        if not self.setup_driver():
            return
        
        try:
            # Navigate to project page
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(5)
            
            print(f"Page title: {self.driver.title}")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Look for Preparation Phase
            prep_phase = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
            print(f"Found {len(prep_phase)} Preparation Phase elements")
            
            if prep_phase:
                # Click to expand
                for element in prep_phase:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)
                        print("Clicked on Preparation Phase")
                    except Exception as e:
                        print(f"Error clicking Preparation Phase: {e}")
            
            # Find document cards
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            print(f"Found {len(document_cards)} document cards")
            
            # Print details of first few cards
            for i, card in enumerate(document_cards[:3]):
                print(f"\nDocument Card {i+1}:")
                print(f"  Tag name: {card.tag_name}")
                print(f"  Text: {card.text[:100]}...")
                print(f"  HTML: {card.get_attribute('outerHTML')[:200]}...")
                
                # Look for any clickable elements inside
                try:
                    buttons = card.find_elements(By.TAG_NAME, "button")
                    links = card.find_elements(By.TAG_NAME, "a")
                    print(f"  Buttons: {len(buttons)}")
                    print(f"  Links: {len(links)}")
                    
                    for j, link in enumerate(links):
                        href = link.get_attribute('href')
                        text = link.text
                        print(f"    Link {j+1}: {text} -> {href}")
                        
                except Exception as e:
                    print(f"  Error examining card: {e}")
            
            # Try clicking on first card
            if document_cards:
                try:
                    print(f"\nClicking on first document card...")
                    self.driver.execute_script("arguments[0].click();", document_cards[0])
                    time.sleep(3)
                    
                    # Look for download options after clicking
                    download_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'English') or contains(text(), 'Spanish')]")
                    download_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(@href, '.doc')]")
                    
                    print(f"After clicking, found:")
                    print(f"  Download buttons: {len(download_buttons)}")
                    print(f"  Download links: {len(download_links)}")
                    
                    for i, btn in enumerate(download_buttons):
                        print(f"    Button {i+1}: {btn.text}")
                    
                    for i, link in enumerate(download_links):
                        href = link.get_attribute('href')
                        text = link.text
                        print(f"    Link {i+1}: {text} -> {href}")
                        
                except Exception as e:
                    print(f"Error clicking card: {e}")
            
            # Save page source for analysis
            with open(f"page_source_{project_number}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"\nPage source saved to page_source_{project_number}.html")
            
        except Exception as e:
            print(f"Error testing project: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    tester = TestSingleProject()
    tester.test_project("PE-L1187")

if __name__ == "__main__":
    main()


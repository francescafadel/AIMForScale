#!/usr/bin/env python3
"""
Browser Downloader
This script uses Selenium to simulate a real browser and download IDB documents.
"""

import pandas as pd
import time
import re
from pathlib import Path
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import urllib.parse

class BrowserDownloader:
    def __init__(self):
        # Create downloads directory
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable SSL certificate errors
        self.chrome_options.add_argument("--ignore-ssl-errors")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--allow-running-insecure-content")
        
        # Setup download preferences
        prefs = {
            "download.default_directory": str(self.downloads_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = None
        
    def setup_driver(self):
        """Setup the Chrome WebDriver."""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            print("✓ Chrome WebDriver setup successfully")
            return True
        except Exception as e:
            print(f"✗ Error setting up Chrome WebDriver: {e}")
            return False
    
    def get_pe_l1187_data(self):
        """Get PE-L1187 project data from the CSV."""
        print("Loading PE-L1187 project data...")
        
        # Read the CSV file
        df = pd.read_csv("IDB Corpus Key Words.csv", skiprows=1)
        
        # Find PE-L1187
        pe_l1187_row = df[df['Project Number'] == 'PE-L1187']
        
        if pe_l1187_row.empty:
            print("PE-L1187 not found in CSV!")
            return None
        
        project = {
            'project_number': 'PE-L1187',
            'project_name': pe_l1187_row.iloc[0]['Project Name'],
            'country': pe_l1187_row.iloc[0]['Project Country'],
            'operation_number': pe_l1187_row.iloc[0]['Operation Number'],
            'approval_date': pe_l1187_row.iloc[0]['Approval Date'],
            'status': pe_l1187_row.iloc[0]['Status'],
            'project_type': pe_l1187_row.iloc[0]['Project Type'],
            'total_cost': pe_l1187_row.iloc[0]['Total Cost']
        }
        
        print(f"Found PE-L1187: {project['project_name']}")
        print(f"Country: {project['country']}")
        print(f"Operation: {project['operation_number']}")
        print(f"Type: {project['project_type']}")
        print(f"Cost: ${project['total_cost']:,.0f}")
        
        return project
    
    def download_documents_via_browser(self, project):
        """Download documents using browser automation."""
        if not self.setup_driver():
            return 0
        
        try:
            print(f"\nDownloading documents for {project['project_number']} via browser...")
            
            # Navigate to the project page
            project_url = f"https://www.iadb.org/en/project/{project['project_number']}"
            print(f"Navigating to: {project_url}")
            
            self.driver.get(project_url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded successfully
            if "Increasing Cocoa Productivity" in self.driver.page_source:
                print("✓ Project page loaded successfully")
            else:
                print("✗ Project page not loaded correctly")
                return 0
            
            # Scroll down to find the Preparation Phase section
            print("Looking for Preparation Phase section...")
            self.scroll_to_preparation_phase()
            
            # Look for download buttons
            downloaded_count = self.find_and_click_download_buttons(project)
            
            return downloaded_count
            
        except Exception as e:
            print(f"✗ Error during browser automation: {e}")
            return 0
        finally:
            if self.driver:
                self.driver.quit()
    
    def scroll_to_preparation_phase(self):
        """Scroll down to find the Preparation Phase section."""
        try:
            # Scroll down to find "Preparation Phase"
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for "Preparation Phase" text
            preparation_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
            
            if preparation_elements:
                print("✓ Found Preparation Phase section")
                # Scroll to the first occurrence
                self.driver.execute_script("arguments[0].scrollIntoView();", preparation_elements[0])
                time.sleep(2)
            else:
                print("✗ Preparation Phase section not found")
                
        except Exception as e:
            print(f"Error scrolling to Preparation Phase: {e}")
    
    def find_and_click_download_buttons(self, project):
        """Find and click download buttons for TC Abstract documents."""
        downloaded_count = 0
        
        try:
            # Look for download buttons or links
            # Try different selectors for download buttons
            download_selectors = [
                "//button[contains(text(), 'English')]",
                "//button[contains(text(), 'Spanish')]",
                "//a[contains(text(), 'English')]",
                "//a[contains(text(), 'Spanish')]",
                "//button[contains(@class, 'download')]",
                "//a[contains(@class, 'download')]",
                "//button[contains(@aria-label, 'download')]",
                "//a[contains(@aria-label, 'download')]"
            ]
            
            for selector in download_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    if buttons:
                        print(f"Found {len(buttons)} download buttons with selector: {selector}")
                        
                        for button in buttons:
                            try:
                                # Get button text to identify language
                                button_text = button.text.strip()
                                print(f"Clicking download button: {button_text}")
                                
                                # Click the button
                                button.click()
                                time.sleep(3)  # Wait for download to start
                                
                                downloaded_count += 1
                                print(f"✓ Clicked download button for: {button_text}")
                                
                            except Exception as e:
                                print(f"Error clicking button: {e}")
                                continue
                        
                        if downloaded_count > 0:
                            break
                            
                except Exception as e:
                    continue
            
            # If no buttons found, try to find document cards
            if downloaded_count == 0:
                downloaded_count = self.find_document_cards(project)
            
            return downloaded_count
            
        except Exception as e:
            print(f"Error finding download buttons: {e}")
            return 0
    
    def find_document_cards(self, project):
        """Find document cards and extract download URLs."""
        try:
            print("Looking for document cards...")
            
            # Look for idb-document-card elements
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            
            if document_cards:
                print(f"Found {len(document_cards)} document cards")
                
                for card in document_cards:
                    try:
                        # Get the URL attribute
                        url = card.get_attribute("url")
                        if url and "EZSHARE" in url:
                            print(f"Found document URL: {url}")
                            
                            # Try to download directly
                            if self.download_via_url(url, project):
                                return 1
                    except Exception as e:
                        print(f"Error processing document card: {e}")
                        continue
            
            return 0
            
        except Exception as e:
            print(f"Error finding document cards: {e}")
            return 0
    
    def download_via_url(self, url, project):
        """Download document via direct URL."""
        try:
            print(f"Attempting direct download from: {url}")
            
            # Create country directory
            country = project['country']
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Determine filename based on URL
            if "1121147323-4" in url:
                filename = f"{project['project_number']}_TC_Abstract_Spanish_PERU_Sintesis_proyecto_PES_PE-L1187.pdf"
            elif "1121147323-5" in url:
                filename = f"{project['project_number']}_TC_Abstract_English_PERU_Project_Synthesis_SEP_PE-L1187.pdf"
            else:
                filename = f"{project['project_number']}_TC_Abstract_{hash(url) % 10000}.pdf"
            
            filepath = country_dir / filename
            
            # Use urllib to download (bypass SSL issues)
            try:
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                
                urllib.request.urlretrieve(url, filepath)
                
                if filepath.exists() and filepath.stat().st_size > 0:
                    print(f"✓ Downloaded: {filename}")
                    print(f"File size: {filepath.stat().st_size:,} bytes")
                    return True
                else:
                    print(f"✗ Download failed or file is empty")
                    return False
                    
            except Exception as e:
                print(f"✗ Error downloading via URL: {e}")
                return False
                
        except Exception as e:
            print(f"✗ Error in download_via_url: {e}")
            return False
    
    def test_pe_l1187(self):
        """Test downloading documents for PE-L1187 using browser automation."""
        print("=" * 80)
        print("BROWSER DOWNLOADER TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Download documents via browser
        downloaded_count = self.download_documents_via_browser(project)
        
        print(f"\nDownload Summary:")
        print(f"  Documents attempted: 2")
        print(f"  Successfully downloaded: {downloaded_count}")
        print(f"  Failed downloads: {2 - downloaded_count}")
        
        if downloaded_count > 0:
            print(f"\n✓ SUCCESS: Downloaded {downloaded_count} documents for PE-L1187!")
            print(f"Files saved in: {self.downloads_dir}/{project['country']}")
        else:
            print(f"\n✗ Browser automation failed to download documents.")
            print("The documents may require manual intervention or have additional security measures.")

def main():
    downloader = BrowserDownloader()
    downloader.test_pe_l1187()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Advanced Browser Downloader
This script uses advanced browser automation to handle 403 Forbidden errors and download IDB documents.
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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import urllib.parse

class AdvancedBrowserDownloader:
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
        
        # Enable JavaScript and cookies
        self.chrome_options.add_argument("--enable-javascript")
        self.chrome_options.add_argument("--enable-cookies")
        
        # Setup download preferences
        prefs = {
            "download.default_directory": str(self.downloads_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.notifications": 2
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
        """Download documents using advanced browser automation."""
        if not self.setup_driver():
            return 0
        
        try:
            print(f"\nDownloading documents for {project['project_number']} via advanced browser...")
            
            # First, visit the main IDB site to establish a session
            print("Establishing browser session...")
            self.driver.get("https://www.iadb.org/en")
            time.sleep(3)
            
            # Navigate to the project page
            project_url = f"https://www.iadb.org/en/project/{project['project_number']}"
            print(f"Navigating to: {project_url}")
            
            self.driver.get(project_url)
            time.sleep(5)  # Wait for page to load
            
            # Check if page loaded successfully
            if "Increasing Cocoa Productivity" in self.driver.page_source:
                print("✓ Project page loaded successfully")
            else:
                print("✗ Project page not loaded correctly")
                return 0
            
            # Scroll down to find the Preparation Phase section
            print("Looking for Preparation Phase section...")
            self.scroll_to_preparation_phase()
            
            # Try to click download buttons with proper interaction
            downloaded_count = self.advanced_download_attempt(project)
            
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
            time.sleep(3)
            
            # Look for "Preparation Phase" text
            preparation_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
            
            if preparation_elements:
                print("✓ Found Preparation Phase section")
                # Scroll to the first occurrence
                self.driver.execute_script("arguments[0].scrollIntoView();", preparation_elements[0])
                time.sleep(3)
            else:
                print("✗ Preparation Phase section not found")
                
        except Exception as e:
            print(f"Error scrolling to Preparation Phase: {e}")
    
    def advanced_download_attempt(self, project):
        """Advanced download attempt with proper browser interaction."""
        downloaded_count = 0
        
        try:
            # Look for document cards first
            print("Looking for document cards...")
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            
            if document_cards:
                print(f"Found {len(document_cards)} document cards")
                
                for i, card in enumerate(document_cards):
                    try:
                        print(f"Processing document card {i+1}/{len(document_cards)}")
                        
                        # Get the URL attribute
                        url = card.get_attribute("url")
                        if url and "EZSHARE" in url:
                            print(f"Found document URL: {url}")
                            
                            # Try to click the card to trigger download
                            if self.click_document_card(card, project):
                                downloaded_count += 1
                                time.sleep(2)  # Wait between downloads
                            
                    except Exception as e:
                        print(f"Error processing document card {i+1}: {e}")
                        continue
            
            # If no cards found or no downloads, try alternative methods
            if downloaded_count == 0:
                downloaded_count = self.try_alternative_download_methods(project)
            
            return downloaded_count
            
        except Exception as e:
            print(f"Error in advanced download attempt: {e}")
            return 0
    
    def click_document_card(self, card, project):
        """Click on document card to trigger download."""
        try:
            # Scroll to the card
            self.driver.execute_script("arguments[0].scrollIntoView();", card)
            time.sleep(1)
            
            # Try different click methods
            try:
                # Method 1: Direct click
                card.click()
                print("✓ Clicked document card directly")
                return True
            except:
                try:
                    # Method 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", card)
                    print("✓ Clicked document card via JavaScript")
                    return True
                except:
                    try:
                        # Method 3: Action chains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(card).click().perform()
                        print("✓ Clicked document card via ActionChains")
                        return True
                    except Exception as e:
                        print(f"All click methods failed: {e}")
                        return False
                        
        except Exception as e:
            print(f"Error clicking document card: {e}")
            return False
    
    def try_alternative_download_methods(self, project):
        """Try alternative download methods."""
        try:
            print("Trying alternative download methods...")
            
            # Look for any clickable elements that might be download buttons
            download_selectors = [
                "//button[contains(text(), 'English')]",
                "//button[contains(text(), 'Spanish')]",
                "//a[contains(text(), 'English')]",
                "//a[contains(text(), 'Spanish')]",
                "//button[contains(@class, 'download')]",
                "//a[contains(@class, 'download')]",
                "//button[contains(@aria-label, 'download')]",
                "//a[contains(@aria-label, 'download')]",
                "//*[contains(@class, 'download')]",
                "//*[contains(@onclick, 'download')]"
            ]
            
            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements:
                            try:
                                # Scroll to element
                                self.driver.execute_script("arguments[0].scrollIntoView();", element)
                                time.sleep(1)
                                
                                # Try to click
                                element.click()
                                print(f"✓ Clicked element: {element.text}")
                                time.sleep(3)  # Wait for download
                                
                                return 1  # Success
                                
                            except Exception as e:
                                print(f"Error clicking element: {e}")
                                continue
                                
                except Exception as e:
                    continue
            
            return 0
            
        except Exception as e:
            print(f"Error in alternative download methods: {e}")
            return 0
    
    def check_downloads_directory(self):
        """Check if any files were downloaded."""
        try:
            # Check the downloads directory for new files
            files_before = set()
            for file in self.downloads_dir.rglob("*.pdf"):
                files_before.add(file.name)
            
            print(f"Files in downloads directory before: {len(files_before)}")
            
            # Wait a bit for downloads to complete
            time.sleep(5)
            
            files_after = set()
            for file in self.downloads_dir.rglob("*.pdf"):
                files_after.add(file.name)
            
            print(f"Files in downloads directory after: {len(files_after)}")
            
            new_files = files_after - files_before
            if new_files:
                print(f"New files downloaded: {new_files}")
                return len(new_files)
            else:
                print("No new files downloaded")
                return 0
                
        except Exception as e:
            print(f"Error checking downloads directory: {e}")
            return 0
    
    def test_pe_l1187(self):
        """Test downloading documents for PE-L1187 using advanced browser automation."""
        print("=" * 80)
        print("ADVANCED BROWSER DOWNLOADER TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Download documents via browser
        downloaded_count = self.download_documents_via_browser(project)
        
        # Check if files were actually downloaded
        actual_downloads = self.check_downloads_directory()
        
        print(f"\nDownload Summary:")
        print(f"  Documents attempted: 2")
        print(f"  Click events triggered: {downloaded_count}")
        print(f"  Actual files downloaded: {actual_downloads}")
        
        if actual_downloads > 0:
            print(f"\n✓ SUCCESS: Downloaded {actual_downloads} documents for PE-L1187!")
            print(f"Files saved in: {self.downloads_dir}")
        else:
            print(f"\n✗ Advanced browser automation failed to download documents.")
            print("The documents may require manual intervention or have additional security measures.")

def main():
    downloader = AdvancedBrowserDownloader()
    downloader.test_pe_l1187()

if __name__ == "__main__":
    main()

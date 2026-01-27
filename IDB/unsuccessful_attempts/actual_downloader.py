#!/usr/bin/env python3
"""
Actual Document Downloader
==========================
Downloads the actual documents by going back to project pages and extracting real URLs.
"""

import pandas as pd
import requests
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import ssl

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

class ActualDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*',
            'Referer': 'https://www.iadb.org/',
        })
        self.session.verify = False
        
        # Tracking data
        self.tracking_data = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def setup_driver(self):
        """Setup Chrome WebDriver."""
        try:
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
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("✓ Chrome WebDriver setup successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup WebDriver: {e}")
            return False
    
    def load_tracking_data(self):
        """Load existing tracking data to see what documents were found."""
        try:
            df = pd.read_csv("final_complete_tracking_data.csv")
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            return []
    
    def extract_and_download_documents(self, project):
        """Extract document URLs and download them."""
        project_number = project['project_number']
        country = project['country']
        
        print(f"Processing project {project_number}: {project['project_name']}")
        print(f"  Country: {country}")
        
        try:
            # Navigate to project page
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"  Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded correctly
            if "Project not found" in self.driver.page_source or "404" in self.driver.page_source:
                print(f"  ✗ Project page not accessible")
                return 0
            
            print(f"  ✓ Project page loaded successfully")
            
            # Look for Preparation Phase section
            try:
                # Scroll to find Preparation Phase
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Look for Preparation Phase
                prep_phase = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
                if prep_phase:
                    print(f"    ✓ Found Preparation Phase section")
                    # Click to expand if needed
                    for element in prep_phase:
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(1)
                        except:
                            pass
                else:
                    print(f"    ✗ Preparation Phase section not found")
                    
            except Exception as e:
                print(f"    Error looking for Preparation Phase: {e}")
            
            # Find document cards
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            print(f"  Found {len(document_cards)} document cards")
            
            documents_downloaded = 0
            
            for i, card in enumerate(document_cards):
                try:
                    print(f"    Processing document {i+1}/{len(document_cards)}")
                    
                    # Get document URL
                    doc_url = card.get_attribute('href') or card.get_attribute('data-href')
                    if not doc_url:
                        continue
                    
                    # Get document title
                    title_elem = card.find_element(By.TAG_NAME, "h3") if card.find_elements(By.TAG_NAME, "h3") else None
                    if not title_elem:
                        title_elem = card.find_element(By.TAG_NAME, "h4") if card.find_elements(By.TAG_NAME, "h4") else None
                    
                    doc_title = title_elem.text if title_elem else f"Document {i+1}"
                    
                    print(f"      Found document URL: {doc_url}")
                    
                    # Download the document
                    if self.download_document(doc_url, project_number, country, doc_title):
                        documents_downloaded += 1
                    
                except Exception as e:
                    print(f"    Error processing document card: {e}")
                    continue
            
            return documents_downloaded
            
        except Exception as e:
            print(f"  ✗ Error processing project: {e}")
            return 0
    
    def download_document(self, doc_url, project_number, country, doc_title):
        """Download document using reliable method."""
        try:
            print(f"      Downloading: {doc_title}")
            
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', doc_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{project_number}_{safe_title}.pdf"
            
            # Create country directory
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Method 1: Try requests first
            try:
                response = self.session.get(doc_url, timeout=60, stream=True)
                if response.status_code == 200:
                    file_path = country_dir / filename
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"      ✓ Downloaded: {filename}")
                    print(f"      ✓ Saved to: {country}/")
                    return True
            except Exception as e:
                print(f"      Requests failed: {e}")
            
            # Method 2: Try urllib as fallback
            try:
                file_path = country_dir / filename
                urllib.request.urlretrieve(doc_url, file_path)
                print(f"      ✓ Downloaded: {filename}")
                print(f"      ✓ Saved to: {country}/")
                return True
            except Exception as e:
                print(f"      urllib failed: {e}")
            
            print(f"      ✗ All download methods failed")
            return False
            
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
    def process_projects_with_documents(self, tracking_data, max_projects=50):
        """Process projects that have documents found."""
        print(f"Processing projects with documents...")
        
        projects_with_docs = [p for p in tracking_data if p['documents_found'] > 0]
        print(f"Found {len(projects_with_docs)} projects with documents")
        
        # Limit to max_projects for testing
        projects_to_process = projects_with_docs[:max_projects]
        print(f"Processing first {len(projects_to_process)} projects")
        
        if not self.setup_driver():
            print("Failed to setup WebDriver. Exiting.")
            return
        
        try:
            for i, project in enumerate(projects_to_process):
                documents_downloaded = self.extract_and_download_documents(project)
                
                self.processed_count += 1
                if documents_downloaded > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 10 projects
                if (i + 1) % 10 == 0:
                    print(f"\nProgress: {i + 1} projects processed")
                    print(f"Successful: {self.success_count}")
                    print(f"Failed: {self.error_count}")
                
                # Be respectful with delays
                time.sleep(2)
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.tracking_data
    
    def generate_summary_report(self):
        """Generate a summary report."""
        print("\n" + "="*80)
        print("ACTUAL DOWNLOADER SUMMARY")
        print("="*80)
        
        print(f"Projects Processed: {self.processed_count}")
        print(f"Successful Downloads: {self.success_count}")
        print(f"Failed Downloads: {self.error_count}")
        
        # Show downloads directory structure
        print(f"\nDownloads Directory Structure:")
        for country_dir in self.downloads_dir.iterdir():
            if country_dir.is_dir():
                files = list(country_dir.glob("*"))
                print(f"  {country_dir.name}: {len(files)} files")

def main():
    downloader = ActualDownloader()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process projects with documents (limit to 50 for testing)
    downloader.process_projects_with_documents(tracking_data, max_projects=50)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== ACTUAL DOWNLOADER COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()

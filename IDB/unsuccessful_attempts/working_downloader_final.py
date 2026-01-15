#!/usr/bin/env python3
"""
Working Downloader Final
========================
Actually downloads documents by extracting URLs from idb-document-card elements.
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
import os

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

class WorkingDownloaderFinal:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Tracking data
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
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
    
    def load_tracking_data(self):
        """Load existing tracking data."""
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
        
        print(f"\nProcessing project {project_number}: {project['project_name']}")
        print(f"  Country: {country}")
        
        try:
            # Navigate to project page
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"  Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(5)
            
            # Check if page loaded correctly
            if "Project not found" in self.driver.page_source or "404" in self.driver.title:
                print(f"  ✗ Project page not accessible")
                return 0
            
            print(f"  ✓ Project page loaded successfully")
            
            # Scroll to find document sections
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Look for Preparation Phase and expand it
            try:
                prep_phase = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
                if prep_phase:
                    print(f"    ✓ Found Preparation Phase section")
                    # Click to expand
                    for element in prep_phase:
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(2)
                        except:
                            pass
                else:
                    print(f"    ✗ Preparation Phase section not found")
            except Exception as e:
                print(f"    Error with Preparation Phase: {e}")
            
            # Find document cards
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            print(f"  Found {len(document_cards)} document cards")
            
            documents_downloaded = 0
            
            for i, card in enumerate(document_cards):
                try:
                    # Get document URL from the url attribute
                    doc_url = card.get_attribute('url')
                    if not doc_url:
                        continue
                    
                    # Get document title from the heading slot
                    try:
                        heading_elem = card.find_element(By.XPATH, ".//div[@slot='heading']")
                        doc_title = heading_elem.text if heading_elem else f"Document_{project_number}_{i+1}"
                    except:
                        doc_title = f"Document_{project_number}_{i+1}"
                    
                    # Get document type from the detail slot
                    try:
                        detail_elem = card.find_element(By.XPATH, ".//div[@slot='detail']")
                        doc_type = detail_elem.text if detail_elem else ""
                    except:
                        doc_type = ""
                    
                    # Get language from the cta slot
                    try:
                        cta_elem = card.find_element(By.XPATH, ".//div[@slot='cta']")
                        language = cta_elem.text if cta_elem else ""
                    except:
                        language = ""
                    
                    print(f"    Document {i+1}: {doc_title}")
                    print(f"      Type: {doc_type}")
                    print(f"      Language: {language}")
                    print(f"      URL: {doc_url}")
                    
                    # Download the document
                    if self.download_document(doc_url, project_number, country, doc_title, doc_type, language):
                        documents_downloaded += 1
                    
                except Exception as e:
                    print(f"    Error processing document card: {e}")
                    continue
            
            return documents_downloaded
            
        except Exception as e:
            print(f"  ✗ Error processing project: {e}")
            return 0
    
    def download_document(self, doc_url, project_number, country, doc_title, doc_type, language):
        """Download document using reliable method."""
        try:
            print(f"      Downloading: {doc_title}")
            
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', doc_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{project_number}_{doc_type}_{language}_{safe_title}.pdf"
            
            # Create country directory
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Method 1: Try urllib first
            try:
                file_path = country_dir / filename
                urllib.request.urlretrieve(doc_url, file_path)
                
                # Check if file was actually downloaded
                if file_path.exists() and file_path.stat().st_size > 0:
                    print(f"      ✓ Downloaded: {filename}")
                    print(f"      ✓ Saved to: {country}/")
                    return True
                else:
                    print(f"      ✗ File download failed or empty")
                    if file_path.exists():
                        file_path.unlink()  # Remove empty file
            except Exception as e:
                print(f"      urllib failed: {e}")
            
            # Method 2: Try requests as fallback
            try:
                import requests
                response = requests.get(doc_url, timeout=60, stream=True, verify=False)
                if response.status_code == 200:
                    file_path = country_dir / filename
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if file_path.exists() and file_path.stat().st_size > 0:
                        print(f"      ✓ Downloaded: {filename}")
                        print(f"      ✓ Saved to: {country}/")
                        return True
                    else:
                        print(f"      ✗ File download failed or empty")
                        if file_path.exists():
                            file_path.unlink()
            except Exception as e:
                print(f"      requests failed: {e}")
            
            print(f"      ✗ All download methods failed")
            return False
            
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
    def process_top_projects(self, tracking_data, top_n=10):
        """Process top projects with most documents."""
        print(f"Processing top {top_n} projects with most documents...")
        
        # Sort by documents found
        projects_with_docs = [p for p in tracking_data if p['documents_found'] > 0]
        projects_with_docs.sort(key=lambda x: x['documents_found'], reverse=True)
        
        top_projects = projects_with_docs[:top_n]
        print(f"Top projects by document count:")
        
        for i, project in enumerate(top_projects):
            print(f"  {i+1}. {project['project_number']} ({project['country']}): {project['documents_found']} documents")
        
        if not self.setup_driver():
            print("Failed to setup WebDriver. Exiting.")
            return
        
        try:
            for i, project in enumerate(top_projects):
                documents_downloaded = self.extract_and_download_documents(project)
                
                self.processed_count += 1
                if documents_downloaded > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 5 projects
                if (i + 1) % 5 == 0:
                    print(f"\nProgress: {i + 1} projects processed")
                    print(f"Successful: {self.success_count}")
                    print(f"Failed: {self.error_count}")
                
                # Be respectful with delays
                time.sleep(3)
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_summary_report(self):
        """Generate a summary report."""
        print("\n" + "="*80)
        print("WORKING DOWNLOADER FINAL SUMMARY")
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
    downloader = WorkingDownloaderFinal()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process top 10 projects with most documents
    downloader.process_top_projects(tracking_data, top_n=10)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== WORKING DOWNLOADER FINAL COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()

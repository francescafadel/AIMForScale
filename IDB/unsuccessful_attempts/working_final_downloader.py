#!/usr/bin/env python3
"""
Working Final Downloader
========================
Actually downloads documents using Selenium with proper setup.
"""

import pandas as pd
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
import ssl
import os

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

class WorkingFinalDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Tracking data
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver with proper configuration."""
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
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Set download preferences
            prefs = {
                "download.default_directory": str(self.downloads_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
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
            time.sleep(5)  # Wait for page to load
            
            # Check if page loaded correctly
            if "Project not found" in self.driver.page_source or "404" in self.driver.title:
                print(f"  ✗ Project page not accessible")
                return 0
            
            print(f"  ✓ Project page loaded successfully")
            
            # Scroll to find document sections
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Look for Preparation Phase and other document sections
            sections = [
                "//*[contains(text(), 'Preparation Phase')]",
                "//*[contains(text(), 'Project Documentation')]",
                "//*[contains(text(), 'Documents')]",
                "//*[contains(@class, 'document')]"
            ]
            
            for section_xpath in sections:
                try:
                    elements = self.driver.find_elements(By.XPATH, section_xpath)
                    if elements:
                        print(f"    ✓ Found section: {section_xpath}")
                        # Click to expand if needed
                        for element in elements:
                            try:
                                self.driver.execute_script("arguments[0].click();", element)
                                time.sleep(2)
                            except:
                                pass
                except:
                    pass
            
            # Find document cards and links
            document_elements = []
            
            # Method 1: Look for idb-document-card elements
            try:
                cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
                document_elements.extend(cards)
                print(f"    Found {len(cards)} idb-document-card elements")
            except:
                pass
            
            # Method 2: Look for document links
            try:
                doc_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(@href, '.doc')]")
                document_elements.extend(doc_links)
                print(f"    Found {len(doc_links)} document links")
            except:
                pass
            
            # Method 3: Look for download buttons
            try:
                download_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'English') or contains(text(), 'Spanish')]")
                document_elements.extend(download_buttons)
                print(f"    Found {len(download_buttons)} download buttons")
            except:
                pass
            
            documents_downloaded = 0
            
            for i, element in enumerate(document_elements):
                try:
                    print(f"    Processing document element {i+1}/{len(document_elements)}")
                    
                    # Get document URL
                    doc_url = None
                    if element.tag_name == "idb-document-card":
                        doc_url = element.get_attribute('href') or element.get_attribute('data-href')
                    elif element.tag_name == "a":
                        doc_url = element.get_attribute('href')
                    elif element.tag_name == "button":
                        # For buttons, try to find the associated link
                        parent = element.find_element(By.XPATH, "./..")
                        link = parent.find_element(By.TAG_NAME, "a") if parent.find_elements(By.TAG_NAME, "a") else None
                        doc_url = link.get_attribute('href') if link else None
                    
                    if not doc_url:
                        continue
                    
                    # Get document title
                    doc_title = f"Document_{project_number}_{i+1}"
                    try:
                        if element.tag_name == "idb-document-card":
                            title_elem = element.find_element(By.TAG_NAME, "h3") if element.find_elements(By.TAG_NAME, "h3") else None
                            if not title_elem:
                                title_elem = element.find_element(By.TAG_NAME, "h4") if element.find_elements(By.TAG_NAME, "h4") else None
                            doc_title = title_elem.text if title_elem else doc_title
                        elif element.tag_name == "a":
                            doc_title = element.text if element.text else doc_title
                    except:
                        pass
                    
                    print(f"      Found document URL: {doc_url}")
                    print(f"      Document title: {doc_title}")
                    
                    # Download the document
                    if self.download_document(doc_url, project_number, country, doc_title):
                        documents_downloaded += 1
                    
                except Exception as e:
                    print(f"    Error processing document element: {e}")
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
        
        return self.tracking_data
    
    def generate_summary_report(self):
        """Generate a summary report."""
        print("\n" + "="*80)
        print("WORKING FINAL DOWNLOADER SUMMARY")
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
    downloader = WorkingFinalDownloader()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process top 10 projects with most documents
    downloader.process_top_projects(tracking_data, top_n=10)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== WORKING FINAL DOWNLOADER COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()


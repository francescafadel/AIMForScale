#!/usr/bin/env python3
"""
Click and Download
==================
Clicks on document cards to reveal download links and downloads documents.
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

class ClickAndDownload:
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
    
    def click_and_extract_documents(self, project):
        """Click on document cards and extract download URLs."""
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
            
            # Process first 5 document cards to avoid overwhelming
            for i, card in enumerate(document_cards[:5]):
                try:
                    print(f"    Processing document card {i+1}/5")
                    
                    # Scroll to the card
                    self.driver.execute_script("arguments[0].scrollIntoView();", card)
                    time.sleep(1)
                    
                    # Click on the card to reveal download options
                    try:
                        self.driver.execute_script("arguments[0].click();", card)
                        time.sleep(2)
                        print(f"      ✓ Clicked on document card")
                    except Exception as e:
                        print(f"      ✗ Failed to click card: {e}")
                        continue
                    
                    # Look for download links that appeared after clicking
                    download_links = []
                    
                    # Method 1: Look for download buttons
                    try:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'English') or contains(text(), 'Spanish')]")
                        download_links.extend(buttons)
                        print(f"      Found {len(buttons)} download buttons")
                    except:
                        pass
                    
                    # Method 2: Look for download links
                    try:
                        links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(@href, '.doc')]")
                        download_links.extend(links)
                        print(f"      Found {len(links)} download links")
                    except:
                        pass
                    
                    # Method 3: Look for any clickable elements with download URLs
                    try:
                        all_links = self.driver.find_elements(By.TAG_NAME, "a")
                        for link in all_links:
                            href = link.get_attribute('href')
                            if href and ('.pdf' in href or '.doc' in href):
                                download_links.append(link)
                        print(f"      Found {len([l for l in all_links if l.get_attribute('href') and ('.pdf' in l.get_attribute('href') or '.doc' in l.get_attribute('href'))])} document links")
                    except:
                        pass
                    
                    # Download documents
                    for j, download_element in enumerate(download_links):
                        try:
                            if download_element.tag_name == "button":
                                # For buttons, try to find the associated link
                                parent = download_element.find_element(By.XPATH, "./..")
                                link = parent.find_element(By.TAG_NAME, "a") if parent.find_elements(By.TAG_NAME, "a") else None
                                doc_url = link.get_attribute('href') if link else None
                            else:
                                doc_url = download_element.get_attribute('href')
                            
                            if not doc_url:
                                continue
                            
                            # Get document title
                            doc_title = f"Document_{project_number}_{i+1}_{j+1}"
                            try:
                                doc_title = download_element.text if download_element.text else doc_title
                            except:
                                pass
                            
                            print(f"        Found document URL: {doc_url}")
                            print(f"        Document title: {doc_title}")
                            
                            # Download the document
                            if self.download_document(doc_url, project_number, country, doc_title):
                                documents_downloaded += 1
                            
                        except Exception as e:
                            print(f"        Error processing download element: {e}")
                            continue
                    
                    # Close any modal or popup that might have opened
                    try:
                        close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'close') or contains(@class, 'modal')]")
                        for close_btn in close_buttons:
                            self.driver.execute_script("arguments[0].click();", close_btn)
                            time.sleep(1)
                    except:
                        pass
                    
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
            print(f"          Downloading: {doc_title}")
            
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
                    print(f"          ✓ Downloaded: {filename}")
                    print(f"          ✓ Saved to: {country}/")
                    return True
                else:
                    print(f"          ✗ File download failed or empty")
                    if file_path.exists():
                        file_path.unlink()  # Remove empty file
            except Exception as e:
                print(f"          urllib failed: {e}")
            
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
                        print(f"          ✓ Downloaded: {filename}")
                        print(f"          ✓ Saved to: {country}/")
                        return True
                    else:
                        print(f"          ✗ File download failed or empty")
                        if file_path.exists():
                            file_path.unlink()
            except Exception as e:
                print(f"          requests failed: {e}")
            
            print(f"          ✗ All download methods failed")
            return False
            
        except Exception as e:
            print(f"          ✗ Download error: {e}")
            return False
    
    def process_top_projects(self, tracking_data, top_n=5):
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
                documents_downloaded = self.click_and_extract_documents(project)
                
                self.processed_count += 1
                if documents_downloaded > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 2 projects
                if (i + 1) % 2 == 0:
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
        print("CLICK AND DOWNLOAD SUMMARY")
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
    downloader = ClickAndDownload()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process top 5 projects with most documents
    downloader.process_top_projects(tracking_data, top_n=5)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== CLICK AND DOWNLOAD COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Hybrid IDB Document Downloader
==============================
Combines HTTP requests for efficiency with Selenium for document extraction
when needed. This approach is both fast and reliable.
"""

import pandas as pd
import requests
import time
import re
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote
import urllib3
from bs4 import BeautifulSoup
import ssl
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib.request

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HybridIDBDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.session.verify = False
        
        # Selenium driver (will be initialized when needed)
        self.driver = None
        
        # Tracking data
        self.tracking_data = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def setup_driver(self):
        """Setup Chrome WebDriver for Selenium."""
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
            
            # Set download preferences
            prefs = {
                "download.default_directory": str(self.downloads_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Disable SSL verification for urllib
            ssl._create_default_https_context = ssl._create_unverified_context
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("✓ Chrome WebDriver setup successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup WebDriver: {e}")
            return False
    
    def load_project_data(self, csv_file):
        """Load project data from CSV file."""
        try:
            print(f"Loading project data from {csv_file}...")
            df = pd.read_csv(csv_file, skiprows=1)
            projects = df.to_dict('records')
            print(f"Loaded {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"Error loading project data: {e}")
            return []
    
    def strategy_1_http_direct(self, project_number):
        """Strategy 1: Direct HTTP request to project page."""
        url = f"https://www.iadb.org/en/project/{project_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"    Strategy 1 failed: {e}")
        
        return None
    
    def strategy_2_selenium_extraction(self, project_number):
        """Strategy 2: Use Selenium to extract documents from project page."""
        if not self.driver:
            if not self.setup_driver():
                return []
        
        try:
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"    Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded correctly
            if "Project not found" in self.driver.page_source or "404" in self.driver.page_source:
                print(f"    ✗ Project page not found")
                return []
            
            print(f"    ✓ Project page loaded successfully")
            
            # Look for Preparation Phase section
            print(f"    Looking for Preparation Phase section...")
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
            print(f"    Found {len(document_cards)} document cards")
            
            documents = []
            for i, card in enumerate(document_cards):
                try:
                    print(f"      Processing document {i+1}/{len(document_cards)}")
                    
                    # Get document URL
                    doc_url = card.get_attribute('href') or card.get_attribute('data-href')
                    if not doc_url:
                        continue
                    
                    # Get document title
                    title_elem = card.find_element(By.TAG_NAME, "h3") if card.find_elements(By.TAG_NAME, "h3") else None
                    if not title_elem:
                        title_elem = card.find_element(By.TAG_NAME, "h4") if card.find_elements(By.TAG_NAME, "h4") else None
                    
                    title = title_elem.text if title_elem else f"Document {i+1}"
                    
                    print(f"        Found document URL: {doc_url}")
                    
                    # Click the document card to trigger download
                    try:
                        self.driver.execute_script("arguments[0].click();", card)
                        print(f"        ✓ Clicked document card via JavaScript")
                        time.sleep(2)  # Wait for download to start
                    except Exception as e:
                        print(f"        ✗ Failed to click document card: {e}")
                    
                    documents.append({
                        'url': doc_url,
                        'title': title,
                        'type': 'Document Card'
                    })
                    
                except Exception as e:
                    print(f"      Error processing document card: {e}")
                    continue
            
            return documents
            
        except Exception as e:
            print(f"    ✗ Error processing project: {e}")
            return []
    
    def download_document_hybrid(self, doc_info, project_number, country):
        """Download document using hybrid approach."""
        try:
            doc_url = doc_info['url']
            if not doc_url.startswith('http'):
                doc_url = urljoin('https://www.iadb.org', doc_url)
            
            print(f"    Downloading: {doc_info['title']}")
            
            # Method 1: Direct HTTP download
            try:
                response = self.session.get(doc_url, timeout=60, stream=True)
                if response.status_code == 200:
                    return self.save_document(response, doc_info, project_number, country)
            except Exception as e:
                print(f"      Direct download failed: {e}")
            
            # Method 2: Use urllib with SSL bypass
            try:
                # Create filename
                safe_title = re.sub(r'[^\w\s-]', '', doc_info['title']).strip()
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                filename = f"{project_number}_{safe_title}.pdf"
                
                # Create country directory
                country_dir = self.downloads_dir / country
                country_dir.mkdir(exist_ok=True)
                
                # Download using urllib
                file_path = country_dir / filename
                urllib.request.urlretrieve(doc_url, file_path)
                
                print(f"      ✓ Downloaded: {filename}")
                print(f"      ✓ Saved to: {country}/")
                return True
                
            except Exception as e:
                print(f"      urllib download failed: {e}")
            
            print(f"      ✗ All download methods failed")
            return False
            
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
    def save_document(self, response, doc_info, project_number, country):
        """Save downloaded document to file."""
        try:
            # Determine file extension
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type:
                ext = '.pdf'
            elif 'word' in content_type or 'docx' in content_type:
                ext = '.docx'
            elif 'doc' in content_type:
                ext = '.doc'
            else:
                # Try to determine from URL
                url = response.url
                if '.pdf' in url:
                    ext = '.pdf'
                elif '.docx' in url:
                    ext = '.docx'
                elif '.doc' in url:
                    ext = '.doc'
                else:
                    ext = '.pdf'  # Default
            
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', doc_info['title']).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{project_number}_{safe_title}{ext}"
            
            # Create country directory
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Save file
            file_path = country_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"      ✓ Downloaded: {filename}")
            print(f"      ✓ Saved to: {country}/")
            return True
            
        except Exception as e:
            print(f"      ✗ Save error: {e}")
            return False
    
    def process_project_hybrid(self, project):
        """Process a single project using hybrid approach."""
        project_number = project['Project Number']
        project_name = project['Project Name']
        country = project['Project Country']
        
        print(f"\nProcessing project {self.processed_count + 1}: {project_number}")
        print(f"  Project: {project_name}")
        print(f"  Country: {country}")
        
        # Strategy 1: Try HTTP first (fast)
        print(f"  Trying Strategy 1: HTTP direct access...")
        html_content = self.strategy_1_http_direct(project_number)
        
        if html_content:
            # Try to extract documents from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            document_cards = soup.find_all('idb-document-card')
            
            if document_cards:
                print(f"    Found {len(document_cards)} documents via HTTP")
                documents = []
                for card in document_cards:
                    doc_link = card.get('href') or card.get('data-href')
                    if doc_link:
                        title_elem = card.find('h3') or card.find('h4')
                        title = title_elem.get_text(strip=True) if title_elem else "Document"
                        documents.append({
                            'url': doc_link,
                            'title': title,
                            'type': 'HTTP'
                        })
                
                # Download documents
                downloaded_count = 0
                for doc in documents:
                    if self.download_document_hybrid(doc, project_number, country):
                        downloaded_count += 1
                
                status = 'Documents Available' if downloaded_count > 0 else 'Download Failed'
                
                return {
                    'project_number': project_number,
                    'project_name': project_name,
                    'country': country,
                    'operation_number': project.get('Operation Number', ''),
                    'documents_found': len(documents),
                    'documents_downloaded': downloaded_count,
                    'status': status,
                    'project_url': f"https://www.iadb.org/en/project/{project_number}"
                }
        
        # Strategy 2: Use Selenium (reliable)
        print(f"  Trying Strategy 2: Selenium extraction...")
        documents = self.strategy_2_selenium_extraction(project_number)
        
        if not documents:
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': country,
                'operation_number': project.get('Operation Number', ''),
                'documents_found': 0,
                'documents_downloaded': 0,
                'status': 'No Documents Found',
                'project_url': f"https://www.iadb.org/en/project/{project_number}"
            }
        
        print(f"  Total documents found: {len(documents)}")
        
        # Download documents
        downloaded_count = 0
        for doc in documents:
            if self.download_document_hybrid(doc, project_number, country):
                downloaded_count += 1
        
        status = 'Documents Available' if downloaded_count > 0 else 'Download Failed'
        
        return {
            'project_number': project_number,
            'project_name': project_name,
            'country': country,
            'operation_number': project.get('Operation Number', ''),
            'documents_found': len(documents),
            'documents_downloaded': downloaded_count,
            'status': status,
            'project_url': f"https://www.iadb.org/en/project/{project_number}"
        }
    
    def process_test_projects(self, projects, test_count=10):
        """Process test projects with hybrid approach."""
        print(f"\nStarting hybrid download process...")
        print(f"Processing first {test_count} projects out of {len(projects)}")
        
        for i in range(min(test_count, len(projects))):
            try:
                project = projects[i]
                result = self.process_project_hybrid(project)
                self.tracking_data.append(result)
                self.processed_count += 1
                
                # Update counters
                if result['documents_downloaded'] > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 5 projects
                if (i + 1) % 5 == 0:
                    self.save_tracking_data()
                    print(f"\n--- Progress Update ---")
                    print(f"Processed: {self.processed_count}")
                    print(f"Successful: {self.success_count}")
                    print(f"Failed: {self.error_count}")
                    print(f"Success Rate: {(self.success_count/self.processed_count*100):.1f}%")
                
                # Be respectful with delays
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing project {i + 1}: {e}")
                # Add error entry to tracking
                self.tracking_data.append({
                    'project_number': project.get('Project Number', f'Project_{i+1}'),
                    'project_name': project.get('Project Name', 'Unknown'),
                    'country': project.get('Project Country', 'Unknown'),
                    'operation_number': project.get('Operation Number', ''),
                    'documents_found': 0,
                    'documents_downloaded': 0,
                    'status': f'Error: {str(e)}',
                    'project_url': f"https://www.iadb.org/en/project/{project.get('Project Number', '')}"
                })
                self.processed_count += 1
                self.error_count += 1
        
        return self.tracking_data
    
    def save_tracking_data(self):
        """Save tracking data to CSV."""
        df = pd.DataFrame(self.tracking_data)
        df.to_csv("hybrid_tracking_data.csv", index=False)
        print(f"Tracking data saved to hybrid_tracking_data.csv")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("HYBRID IDB DOWNLOAD ANALYSIS SUMMARY")
        print("="*80)
        
        total_projects = len(df)
        projects_with_documents = len(df[df['documents_downloaded'] > 0])
        total_documents_found = df['documents_found'].sum()
        total_documents_downloaded = df['documents_downloaded'].sum()
        
        print(f"Total Projects Processed: {total_projects}")
        print(f"Projects with Documents Downloaded: {projects_with_documents}")
        print(f"Total Documents Found: {total_documents_found}")
        print(f"Total Documents Downloaded: {total_documents_downloaded}")
        print(f"Success Rate: {(projects_with_documents/total_projects*100):.1f}%")
        print(f"Document Download Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%" if total_documents_found > 0 else "Document Download Success Rate: N/A")
        
        print(f"\nStatus Summary:")
        status_counts = df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Save summary to file
        with open("hybrid_download_summary.txt", "w") as f:
            f.write("HYBRID IDB DOWNLOAD ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Projects Processed: {total_projects}\n")
            f.write(f"Projects with Documents Downloaded: {projects_with_documents}\n")
            f.write(f"Total Documents Found: {total_documents_found}\n")
            f.write(f"Total Documents Downloaded: {total_documents_downloaded}\n")
            f.write(f"Success Rate: {(projects_with_documents/total_projects*100):.1f}%\n")
            f.write(f"Document Download Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%\n\n" if total_documents_found > 0 else "Document Download Success Rate: N/A\n\n")
            
            f.write("Status Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count}\n")
        
        print(f"\nSummary report saved to hybrid_download_summary.txt")
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()

def main():
    downloader = HybridIDBDownloader()
    
    try:
        # Load project data
        projects = downloader.load_project_data("IDB Corpus Key Words.csv")
        
        if not projects:
            print("Failed to load project data. Exiting.")
            return
        
        # Process test projects (first 10)
        print(f"\nStarting hybrid download for first 10 projects...")
        results = downloader.process_test_projects(projects, test_count=10)
        
        # Save final results
        downloader.save_tracking_data()
        downloader.generate_summary_report()
        
        print(f"\n=== HYBRID TEST DOWNLOAD COMPLETE ===")
        print(f"Results saved to: hybrid_tracking_data.csv")
        print(f"Summary saved to: hybrid_download_summary.txt")
        print(f"Documents organized in: downloads/")
        
        # Show current downloads directory structure
        print(f"\nCurrent downloads directory structure:")
        for country_dir in downloader.downloads_dir.iterdir():
            if country_dir.is_dir():
                files = list(country_dir.glob("*"))
                print(f"  {country_dir.name}: {len(files)} files")
    
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Final Complete IDB Document Downloader
======================================
Final version that uses the working download method to ensure documents are actually downloaded
and properly organized for all 565 projects.
"""

import pandas as pd
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib.request
import ssl

class FinalCompleteDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Disable SSL verification for urllib
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Tracking data
        self.tracking_data = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
        # Session management
        self.session_timeout = 30  # Restart session every 30 projects
        self.current_session_count = 0
        
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
            
            # Set download preferences
            prefs = {
                "download.default_directory": str(self.downloads_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("✓ Chrome WebDriver setup successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup WebDriver: {e}")
            return False
    
    def restart_session(self):
        """Restart the browser session to prevent crashes."""
        try:
            if self.driver:
                self.driver.quit()
            time.sleep(2)
            
            # Visit main IDB site to establish fresh session
            if self.setup_driver():
                print("Establishing fresh browser session...")
                self.driver.get("https://www.iadb.org/en")
                time.sleep(3)
                self.current_session_count = 0
                return True
            return False
        except Exception as e:
            print(f"Error restarting session: {e}")
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
    
    def is_page_working(self, project_number):
        """Check if the page is working properly."""
        try:
            # Check if project number is in the page source
            if project_number not in self.driver.page_source:
                return False
            
            # Check if we have a proper page title (not error page)
            title = self.driver.title
            if "404" in title or "Not Found" in title or "Error" in title:
                return False
            
            # Check if we're still on the project page URL
            current_url = self.driver.current_url
            if project_number not in current_url:
                return False
            
            return True
            
        except Exception as e:
            print(f"    Error checking if page is working: {e}")
            return False
    
    def download_document_working(self, doc_url, project_number, country, doc_title):
        """Download document using the working method from previous successful runs."""
        try:
            print(f"      Downloading: {doc_title}")
            
            # Create filename
            safe_title = re.sub(r'[^\w\s-]', '', doc_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{project_number}_{safe_title}.pdf"
            
            # Create country directory
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Download using urllib (the working method)
            file_path = country_dir / filename
            urllib.request.urlretrieve(doc_url, file_path)
            
            print(f"      ✓ Downloaded: {filename}")
            print(f"      ✓ Saved to: {country}/")
            return True
            
        except Exception as e:
            print(f"      ✗ Download failed: {e}")
            return False
    
    def download_project_documents(self, project):
        """Download documents for a single project."""
        project_number = project['Project Number']
        project_name = project['Project Name']
        country = project['Project Country']
        
        print(f"Processing project {project_number}: {project_name}")
        print(f"  Country: {country}")
        
        try:
            # Navigate to project page
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"  Navigating to: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded correctly using proper detection
            if not self.is_page_working(project_number):
                print(f"  ✗ Project page not loaded correctly")
                return {
                    'project_number': project_number,
                    'project_name': project_name,
                    'country': country,
                    'operation_number': project.get('Operation Number', ''),
                    'documents_found': 0,
                    'documents_downloaded': 0,
                    'status': 'Project Page Not Accessible',
                    'project_url': url
                }
            
            print(f"  ✓ Project page loaded successfully")
            
            # Look for Preparation Phase section
            print(f"  Looking for Preparation Phase section...")
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
            
            documents_found = len(document_cards)
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
                    
                    # Download the document using the working method
                    if self.download_document_working(doc_url, project_number, country, doc_title):
                        documents_downloaded += 1
                    
                except Exception as e:
                    print(f"    Error processing document card: {e}")
                    continue
            
            status = 'Documents Available' if documents_downloaded > 0 else 'Download Failed'
            
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': country,
                'operation_number': project.get('Operation Number', ''),
                'documents_found': documents_found,
                'documents_downloaded': documents_downloaded,
                'status': status,
                'project_url': url
            }
            
        except Exception as e:
            print(f"  ✗ Error processing project: {e}")
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': country,
                'operation_number': project.get('Operation Number', ''),
                'documents_found': 0,
                'documents_downloaded': 0,
                'status': f'Error: {str(e)}',
                'project_url': f"https://www.iadb.org/en/project/{project_number}"
            }
    
    def process_projects(self, projects, start_index=0, end_index=None):
        """Process projects with improved session management."""
        if end_index is None:
            end_index = len(projects)
        
        if not self.setup_driver():
            print("Failed to setup WebDriver. Exiting.")
            return []
        
        try:
            # First, visit the main IDB site to establish a session
            print("Establishing browser session...")
            self.driver.get("https://www.iadb.org/en")
            time.sleep(3)
            
            print(f"\nProcessing projects {start_index + 1} to {end_index} of {len(projects)}...")
            
            for i in range(start_index, end_index):
                project = projects[i]
                
                # Check if we need to restart session
                if self.current_session_count >= self.session_timeout:
                    print(f"\nRestarting session after {self.session_timeout} projects...")
                    if not self.restart_session():
                        print("Failed to restart session. Continuing with current session...")
                
                # Download documents for this project
                result = self.download_project_documents(project)
                self.tracking_data.append(result)
                self.processed_count += 1
                self.current_session_count += 1
                
                # Update counters
                if result['documents_downloaded'] > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 10 projects
                if (i + 1) % 10 == 0:
                    self.save_tracking_data()
                    print(f"\nProgress saved: {i + 1} projects processed")
                    print(f"Current session count: {self.current_session_count}")
                    print(f"Successful downloads: {self.success_count}")
                    print(f"Failed downloads: {self.error_count}")
                
                # Be respectful with delays
                time.sleep(2)
            
            return self.tracking_data
            
        except Exception as e:
            print(f"Error during project processing: {e}")
            return self.tracking_data
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_tracking_data(self):
        """Save tracking data to CSV."""
        df = pd.DataFrame(self.tracking_data)
        df.to_csv("final_complete_tracking_data.csv", index=False)
        print(f"Tracking data saved to final_complete_tracking_data.csv")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("FINAL COMPLETE IDB DOWNLOAD ANALYSIS SUMMARY")
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
        
        # Show country breakdown
        print(f"\nCountry Breakdown:")
        country_stats = df.groupby('country').agg({
            'documents_found': 'sum',
            'documents_downloaded': 'sum',
            'project_number': 'count'
        }).rename(columns={'project_number': 'projects'})
        
        for country, stats in country_stats.iterrows():
            print(f"  {country}: {stats['projects']} projects, {stats['documents_found']} found, {stats['documents_downloaded']} downloaded")
        
        # Save summary to file
        with open("final_complete_download_summary.txt", "w") as f:
            f.write("FINAL COMPLETE IDB DOWNLOAD ANALYSIS SUMMARY\n")
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
            
            f.write("\nCountry Breakdown:\n")
            for country, stats in country_stats.iterrows():
                f.write(f"  {country}: {stats['projects']} projects, {stats['documents_found']} found, {stats['documents_downloaded']} downloaded\n")
        
        print(f"\nSummary report saved to final_complete_download_summary.txt")
        
        # Show downloads directory structure
        print(f"\nDownloads Directory Structure:")
        for country_dir in self.downloads_dir.iterdir():
            if country_dir.is_dir():
                files = list(country_dir.glob("*"))
                print(f"  {country_dir.name}: {len(files)} files")

def main():
    downloader = FinalCompleteDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    if not projects:
        print("Failed to load project data. Exiting.")
        return
    
    # Process all projects
    print(f"\nStarting complete download for all {len(projects)} projects...")
    results = downloader.process_projects(projects)
    
    # Save final results
    downloader.save_tracking_data()
    downloader.generate_summary_report()
    
    print(f"\n=== FINAL COMPLETE DOWNLOAD COMPLETE ===")
    print(f"Results saved to: final_complete_tracking_data.csv")
    print(f"Summary saved to: final_complete_download_summary.txt")
    print(f"Documents organized in: downloads/")
    print(f"\nThe CSV file 'final_complete_tracking_data.csv' contains:")
    print(f"- All 565 projects")
    print(f"- Document counts found and downloaded for each project")
    print(f"- Status of each project")
    print(f"- Project URLs for verification")

if __name__ == "__main__":
    main()

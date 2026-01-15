#!/usr/bin/env python3
"""
Fixed Working IDB Document Downloader
====================================
Fixed version that properly detects working pages and downloads documents correctly.
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

class FixedWorkingDownloader:
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
                    
                    print(f"      Found document URL: {doc_url}")
                    
                    # Click the document card to trigger download
                    try:
                        self.driver.execute_script("arguments[0].click();", card)
                        print(f"      ✓ Clicked document card via JavaScript")
                        time.sleep(2)  # Wait for download to start
                        documents_downloaded += 1
                    except Exception as e:
                        print(f"      ✗ Failed to click document card: {e}")
                    
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
    
    def organize_downloaded_files(self):
        """Organize downloaded files into country directories."""
        try:
            print("\nOrganizing downloaded files...")
            
            # Get all document files in the downloads directory (PDF, DOCX, etc.)
            document_extensions = ['*.pdf', '*.docx', '*.doc', '*.xlsx', '*.xls', 
                                 '*.PDF', '*.DOCX', '*.DOC', '*.XLSX', '*.XLS']
            all_files = []
            for ext in document_extensions:
                all_files.extend(list(self.downloads_dir.glob(ext)))
            
            print(f"Found {len(all_files)} document files to organize...")
            
            moved_count = 0
            skipped_count = 0
            error_count = 0
            
            for file_path in all_files:
                filename = file_path.name
                print(f"Processing: {filename}")
                
                # Try multiple patterns to extract project number or operation number
                project_number = None
                operation_number = None
                
                # Pattern 1: Standard project format (PE-L1187, CO-M1089, etc.)
                project_match = re.search(r'([A-Z]{2}-[A-Z]\d+)', filename)
                if project_match:
                    project_number = project_match.group(1)
                
                # Pattern 2: Operation number format (ATN_ME-14908-PR, ATN_ME-13560-CO, etc.)
                operation_match = re.search(r'(ATN_[A-Z]+-\d+-[A-Z]+)', filename)
                if operation_match:
                    operation_number = operation_match.group(1)
                
                # Pattern 3: Look for project numbers in the filename with different formats
                if not project_number:
                    patterns = [
                        r'([A-Z]{2}-[A-Z]\d+)',  # PE-L1187, CO-M1089
                        r'([A-Z]{2}-[A-Z]\d{4})',  # PE-L1187, CO-M1089
                        r'([A-Z]{2}-[A-Z]\d{3})',  # PE-L1187, CO-M1089
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, filename)
                        if match:
                            project_number = match.group(1)
                            break
                
                # Pattern 4: Look for project numbers in the filename without hyphens
                if not project_number:
                    match = re.search(r'([A-Z]{2}[A-Z]\d+)', filename)
                    if match:
                        raw_number = match.group(1)
                        if len(raw_number) >= 6:
                            project_number = f"{raw_number[:2]}-{raw_number[2:]}"
                
                if project_number:
                    print(f"  Extracted project number: {project_number}")
                    
                    # Find the project in our tracking data to get country
                    country = None
                    for project_data in self.tracking_data:
                        if project_data['project_number'] == project_number:
                            country = project_data['country']
                            break
                    
                    if country:
                        # Create country directory
                        country_dir = self.downloads_dir / country
                        country_dir.mkdir(exist_ok=True)
                        
                        # Move file to country directory
                        new_path = country_dir / filename
                        if not new_path.exists():
                            file_path.rename(new_path)
                            print(f"  ✓ Moved {filename} to {country}/")
                            moved_count += 1
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                            skipped_count += 1
                    else:
                        print(f"  ❌ Could not determine country for {filename} (project: {project_number})")
                        error_count += 1
                
                elif operation_number:
                    print(f"  Extracted operation number: {operation_number}")
                    
                    # Find the project in our tracking data to get country
                    country = None
                    for project_data in self.tracking_data:
                        # Convert operation number format for comparison
                        # ATN_ME-14908-PR -> ATN/ME-14908-PR
                        normalized_op = operation_number.replace('_', '/')
                        if project_data['operation_number'] == normalized_op:
                            country = project_data['country']
                            break
                    
                    if country:
                        # Create country directory
                        country_dir = self.downloads_dir / country
                        country_dir.mkdir(exist_ok=True)
                        
                        # Move file to country directory
                        new_path = country_dir / filename
                        if not new_path.exists():
                            file_path.rename(new_path)
                            print(f"  ✓ Moved {filename} to {country}/")
                            moved_count += 1
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                            skipped_count += 1
                    else:
                        print(f"  ❌ Could not determine country for {filename} (operation: {operation_number})")
                        error_count += 1
                else:
                    print(f"  ❌ Could not extract project or operation number from {filename}")
                    error_count += 1
            
            print(f"\nOrganization Summary:")
            print(f"  ✓ Files moved: {moved_count}")
            print(f"  ⚠ Files skipped (already exists): {skipped_count}")
            print(f"  ❌ Files with errors: {error_count}")
                    
        except Exception as e:
            print(f"Error organizing files: {e}")
            import traceback
            traceback.print_exc()
    
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
        df.to_csv("fixed_working_tracking_data.csv", index=False)
        print(f"Tracking data saved to fixed_working_tracking_data.csv")
    
    def generate_summary_report(self):
        """Generate a summary report of findings."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("FIXED WORKING IDB DOWNLOAD ANALYSIS SUMMARY")
        print("="*80)
        
        total_projects = len(df)
        projects_with_documents = len(df[df['documents_downloaded'] > 0])
        total_documents_found = df['documents_found'].sum()
        total_documents_downloaded = df['documents_downloaded'].sum()
        
        print(f"Total Projects Processed: {total_projects}")
        print(f"Projects with Documents: {projects_with_documents}")
        print(f"Total Documents Found: {total_documents_found}")
        print(f"Total Documents Downloaded: {total_documents_downloaded}")
        print(f"Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%" if total_documents_found > 0 else "Success Rate: N/A")
        
        print(f"\nStatus Summary:")
        status_counts = df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Save summary to file
        with open("fixed_working_download_summary.txt", "w") as f:
            f.write("FIXED WORKING IDB DOWNLOAD ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Projects Processed: {total_projects}\n")
            f.write(f"Projects with Documents: {projects_with_documents}\n")
            f.write(f"Total Documents Found: {total_documents_found}\n")
            f.write(f"Total Documents Downloaded: {total_documents_downloaded}\n")
            f.write(f"Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%\n\n" if total_documents_found > 0 else "Success Rate: N/A\n\n")
            
            f.write("Status Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count}\n")
        
        print(f"\nSummary report saved to fixed_working_download_summary.txt")

def main():
    downloader = FixedWorkingDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    # Test with first 10 projects
    print("\nTesting with first 10 projects...")
    test_results = downloader.process_projects(projects, 0, 10)
    
    if test_results:
        downloader.organize_downloaded_files()
        downloader.save_tracking_data()
        downloader.generate_summary_report()
        
        # Ask user if they want to continue with all projects
        response = input("\nDo you want to continue with all projects? (y/n): ")
        if response.lower() == 'y':
            print("\nProcessing all projects...")
            all_results = downloader.process_projects(projects)
            downloader.organize_downloaded_files()
            downloader.save_tracking_data()
            downloader.generate_summary_report()
            
            print(f"\n=== FIXED WORKING DOWNLOAD COMPLETE ===")
            print(f"Results saved to: fixed_working_tracking_data.csv")
            print(f"Summary saved to: fixed_working_download_summary.txt")
            print(f"Documents organized in: downloads/")
        else:
            print("Processing stopped after test run.")
    else:
        print("No results obtained from test run.")

if __name__ == "__main__":
    main()

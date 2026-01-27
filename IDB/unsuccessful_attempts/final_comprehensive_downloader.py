#!/usr/bin/env python3
"""
Final Comprehensive Downloader
This script processes all IDB projects and downloads their TC Abstract documents using browser automation.
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

class FinalComprehensiveDownloader:
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
        self.tracking_data = []
        
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
    
    def load_project_data(self, csv_file):
        """Load and process the IDB project CSV data."""
        print(f"Loading project data from {csv_file}...")
        
        # Read the CSV file, skipping the first row (methodology) and using row 1 as headers
        df = pd.read_csv(csv_file, skiprows=1)
        
        # Extract relevant columns
        projects = []
        for _, row in df.iterrows():
            # Skip rows that don't have project numbers
            if pd.isna(row['Project Number']) or row['Project Number'] == '':
                continue
                
            project = {
                'project_number': row['Project Number'],
                'project_name': row['Project Name'] if pd.notna(row['Project Name']) else '',
                'country': row['Project Country'] if pd.notna(row['Project Country']) else '',
                'approval_date': row['Approval Date'] if pd.notna(row['Approval Date']) else '',
                'status': row['Status'] if pd.notna(row['Status']) else '',
                'lending_type': row['Lending Type'] if pd.notna(row['Lending Type']) else '',
                'project_type': row['Project Type'] if pd.notna(row['Project Type']) else '',
                'sector': row['Sector'] if pd.notna(row['Sector']) else '',
                'sub_sector': row['Sub-Sector'] if pd.notna(row['Sub-Sector']) else '',
                'total_cost': row['Total Cost'] if pd.notna(row['Total Cost']) else 0,
                'operation_number': row['Operation Number'] if pd.notna(row['Operation Number']) else ''
            }
            projects.append(project)
        
        print(f"Loaded {len(projects)} projects")
        return projects
    
    def download_project_documents(self, project):
        """Download documents for a single project."""
        project_number = project['project_number']
        project_name = project['project_name']
        
        print(f"\nProcessing project {project_number}: {project_name}")
        
        try:
            # Navigate to the project page
            project_url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"  Navigating to: {project_url}")
            
            self.driver.get(project_url)
            time.sleep(3)  # Wait for page to load
            
            # Check if page loaded successfully
            if project_name in self.driver.page_source:
                print(f"  ✓ Project page loaded successfully")
            else:
                print(f"  ✗ Project page not loaded correctly")
                return {
                    'project_number': project_number,
                    'project_name': project_name,
                    'country': project['country'],
                    'operation_number': project['operation_number'],
                    'documents_found': 0,
                    'documents_downloaded': 0,
                    'status': 'Project Page Not Accessible',
                    'project_url': project_url
                }
            
            # Scroll down to find the Preparation Phase section
            print(f"  Looking for Preparation Phase section...")
            self.scroll_to_preparation_phase()
            
            # Look for document cards
            document_cards = self.driver.find_elements(By.TAG_NAME, "idb-document-card")
            
            if document_cards:
                print(f"  Found {len(document_cards)} document cards")
                
                # Count documents found
                documents_found = len(document_cards)
                documents_downloaded = 0
                
                # Try to download each document
                for i, card in enumerate(document_cards):
                    try:
                        print(f"    Processing document {i+1}/{len(document_cards)}")
                        
                        # Get the URL attribute
                        url = card.get_attribute("url")
                        if url and "EZSHARE" in url:
                            print(f"    Found document URL: {url}")
                            
                            # Try to click the card to trigger download
                            if self.click_document_card(card):
                                documents_downloaded += 1
                                time.sleep(2)  # Wait between downloads
                            
                    except Exception as e:
                        print(f"    Error processing document {i+1}: {e}")
                        continue
                
                return {
                    'project_number': project_number,
                    'project_name': project_name,
                    'country': project['country'],
                    'operation_number': project['operation_number'],
                    'documents_found': documents_found,
                    'documents_downloaded': documents_downloaded,
                    'status': 'Documents Available' if documents_found > 0 else 'No Documents Found',
                    'project_url': project_url
                }
            else:
                print(f"  ✗ No document cards found")
                return {
                    'project_number': project_number,
                    'project_name': project_name,
                    'country': project['country'],
                    'operation_number': project['operation_number'],
                    'documents_found': 0,
                    'documents_downloaded': 0,
                    'status': 'No Documents Found',
                    'project_url': project_url
                }
                
        except Exception as e:
            print(f"  ✗ Error processing project: {e}")
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': project['country'],
                'operation_number': project['operation_number'],
                'documents_found': 0,
                'documents_downloaded': 0,
                'status': f'Error: {str(e)[:50]}',
                'project_url': project_url
            }
    
    def scroll_to_preparation_phase(self):
        """Scroll down to find the Preparation Phase section."""
        try:
            # Scroll down to find "Preparation Phase"
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for "Preparation Phase" text
            preparation_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Preparation Phase')]")
            
            if preparation_elements:
                print(f"    ✓ Found Preparation Phase section")
                # Scroll to the first occurrence
                self.driver.execute_script("arguments[0].scrollIntoView();", preparation_elements[0])
                time.sleep(2)
            else:
                print(f"    ✗ Preparation Phase section not found")
                
        except Exception as e:
            print(f"    Error scrolling to Preparation Phase: {e}")
    
    def click_document_card(self, card):
        """Click on document card to trigger download."""
        try:
            # Scroll to the card
            self.driver.execute_script("arguments[0].scrollIntoView();", card)
            time.sleep(1)
            
            # Try different click methods
            try:
                # Method 1: Direct click
                card.click()
                print(f"      ✓ Clicked document card directly")
                return True
            except:
                try:
                    # Method 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", card)
                    print(f"      ✓ Clicked document card via JavaScript")
                    return True
                except:
                    try:
                        # Method 3: Action chains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(card).click().perform()
                        print(f"      ✓ Clicked document card via ActionChains")
                        return True
                    except Exception as e:
                        print(f"      ✗ All click methods failed: {e}")
                        return False
                        
        except Exception as e:
            print(f"      ✗ Error clicking document card: {e}")
            return False
    
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
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                    else:
                        print(f"  ❌ Could not determine country for {filename} (project: {project_number})")
                
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
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                    else:
                        print(f"  ❌ Could not determine country for {filename} (operation: {operation_number})")
                else:
                    print(f"  ❌ Could not extract project or operation number from {filename}")
                    
        except Exception as e:
            print(f"Error organizing files: {e}")
            import traceback
            traceback.print_exc()
    
    def process_projects(self, projects, start_index=0, end_index=None):
        """Process projects and download available documents."""
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
                print(f"\nProcessing project {i+1}/{len(projects)}: {project['project_number']}")
                
                # Download documents for this project
                result = self.download_project_documents(project)
                self.tracking_data.append(result)
                
                # Save progress every 10 projects
                if (i + 1) % 10 == 0:
                    self.save_tracking_data()
                    print(f"\nProgress saved: {i + 1} projects processed")
                
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
        df.to_csv("final_comprehensive_tracking.csv", index=False)
        print(f"Tracking data saved to final_comprehensive_tracking.csv")
    
    def generate_summary_report(self):
        """Generate a summary report of findings."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("FINAL COMPREHENSIVE DOWNLOAD ANALYSIS SUMMARY")
        print("="*80)
        
        total_projects = len(df)
        projects_with_documents = len(df[df['documents_found'] > 0])
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
        with open("final_download_summary.txt", "w") as f:
            f.write("FINAL COMPREHENSIVE DOWNLOAD ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Projects Processed: {total_projects}\n")
            f.write(f"Projects with Documents: {projects_with_documents}\n")
            f.write(f"Total Documents Found: {total_documents_found}\n")
            f.write(f"Total Documents Downloaded: {total_documents_downloaded}\n")
            f.write(f"Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%\n\n" if total_documents_found > 0 else "Success Rate: N/A\n\n")
            
            f.write("Status Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count}\n")
        
        print(f"\nSummary report saved to final_download_summary.txt")

def main():
    downloader = FinalComprehensiveDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    # Test with first 5 projects
    print("\nTesting with first 5 projects...")
    test_results = downloader.process_projects(projects, 0, 5)
    
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
            
            print(f"\n=== DOWNLOAD COMPLETE ===")
            print(f"Results saved to: final_comprehensive_tracking.csv")
            print(f"Summary saved to: final_download_summary.txt")
            print(f"Documents organized in: downloads/")
        else:
            print("Processing stopped after test run.")
    else:
        print("No results obtained from test run.")

if __name__ == "__main__":
    main()

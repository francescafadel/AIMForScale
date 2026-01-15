#!/usr/bin/env python3
"""
Simple Document Downloader
==========================
Downloads documents using direct HTTP requests without Selenium.
"""

import pandas as pd
import requests
import time
import re
from pathlib import Path
import urllib.request
import ssl

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

class SimpleDownloader:
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
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def load_tracking_data(self):
        """Load existing tracking data to see what documents were found."""
        try:
            df = pd.read_csv("final_complete_tracking_data.csv")
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            return []
    
    def download_sample_documents(self):
        """Download sample documents for testing."""
        print("Downloading sample documents for testing...")
        
        # Sample document URLs (these would normally come from the project pages)
        sample_docs = [
            {
                'project': 'PE-L1187',
                'country': 'Peru',
                'title': 'TC_Abstract_English',
                'url': 'https://www.iadb.org/en/project/PE-L1187'
            },
            {
                'project': 'CO-M1089',
                'country': 'Colombia', 
                'title': 'Abstract_Document',
                'url': 'https://www.iadb.org/en/project/CO-M1089'
            }
        ]
        
        for doc in sample_docs:
            print(f"Processing {doc['project']} - {doc['title']}")
            
            # Create filename
            filename = f"{doc['project']}_{doc['title']}.pdf"
            
            # Create country directory
            country_dir = self.downloads_dir / doc['country']
            country_dir.mkdir(exist_ok=True)
            
            # Try to download from project page
            try:
                response = self.session.get(doc['url'], timeout=30)
                if response.status_code == 200:
                    # Look for document links in the HTML
                    import re
                    doc_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', response.text)
                    
                    if doc_links:
                        for i, link in enumerate(doc_links[:3]):  # Limit to 3 documents
                            if not link.startswith('http'):
                                link = 'https://www.iadb.org' + link
                            
                            try:
                                doc_response = self.session.get(link, timeout=60, stream=True)
                                if doc_response.status_code == 200:
                                    doc_filename = f"{doc['project']}_document_{i+1}.pdf"
                                    file_path = country_dir / doc_filename
                                    
                                    with open(file_path, 'wb') as f:
                                        for chunk in doc_response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    print(f"  ✓ Downloaded: {doc_filename}")
                                    self.success_count += 1
                                else:
                                    print(f"  ✗ Failed to download: HTTP {doc_response.status_code}")
                                    self.error_count += 1
                            except Exception as e:
                                print(f"  ✗ Download error: {e}")
                                self.error_count += 1
                    else:
                        print(f"  ✗ No document links found")
                        self.error_count += 1
                else:
                    print(f"  ✗ Failed to access project page: HTTP {response.status_code}")
                    self.error_count += 1
            except Exception as e:
                print(f"  ✗ Error accessing project page: {e}")
                self.error_count += 1
            
            self.processed_count += 1
            time.sleep(2)  # Be respectful
    
    def process_top_projects(self, tracking_data, top_n=20):
        """Process top projects with most documents."""
        print(f"Processing top {top_n} projects with most documents...")
        
        # Sort by documents found
        projects_with_docs = [p for p in tracking_data if p['documents_found'] > 0]
        projects_with_docs.sort(key=lambda x: x['documents_found'], reverse=True)
        
        top_projects = projects_with_docs[:top_n]
        print(f"Top projects by document count:")
        
        for i, project in enumerate(top_projects):
            print(f"  {i+1}. {project['project_number']} ({project['country']}): {project['documents_found']} documents")
        
        # Process each project
        for i, project in enumerate(top_projects):
            print(f"\nProcessing {i+1}/{len(top_projects)}: {project['project_number']}")
            print(f"  Country: {project['country']}")
            print(f"  Documents found: {project['documents_found']}")
            
            # Try to access project page and find documents
            project_url = f"https://www.iadb.org/en/project/{project['project_number']}"
            
            try:
                response = self.session.get(project_url, timeout=30)
                if response.status_code == 200:
                    print(f"  ✓ Project page accessible")
                    
                    # Look for document links
                    import re
                    doc_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', response.text)
                    
                    if doc_links:
                        print(f"  Found {len(doc_links)} potential document links")
                        
                        # Download first few documents
                        for j, link in enumerate(doc_links[:min(3, len(doc_links))]):
                            if not link.startswith('http'):
                                link = 'https://www.iadb.org' + link
                            
                            try:
                                doc_response = self.session.get(link, timeout=60, stream=True)
                                if doc_response.status_code == 200:
                                    # Create filename
                                    filename = f"{project['project_number']}_document_{j+1}.pdf"
                                    
                                    # Create country directory
                                    country_dir = self.downloads_dir / project['country']
                                    country_dir.mkdir(exist_ok=True)
                                    
                                    file_path = country_dir / filename
                                    with open(file_path, 'wb') as f:
                                        for chunk in doc_response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    print(f"    ✓ Downloaded: {filename}")
                                    self.success_count += 1
                                else:
                                    print(f"    ✗ Failed to download: HTTP {doc_response.status_code}")
                                    self.error_count += 1
                            except Exception as e:
                                print(f"    ✗ Download error: {e}")
                                self.error_count += 1
                    else:
                        print(f"  ✗ No document links found")
                        self.error_count += 1
                else:
                    print(f"  ✗ Failed to access project page: HTTP {response.status_code}")
                    self.error_count += 1
            except Exception as e:
                print(f"  ✗ Error accessing project page: {e}")
                self.error_count += 1
            
            self.processed_count += 1
            time.sleep(2)  # Be respectful
    
    def generate_summary_report(self):
        """Generate a summary report."""
        print("\n" + "="*80)
        print("SIMPLE DOWNLOADER SUMMARY")
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
    downloader = SimpleDownloader()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process top 20 projects with most documents
    downloader.process_top_projects(tracking_data, top_n=20)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== SIMPLE DOWNLOADER COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()

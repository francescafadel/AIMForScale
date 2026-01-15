#!/usr/bin/env python3
"""
Simple Working Downloader
=========================
Downloads documents by extracting URLs from page source without Selenium.
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

class SimpleWorkingDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.session.verify = False
        
        # Tracking data
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def load_tracking_data(self):
        """Load existing tracking data."""
        try:
            df = pd.read_csv("final_complete_tracking_data.csv")
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            return []
    
    def extract_and_download_documents(self, project):
        """Extract document URLs from page source and download them."""
        project_number = project['project_number']
        country = project['country']
        
        print(f"\nProcessing project {project_number}: {project['project_name']}")
        print(f"  Country: {country}")
        
        try:
            # Get project page
            url = f"https://www.iadb.org/en/project/{project_number}"
            print(f"  Fetching: {url}")
            
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                print(f"  ✗ Failed to fetch page: HTTP {response.status_code}")
                return 0
            
            print(f"  ✓ Page fetched successfully")
            
            # Extract document URLs from page source
            page_source = response.text
            
            # Look for EZSHARE URLs in the page source
            ezshare_urls = re.findall(r'https://www\.iadb\.org/document\.cfm\?id=EZSHARE-[^"\s]+', page_source)
            
            if not ezshare_urls:
                print(f"  ✗ No EZSHARE URLs found")
                return 0
            
            print(f"  Found {len(ezshare_urls)} EZSHARE URLs")
            
            # Remove duplicates
            unique_urls = list(set(ezshare_urls))
            print(f"  Unique URLs: {len(unique_urls)}")
            
            documents_downloaded = 0
            
            for i, doc_url in enumerate(unique_urls):
                try:
                    print(f"    Downloading document {i+1}/{len(unique_urls)}")
                    print(f"      URL: {doc_url}")
                    
                    # Extract document ID from URL
                    doc_id = doc_url.split('id=')[1]
                    
                    # Create filename
                    filename = f"{project_number}_Document_{doc_id}.pdf"
                    
                    # Create country directory
                    country_dir = self.downloads_dir / country
                    country_dir.mkdir(exist_ok=True)
                    
                    # Download the document
                    if self.download_document(doc_url, country_dir, filename):
                        documents_downloaded += 1
                    
                except Exception as e:
                    print(f"    Error downloading document: {e}")
                    continue
            
            return documents_downloaded
            
        except Exception as e:
            print(f"  ✗ Error processing project: {e}")
            return 0
    
    def download_document(self, doc_url, country_dir, filename):
        """Download document using curl."""
        try:
            file_path = country_dir / filename
            
            # Use curl for reliable download
            import subprocess
            result = subprocess.run([
                'curl', '-L', '-o', str(file_path), 
                '--connect-timeout', '30',
                '--max-time', '300',
                doc_url
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and file_path.exists() and file_path.stat().st_size > 0:
                print(f"      ✓ Downloaded: {filename}")
                print(f"      ✓ Saved to: {country_dir.name}/")
                return True
            else:
                print(f"      ✗ Download failed: {result.stderr}")
                if file_path.exists():
                    file_path.unlink()
                return False
                
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
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
            time.sleep(2)
    
    def generate_summary_report(self):
        """Generate a summary report."""
        print("\n" + "="*80)
        print("SIMPLE WORKING DOWNLOADER SUMMARY")
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
    downloader = SimpleWorkingDownloader()
    
    # Load existing tracking data
    tracking_data = downloader.load_tracking_data()
    
    if not tracking_data:
        print("No tracking data found. Exiting.")
        return
    
    # Process top 20 projects with most documents
    downloader.process_top_projects(tracking_data, top_n=20)
    
    # Generate summary
    downloader.generate_summary_report()
    
    print(f"\n=== SIMPLE WORKING DOWNLOADER COMPLETE ===")
    print(f"Check the downloads/ folder for organized documents")

if __name__ == "__main__":
    main()

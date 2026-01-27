#!/usr/bin/env python3
"""
Working Document Downloader
This script successfully downloads TC Abstract documents from IDB projects.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WorkingDocumentDownloader:
    def __init__(self):
        self.base_url = "https://www.iadb.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Disable SSL verification
        self.session.verify = False
        
        # Create downloads directory
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
    def get_pe_l1187_data(self):
        """Get PE-L1187 project data from the CSV."""
        print("Loading PE-L1187 project data...")
        
        # Read the CSV file
        df = pd.read_csv("IDB Corpus Key Words.csv", skiprows=1)
        
        # Find PE-L1187
        pe_l1187_row = df[df['Project Number'] == 'PE-L1187']
        
        if pe_l1187_row.empty:
            print("PE-L1187 not found in CSV!")
            return None
        
        project = {
            'project_number': 'PE-L1187',
            'project_name': pe_l1187_row.iloc[0]['Project Name'],
            'country': pe_l1187_row.iloc[0]['Project Country'],
            'operation_number': pe_l1187_row.iloc[0]['Operation Number'],
            'approval_date': pe_l1187_row.iloc[0]['Approval Date'],
            'status': pe_l1187_row.iloc[0]['Status'],
            'project_type': pe_l1187_row.iloc[0]['Project Type'],
            'total_cost': pe_l1187_row.iloc[0]['Total Cost']
        }
        
        print(f"Found PE-L1187: {project['project_name']}")
        print(f"Country: {project['country']}")
        print(f"Operation: {project['operation_number']}")
        print(f"Type: {project['project_type']}")
        print(f"Cost: ${project['total_cost']:,.0f}")
        
        return project
    
    def download_tc_abstract_documents(self, project):
        """Download TC Abstract documents for PE-L1187."""
        print(f"\nDownloading TC Abstract documents for {project['project_number']}...")
        
        # Known document URLs from the web search results
        documents = [
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-4',
                'language': 'Spanish',
                'title': 'PERU Síntesis proyecto PES PE-L1187.pdf',
                'filename': 'PERU_Sintesis_proyecto_PES_PE-L1187.pdf'
            },
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-5',
                'language': 'English',
                'title': 'PERU - Project Syntheis SEP PE-L1187.pdf',
                'filename': 'PERU_Project_Synthesis_SEP_PE-L1187.pdf'
            }
        ]
        
        downloaded_count = 0
        
        for doc in documents:
            print(f"\nDownloading {doc['language']} version...")
            print(f"URL: {doc['url']}")
            
            try:
                # First, get the document page to handle any redirects
                print(f"  Accessing document page...")
                response = self.session.get(doc['url'], timeout=30, allow_redirects=True)
                
                print(f"  Response status: {response.status_code}")
                print(f"  Final URL: {response.url}")
                
                if response.status_code == 200:
                    # Check if we got a PDF or HTML page
                    content_type = response.headers.get('content-type', '')
                    print(f"  Content-Type: {content_type}")
                    
                    if 'application/pdf' in content_type.lower():
                        # Direct PDF download
                        print(f"  ✓ Direct PDF download")
                        success = self.save_document(response.content, doc, project)
                        if success:
                            downloaded_count += 1
                    else:
                        # HTML page - look for download link
                        print(f"  HTML page received, looking for download link...")
                        success = self.extract_download_from_html(response.text, doc, project)
                        if success:
                            downloaded_count += 1
                else:
                    print(f"  ✗ Failed to access document: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ Error downloading {doc['language']} version: {e}")
        
        return downloaded_count
    
    def extract_download_from_html(self, html_content, doc, project):
        """Extract download link from HTML page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for download links
            download_links = soup.find_all('a', href=True)
            
            for link in download_links:
                link_href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()
                
                # Look for download indicators
                if any(keyword in link_text for keyword in ['download', 'descargar', 'pdf']):
                    print(f"    Found download link: {link_href}")
                    
                    # Make URL absolute
                    if link_href.startswith('/'):
                        download_url = urljoin(self.base_url, link_href)
                    elif link_href.startswith('http'):
                        download_url = link_href
                    else:
                        download_url = urljoin(doc['url'], link_href)
                    
                    # Try to download from this link
                    response = self.session.get(download_url, timeout=30, stream=True)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type.lower():
                            print(f"    ✓ PDF found at download link")
                            return self.save_document(response.content, doc, project)
            
            print(f"    ✗ No download link found in HTML")
            return False
            
        except Exception as e:
            print(f"    ✗ Error extracting download link: {e}")
            return False
    
    def save_document(self, content, doc, project):
        """Save document content to file."""
        try:
            # Create country directory
            country = project['country']
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Create filename
            project_number = project['project_number']
            language = doc['language']
            filename = f"{project_number}_TC_Abstract_{language}_{doc['filename']}"
            
            # Ensure filename is valid
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            filepath = country_dir / filename
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(content)
            
            print(f"    ✓ Saved: {filename}")
            print(f"    File size: {filepath.stat().st_size:,} bytes")
            return True
            
        except Exception as e:
            print(f"    ✗ Error saving file: {e}")
            return False
    
    def test_pe_l1187(self):
        """Test downloading documents for PE-L1187."""
        print("=" * 80)
        print("WORKING DOCUMENT DOWNLOADER TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Download TC Abstract documents
        downloaded_count = self.download_tc_abstract_documents(project)
        
        print(f"\nDownload Summary:")
        print(f"  Documents attempted: 2")
        print(f"  Successfully downloaded: {downloaded_count}")
        print(f"  Failed downloads: {2 - downloaded_count}")
        
        if downloaded_count > 0:
            print(f"\n✓ SUCCESS: Downloaded {downloaded_count} documents for PE-L1187!")
            print(f"Files saved in: {self.downloads_dir}/{project['country']}")
        else:
            print(f"\n✗ No documents were successfully downloaded.")
            print("The documents may require authentication or have access restrictions.")

def main():
    downloader = WorkingDocumentDownloader()
    downloader.test_pe_l1187()

if __name__ == "__main__":
    main()

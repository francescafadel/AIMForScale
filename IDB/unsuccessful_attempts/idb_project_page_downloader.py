#!/usr/bin/env python3
"""
IDB Project Page Document Downloader
This script replicates the exact process used by the user to download documents:
1. Search for project number on IDB website
2. Navigate to project page
3. Find Preparation Phase section
4. Download TC Abstract documents
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup

class IDBProjectPageDownloader:
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
        
        # Create downloads directory structure
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Tracking file
        self.tracking_file = "project_page_download_tracking.csv"
        
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
    
    def search_project_on_idb(self, project):
        """Search for project on IDB website using project number."""
        project_number = project['project_number']
        project_name = project['project_name']
        
        print(f"\nSearching for project: {project_number}")
        print(f"Project name: {project_name}")
        
        # Step 1: Search for project number on IDB website
        search_url = f"{self.base_url}/en/search?q={quote(project_number)}"
        
        try:
            print(f"  Searching: {search_url}")
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                print(f"  ✓ Search page loaded successfully")
                
                # Step 2: Look for project page link in search results
                project_page_url = self.find_project_page_link(response.text, project)
                
                if project_page_url:
                    print(f"  ✓ Found project page: {project_page_url}")
                    
                    # Step 3: Navigate to project page
                    documents = self.navigate_to_project_page(project_page_url, project)
                    return documents
                else:
                    print(f"  ✗ Project page link not found in search results")
                    return []
            else:
                print(f"  ✗ Search failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  ✗ Error searching for project: {e}")
            return []
    
    def find_project_page_link(self, html_content, project):
        """Find the project page link in search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for links that contain the project number or project name
        project_number = project['project_number']
        project_name = project['project_name']
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
            # Check if link contains project number or project name
            if (project_number in link_text or 
                project_number in link_href or
                any(word in link_text.lower() for word in project_name.lower().split()[:3])):
                
                # Make URL absolute
                if link_href.startswith('/'):
                    return urljoin(self.base_url, link_href)
                elif link_href.startswith('http'):
                    return link_href
                else:
                    return urljoin(self.base_url, link_href)
        
        return None
    
    def navigate_to_project_page(self, project_page_url, project):
        """Navigate to project page and find documents."""
        try:
            print(f"  Navigating to project page...")
            response = self.session.get(project_page_url, timeout=15)
            
            if response.status_code == 200:
                print(f"  ✓ Project page loaded successfully")
                
                # Look for "Preparation Phase" section
                documents = self.find_preparation_phase_documents(response.text, project_page_url, project)
                return documents
            else:
                print(f"  ✗ Failed to load project page: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  ✗ Error navigating to project page: {e}")
            return []
    
    def find_preparation_phase_documents(self, html_content, base_url, project):
        """Find documents in the Preparation Phase section."""
        documents = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for "Preparation Phase" section
        preparation_section = None
        
        # Try different ways to find the Preparation Phase section
        preparation_selectors = [
            'h2:contains("Preparation Phase")',
            'h3:contains("Preparation Phase")',
            'div:contains("Preparation Phase")',
            '[class*="preparation"]',
            '[id*="preparation"]'
        ]
        
        # Look for text containing "Preparation Phase"
        for element in soup.find_all(text=re.compile(r'Preparation Phase', re.IGNORECASE)):
            preparation_section = element.parent
            break
        
        if not preparation_section:
            # Look for any element containing "Preparation Phase"
            for element in soup.find_all():
                if element.get_text() and 'preparation phase' in element.get_text().lower():
                    preparation_section = element
                    break
        
        if preparation_section:
            print(f"  ✓ Found Preparation Phase section")
            
            # Look for TC Abstract documents in this section
            documents = self.extract_tc_abstract_documents(preparation_section, base_url, project)
        else:
            print(f"  ✗ Preparation Phase section not found")
            
            # Fallback: look for any TC Abstract documents on the page
            documents = self.extract_tc_abstract_documents(soup, base_url, project)
        
        return documents
    
    def extract_tc_abstract_documents(self, section, base_url, project):
        """Extract TC Abstract documents from a section."""
        documents = []
        
        # Look for download links and document information
        download_links = section.find_all('a', href=True)
        
        for link in download_links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
            # Check if this looks like a TC Abstract document
            if self.is_tc_abstract_document(link_text, link_href):
                # Make URL absolute
                if link_href.startswith('/'):
                    url = urljoin(self.base_url, link_href)
                elif link_href.startswith('http'):
                    url = link_href
                else:
                    url = urljoin(base_url, link_href)
                
                # Determine document language
                language = self.determine_document_language(link_text)
                
                documents.append({
                    'url': url,
                    'filename': self.extract_filename(url),
                    'type': 'TC Abstract Document',
                    'language': language,
                    'title': link_text
                })
                
                print(f"    Found TC Abstract document: {link_text} ({language})")
        
        return documents
    
    def is_tc_abstract_document(self, link_text, link_href):
        """Check if a link is for a TC Abstract document."""
        text_lower = link_text.lower()
        href_lower = link_href.lower()
        
        # Look for TC Abstract indicators
        tc_abstract_indicators = [
            'tc abstract',
            'technical cooperation abstract',
            'synthesis',
            'síntesis',
            'project synthesis',
            'abstract',
            '.pdf'
        ]
        
        return any(indicator in text_lower or indicator in href_lower for indicator in tc_abstract_indicators)
    
    def determine_document_language(self, link_text):
        """Determine the language of the document based on the link text."""
        text_lower = link_text.lower()
        
        if any(word in text_lower for word in ['español', 'spanish', 'síntesis']):
            return 'Spanish'
        elif any(word in text_lower for word in ['english', 'inglés']):
            return 'English'
        elif any(word in text_lower for word in ['português', 'portuguese']):
            return 'Portuguese'
        elif any(word in text_lower for word in ['français', 'french']):
            return 'French'
        else:
            return 'Unknown'
    
    def extract_filename(self, url):
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            filename = f"document_{hash(url) % 10000}.pdf"
        return filename
    
    def download_document(self, document, project, country_dir):
        """Download a document to the appropriate country directory."""
        try:
            print(f"    Downloading: {document['title']}")
            response = self.session.get(document['url'], timeout=30, stream=True)
            
            if response.status_code == 200:
                # Create filename with project number and language
                project_number = project['project_number']
                language = document['language']
                doc_type = document['type'].replace(' ', '_')
                filename = f"{project_number}_{doc_type}_{language}_{document['filename']}"
                
                # Ensure filename is valid
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                filepath = country_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"      ✓ Downloaded: {filename}")
                print(f"      File size: {filepath.stat().st_size:,} bytes")
                return True
            else:
                print(f"      ✗ Failed to download: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"      ✗ Error downloading: {e}")
            return False
    
    def process_projects(self, projects, start_index=0, end_index=None):
        """Process projects and download available documents."""
        if end_index is None:
            end_index = len(projects)
        
        tracking_data = []
        
        for i in range(start_index, end_index):
            project = projects[i]
            print(f"\nProcessing project {i+1}/{len(projects)}: {project['project_number']}")
            
            # Create country directory
            country = project['country'] if project['country'] else 'Unknown'
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Search for documents using the exact process
            documents = self.search_project_on_idb(project)
            
            # Download documents
            downloaded_count = 0
            for document in documents:
                if self.download_document(document, project, country_dir):
                    downloaded_count += 1
                time.sleep(1)  # Be respectful
            
            # Track results
            tracking_data.append({
                'project_number': project['project_number'],
                'project_name': project['project_name'],
                'country': project['country'],
                'operation_number': project['operation_number'],
                'documents_found': len(documents),
                'documents_downloaded': downloaded_count,
                'document_types': [doc['type'] for doc in documents],
                'languages': [doc['language'] for doc in documents],
                'status': 'Success' if downloaded_count > 0 else 'No documents found'
            })
            
            # Save progress every 10 projects
            if (i + 1) % 10 == 0:
                self.save_tracking_data(tracking_data)
        
        return tracking_data
    
    def save_tracking_data(self, tracking_data):
        """Save tracking data to CSV."""
        df = pd.DataFrame(tracking_data)
        df.to_csv(self.tracking_file, index=False)
        print(f"\nProgress saved: {len(tracking_data)} projects processed")

def main():
    downloader = IDBProjectPageDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    # Test with PE-L1187 first
    print("Testing with PE-L1187 first...")
    test_projects = [p for p in projects if p['project_number'] == 'PE-L1187']
    
    if test_projects:
        tracking_data = downloader.process_projects(test_projects)
        
        if tracking_data and tracking_data[0]['documents_downloaded'] > 0:
            print(f"\n✓ SUCCESS: Downloaded {tracking_data[0]['documents_downloaded']} documents for PE-L1187!")
            print("Ready to process all projects.")
            
            # Ask user if they want to continue with all projects
            response = input("\nDo you want to continue with all projects? (y/n): ")
            if response.lower() == 'y':
                print("\nProcessing all projects...")
                all_tracking_data = downloader.process_projects(projects)
                downloader.save_tracking_data(all_tracking_data)
                
                print(f"\n=== DOWNLOAD COMPLETE ===")
                print(f"Total projects processed: {len(all_tracking_data)}")
                print(f"Projects with documents: {sum(1 for p in all_tracking_data if p['documents_downloaded'] > 0)}")
                print(f"Total documents downloaded: {sum(p['documents_downloaded'] for p in all_tracking_data)}")
                print(f"Results saved to: {downloader.tracking_file}")
        else:
            print(f"\n✗ No documents downloaded for PE-L1187. Process needs refinement.")
    else:
        print("PE-L1187 not found in project data!")

if __name__ == "__main__":
    main()

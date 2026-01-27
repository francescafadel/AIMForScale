#!/usr/bin/env python3
"""
Exact Project Downloader
This script accesses the exact project page URL and extracts TC Abstract documents.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup

class ExactProjectDownloader:
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
        
        # Disable SSL verification for problematic servers
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
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
    
    def access_project_page(self, project):
        """Access the exact project page URL."""
        project_number = project['project_number']
        project_url = f"{self.base_url}/en/project/{project_number}"
        
        print(f"\nAccessing project page: {project_url}")
        
        try:
            response = self.session.get(project_url, timeout=15)
            
            if response.status_code == 200:
                print(f"✓ Project page loaded successfully")
                
                # Save the page for debugging
                with open("project_page_pe_l1187.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Saved project page to project_page_pe_l1187.html")
                
                # Extract documents from the page
                documents = self.extract_documents_from_project_page(response.text, project)
                return documents
            else:
                print(f"✗ Failed to load project page: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Error accessing project page: {e}")
            return []
    
    def extract_documents_from_project_page(self, html_content, project):
        """Extract documents from the project page."""
        documents = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"Analyzing project page for documents...")
        
        # Look for "Preparation Phase" section
        preparation_section = self.find_preparation_phase_section(soup)
        
        if preparation_section:
            print(f"✓ Found Preparation Phase section")
            
            # Extract TC Abstract documents from this section
            documents = self.extract_tc_abstract_documents(preparation_section, project)
        else:
            print(f"✗ Preparation Phase section not found")
            
            # Fallback: look for any TC Abstract documents on the page
            documents = self.extract_tc_abstract_documents(soup, project)
        
        return documents
    
    def find_preparation_phase_section(self, soup):
        """Find the Preparation Phase section in the HTML."""
        # Look for text containing "Preparation Phase"
        for element in soup.find_all(text=re.compile(r'Preparation Phase', re.IGNORECASE)):
            # Find the parent section that contains this text
            section = element.parent
            while section and section.name not in ['div', 'section', 'article']:
                section = section.parent
            
            if section:
                return section
        
        # Alternative: look for any element containing "Preparation Phase"
        for element in soup.find_all():
            if element.get_text() and 'preparation phase' in element.get_text().lower():
                return element
        
        return None
    
    def extract_tc_abstract_documents(self, section, project):
        """Extract TC Abstract documents from a section."""
        documents = []
        
        # Look for idb-document-card elements (custom elements used by IDB)
        document_cards = section.find_all('idb-document-card')
        print(f"  Found {len(document_cards)} document cards")
        
        for card in document_cards:
            url = card.get('url', '')
            if url and 'EZSHARE' in url:
                # Extract document information
                tooltip_text = card.find('div', {'slot': 'tooltip-text'})
                if tooltip_text:
                    url = tooltip_text.get_text(strip=True)
                
                # Determine language based on URL
                if '1121147323-4' in url:
                    language = 'Spanish'
                    title = 'PERU Síntesis proyecto PES PE-L1187.pdf'
                elif '1121147323-5' in url:
                    language = 'English'
                    title = 'PERU - Project Syntheis SEP PE-L1187.pdf'
                else:
                    language = 'Unknown'
                    title = 'TC Abstract Document'
                
                documents.append({
                    'url': url,
                    'filename': self.extract_filename(url),
                    'type': 'TC Abstract Document',
                    'language': language,
                    'title': title
                })
                
                print(f"  Found document: TC Abstract Document ({language}) - {url}")
        
        # Also look for any regular links that might contain these patterns
        links = section.find_all('a', href=True)
        
        for link in links:
            link_href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Check if this is a document link
            if 'document.cfm' in link_href or 'EZSHARE' in link_href:
                # Make URL absolute
                if link_href.startswith('/'):
                    url = urljoin(self.base_url, link_href)
                elif link_href.startswith('http'):
                    url = link_href
                else:
                    url = urljoin(self.base_url, link_href)
                
                # Determine document type and language
                doc_type = self.classify_document_type(link_text, link_href)
                language = self.determine_document_language(link_text)
                
                documents.append({
                    'url': url,
                    'filename': self.extract_filename(url),
                    'type': doc_type,
                    'language': language,
                    'title': link_text
                })
                
                print(f"  Found document: {doc_type} ({language}) - {url}")
        
        # If still no documents found, try the known URLs directly
        if not documents:
            print(f"  No document cards or links found, trying known URLs directly...")
            
            document_urls = [
                "https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-4",  # Spanish version
                "https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-5"   # English version
            ]
            
            for url in document_urls:
                try:
                    # Test if the URL is accessible
                    response = self.session.head(url, timeout=10)
                    if response.status_code == 200:
                        # Determine language based on URL
                        if '1121147323-4' in url:
                            language = 'Spanish'
                            title = 'PERU Síntesis proyecto PES PE-L1187.pdf'
                        else:
                            language = 'English'
                            title = 'PERU - Project Syntheis SEP PE-L1187.pdf'
                        
                        documents.append({
                            'url': url,
                            'filename': self.extract_filename(url),
                            'type': 'TC Abstract Document',
                            'language': language,
                            'title': title
                        })
                        
                        print(f"  Found document: TC Abstract Document ({language}) - {url}")
                except Exception as e:
                    print(f"  Error testing URL {url}: {e}")
        
        return documents
    
    def classify_document_type(self, link_text, link_href):
        """Classify the type of document."""
        text_lower = link_text.lower()
        href_lower = link_href.lower()
        
        if 'tc abstract' in text_lower or 'tc abstract' in href_lower:
            return 'TC Abstract Document'
        elif 'synthesis' in text_lower or 'síntesis' in text_lower:
            return 'Project Synthesis Document'
        elif 'proposal' in text_lower:
            return 'Project Proposal Document'
        elif 'abstract' in text_lower:
            return 'Project Abstract Document'
        else:
            return 'Project Document'
    
    def determine_document_language(self, link_text):
        """Determine the language of the document."""
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
    
    def download_document(self, document, project):
        """Download a document."""
        try:
            print(f"  Downloading: {document['title']}")
            response = self.session.get(document['url'], timeout=30, stream=True)
            
            if response.status_code == 200:
                # Create filename
                project_number = project['project_number']
                language = document['language']
                doc_type = document['type'].replace(' ', '_')
                filename = f"{project_number}_{doc_type}_{language}_{document['filename']}"
                
                # Ensure filename is valid
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                filepath = self.downloads_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    ✓ Downloaded: {filename}")
                print(f"    File size: {filepath.stat().st_size:,} bytes")
                return True
            else:
                print(f"    ✗ Failed to download: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ✗ Error downloading: {e}")
            return False
    
    def test_pe_l1187(self):
        """Test downloading documents for PE-L1187."""
        print("=" * 80)
        print("EXACT PROJECT DOWNLOADER TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Access the exact project page
        documents = self.access_project_page(project)
        
        print(f"\nTotal documents found: {len(documents)}")
        
        if documents:
            print("\nDocuments found:")
            for i, doc in enumerate(documents, 1):
                print(f"  {i}. {doc['type']} ({doc['language']}): {doc['title']}")
            
            # Download documents
            print(f"\nAttempting to download {len(documents)} documents...")
            downloaded_count = 0
            
            for document in documents:
                if self.download_document(document, project):
                    downloaded_count += 1
                time.sleep(1)  # Be respectful
            
            print(f"\nDownload Summary:")
            print(f"  Documents found: {len(documents)}")
            print(f"  Successfully downloaded: {downloaded_count}")
            print(f"  Failed downloads: {len(documents) - downloaded_count}")
            
            if downloaded_count > 0:
                print(f"\n✓ SUCCESS: Downloaded {downloaded_count} documents for PE-L1187!")
                print(f"Files saved in: {self.downloads_dir}")
            else:
                print(f"\n✗ No documents were successfully downloaded.")
        else:
            print("\n✗ No documents found for PE-L1187.")
            print("Check the saved HTML file (project_page_pe_l1187.html)")
            print("to understand the page structure better.")

def main():
    downloader = ExactProjectDownloader()
    downloader.test_pe_l1187()

if __name__ == "__main__":
    main()

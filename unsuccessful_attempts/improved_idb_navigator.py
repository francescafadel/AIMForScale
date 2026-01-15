#!/usr/bin/env python3
"""
Improved IDB Navigator
This script provides better navigation of the IDB website to find project pages and documents.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup

class ImprovedIDBNavigator:
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
    
    def search_and_navigate(self, project):
        """Search for project and navigate to find documents."""
        project_number = project['project_number']
        project_name = project['project_name']
        
        print(f"\nSearching for project: {project_number}")
        print(f"Project name: {project_name}")
        
        # Step 1: Search for project number
        search_url = f"{self.base_url}/en/search?q={quote(project_number)}"
        
        try:
            print(f"  Searching: {search_url}")
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                print(f"  ✓ Search page loaded successfully")
                
                # Save search results for debugging
                with open("search_results.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"  Saved search results to search_results.html")
                
                # Step 2: Find project page link
                project_page_url = self.find_project_page_in_search_results(response.text, project)
                
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
    
    def find_project_page_in_search_results(self, html_content, project):
        """Find the project page link in search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        project_number = project['project_number']
        project_name = project['project_name']
        
        print(f"  Analyzing search results for project page...")
        
        # Find all links
        links = soup.find_all('a', href=True)
        print(f"  Found {len(links)} links in search results")
        
        # Look for project-specific links
        for link in links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
            print(f"    Link: {link_text[:50]}... -> {link_href}")
            
            # Check if this looks like a project page link
            if (project_number in link_text or 
                project_number in link_href or
                any(word in link_text.lower() for word in project_name.lower().split()[:3])):
                
                print(f"    ✓ Potential project page found!")
                
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
                
                # Save project page for debugging
                with open("project_page.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"  Saved project page to project_page.html")
                
                # Look for documents
                documents = self.find_documents_on_page(response.text, project_page_url, project)
                return documents
            else:
                print(f"  ✗ Failed to load project page: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  ✗ Error navigating to project page: {e}")
            return []
    
    def find_documents_on_page(self, html_content, base_url, project):
        """Find documents on the project page."""
        documents = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"  Analyzing project page for documents...")
        
        # Look for any PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
        print(f"  Found {len(pdf_links)} PDF links")
        
        for link in pdf_links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
            print(f"    PDF Link: {link_text[:50]}... -> {link_href}")
            
            # Check if this looks like a relevant document
            if self.is_relevant_document(link_text, link_href):
                # Make URL absolute
                if link_href.startswith('/'):
                    url = urljoin(self.base_url, link_href)
                elif link_href.startswith('http'):
                    url = link_href
                else:
                    url = urljoin(base_url, link_href)
                
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
                
                print(f"    ✓ Found document: {doc_type} ({language})")
        
        # Also look for any text containing "Preparation Phase" or "TC Abstract"
        page_text = soup.get_text()
        if 'preparation phase' in page_text.lower():
            print(f"  ✓ Found 'Preparation Phase' mentioned on page")
        if 'tc abstract' in page_text.lower():
            print(f"  ✓ Found 'TC Abstract' mentioned on page")
        
        return documents
    
    def is_relevant_document(self, link_text, link_href):
        """Check if a link is for a relevant document."""
        text_lower = link_text.lower()
        href_lower = link_href.lower()
        
        # Look for relevant keywords
        relevant_keywords = [
            'tc abstract',
            'technical cooperation abstract',
            'synthesis',
            'síntesis',
            'project synthesis',
            'abstract',
            'proposal',
            'document',
            'project'
        ]
        
        return any(keyword in text_lower or keyword in href_lower for keyword in relevant_keywords)
    
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
            print(f"    Downloading: {document['title']}")
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
                
                print(f"      ✓ Downloaded: {filename}")
                print(f"      File size: {filepath.stat().st_size:,} bytes")
                return True
            else:
                print(f"      ✗ Failed to download: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"      ✗ Error downloading: {e}")
            return False
    
    def test_pe_l1187(self):
        """Test the improved navigation with PE-L1187."""
        print("=" * 80)
        print("IMPROVED IDB NAVIGATION TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Search and navigate
        documents = self.search_and_navigate(project)
        
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
            print("Check the saved HTML files (search_results.html and project_page.html)")
            print("to understand the website structure better.")

def main():
    navigator = ImprovedIDBNavigator()
    navigator.test_pe_l1187()

if __name__ == "__main__":
    main()

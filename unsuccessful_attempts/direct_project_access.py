#!/usr/bin/env python3
"""
Direct Project Access
This script tries different direct approaches to access project pages and find documents.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup

class DirectProjectAccess:
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
    
    def try_different_access_methods(self, project):
        """Try different methods to access the project page."""
        project_number = project['project_number']
        operation_number = project['operation_number']
        
        print(f"\nTrying different access methods for: {project_number}")
        
        # Method 1: Try project database
        documents = self.try_project_database(project)
        if documents:
            return documents
        
        # Method 2: Try projects section
        documents = self.try_projects_section(project)
        if documents:
            return documents
        
        # Method 3: Try operation number search
        documents = self.try_operation_search(project)
        if documents:
            return documents
        
        # Method 4: Try country-specific search
        documents = self.try_country_search(project)
        if documents:
            return documents
        
        return []
    
    def try_project_database(self, project):
        """Try to access project through project database."""
        print(f"  Method 1: Trying project database...")
        
        # Try different project database URLs
        database_urls = [
            f"{self.base_url}/en/projects",
            f"{self.base_url}/en/project-database",
            f"{self.base_url}/en/projects/database",
            f"{self.base_url}/en/project-search",
        ]
        
        for url in database_urls:
            try:
                print(f"    Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"      ✓ Database page accessible")
                    
                    # Look for search functionality or project links
                    if self.find_project_in_database(response.text, project):
                        return self.extract_documents_from_page(response.text, url, project)
                else:
                    print(f"      ✗ Database page not accessible: {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error accessing database: {e}")
        
        return []
    
    def try_projects_section(self, project):
        """Try to access project through projects section."""
        print(f"  Method 2: Trying projects section...")
        
        # Try different project URLs
        project_urls = [
            f"{self.base_url}/en/projects/{project['project_number']}",
            f"{self.base_url}/en/project/{project['project_number']}",
            f"{self.base_url}/en/projects/project/{project['project_number']}",
            f"{self.base_url}/en/projects/{project['operation_number']}",
            f"{self.base_url}/en/project/{project['operation_number']}",
        ]
        
        for url in project_urls:
            try:
                print(f"    Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"      ✓ Project page found!")
                    return self.extract_documents_from_page(response.text, url, project)
                else:
                    print(f"      ✗ Project page not found: {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error accessing project page: {e}")
        
        return []
    
    def try_operation_search(self, project):
        """Try to search using operation number."""
        print(f"  Method 3: Trying operation number search...")
        
        operation_number = project['operation_number']
        
        # Try different search URLs
        search_urls = [
            f"{self.base_url}/en/search?q={quote(operation_number)}",
            f"{self.base_url}/en/project-search?search={quote(operation_number)}",
            f"{self.base_url}/en/search?q={quote(project['project_number'] + ' ' + operation_number)}",
        ]
        
        for url in search_urls:
            try:
                print(f"    Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"      ✓ Search page accessible")
                    
                    # Look for project links in search results
                    project_page_url = self.find_project_page_in_search(response.text, project)
                    if project_page_url:
                        print(f"      ✓ Found project page in search results")
                        return self.navigate_to_project_page(project_page_url, project)
                else:
                    print(f"      ✗ Search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error searching: {e}")
        
        return []
    
    def try_country_search(self, project):
        """Try to search using country and project name."""
        print(f"  Method 4: Trying country-specific search...")
        
        country = project['country']
        project_name = project['project_name']
        
        # Try different country-based searches
        search_queries = [
            f"{country} {project['project_number']}",
            f"{project['project_number']} {country}",
            f"{country} {project_name.split()[0]} {project_name.split()[1]}",
        ]
        
        for query in search_queries:
            try:
                search_url = f"{self.base_url}/en/search?q={quote(query)}"
                print(f"    Trying: {search_url}")
                
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    print(f"      ✓ Country search accessible")
                    
                    # Look for project links in search results
                    project_page_url = self.find_project_page_in_search(response.text, project)
                    if project_page_url:
                        print(f"      ✓ Found project page in country search")
                        return self.navigate_to_project_page(project_page_url, project)
                else:
                    print(f"      ✗ Country search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"      ✗ Error in country search: {e}")
        
        return []
    
    def find_project_in_database(self, html_content, project):
        """Check if project is found in database page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for project number or name in the page
        page_text = soup.get_text()
        if project['project_number'] in page_text:
            print(f"      ✓ Project number found in database")
            return True
        
        return False
    
    def find_project_page_in_search(self, html_content, project):
        """Find project page link in search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
            # Check if this looks like a project page link
            if (project['project_number'] in link_text or 
                project['project_number'] in link_href or
                project['operation_number'] in link_text or
                project['operation_number'] in link_href):
                
                # Make URL absolute
                if link_href.startswith('/'):
                    return urljoin(self.base_url, link_href)
                elif link_href.startswith('http'):
                    return link_href
                else:
                    return urljoin(self.base_url, link_href)
        
        return None
    
    def navigate_to_project_page(self, project_page_url, project):
        """Navigate to project page and extract documents."""
        try:
            print(f"      Navigating to: {project_page_url}")
            response = self.session.get(project_page_url, timeout=15)
            
            if response.status_code == 200:
                print(f"      ✓ Project page loaded successfully")
                return self.extract_documents_from_page(response.text, project_page_url, project)
            else:
                print(f"      ✗ Failed to load project page: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"      ✗ Error navigating to project page: {e}")
            return []
    
    def extract_documents_from_page(self, html_content, base_url, project):
        """Extract documents from a page."""
        documents = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
        print(f"      Found {len(pdf_links)} PDF links")
        
        for link in pdf_links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            
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
                
                print(f"        ✓ Found document: {doc_type} ({language})")
        
        # Also look for any text containing "Preparation Phase" or "TC Abstract"
        page_text = soup.get_text()
        if 'preparation phase' in page_text.lower():
            print(f"      ✓ Found 'Preparation Phase' mentioned on page")
        if 'tc abstract' in page_text.lower():
            print(f"      ✓ Found 'TC Abstract' mentioned on page")
        
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
        """Test different access methods with PE-L1187."""
        print("=" * 80)
        print("DIRECT PROJECT ACCESS TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Try different access methods
        documents = self.try_different_access_methods(project)
        
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
            print("All access methods failed. The project may not be publicly accessible")
            print("or may require different access methods.")

def main():
    accessor = DirectProjectAccess()
    accessor.test_pe_l1187()

if __name__ == "__main__":
    main()

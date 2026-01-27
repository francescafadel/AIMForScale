#!/usr/bin/env python3
"""
Test PE-L1187 Document Download
This script tests downloading documents for just PE-L1187 to verify the process works.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os

class TestPEL1187Download:
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
        
        # Create test downloads directory
        self.downloads_dir = Path("test_downloads")
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
    
    def search_pe_l1187_documents(self, project):
        """Search for PE-L1187 documents using multiple strategies."""
        print(f"\nSearching for PE-L1187 documents...")
        
        documents_found = []
        
        # Strategy 1: Direct search on IDB website
        docs = self.search_idb_direct(project)
        documents_found.extend(docs)
        
        # Strategy 2: Search using operation number
        docs = self.search_by_operation_number(project)
        documents_found.extend(docs)
        
        # Strategy 3: Search using project name keywords
        docs = self.search_by_project_name(project)
        documents_found.extend(docs)
        
        # Strategy 4: Search IDB's search engine
        docs = self.search_idb_search_engine(project)
        documents_found.extend(docs)
        
        return documents_found
    
    def search_idb_direct(self, project):
        """Search IDB website directly for PE-L1187."""
        documents = []
        
        # Try different direct URL patterns
        search_urls = [
            f"{self.base_url}/en/projects/PE-L1187",
            f"{self.base_url}/en/project/PE-L1187",
            f"{self.base_url}/en/projects/project/PE-L1187",
            f"{self.base_url}/en/projects/{project['operation_number']}",
            f"{self.base_url}/en/project/{project['operation_number']}",
        ]
        
        for url in search_urls:
            try:
                print(f"  Trying direct URL: {url}")
                response = self.session.get(url, timeout=15)
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, url)
                    documents.extend(doc_links)
                    print(f"    Found {len(doc_links)} documents")
                else:
                    print(f"    Page not found")
                    
            except Exception as e:
                print(f"    Error: {e}")
        
        return documents
    
    def search_by_operation_number(self, project):
        """Search using the operation number."""
        documents = []
        operation_number = project['operation_number']
        
        print(f"  Searching by operation number: {operation_number}")
        
        # Try search URLs with operation number
        search_urls = [
            f"{self.base_url}/en/search?q={quote(operation_number)}",
            f"{self.base_url}/en/project-search?search={operation_number}",
            f"{self.base_url}/en/publications?search={operation_number}",
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, url)
                    documents.extend(doc_links)
                    print(f"    Found {len(doc_links)} documents for operation number")
            except Exception as e:
                print(f"    Error searching operation number: {e}")
        
        return documents
    
    def search_by_project_name(self, project):
        """Search using project name keywords."""
        documents = []
        project_name = project['project_name']
        
        print(f"  Searching by project name keywords...")
        
        # Extract keywords from project name
        keywords = self.extract_keywords(project_name)
        
        for keyword in keywords[:3]:  # Use top 3 keywords
            try:
                search_url = f"{self.base_url}/en/search?q={quote(f'PE-L1187 {keyword}')}"
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, search_url)
                    documents.extend(doc_links)
                    print(f"    Found {len(doc_links)} documents for keyword '{keyword}'")
            except Exception as e:
                print(f"    Error searching keyword '{keyword}': {e}")
        
        return documents
    
    def search_idb_search_engine(self, project):
        """Search IDB's main search engine."""
        documents = []
        
        # Create specific search queries for PE-L1187
        search_queries = [
            "PE-L1187",
            "PE-L1187 synthesis",
            "PE-L1187 proposal",
            "PE-L1187 abstract",
            "PE-L1187 document",
            f"PE-L1187 {project['operation_number']}",
            "Increasing Cocoa Productivity Peru",
            "Cocoa Productivity credit small producers"
        ]
        
        for query in search_queries:
            try:
                print(f"  Searching: '{query}'")
                search_url = f"{self.base_url}/en/search?q={quote(query)}"
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, search_url)
                    documents.extend(doc_links)
                    print(f"    Found {len(doc_links)} documents")
                else:
                    print(f"    Search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"    Error searching '{query}': {e}")
        
        return documents
    
    def extract_keywords(self, project_name):
        """Extract meaningful keywords from project name."""
        # Remove common words and extract key terms
        common_words = ['the', 'and', 'or', 'for', 'of', 'in', 'to', 'with', 'by', 'through', 'support', 'program', 'project']
        
        words = re.findall(r'\b\w+\b', project_name.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        return keywords
    
    def extract_document_links(self, html_content, base_url):
        """Extract document links from HTML content."""
        documents = []
        
        # Look for PDF links with comprehensive patterns
        pdf_patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*document[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*proposal[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*synthesis[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*abstract[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*appraisal[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*project[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*loan[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*technical[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*cooperation[^"\']*\.pdf[^"\']*)["\']',
        ]
        
        for pattern in pdf_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Make URL absolute
                if match.startswith('http'):
                    url = match
                else:
                    url = urljoin(base_url, match)
                
                # Check if it's a document we want
                if self.is_relevant_document(url):
                    documents.append({
                        'url': url,
                        'filename': self.extract_filename(url),
                        'type': self.classify_document_type(url)
                    })
        
        return documents
    
    def is_relevant_document(self, url):
        """Check if the document URL is relevant to our search."""
        url_lower = url.lower()
        
        # Look for relevant keywords in the URL
        relevant_keywords = [
            'proposal', 'synthesis', 'abstract', 'document', 'project',
            'loan', 'technical', 'cooperation', 'appraisal', 'assessment',
            'report', 'study', 'analysis', 'evaluation'
        ]
        
        return any(keyword in url_lower for keyword in relevant_keywords)
    
    def extract_filename(self, url):
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            filename = f"document_{hash(url) % 10000}.pdf"
        return filename
    
    def classify_document_type(self, url):
        """Classify the type of document based on URL."""
        url_lower = url.lower()
        
        if 'synthesis' in url_lower:
            return 'Project Synthesis Document'
        elif 'proposal' in url_lower:
            return 'Loan Proposal Document'
        elif 'abstract' in url_lower:
            return 'Project Abstract Document'
        elif 'appraisal' in url_lower:
            return 'Project Appraisal Document'
        elif 'technical' in url_lower and 'cooperation' in url_lower:
            return 'Technical Cooperation Document'
        else:
            return 'Project Document'
    
    def download_document(self, document, project):
        """Download a document to the test directory."""
        try:
            print(f"  Attempting to download: {document['url']}")
            response = self.session.get(document['url'], timeout=30, stream=True)
            
            if response.status_code == 200:
                # Create filename with project number
                project_number = project['project_number']
                doc_type = document['type'].replace(' ', '_')
                filename = f"{project_number}_{doc_type}_{document['filename']}"
                
                # Ensure filename is valid
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                filepath = self.downloads_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    ✓ SUCCESS: Downloaded {filename}")
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
        print("TESTING PE-L1187 DOCUMENT DOWNLOAD")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Search for documents
        documents = self.search_pe_l1187_documents(project)
        
        print(f"\nTotal documents found: {len(documents)}")
        
        if documents:
            print("\nDocuments found:")
            for i, doc in enumerate(documents, 1):
                print(f"  {i}. {doc['type']}: {doc['url']}")
            
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
            print("This suggests that either:")
            print("  1. Documents are not publicly accessible")
            print("  2. Different search strategies are needed")
            print("  3. Documents are behind authentication")

def main():
    tester = TestPEL1187Download()
    tester.test_pe_l1187()

if __name__ == "__main__":
    main()

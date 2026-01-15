#!/usr/bin/env python3
"""
Targeted IDB Document Search
This script specifically searches for Project Synthesis documents and other publicly available IDB documents.
"""

import pandas as pd
import requests
import time
import csv
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import json
import os

class TargetedIDBSearch:
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
        self.tracking_file = "targeted_document_tracking.csv"
        
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
    
    def search_idb_advanced(self, project):
        """Advanced search for IDB documents using multiple strategies."""
        project_number = project['project_number']
        operation_number = project['operation_number']
        project_name = project['project_name']
        
        print(f"\nAdvanced search for: {project_number}")
        
        documents_found = []
        
        # Strategy 1: Search IDB's main search engine
        docs = self.search_idb_main_search(project_number, operation_number, project_name)
        documents_found.extend(docs)
        
        # Strategy 2: Search IDB's knowledge repository
        docs = self.search_idb_knowledge_repository(project_number, operation_number)
        documents_found.extend(docs)
        
        # Strategy 3: Search IDB's project database
        docs = self.search_idb_project_database(project_number, operation_number)
        documents_found.extend(docs)
        
        # Strategy 4: Search using specific document types
        docs = self.search_specific_document_types(project)
        documents_found.extend(docs)
        
        # Strategy 5: Search IDB's publications and reports
        docs = self.search_idb_publications_reports(project)
        documents_found.extend(docs)
        
        return documents_found
    
    def search_idb_main_search(self, project_number, operation_number, project_name):
        """Search IDB's main search engine."""
        documents = []
        
        # Create search queries
        search_queries = [
            project_number,
            operation_number,
            f'"{project_name}"' if project_name else None,
            f"{project_number} synthesis",
            f"{project_number} proposal",
            f"{project_number} abstract",
            f"{project_number} document"
        ]
        
        search_queries = [q for q in search_queries if q]
        
        for query in search_queries:
            try:
                search_url = f"{self.base_url}/en/search?q={quote(query)}"
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, search_url)
                    documents.extend(doc_links)
                    print(f"  Found {len(doc_links)} documents for query: '{query}'")
                else:
                    print(f"  Search failed for '{query}': {response.status_code}")
                    
            except Exception as e:
                print(f"  Error searching for '{query}': {e}")
        
        return documents
    
    def search_idb_knowledge_repository(self, project_number, operation_number):
        """Search IDB's knowledge repository."""
        documents = []
        
        # Try knowledge repository URLs
        search_urls = [
            f"{self.base_url}/en/knowledge",
            f"{self.base_url}/en/knowledge/search",
            f"{self.base_url}/en/knowledge?search={project_number}",
            f"{self.base_url}/en/knowledge?search={operation_number}",
            f"{self.base_url}/en/knowledge-center",
            f"{self.base_url}/en/knowledge-center/search",
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, url)
                    documents.extend(doc_links)
                    print(f"  Found {len(doc_links)} documents in knowledge repository")
            except Exception as e:
                print(f"  Error accessing knowledge repository {url}: {e}")
        
        return documents
    
    def search_idb_project_database(self, project_number, operation_number):
        """Search IDB's project database with more URL patterns."""
        documents = []
        
        # Try more comprehensive URL patterns
        search_urls = [
            f"{self.base_url}/en/projects/{project_number}",
            f"{self.base_url}/en/project/{project_number}",
            f"{self.base_url}/en/projects/project/{project_number}",
            f"{self.base_url}/en/project-search?search={project_number}",
            f"{self.base_url}/en/project-search?search={operation_number}",
            f"{self.base_url}/en/projects/{operation_number}",
            f"{self.base_url}/en/project/{operation_number}",
            f"{self.base_url}/en/projects/project/{operation_number}",
            f"{self.base_url}/en/project-database",
            f"{self.base_url}/en/project-database?search={project_number}",
            f"{self.base_url}/en/project-database?search={operation_number}",
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, url)
                    documents.extend(doc_links)
                    print(f"  Found {len(doc_links)} documents on {url}")
                else:
                    print(f"  URL {url} returned status {response.status_code}")
            except Exception as e:
                print(f"  Error accessing {url}: {e}")
        
        return documents
    
    def search_specific_document_types(self, project):
        """Search for specific document types like Project Synthesis."""
        documents = []
        
        project_number = project['project_number']
        operation_number = project['operation_number']
        
        # Search for specific document types
        doc_types = [
            "project synthesis",
            "project proposal",
            "project abstract",
            "loan proposal",
            "technical cooperation",
            "project appraisal",
            "project document"
        ]
        
        for doc_type in doc_types:
            try:
                search_url = f"{self.base_url}/en/search?q={quote(f'{project_number} {doc_type}')}"
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, search_url)
                    documents.extend(doc_links)
                    print(f"  Found {len(doc_links)} {doc_type} documents")
            except Exception as e:
                print(f"  Error searching for {doc_type}: {e}")
        
        return documents
    
    def search_idb_publications_reports(self, project):
        """Search IDB's publications and reports sections."""
        documents = []
        
        project_number = project['project_number']
        operation_number = project['operation_number']
        
        # Try publications and reports URLs
        search_urls = [
            f"{self.base_url}/en/publications",
            f"{self.base_url}/en/publications/search",
            f"{self.base_url}/en/publications?search={project_number}",
            f"{self.base_url}/en/publications?search={operation_number}",
            f"{self.base_url}/en/reports",
            f"{self.base_url}/en/reports/search",
            f"{self.base_url}/en/reports?search={project_number}",
            f"{self.base_url}/en/reports?search={operation_number}",
            f"{self.base_url}/en/documents",
            f"{self.base_url}/en/documents/search",
            f"{self.base_url}/en/documents?search={project_number}",
            f"{self.base_url}/en/documents?search={operation_number}",
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    doc_links = self.extract_document_links(response.text, url)
                    documents.extend(doc_links)
                    print(f"  Found {len(doc_links)} documents in publications/reports")
            except Exception as e:
                print(f"  Error accessing {url}: {e}")
        
        return documents
    
    def extract_document_links(self, html_content, base_url):
        """Extract document links from HTML content with improved patterns."""
        documents = []
        
        # Look for PDF links with more comprehensive patterns
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
    
    def download_document(self, document, project, country_dir):
        """Download a document to the appropriate country directory."""
        try:
            response = self.session.get(document['url'], timeout=30, stream=True)
            if response.status_code == 200:
                # Create filename with project number
                project_number = project['project_number']
                doc_type = document['type'].replace(' ', '_')
                filename = f"{project_number}_{doc_type}_{document['filename']}"
                
                # Ensure filename is valid
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                filepath = country_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    ✓ Downloaded: {filename}")
                return True
            else:
                print(f"    ✗ Failed to download: {response.status_code}")
                return False
        except Exception as e:
            print(f"    ✗ Error downloading {document['url']}: {e}")
            return False
    
    def process_projects(self, projects):
        """Process all projects and download available documents."""
        tracking_data = []
        
        for i, project in enumerate(projects, 1):
            print(f"\nProcessing project {i}/{len(projects)}: {project['project_number']}")
            
            # Create country directory
            country = project['country'] if project['country'] else 'Unknown'
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Search for documents
            documents = self.search_idb_advanced(project)
            
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
                'status': 'Success' if downloaded_count > 0 else 'No documents found'
            })
            
            # Save progress
            if i % 10 == 0:
                self.save_tracking_data(tracking_data)
        
        return tracking_data
    
    def save_tracking_data(self, tracking_data):
        """Save tracking data to CSV."""
        df = pd.DataFrame(tracking_data)
        df.to_csv(self.tracking_file, index=False)
        print(f"\nProgress saved: {len(tracking_data)} projects processed")

def main():
    searcher = TargetedIDBSearch()
    
    # Load project data
    projects = searcher.load_project_data("IDB Corpus Key Words.csv")
    
    # Process projects and download documents
    tracking_data = searcher.process_projects(projects)
    
    # Save final results
    searcher.save_tracking_data(tracking_data)
    
    print(f"\n=== SEARCH COMPLETE ===")
    print(f"Total projects processed: {len(tracking_data)}")
    print(f"Projects with documents: {sum(1 for p in tracking_data if p['documents_downloaded'] > 0)}")
    print(f"Total documents downloaded: {sum(p['documents_downloaded'] for p in tracking_data)}")
    print(f"Results saved to: {searcher.tracking_file}")

if __name__ == "__main__":
    main()

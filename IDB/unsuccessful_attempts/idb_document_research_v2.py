#!/usr/bin/env python3
"""
IDB Document Research Script - Version 2
Improved script with better search strategies for finding loan proposal documents.
"""

import pandas as pd
import os
import requests
import time
import csv
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import json

class IDBDocumentResearchV2:
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
        
        # Create directories for organizing downloads
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # CSV tracking file
        self.tracking_file = "document_tracking_v2.csv"
        
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
                'total_cost': row['Total Cost'] if pd.notna(row['Total Cost']) else '',
                'operation_number': row['Operation Number'] if pd.notna(row['Operation Number']) else ''
            }
            projects.append(project)
        
        print(f"Loaded {len(projects)} projects")
        return projects
    
    def search_project_documents_advanced(self, project_number, project_name):
        """Advanced search for documents using multiple strategies."""
        print(f"Advanced search for project {project_number}: {project_name}")
        
        documents_found = []
        
        # Strategy 1: Try IDB's project search API
        api_docs = self.search_idb_api(project_number, project_name)
        documents_found.extend(api_docs)
        
        # Strategy 2: Try direct project URLs with different patterns
        direct_docs = self.try_direct_project_urls(project_number)
        documents_found.extend(direct_docs)
        
        # Strategy 3: Search IDB's document repository
        repo_docs = self.search_document_repository(project_number, project_name)
        documents_found.extend(repo_docs)
        
        # Strategy 4: Try Google search for IDB documents
        google_docs = self.search_google_for_idb_docs(project_number, project_name)
        documents_found.extend(google_docs)
        
        return documents_found
    
    def search_idb_api(self, project_number, project_name):
        """Search IDB's API for project documents."""
        documents = []
        
        # Try different API endpoints
        api_endpoints = [
            f"{self.base_url}/api/projects/{project_number}/documents",
            f"{self.base_url}/api/projects/{project_number}",
            f"{self.base_url}/api/search?q={quote(project_number)}&type=document"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        docs = self.extract_docs_from_api_response(data, project_number)
                        documents.extend(docs)
                    except json.JSONDecodeError:
                        # Not JSON, try to extract from HTML
                        docs = self.extract_document_links(response.text, project_number)
                        documents.extend(docs)
            except Exception as e:
                print(f"API search error for {endpoint}: {e}")
        
        return documents
    
    def try_direct_project_urls(self, project_number):
        """Try different URL patterns for project pages."""
        documents = []
        
        # Different URL patterns to try
        url_patterns = [
            f"{self.base_url}/en/projects/{project_number}",
            f"{self.base_url}/projects/{project_number}",
            f"{self.base_url}/en/project/{project_number}",
            f"{self.base_url}/project/{project_number}",
            f"{self.base_url}/en/operations/{project_number}",
            f"{self.base_url}/operations/{project_number}"
        ]
        
        for url in url_patterns:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    docs = self.extract_document_links(response.text, project_number)
                    documents.extend(docs)
                    print(f"Found {len(docs)} documents at {url}")
            except Exception as e:
                print(f"Error accessing {url}: {e}")
        
        return documents
    
    def search_document_repository(self, project_number, project_name):
        """Search IDB's document repository."""
        documents = []
        
        # Try IDB's document search
        search_urls = [
            f"{self.base_url}/en/search?q={quote(project_number)}",
            f"{self.base_url}/en/documents?q={quote(project_number)}",
            f"{self.base_url}/en/publications?q={quote(project_number)}"
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    docs = self.extract_document_links(response.text, project_number)
                    documents.extend(docs)
            except Exception as e:
                print(f"Repository search error for {url}: {e}")
        
        return documents
    
    def search_google_for_idb_docs(self, project_number, project_name):
        """Search Google for IDB documents (simulated)."""
        documents = []
        
        # This would require Google Search API or web scraping
        # For now, we'll simulate by trying common document patterns
        common_doc_patterns = [
            f"https://publications.iadb.org/publications/english/document/{project_number}",
            f"https://publications.iadb.org/en/document/{project_number}",
            f"https://www.iadb.org/en/projects/{project_number}/documents"
        ]
        
        for url in common_doc_patterns:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    docs = self.extract_document_links(response.text, project_number)
                    documents.extend(docs)
            except Exception as e:
                print(f"Google search simulation error for {url}: {e}")
        
        return documents
    
    def extract_docs_from_api_response(self, data, project_number):
        """Extract document information from API response."""
        documents = []
        
        # Handle different API response structures
        if isinstance(data, dict):
            # Look for documents in the response
            if 'documents' in data:
                for doc in data['documents']:
                    if isinstance(doc, dict):
                        doc_url = doc.get('url') or doc.get('link') or doc.get('file')
                        if doc_url:
                            doc_type = self.classify_document(doc_url)
                            documents.append({
                                'url': doc_url,
                                'type': doc_type,
                                'project_number': project_number
                            })
            
            # Also check for direct document links
            if 'files' in data:
                for file_info in data['files']:
                    if isinstance(file_info, dict):
                        file_url = file_info.get('url') or file_info.get('link')
                        if file_url:
                            doc_type = self.classify_document(file_url)
                            documents.append({
                                'url': file_url,
                                'type': doc_type,
                                'project_number': project_number
                            })
        
        return documents
    
    def extract_document_links(self, html_content, project_number):
        """Extract document links from HTML content."""
        documents = []
        
        # Look for common document patterns
        patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*loan[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*proposal[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*abstract[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*project[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*document[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*report[^"\']*\.pdf[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(self.base_url, match)
                elif match.startswith('http'):
                    full_url = match
                else:
                    full_url = urljoin(self.base_url, '/' + match)
                
                doc_type = self.classify_document(full_url)
                documents.append({
                    'url': full_url,
                    'type': doc_type,
                    'project_number': project_number
                })
        
        return documents
    
    def classify_document(self, url):
        """Classify document type based on URL or filename."""
        url_lower = url.lower()
        
        if 'loan' in url_lower and 'proposal' in url_lower:
            return 'Loan Proposal Document'
        elif 'proposal' in url_lower:
            return 'Project Proposal Document'
        elif 'abstract' in url_lower:
            return 'Project Abstract Document'
        elif 'project' in url_lower:
            return 'Project Document'
        elif 'loan' in url_lower:
            return 'Loan Document'
        else:
            return 'Other Document'
    
    def download_document(self, document, country):
        """Download a document and save it to the appropriate country folder."""
        try:
            response = self.session.get(document['url'], timeout=30)
            if response.status_code == 200:
                # Check if it's actually a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and not document['url'].lower().endswith('.pdf'):
                    print(f"Skipping non-PDF document: {document['url']}")
                    return None
                
                # Create country directory
                country_dir = self.downloads_dir / self.sanitize_filename(country)
                country_dir.mkdir(exist_ok=True)
                
                # Create filename
                filename = f"{document['project_number']}_{document['type'].replace(' ', '_')}.pdf"
                filename = self.sanitize_filename(filename)
                
                filepath = country_dir / filename
                
                # Save the document
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Downloaded: {filepath}")
                return str(filepath)
            else:
                print(f"Failed to download {document['url']}: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading {document['url']}: {e}")
            return None
    
    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename
    
    def create_tracking_csv(self, projects_data):
        """Create a CSV file to track document availability for each project."""
        tracking_data = []
        
        for project in projects_data:
            tracking_row = {
                'Project_Number': project['project_number'],
                'Project_Name': project['project_name'],
                'Country': project['country'],
                'Approval_Date': project['approval_date'],
                'Status': project['status'],
                'Documents_Found': '; '.join([doc['type'] for doc in project.get('documents', [])]),
                'Documents_Downloaded': '; '.join([doc.get('local_path', '') for doc in project.get('documents', []) if doc.get('local_path')]),
                'Total_Documents': len(project.get('documents', []))
            }
            tracking_data.append(tracking_row)
        
        # Write to CSV
        with open(self.tracking_file, 'w', newline='', encoding='utf-8') as f:
            if tracking_data:
                fieldnames = tracking_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tracking_data)
        
        print(f"Tracking CSV created: {self.tracking_file}")
    
    def process_projects(self, csv_file, max_projects=None):
        """Main processing function."""
        # Load project data
        projects = self.load_project_data(csv_file)
        
        if max_projects:
            projects = projects[:max_projects]
        
        # Process each project
        for i, project in enumerate(projects, 1):
            print(f"\nProcessing project {i}/{len(projects)}: {project['project_number']}")
            
            # Search for documents
            documents = self.search_project_documents_advanced(project['project_number'], project['project_name'])
            project['documents'] = documents
            
            # Download documents if found
            if documents:
                print(f"Found {len(documents)} documents")
                for doc in documents:
                    local_path = self.download_document(doc, project['country'])
                    if local_path:
                        doc['local_path'] = local_path
            else:
                print("No documents found")
            
            # Be respectful to the server
            time.sleep(2)
        
        # Create tracking CSV
        self.create_tracking_csv(projects)
        
        return projects

def main():
    """Main function."""
    researcher = IDBDocumentResearchV2()
    
    # Process projects (limit to first 5 for testing)
    projects = researcher.process_projects("IDB Corpus Key Words.csv", max_projects=5)
    
    print(f"\nProcessing complete. Processed {len(projects)} projects.")
    print(f"Check the '{researcher.downloads_dir}' directory for downloaded documents.")
    print(f"Check '{researcher.tracking_file}' for the tracking report.")

if __name__ == "__main__":
    main()

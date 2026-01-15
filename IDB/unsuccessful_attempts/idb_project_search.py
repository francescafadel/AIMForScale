#!/usr/bin/env python3
"""
IDB Project Search Script
This script uses IDB's project search functionality to find project documents.
"""

import pandas as pd
import requests
import time
import csv
from urllib.parse import urljoin, quote
import re
from pathlib import Path
import json

class IDBProjectSearch:
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
        self.tracking_file = "document_tracking_search.csv"
        
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
    
    def search_project_using_search_page(self, project_number, project_name):
        """Search for project using IDB's project search page."""
        print(f"Searching for project {project_number} using IDB search...")
        
        documents_found = []
        
        # First, get the search page to understand its structure
        search_url = f"{self.base_url}/en/project-search"
        
        try:
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                print("Search page accessed successfully")
                
                # Look for search forms and understand the structure
                search_forms = re.findall(r'<form[^>]*>', response.text, re.IGNORECASE)
                print(f"Found {len(search_forms)} search forms")
                
                # Try to find project by searching
                search_results = self.perform_project_search(project_number, project_name)
                documents_found.extend(search_results)
                
            else:
                print(f"Failed to access search page: {response.status_code}")
                
        except Exception as e:
            print(f"Error accessing search page: {e}")
        
        return documents_found
    
    def perform_project_search(self, project_number, project_name):
        """Perform a search for the project and extract document links."""
        documents = []
        
        # Try different search strategies
        search_terms = [
            project_number,
            f'"{project_number}"',
            project_name[:30] if project_name else project_number
        ]
        
        for term in search_terms:
            try:
                # Try to search using the project search page
                search_url = f"{self.base_url}/en/project-search"
                
                # Prepare search parameters (this might need to be adjusted based on the actual form)
                search_params = {
                    'q': term,
                    'search': 'Search'
                }
                
                response = self.session.post(search_url, data=search_params, timeout=10)
                
                if response.status_code == 200:
                    # Extract document links from search results
                    doc_links = self.extract_document_links_from_search(response.text, project_number)
                    documents.extend(doc_links)
                    
                    # Also look for project detail links
                    project_links = self.extract_project_links(response.text, project_number)
                    
                    # Follow project links to find documents
                    for project_link in project_links:
                        project_docs = self.extract_documents_from_project_page(project_link, project_number)
                        documents.extend(project_docs)
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"Search error for term '{term}': {e}")
        
        return documents
    
    def extract_document_links_from_search(self, html_content, project_number):
        """Extract document links from search results page."""
        documents = []
        
        # Look for PDF links in search results
        pdf_patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*loan[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*proposal[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*abstract[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*project[^"\']*\.pdf[^"\']*)["\']'
        ]
        
        for pattern in pdf_patterns:
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
    
    def extract_project_links(self, html_content, project_number):
        """Extract links to project detail pages from search results."""
        project_links = []
        
        # Look for project links
        project_patterns = [
            r'href=["\']([^"\']*project[^"\']*)["\']',
            r'href=["\']([^"\']*operation[^"\']*)["\']',
            r'href=["\']([^"\']*{project_number}[^"\']*)["\']'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(self.base_url, match)
                elif match.startswith('http'):
                    full_url = match
                else:
                    full_url = urljoin(self.base_url, '/' + match)
                
                project_links.append(full_url)
        
        return list(set(project_links))  # Remove duplicates
    
    def extract_documents_from_project_page(self, project_url, project_number):
        """Extract documents from a project detail page."""
        documents = []
        
        try:
            response = self.session.get(project_url, timeout=10)
            if response.status_code == 200:
                doc_links = self.extract_document_links_from_search(response.text, project_number)
                documents.extend(doc_links)
                print(f"Found {len(doc_links)} documents on project page: {project_url}")
            else:
                print(f"Failed to access project page {project_url}: {response.status_code}")
                
        except Exception as e:
            print(f"Error accessing project page {project_url}: {e}")
        
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
            
            # Search for documents using IDB search
            documents = self.search_project_using_search_page(project['project_number'], project['project_name'])
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
            time.sleep(3)
        
        # Create tracking CSV
        self.create_tracking_csv(projects)
        
        return projects

def main():
    """Main function."""
    searcher = IDBProjectSearch()
    
    # Process projects (limit to first 3 for testing)
    projects = searcher.process_projects("IDB Corpus Key Words.csv", max_projects=3)
    
    print(f"\nProcessing complete. Processed {len(projects)} projects.")
    print(f"Check the '{searcher.downloads_dir}' directory for downloaded documents.")
    print(f"Check '{searcher.tracking_file}' for the tracking report.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
IDB Document Research Script
This script processes IDB project data and searches for loan proposal documents or project proposal documents.
"""

import pandas as pd
import os
import requests
import time
import csv
from urllib.parse import urljoin, quote
import re
from pathlib import Path

class IDBDocumentResearch:
    def __init__(self):
        self.base_url = "https://www.iadb.org"
        self.projects_url = "https://www.iadb.org/en/projects"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories for organizing downloads
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # CSV tracking file
        self.tracking_file = "document_tracking.csv"
        
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
    
    def search_project_documents(self, project_number, project_name):
        """Search for documents related to a specific project."""
        print(f"Searching for documents for project {project_number}: {project_name}")
        
        documents_found = []
        
        # Search strategies:
        # 1. Direct project page
        # 2. Search functionality
        # 3. Document repository
        
        # Strategy 1: Try direct project URL
        project_url = f"{self.base_url}/en/projects/{project_number}"
        try:
            response = self.session.get(project_url, timeout=10)
            if response.status_code == 200:
                # Look for document links
                doc_links = self.extract_document_links(response.text, project_number)
                documents_found.extend(doc_links)
        except Exception as e:
            print(f"Error accessing project page: {e}")
        
        # Strategy 2: Search for project documents
        search_results = self.search_project_in_documents(project_number, project_name)
        documents_found.extend(search_results)
        
        return documents_found
    
    def extract_document_links(self, html_content, project_number):
        """Extract document links from HTML content."""
        documents = []
        
        # Look for common document patterns
        patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*loan[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*proposal[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*abstract[^"\']*\.pdf[^"\']*)["\']',
            r'href=["\']([^"\']*project[^"\']*\.pdf[^"\']*)["\']'
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
        else:
            return 'Other Document'
    
    def search_project_in_documents(self, project_number, project_name):
        """Search for project documents using IDB's search functionality."""
        documents = []
        
        # Search terms to try
        search_terms = [
            project_number,
            f'"{project_number}"',
            project_name[:50] if project_name else project_number
        ]
        
        for term in search_terms:
            try:
                search_url = f"{self.base_url}/en/search"
                params = {
                    'q': term,
                    'type': 'document'
                }
                
                response = self.session.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    # Extract document links from search results
                    doc_links = self.extract_document_links(response.text, project_number)
                    documents.extend(doc_links)
                
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                print(f"Error searching for {term}: {e}")
        
        return documents
    
    def download_document(self, document, country):
        """Download a document and save it to the appropriate country folder."""
        try:
            response = self.session.get(document['url'], timeout=30)
            if response.status_code == 200:
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
            documents = self.search_project_documents(project['project_number'], project['project_name'])
            project['documents'] = documents
            
            # Download documents if found
            if documents:
                print(f"Found {len(documents)} documents")
                for doc in documents:
                    # Only download English documents (we'll need to check content)
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
    researcher = IDBDocumentResearch()
    
    # Process projects (limit to first 10 for testing)
    projects = researcher.process_projects("IDB Corpus Key Words.csv", max_projects=10)
    
    print(f"\nProcessing complete. Processed {len(projects)} projects.")
    print(f"Check the '{researcher.downloads_dir}' directory for downloaded documents.")
    print(f"Check '{researcher.tracking_file}' for the tracking report.")

if __name__ == "__main__":
    main()
sh p twn
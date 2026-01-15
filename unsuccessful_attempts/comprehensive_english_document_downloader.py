#!/usr/bin/env python3
"""
Comprehensive English Document Downloader for IDB Projects
This script downloads only English versions of Loan Proposal Documents, Project Proposal Documents, 
and Project Abstract Documents for all projects in the dataset, but only if they are publicly accessible.
"""

import pandas as pd
import requests
import time
import re
from pathlib import Path
import urllib3
from urllib.parse import urljoin
import csv

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ComprehensiveEnglishDocumentDownloader:
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
        
        # Tracking file
        self.tracking_file = "english_document_tracking.csv"
        
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
                'operation_number': row['Operation Number'] if pd.notna(row['Operation Number']) else '',
                'project_type': row['Project Type'] if pd.notna(row['Project Type']) else ''
            }
            projects.append(project)
        
        print(f"Loaded {len(projects)} projects")
        return projects
    
    def get_project_page(self, project_number):
        """Get the project page for a specific project."""
        # Try different URL patterns for the project page
        project_urls = [
            f"{self.base_url}/en/project/{project_number}",
            f"{self.base_url}/en/projects/{project_number}",
            f"{self.base_url}/projects/{project_number}"
        ]
        
        for url in project_urls:
            try:
                response = self.session.get(url, timeout=30, verify=False)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                continue
        
        return None
    
    def extract_document_urls(self, html_content, project_number):
        """Extract document URLs from the project page HTML, focusing on English documents only."""
        documents = []
        
        if not html_content:
            return documents
        
        # Look for document card patterns
        doc_patterns = [
            r'<idb-document-card[^>]*url="([^"]*)"[^>]*>.*?<div slot="heading">([^<]*)</div>.*?<div slot="cta">([^<]*)</div>',
            r'url="([^"]*document\.cfm[^"]*)"[^>]*>.*?<div slot="heading">([^<]*)</div>.*?<div slot="cta">([^<]*)</div>'
        ]
        
        for pattern in doc_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:
                    url = match[0]
                    title = match[1].strip()
                    language = match[2].strip()
                    
                    # Only process English documents
                    if 'english' in language.lower() or 'en' in language.lower():
                        doc_type = self.classify_document_type(title, project_number)
                        
                        if doc_type:  # Only include if it's one of the requested document types
                            documents.append({
                                'url': url,
                                'title': title,
                                'language': 'English',
                                'type': doc_type,
                                'project_number': project_number
                            })
        
        # Remove duplicates
        unique_docs = []
        seen_urls = set()
        for doc in documents:
            if doc['url'] not in seen_urls:
                unique_docs.append(doc)
                seen_urls.add(doc['url'])
        
        return unique_docs
    
    def classify_document_type(self, title, project_number):
        """Classify document type based on title and project number."""
        title_lower = title.lower()
        project_lower = project_number.lower()
        
        # Look for Loan Proposal Documents
        if any(keyword in title_lower for keyword in ['loan', 'proposal', 'loan proposal']):
            return 'Loan Proposal Document'
        
        # Look for Project Proposal Documents
        if any(keyword in title_lower for keyword in ['project proposal', 'proposal document']):
            return 'Project Proposal Document'
        
        # Look for Project Abstract Documents
        if any(keyword in title_lower for keyword in ['abstract', 'synthesis', 'syntheis', 'tc abstract']):
            return 'Project Abstract Document'
        
        # Look for project-specific patterns
        if project_lower in title_lower:
            if 'abstract' in title_lower:
                return 'Project Abstract Document'
            elif 'proposal' in title_lower:
                return 'Project Proposal Document'
        
        return None  # Not one of the requested document types
    
    def download_document(self, document):
        """Download a single document."""
        try:
            print(f"   Requesting document from: {document['url']}")
            
            response = self.session.get(document['url'], timeout=30, verify=False, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/pdf' in content_type:
                    # Create country directory
                    country = self.get_country_from_project(document['project_number'])
                    country_dir = self.downloads_dir / self.sanitize_filename(country)
                    country_dir.mkdir(exist_ok=True)
                    
                    # Create filename
                    filename = f"{document['project_number']}_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                    filename = self.sanitize_filename(filename)
                    
                    filepath = country_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   ✓ Saved as: {filename}")
                    return str(filepath)
                    
                elif 'text/html' in content_type:
                    # Check if this is a redirect page
                    print(f"   Received HTML response, checking for redirect...")
                    
                    # Look for PDF links or redirects
                    pdf_patterns = [
                        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                        r'window\.location\.href\s*=\s*["\']([^"\']*)["\']',
                        r'location\.href\s*=\s*["\']([^"\']*)["\']'
                    ]
                    
                    for pattern in pdf_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        for match in matches:
                            if '.pdf' in match.lower():
                                pdf_url = match if match.startswith('http') else f"{self.base_url}{match}"
                                print(f"   Found PDF URL: {pdf_url}")
                                
                                # Try to download the PDF
                                pdf_response = self.session.get(pdf_url, timeout=30, verify=False)
                                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', '').lower():
                                    # Create country directory
                                    country = self.get_country_from_project(document['project_number'])
                                    country_dir = self.downloads_dir / self.sanitize_filename(country)
                                    country_dir.mkdir(exist_ok=True)
                                    
                                    # Create filename
                                    filename = f"{document['project_number']}_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                                    filename = self.sanitize_filename(filename)
                                    
                                    filepath = country_dir / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(pdf_response.content)
                                    
                                    print(f"   ✓ Saved as: {filename}")
                                    return str(filepath)
                    
                    print(f"   Could not extract PDF URL from HTML response")
                    return None
                    
                else:
                    print(f"   Unexpected content type: {content_type}")
                    return None
                    
            else:
                print(f"   HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   Error downloading: {e}")
            return None
    
    def get_country_from_project(self, project_number):
        """Get country from project number or use a default."""
        # Extract country code from project number (e.g., PE-L1187 -> Peru)
        country_codes = {
            'PE': 'Peru',
            'CO': 'Colombia',
            'AR': 'Argentina',
            'BR': 'Brazil',
            'MX': 'Mexico',
            'CL': 'Chile',
            'BO': 'Bolivia',
            'EC': 'Ecuador',
            'PY': 'Paraguay',
            'UY': 'Uruguay',
            'VE': 'Venezuela',
            'GT': 'Guatemala',
            'HN': 'Honduras',
            'SV': 'El Salvador',
            'NI': 'Nicaragua',
            'CR': 'Costa Rica',
            'PA': 'Panama',
            'DO': 'Dominican Republic',
            'JM': 'Jamaica',
            'TT': 'Trinidad and Tobago',
            'BB': 'Barbados',
            'GY': 'Guyana',
            'SR': 'Suriname',
            'HT': 'Haiti',
            'RG': 'Regional'
        }
        
        country_code = project_number.split('-')[0] if '-' in project_number else 'Unknown'
        return country_codes.get(country_code, 'Unknown')
    
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
                'Project_Type': project['project_type'],
                'Approval_Date': project['approval_date'],
                'Status': project['status'],
                'Loan_Proposal_Document': 'No',
                'Project_Proposal_Document': 'No',
                'Project_Abstract_Document': 'No',
                'Documents_Found': '; '.join([doc['type'] for doc in project.get('documents', [])]),
                'Documents_Downloaded': '; '.join([doc.get('local_path', '') for doc in project.get('documents', []) if doc.get('local_path')]),
                'Total_Documents': len(project.get('documents', []))
            }
            
            # Mark which document types were found
            for doc in project.get('documents', []):
                if doc['type'] == 'Loan Proposal Document':
                    tracking_row['Loan_Proposal_Document'] = 'Yes'
                elif doc['type'] == 'Project Proposal Document':
                    tracking_row['Project_Proposal_Document'] = 'Yes'
                elif doc['type'] == 'Project Abstract Document':
                    tracking_row['Project_Abstract_Document'] = 'Yes'
            
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
        
        total_documents_found = 0
        total_documents_downloaded = 0
        
        # Process each project
        for i, project in enumerate(projects, 1):
            print(f"\nProcessing project {i}/{len(projects)}: {project['project_number']}")
            print(f"Project: {project['project_name']}")
            print(f"Country: {project['country']}")
            print(f"Type: {project['project_type']}")
            
            # Get project page
            html_content = self.get_project_page(project['project_number'])
            
            if html_content:
                # Extract document URLs
                documents = self.extract_document_urls(html_content, project['project_number'])
                project['documents'] = documents
                
                if documents:
                    print(f"Found {len(documents)} English documents of requested types:")
                    for doc in documents:
                        print(f"  - {doc['type']}: {doc['title']}")
                    
                    # Download documents
                    downloaded_count = 0
                    for doc in documents:
                        local_path = self.download_document(doc)
                        if local_path:
                            doc['local_path'] = local_path
                            downloaded_count += 1
                    
                    total_documents_found += len(documents)
                    total_documents_downloaded += downloaded_count
                    
                    print(f"Downloaded {downloaded_count}/{len(documents)} documents")
                else:
                    print("No English documents of requested types found")
                    project['documents'] = []
            else:
                print("Could not access project page")
                project['documents'] = []
            
            # Be respectful to the server
            time.sleep(2)
        
        # Create tracking CSV
        self.create_tracking_csv(projects)
        
        print(f"\n" + "=" * 80)
        print(f"FINAL SUMMARY")
        print(f"=" * 80)
        print(f"Projects processed: {len(projects)}")
        print(f"Total English documents found: {total_documents_found}")
        print(f"Total documents downloaded: {total_documents_downloaded}")
        print(f"Success rate: {(total_documents_downloaded/total_documents_found*100):.1f}%" if total_documents_found > 0 else "No documents found")
        print(f"Check '{self.tracking_file}' for detailed tracking information")
        
        return projects

def main():
    """Main function."""
    downloader = ComprehensiveEnglishDocumentDownloader()
    
    # Process all projects (or limit for testing)
    projects = downloader.process_projects("IDB Corpus Key Words.csv", max_projects=None)
    
    print(f"\nProcessing complete. Processed {len(projects)} projects.")
    print(f"Check the '{downloader.downloads_dir}' directory for downloaded documents.")
    print(f"Check '{downloader.tracking_file}' for the tracking report.")

if __name__ == "__main__":
    main()

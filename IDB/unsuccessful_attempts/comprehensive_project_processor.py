#!/usr/bin/env python3
"""
Comprehensive Project Processor
This script processes all IDB projects, identifies available documents, and creates a tracking CSV.
"""

import pandas as pd
import requests
import time
from urllib.parse import urljoin, quote, urlparse
import re
from pathlib import Path
import os
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ComprehensiveProjectProcessor:
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
        
        # Disable SSL verification
        self.session.verify = False
        
        # Create downloads directory
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Tracking data
        self.tracking_data = []
        
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
    
    def check_project_documents(self, project):
        """Check if documents are available for a project."""
        project_number = project['project_number']
        project_url = f"{self.base_url}/en/project/{project_number}"
        
        print(f"  Checking: {project_number}")
        
        try:
            response = self.session.get(project_url, timeout=15)
            
            if response.status_code == 200:
                # Parse the page to look for documents
                documents = self.extract_documents_from_page(response.text, project)
                
                if documents:
                    print(f"    ✓ Found {len(documents)} documents")
                    return {
                        'project_number': project_number,
                        'project_name': project['project_name'],
                        'country': project['country'],
                        'operation_number': project['operation_number'],
                        'documents_found': len(documents),
                        'document_types': [doc['type'] for doc in documents],
                        'languages': [doc['language'] for doc in documents],
                        'document_urls': [doc['url'] for doc in documents],
                        'status': 'Documents Available',
                        'project_url': project_url
                    }
                else:
                    print(f"    ✗ No documents found")
                    return {
                        'project_number': project_number,
                        'project_name': project['project_name'],
                        'country': project['country'],
                        'operation_number': project['operation_number'],
                        'documents_found': 0,
                        'document_types': [],
                        'languages': [],
                        'document_urls': [],
                        'status': 'No Documents Found',
                        'project_url': project_url
                    }
            else:
                print(f"    ✗ Project page not accessible: {response.status_code}")
                return {
                    'project_number': project_number,
                    'project_name': project['project_name'],
                    'country': project['country'],
                    'operation_number': project['operation_number'],
                    'documents_found': 0,
                    'document_types': [],
                    'languages': [],
                    'document_urls': [],
                    'status': 'Project Page Not Accessible',
                    'project_url': project_url
                }
                
        except Exception as e:
            print(f"    ✗ Error checking project: {e}")
            return {
                'project_number': project_number,
                'project_name': project['project_name'],
                'country': project['country'],
                'operation_number': project['operation_number'],
                'documents_found': 0,
                'document_types': [],
                'languages': [],
                'document_urls': [],
                'status': f'Error: {str(e)[:50]}',
                'project_url': project_url
            }
    
    def extract_documents_from_page(self, html_content, project):
        """Extract documents from a project page."""
        documents = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for "Preparation Phase" section
        preparation_section = self.find_preparation_phase_section(soup)
        
        if preparation_section:
            # Extract TC Abstract documents from this section
            documents = self.extract_tc_abstract_documents(preparation_section, project)
        else:
            # Fallback: look for any TC Abstract documents on the page
            documents = self.extract_tc_abstract_documents(soup, project)
        
        return documents
    
    def find_preparation_phase_section(self, soup):
        """Find the Preparation Phase section in the HTML."""
        # Look for text containing "Preparation Phase"
        for element in soup.find_all(string=re.compile(r'Preparation Phase', re.IGNORECASE)):
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
                    title = 'TC Abstract Document (Spanish)'
                elif '1121147323-5' in url:
                    language = 'English'
                    title = 'TC Abstract Document (English)'
                else:
                    language = 'Unknown'
                    title = 'TC Abstract Document'
                
                documents.append({
                    'url': url,
                    'type': 'TC Abstract Document',
                    'language': language,
                    'title': title
                })
        
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
                    'type': doc_type,
                    'language': language,
                    'title': link_text
                })
        
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
    
    def process_projects(self, projects, start_index=0, end_index=None):
        """Process projects and check for available documents."""
        if end_index is None:
            end_index = len(projects)
        
        print(f"\nProcessing projects {start_index + 1} to {end_index} of {len(projects)}...")
        
        for i in range(start_index, end_index):
            project = projects[i]
            print(f"\nProcessing project {i+1}/{len(projects)}: {project['project_number']}")
            
            # Check for documents
            result = self.check_project_documents(project)
            self.tracking_data.append(result)
            
            # Save progress every 10 projects
            if (i + 1) % 10 == 0:
                self.save_tracking_data()
                print(f"\nProgress saved: {i + 1} projects processed")
            
            # Be respectful with delays
            time.sleep(1)
        
        return self.tracking_data
    
    def save_tracking_data(self):
        """Save tracking data to CSV."""
        df = pd.DataFrame(self.tracking_data)
        df.to_csv("comprehensive_document_tracking.csv", index=False)
        print(f"Tracking data saved to comprehensive_document_tracking.csv")
    
    def generate_summary_report(self):
        """Generate a summary report of findings."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("COMPREHENSIVE DOCUMENT ANALYSIS SUMMARY")
        print("="*80)
        
        total_projects = len(df)
        projects_with_documents = len(df[df['documents_found'] > 0])
        projects_accessible = len(df[df['status'] == 'Documents Available']) + len(df[df['status'] == 'No Documents Found'])
        
        print(f"Total Projects Analyzed: {total_projects}")
        print(f"Projects with Documents: {projects_with_documents}")
        print(f"Projects Accessible: {projects_accessible}")
        print(f"Projects Not Accessible: {total_projects - projects_accessible}")
        
        if projects_with_documents > 0:
            print(f"\nDocument Types Found:")
            all_types = []
            for types in df[df['documents_found'] > 0]['document_types']:
                all_types.extend(types)
            
            type_counts = pd.Series(all_types).value_counts()
            for doc_type, count in type_counts.items():
                print(f"  {doc_type}: {count}")
            
            print(f"\nLanguages Available:")
            all_languages = []
            for languages in df[df['documents_found'] > 0]['languages']:
                all_languages.extend(languages)
            
            language_counts = pd.Series(all_languages).value_counts()
            for language, count in language_counts.items():
                print(f"  {language}: {count}")
        
        print(f"\nStatus Summary:")
        status_counts = df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Save summary to file
        with open("document_analysis_summary.txt", "w") as f:
            f.write("COMPREHENSIVE DOCUMENT ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Projects Analyzed: {total_projects}\n")
            f.write(f"Projects with Documents: {projects_with_documents}\n")
            f.write(f"Projects Accessible: {projects_accessible}\n")
            f.write(f"Projects Not Accessible: {total_projects - projects_accessible}\n\n")
            
            if projects_with_documents > 0:
                f.write("Document Types Found:\n")
                for doc_type, count in type_counts.items():
                    f.write(f"  {doc_type}: {count}\n")
                
                f.write("\nLanguages Available:\n")
                for language, count in language_counts.items():
                    f.write(f"  {language}: {count}\n")
            
            f.write(f"\nStatus Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count}\n")
        
        print(f"\nSummary report saved to document_analysis_summary.txt")

def main():
    processor = ComprehensiveProjectProcessor()
    
    # Load project data
    projects = processor.load_project_data("IDB Corpus Key Words.csv")
    
    # Test with first 10 projects
    print("\nTesting with first 10 projects...")
    test_results = processor.process_projects(projects, 0, 10)
    
    if test_results:
        processor.save_tracking_data()
        processor.generate_summary_report()
        
        # Ask user if they want to continue with all projects
        response = input("\nDo you want to continue with all projects? (y/n): ")
        if response.lower() == 'y':
            print("\nProcessing all projects...")
            all_results = processor.process_projects(projects)
            processor.save_tracking_data()
            processor.generate_summary_report()
            
            print(f"\n=== PROCESSING COMPLETE ===")
            print(f"Results saved to: comprehensive_document_tracking.csv")
            print(f"Summary saved to: document_analysis_summary.txt")
        else:
            print("Processing stopped after test run.")
    else:
        print("No results obtained from test run.")

if __name__ == "__main__":
    main()

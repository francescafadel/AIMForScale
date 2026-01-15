#!/usr/bin/env python3
"""
Robust IDB Document Downloader
==============================
A more efficient and reliable approach to download IDB project documents
using direct HTTP requests with proper session management and retry logic.
"""

import pandas as pd
import requests
import time
import re
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
import urllib3
from bs4 import BeautifulSoup
import ssl
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RobustIDBDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create a robust session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Disable SSL verification for problematic servers
        self.session.verify = False
        
        # Tracking data
        self.tracking_data = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def load_project_data(self, csv_file):
        """Load project data from CSV file."""
        try:
            print(f"Loading project data from {csv_file}...")
            df = pd.read_csv(csv_file, skiprows=1)  # Skip the methodology header row
            projects = df.to_dict('records')
            print(f"Loaded {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"Error loading project data: {e}")
            return []
    
    def get_project_page(self, project_number, max_retries=3):
        """Get project page with retry logic."""
        url = f"https://www.iadb.org/en/project/{project_number}"
        
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}: Fetching {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    print(f"  ✗ Project page not found (404)")
                    return None
                else:
                    print(f"  ✗ HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
    
    def extract_document_links(self, html_content):
        """Extract document links from project page."""
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            documents = []
            
            # Look for document cards
            document_cards = soup.find_all('idb-document-card')
            
            for card in document_cards:
                try:
                    # Extract document information
                    doc_link = card.get('href') or card.get('data-href')
                    if doc_link:
                        # Get document title
                        title_elem = card.find('h3') or card.find('h4') or card.find('div', class_='title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown Document"
                        
                        # Get document type
                        type_elem = card.find('span', class_='type') or card.find('div', class_='document-type')
                        doc_type = type_elem.get_text(strip=True) if type_elem else "Unknown"
                        
                        documents.append({
                            'url': doc_link,
                            'title': title,
                            'type': doc_type
                        })
                        
                except Exception as e:
                    print(f"    Error parsing document card: {e}")
                    continue
            
            # Also look for direct links in the page
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and 'document.cfm' in href:
                    title = link.get_text(strip=True) or "Document"
                    documents.append({
                        'url': href,
                        'title': title,
                        'type': 'Document'
                    })
            
            return documents
            
        except Exception as e:
            print(f"  Error extracting documents: {e}")
            return []
    
    def download_document(self, doc_info, project_number, country):
        """Download a single document."""
        try:
            doc_url = doc_info['url']
            if not doc_url.startswith('http'):
                doc_url = urljoin('https://www.iadb.org', doc_url)
            
            print(f"    Downloading: {doc_info['title']}")
            
            # Get the document page first
            response = self.session.get(doc_url, timeout=30)
            if response.status_code != 200:
                print(f"      ✗ Failed to access document page: {response.status_code}")
                return False
            
            # Look for direct download link
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find download button or link
            download_link = None
            
            # Look for various download button patterns
            download_selectors = [
                'a[href*=".pdf"]',
                'a[href*=".docx"]',
                'a[href*=".doc"]',
                'a[download]',
                'button[onclick*="download"]',
                '.download-button a',
                '.download-link'
            ]
            
            for selector in download_selectors:
                link = soup.select_one(selector)
                if link:
                    download_link = link.get('href')
                    break
            
            # If no direct link found, try to extract from JavaScript
            if not download_link:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Look for download URLs in JavaScript
                        matches = re.findall(r'["\']([^"\']*\.(?:pdf|docx|doc))["\']', script.string)
                        if matches:
                            download_link = matches[0]
                            break
            
            if download_link:
                if not download_link.startswith('http'):
                    download_link = urljoin('https://www.iadb.org', download_link)
                
                # Download the file
                file_response = self.session.get(download_link, timeout=60, stream=True)
                if file_response.status_code == 200:
                    # Determine file extension
                    content_type = file_response.headers.get('content-type', '')
                    if 'pdf' in content_type.lower():
                        ext = '.pdf'
                    elif 'word' in content_type.lower() or 'docx' in content_type.lower():
                        ext = '.docx'
                    elif 'doc' in content_type.lower():
                        ext = '.doc'
                    else:
                        ext = '.pdf'  # Default
                    
                    # Create filename
                    safe_title = re.sub(r'[^\w\s-]', '', doc_info['title']).strip()
                    safe_title = re.sub(r'[-\s]+', '-', safe_title)
                    filename = f"{project_number}_{safe_title}{ext}"
                    
                    # Create country directory
                    country_dir = self.downloads_dir / country
                    country_dir.mkdir(exist_ok=True)
                    
                    # Save file
                    file_path = country_dir / filename
                    with open(file_path, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"      ✓ Downloaded: {filename}")
                    return True
                else:
                    print(f"      ✗ Download failed: {file_response.status_code}")
                    return False
            else:
                print(f"      ✗ No download link found")
                return False
                
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
    def process_project(self, project):
        """Process a single project."""
        project_number = project['Project Number']
        project_name = project['Project Name']
        country = project['Project Country']
        
        print(f"\nProcessing project {self.processed_count + 1}: {project_number}")
        print(f"  Project: {project_name}")
        print(f"  Country: {country}")
        
        # Get project page
        html_content = self.get_project_page(project_number)
        
        if not html_content:
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': country,
                'operation_number': project.get('Operation Number', ''),
                'documents_found': 0,
                'documents_downloaded': 0,
                'status': 'Project Page Not Accessible',
                'project_url': f"https://www.iadb.org/en/project/{project_number}"
            }
        
        # Extract document links
        documents = self.extract_document_links(html_content)
        
        if not documents:
            return {
                'project_number': project_number,
                'project_name': project_name,
                'country': country,
                'operation_number': project.get('Operation Number', ''),
                'documents_found': 0,
                'documents_downloaded': 0,
                'status': 'No Documents Found',
                'project_url': f"https://www.iadb.org/en/project/{project_number}"
            }
        
        print(f"  Found {len(documents)} documents")
        
        # Download documents
        downloaded_count = 0
        for doc in documents:
            if self.download_document(doc, project_number, country):
                downloaded_count += 1
        
        status = 'Documents Available' if downloaded_count > 0 else 'Download Failed'
        
        return {
            'project_number': project_number,
            'project_name': project_name,
            'country': country,
            'operation_number': project.get('Operation Number', ''),
            'documents_found': len(documents),
            'documents_downloaded': downloaded_count,
            'status': status,
            'project_url': f"https://www.iadb.org/en/project/{project_number}"
        }
    
    def process_all_projects(self, projects, start_index=0, end_index=None):
        """Process all projects with robust error handling."""
        if end_index is None:
            end_index = len(projects)
        
        print(f"\nStarting robust download process...")
        print(f"Processing projects {start_index + 1} to {end_index} of {len(projects)}")
        
        for i in range(start_index, end_index):
            try:
                project = projects[i]
                result = self.process_project(project)
                self.tracking_data.append(result)
                self.processed_count += 1
                
                # Update counters
                if result['documents_downloaded'] > 0:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Save progress every 10 projects
                if (i + 1) % 10 == 0:
                    self.save_tracking_data()
                    print(f"\n--- Progress Update ---")
                    print(f"Processed: {self.processed_count}")
                    print(f"Successful: {self.success_count}")
                    print(f"Failed: {self.error_count}")
                    print(f"Success Rate: {(self.success_count/self.processed_count*100):.1f}%")
                
                # Be respectful with delays
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing project {i + 1}: {e}")
                # Add error entry to tracking
                self.tracking_data.append({
                    'project_number': project.get('Project Number', f'Project_{i+1}'),
                    'project_name': project.get('Project Name', 'Unknown'),
                    'country': project.get('Project Country', 'Unknown'),
                    'operation_number': project.get('Operation Number', ''),
                    'documents_found': 0,
                    'documents_downloaded': 0,
                    'status': f'Error: {str(e)}',
                    'project_url': f"https://www.iadb.org/en/project/{project.get('Project Number', '')}"
                })
                self.processed_count += 1
                self.error_count += 1
        
        return self.tracking_data
    
    def save_tracking_data(self):
        """Save tracking data to CSV."""
        df = pd.DataFrame(self.tracking_data)
        df.to_csv("robust_tracking_data.csv", index=False)
        print(f"Tracking data saved to robust_tracking_data.csv")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("ROBUST IDB DOWNLOAD ANALYSIS SUMMARY")
        print("="*80)
        
        total_projects = len(df)
        projects_with_documents = len(df[df['documents_downloaded'] > 0])
        total_documents_found = df['documents_found'].sum()
        total_documents_downloaded = df['documents_downloaded'].sum()
        
        print(f"Total Projects Processed: {total_projects}")
        print(f"Projects with Documents Downloaded: {projects_with_documents}")
        print(f"Total Documents Found: {total_documents_found}")
        print(f"Total Documents Downloaded: {total_documents_downloaded}")
        print(f"Success Rate: {(projects_with_documents/total_projects*100):.1f}%")
        print(f"Document Download Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%" if total_documents_found > 0 else "Document Download Success Rate: N/A")
        
        print(f"\nStatus Summary:")
        status_counts = df['status'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Save summary to file
        with open("robust_download_summary.txt", "w") as f:
            f.write("ROBUST IDB DOWNLOAD ANALYSIS SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total Projects Processed: {total_projects}\n")
            f.write(f"Projects with Documents Downloaded: {projects_with_documents}\n")
            f.write(f"Total Documents Found: {total_documents_found}\n")
            f.write(f"Total Documents Downloaded: {total_documents_downloaded}\n")
            f.write(f"Success Rate: {(projects_with_documents/total_projects*100):.1f}%\n")
            f.write(f"Document Download Success Rate: {(total_documents_downloaded/total_documents_found*100):.1f}%\n\n" if total_documents_found > 0 else "Document Download Success Rate: N/A\n\n")
            
            f.write("Status Summary:\n")
            for status, count in status_counts.items():
                f.write(f"  {status}: {count}\n")
        
        print(f"\nSummary report saved to robust_download_summary.txt")

def main():
    downloader = RobustIDBDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    if not projects:
        print("Failed to load project data. Exiting.")
        return
    
    # Process all projects
    print(f"\nStarting robust download for all {len(projects)} projects...")
    results = downloader.process_all_projects(projects)
    
    # Save final results
    downloader.save_tracking_data()
    downloader.generate_summary_report()
    
    print(f"\n=== ROBUST DOWNLOAD COMPLETE ===")
    print(f"Results saved to: robust_tracking_data.csv")
    print(f"Summary saved to: robust_download_summary.txt")
    print(f"Documents organized in: downloads/")

if __name__ == "__main__":
    main()

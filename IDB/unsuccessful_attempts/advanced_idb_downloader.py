#!/usr/bin/env python3
"""
Advanced IDB Document Downloader
================================
Multi-strategy approach using API calls, search pages, and fallback methods
to ensure maximum document retrieval from all 565 projects.
"""

import pandas as pd
import requests
import time
import re
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote
import urllib3
from bs4 import BeautifulSoup
import ssl
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedIDBDownloader:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create multiple sessions for different strategies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.session.verify = False
        
        # API session for direct API calls
        self.api_session = requests.Session()
        self.api_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        })
        self.api_session.verify = False
        
        # Tracking data
        self.tracking_data = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        
    def load_project_data(self, csv_file):
        """Load project data from CSV file."""
        try:
            print(f"Loading project data from {csv_file}...")
            df = pd.read_csv(csv_file, skiprows=1)
            projects = df.to_dict('records')
            print(f"Loaded {len(projects)} projects")
            return projects
        except Exception as e:
            print(f"Error loading project data: {e}")
            return []
    
    def strategy_1_direct_project_page(self, project_number):
        """Strategy 1: Direct project page access."""
        url = f"https://www.iadb.org/en/project/{project_number}"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"    Strategy 1 failed: {e}")
        
        return None
    
    def strategy_2_search_page(self, project_number, project_name):
        """Strategy 2: Use search page to find project."""
        search_url = "https://www.iadb.org/en/project-search"
        
        try:
            # First get the search page
            response = self.session.get(search_url, timeout=30)
            if response.status_code != 200:
                return None
            
            # Search for the project
            search_data = {
                'search': project_number,
                'sector': '',
                'country': '',
                'year': ''
            }
            
            response = self.session.post(search_url, data=search_data, timeout=30)
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            print(f"    Strategy 2 failed: {e}")
        
        return None
    
    def strategy_3_api_search(self, project_number, project_name):
        """Strategy 3: Use IDB API to search for documents."""
        try:
            # Try different API endpoints
            api_endpoints = [
                f"https://www.iadb.org/api/projects/{project_number}/documents",
                f"https://www.iadb.org/api/documents?project={project_number}",
                f"https://www.iadb.org/api/search?q={quote(project_number)}&type=document"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.api_session.get(endpoint, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            return data
                except:
                    continue
                    
        except Exception as e:
            print(f"    Strategy 3 failed: {e}")
        
        return None
    
    def strategy_4_google_search_simulation(self, project_number, project_name):
        """Strategy 4: Simulate Google search for IDB documents."""
        try:
            search_query = f"site:iadb.org {project_number} document"
            search_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=30)
            if response.status_code == 200:
                # Extract IDB links from search results
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                idb_links = []
                for link in links:
                    href = link.get('href')
                    if href and 'iadb.org' in href and 'document' in href:
                        idb_links.append(href)
                
                if idb_links:
                    # Get the first IDB document page
                    response = self.session.get(idb_links[0], timeout=30)
                    if response.status_code == 200:
                        return response.text
                        
        except Exception as e:
            print(f"    Strategy 4 failed: {e}")
        
        return None
    
    def extract_documents_from_html(self, html_content):
        """Extract document information from HTML content."""
        if not html_content:
            return []
        
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for document cards
            document_cards = soup.find_all('idb-document-card')
            for card in document_cards:
                try:
                    doc_link = card.get('href') or card.get('data-href')
                    if doc_link:
                        title_elem = card.find('h3') or card.find('h4') or card.find('div', class_='title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown Document"
                        
                        documents.append({
                            'url': doc_link,
                            'title': title,
                            'type': 'Document Card'
                        })
                except Exception as e:
                    continue
            
            # Method 2: Look for direct document links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href and ('document.cfm' in href or '.pdf' in href or '.docx' in href):
                    title = link.get_text(strip=True) or "Document"
                    documents.append({
                        'url': href,
                        'title': title,
                        'type': 'Direct Link'
                    })
            
            # Method 3: Look for download buttons
            download_buttons = soup.find_all(['button', 'a'], class_=re.compile(r'download|btn'))
            for button in download_buttons:
                href = button.get('href') or button.get('data-href')
                if href:
                    title = button.get_text(strip=True) or "Download"
                    documents.append({
                        'url': href,
                        'title': title,
                        'type': 'Download Button'
                    })
            
            # Method 4: Look for JavaScript download links
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for document URLs in JavaScript
                    matches = re.findall(r'["\']([^"\']*(?:document\.cfm|\.pdf|\.docx))[^"\']*["\']', script.string)
                    for match in matches:
                        documents.append({
                            'url': match,
                            'title': f"Document from JS: {match.split('/')[-1]}",
                            'type': 'JavaScript'
                        })
            
        except Exception as e:
            print(f"  Error extracting documents: {e}")
        
        return documents
    
    def extract_documents_from_api(self, api_data):
        """Extract document information from API response."""
        documents = []
        
        try:
            if isinstance(api_data, list):
                for item in api_data:
                    if isinstance(item, dict):
                        doc_url = item.get('url') or item.get('link') or item.get('href')
                        title = item.get('title') or item.get('name') or "API Document"
                        
                        if doc_url:
                            documents.append({
                                'url': doc_url,
                                'title': title,
                                'type': 'API'
                            })
                            
        except Exception as e:
            print(f"  Error extracting from API: {e}")
        
        return documents
    
    def download_document_robust(self, doc_info, project_number, country):
        """Download document with multiple fallback methods."""
        try:
            doc_url = doc_info['url']
            if not doc_url.startswith('http'):
                doc_url = urljoin('https://www.iadb.org', doc_url)
            
            print(f"    Downloading: {doc_info['title']}")
            
            # Method 1: Direct download
            try:
                response = self.session.get(doc_url, timeout=60, stream=True)
                if response.status_code == 200:
                    return self.save_document(response, doc_info, project_number, country)
            except Exception as e:
                print(f"      Direct download failed: {e}")
            
            # Method 2: Get document page first, then download
            try:
                response = self.session.get(doc_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for download links
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
                            download_url = link.get('href')
                            if download_url:
                                if not download_url.startswith('http'):
                                    download_url = urljoin('https://www.iadb.org', download_url)
                                
                                file_response = self.session.get(download_url, timeout=60, stream=True)
                                if file_response.status_code == 200:
                                    return self.save_document(file_response, doc_info, project_number, country)
            except Exception as e:
                print(f"      Page-based download failed: {e}")
            
            # Method 3: Try with different headers
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*',
                    'Referer': 'https://www.iadb.org/',
                }
                
                response = self.session.get(doc_url, headers=headers, timeout=60, stream=True)
                if response.status_code == 200:
                    return self.save_document(response, doc_info, project_number, country)
            except Exception as e:
                print(f"      Header-based download failed: {e}")
            
            print(f"      ✗ All download methods failed")
            return False
            
        except Exception as e:
            print(f"      ✗ Download error: {e}")
            return False
    
    def save_document(self, response, doc_info, project_number, country):
        """Save downloaded document to file."""
        try:
            # Determine file extension
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type:
                ext = '.pdf'
            elif 'word' in content_type or 'docx' in content_type:
                ext = '.docx'
            elif 'doc' in content_type:
                ext = '.doc'
            else:
                # Try to determine from URL
                url = response.url
                if '.pdf' in url:
                    ext = '.pdf'
                elif '.docx' in url:
                    ext = '.docx'
                elif '.doc' in url:
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
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"      ✓ Downloaded: {filename}")
            return True
            
        except Exception as e:
            print(f"      ✗ Save error: {e}")
            return False
    
    def process_project_advanced(self, project):
        """Process a single project using multiple strategies."""
        project_number = project['Project Number']
        project_name = project['Project Name']
        country = project['Project Country']
        
        print(f"\nProcessing project {self.processed_count + 1}: {project_number}")
        print(f"  Project: {project_name}")
        print(f"  Country: {country}")
        
        all_documents = []
        
        # Strategy 1: Direct project page
        print(f"  Trying Strategy 1: Direct project page...")
        html_content = self.strategy_1_direct_project_page(project_number)
        if html_content:
            documents = self.extract_documents_from_html(html_content)
            all_documents.extend(documents)
            print(f"    Found {len(documents)} documents via Strategy 1")
        
        # Strategy 2: Search page
        if not all_documents:
            print(f"  Trying Strategy 2: Search page...")
            html_content = self.strategy_2_search_page(project_number, project_name)
            if html_content:
                documents = self.extract_documents_from_html(html_content)
                all_documents.extend(documents)
                print(f"    Found {len(documents)} documents via Strategy 2")
        
        # Strategy 3: API search
        if not all_documents:
            print(f"  Trying Strategy 3: API search...")
            api_data = self.strategy_3_api_search(project_number, project_name)
            if api_data:
                documents = self.extract_documents_from_api(api_data)
                all_documents.extend(documents)
                print(f"    Found {len(documents)} documents via Strategy 3")
        
        # Strategy 4: Google search simulation
        if not all_documents:
            print(f"  Trying Strategy 4: Search simulation...")
            html_content = self.strategy_4_google_search_simulation(project_number, project_name)
            if html_content:
                documents = self.extract_documents_from_html(html_content)
                all_documents.extend(documents)
                print(f"    Found {len(documents)} documents via Strategy 4")
        
        # Remove duplicates
        unique_documents = []
        seen_urls = set()
        for doc in all_documents:
            if doc['url'] not in seen_urls:
                unique_documents.append(doc)
                seen_urls.add(doc['url'])
        
        if not unique_documents:
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
        
        print(f"  Total unique documents found: {len(unique_documents)}")
        
        # Download documents
        downloaded_count = 0
        for doc in unique_documents:
            if self.download_document_robust(doc, project_number, country):
                downloaded_count += 1
        
        status = 'Documents Available' if downloaded_count > 0 else 'Download Failed'
        
        return {
            'project_number': project_number,
            'project_name': project_name,
            'country': country,
            'operation_number': project.get('Operation Number', ''),
            'documents_found': len(unique_documents),
            'documents_downloaded': downloaded_count,
            'status': status,
            'project_url': f"https://www.iadb.org/en/project/{project_number}"
        }
    
    def process_all_projects(self, projects, start_index=0, end_index=None):
        """Process all projects with advanced strategies."""
        if end_index is None:
            end_index = len(projects)
        
        print(f"\nStarting advanced download process...")
        print(f"Processing projects {start_index + 1} to {end_index} of {len(projects)}")
        
        for i in range(start_index, end_index):
            try:
                project = projects[i]
                result = self.process_project_advanced(project)
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
        df.to_csv("advanced_tracking_data.csv", index=False)
        print(f"Tracking data saved to advanced_tracking_data.csv")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        if not self.tracking_data:
            print("No tracking data available.")
            return
        
        df = pd.DataFrame(self.tracking_data)
        
        print("\n" + "="*80)
        print("ADVANCED IDB DOWNLOAD ANALYSIS SUMMARY")
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
        with open("advanced_download_summary.txt", "w") as f:
            f.write("ADVANCED IDB DOWNLOAD ANALYSIS SUMMARY\n")
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
        
        print(f"\nSummary report saved to advanced_download_summary.txt")

def main():
    downloader = AdvancedIDBDownloader()
    
    # Load project data
    projects = downloader.load_project_data("IDB Corpus Key Words.csv")
    
    if not projects:
        print("Failed to load project data. Exiting.")
        return
    
    # Process all projects
    print(f"\nStarting advanced download for all {len(projects)} projects...")
    results = downloader.process_all_projects(projects)
    
    # Save final results
    downloader.save_tracking_data()
    downloader.generate_summary_report()
    
    print(f"\n=== ADVANCED DOWNLOAD COMPLETE ===")
    print(f"Results saved to: advanced_tracking_data.csv")
    print(f"Summary saved to: advanced_download_summary.txt")
    print(f"Documents organized in: downloads/")

if __name__ == "__main__":
    main()

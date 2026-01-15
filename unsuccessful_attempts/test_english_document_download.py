#!/usr/bin/env python3
"""
Test English Document Download
This script tests downloading the specific English document types requested:
- Loan Proposal Document
- Project Proposal Document  
- Project Abstract Document
"""

import requests
import time
import re
from pathlib import Path
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TestEnglishDocumentDownload:
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
        
    def test_specific_projects(self):
        """Test downloading documents for specific projects known to have documents."""
        test_projects = [
            "PE-L1187",  # Peru - known to have documents
            "CO-M1089",  # Colombia - known to have documents
            "PR-M1033",  # Paraguay - known to have documents
        ]
        
        for project_number in test_projects:
            print(f"\n{'='*60}")
            print(f"TESTING PROJECT: {project_number}")
            print(f"{'='*60}")
            
            # Get project page
            html_content = self.get_project_page(project_number)
            
            if html_content:
                print(f"✓ Successfully accessed project page")
                
                # Extract English documents
                documents = self.extract_english_documents(html_content, project_number)
                
                if documents:
                    print(f"Found {len(documents)} English documents:")
                    for doc in documents:
                        print(f"  - {doc['type']}: {doc['title']}")
                    
                    # Try to download each document
                    for doc in documents:
                        print(f"\nAttempting to download: {doc['title']}")
                        success = self.download_document(doc)
                        if success:
                            print(f"✓ SUCCESS: Downloaded {doc['title']}")
                        else:
                            print(f"✗ FAILED: Could not download {doc['title']}")
                else:
                    print("No English documents of requested types found")
            else:
                print("✗ Could not access project page")
            
            time.sleep(2)  # Be respectful
    
    def get_project_page(self, project_number):
        """Get the project page for a specific project."""
        project_urls = [
            f"{self.base_url}/en/project/{project_number}",
            f"{self.base_url}/en/projects/{project_number}",
            f"{self.base_url}/projects/{project_number}"
        ]
        
        for url in project_urls:
            try:
                print(f"Trying URL: {url}")
                response = self.session.get(url, timeout=30, verify=False)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"HTTP {response.status_code} for {url}")
            except Exception as e:
                print(f"Error accessing {url}: {e}")
        
        return None
    
    def extract_english_documents(self, html_content, project_number):
        """Extract English documents of the requested types."""
        documents = []
        
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
        
        return documents
    
    def classify_document_type(self, title, project_number):
        """Classify document type based on title."""
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
        
        return None
    
    def download_document(self, document):
        """Download a single document."""
        try:
            print(f"  Requesting: {document['url']}")
            
            response = self.session.get(document['url'], timeout=30, verify=False, allow_redirects=True)
            
            print(f"  Response status: {response.status_code}")
            print(f"  Final URL: {response.url}")
            print(f"  Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/pdf' in content_type:
                    # Direct PDF download
                    filename = f"{document['project_number']}_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                    filename = filename.replace(' ', '_')
                    
                    filepath = self.downloads_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"  ✓ Saved as: {filename}")
                    return True
                    
                elif 'text/html' in content_type:
                    # Check if this is a redirect page
                    print(f"  HTML response received, checking for redirect...")
                    
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
                                print(f"  Found PDF URL: {pdf_url}")
                                
                                # Try to download the PDF
                                pdf_response = self.session.get(pdf_url, timeout=30, verify=False)
                                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', '').lower():
                                    filename = f"{document['project_number']}_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                                    filename = filename.replace(' ', '_')
                                    
                                    filepath = self.downloads_dir / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(pdf_response.content)
                                    
                                    print(f"  ✓ Saved as: {filename}")
                                    return True
                    
                    print(f"  Could not extract PDF URL from HTML response")
                    return False
                    
                else:
                    print(f"  Unexpected content type: {content_type}")
                    return False
                    
            else:
                print(f"  HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  Error downloading: {e}")
            return False

def main():
    """Main function."""
    tester = TestEnglishDocumentDownload()
    tester.test_specific_projects()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Download Publicly Accessible Documents for PE-L1187 - Version 2
This script accesses the project page first, then downloads the publicly available documents.
"""

import requests
import time
from pathlib import Path
import os
import re
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PEL1187PublicDownloaderV2:
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
        self.downloads_dir = Path("downloads/Peru")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
    def get_project_page(self):
        """Get the PE-L1187 project page."""
        print("Accessing PE-L1187 project page...")
        
        # Try different URL patterns for the project page
        project_urls = [
            "https://www.iadb.org/en/projects/PE-L1187",
            "https://www.iadb.org/en/project/PE-L1187",
            "https://www.iadb.org/projects/PE-L1187"
        ]
        
        for url in project_urls:
            try:
                print(f"Trying URL: {url}")
                response = self.session.get(url, timeout=30, verify=False)
                
                if response.status_code == 200:
                    print(f"✓ Successfully accessed project page")
                    return response.text
                else:
                    print(f"✗ HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                print(f"✗ Error accessing {url}: {e}")
        
        # If direct URLs don't work, try to find the project through search
        print("Trying to find project through search...")
        return self.search_for_project()
    
    def search_for_project(self):
        """Search for the PE-L1187 project."""
        try:
            search_url = "https://www.iadb.org/en/search"
            params = {
                'q': 'PE-L1187',
                'type': 'project'
            }
            
            response = self.session.get(search_url, params=params, timeout=30, verify=False)
            if response.status_code == 200:
                print("✓ Found project through search")
                return response.text
            else:
                print(f"✗ Search failed with HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ Search error: {e}")
        
        return None
    
    def extract_document_urls(self, html_content):
        """Extract document URLs from the project page HTML."""
        documents = []
        
        if not html_content:
            print("No HTML content to parse")
            return documents
        
        # Look for document card patterns
        doc_patterns = [
            r'<idb-document-card[^>]*url="([^"]*)"[^>]*>.*?<div slot="heading">([^<]*)</div>.*?<div slot="cta">([^<]*)</div>',
            r'href="([^"]*document\.cfm[^"]*)"[^>]*>([^<]*\.pdf[^<]*)',
            r'url="([^"]*document\.cfm[^"]*)"[^>]*>.*?<div slot="heading">([^<]*)</div>'
        ]
        
        for pattern in doc_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    url = match[0]
                    title = match[1].strip()
                    language = match[2].strip() if len(match) > 2 else "Unknown"
                    
                    # Determine document type and language
                    doc_type = "TC Abstract"
                    if "synthesis" in title.lower() or "síntesis" in title.lower():
                        doc_type = "Project Synthesis"
                    
                    if "spanish" in language.lower() or "español" in language.lower():
                        lang = "Spanish"
                    elif "english" in language.lower():
                        lang = "English"
                    else:
                        lang = language
                    
                    documents.append({
                        'url': url,
                        'title': title,
                        'language': lang,
                        'type': doc_type
                    })
        
        # Remove duplicates
        unique_docs = []
        seen_urls = set()
        for doc in documents:
            if doc['url'] not in seen_urls:
                unique_docs.append(doc)
                seen_urls.add(doc['url'])
        
        return unique_docs
    
    def download_document(self, document):
        """Download a single document with SSL bypass."""
        try:
            print(f"   Requesting document from: {document['url']}")
            
            # Try with SSL verification disabled
            response = self.session.get(document['url'], timeout=30, verify=False, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/pdf' in content_type:
                    # Direct PDF download
                    filename = f"PE-L1187_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                    filename = filename.replace(' ', '_')
                    
                    filepath = self.downloads_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   ✓ Saved as: {filename}")
                    return True
                    
                elif 'text/html' in content_type:
                    # Check if this is a redirect page
                    print(f"   Received HTML response, checking for redirect...")
                    
                    # Look for PDF links or redirects
                    pdf_patterns = [
                        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                        r'window\.location\.href\s*=\s*["\']([^"\']*)["\']',
                        r'location\.href\s*=\s*["\']([^"\']*)["\']',
                        r'<a[^>]*href=["\']([^"\']*\.pdf[^"\']*)["\'][^>]*>'
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
                                    filename = f"PE-L1187_{document['type'].replace(' ', '_')}_{document['language']}.pdf"
                                    filename = filename.replace(' ', '_')
                                    
                                    filepath = self.downloads_dir / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(pdf_response.content)
                                    
                                    print(f"   ✓ Saved as: {filename}")
                                    return True
                    
                    print(f"   Could not extract PDF URL from HTML response")
                    return False
                    
                else:
                    print(f"   Unexpected content type: {content_type}")
                    return False
                    
            else:
                print(f"   HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Error downloading: {e}")
            return False
    
    def download_public_documents(self):
        """Main function to download publicly accessible documents."""
        print("=" * 80)
        print("DOWNLOADING PUBLICLY ACCESSIBLE DOCUMENTS FOR PE-L1187 - V2")
        print("=" * 80)
        
        # Get the project page
        html_content = self.get_project_page()
        
        if not html_content:
            print("Could not access project page. Using known document URLs...")
            # Fallback to known document URLs
            documents = [
                {
                    'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-4',
                    'title': 'PERU Síntesis proyecto PES PE-L1187.pdf',
                    'language': 'Spanish',
                    'type': 'TC Abstract'
                },
                {
                    'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-5',
                    'title': 'PERU - Project Synthesis SEP PE-L1187.pdf',
                    'language': 'English',
                    'type': 'TC Abstract'
                }
            ]
        else:
            # Extract document URLs from the page
            documents = self.extract_document_urls(html_content)
        
        if not documents:
            print("No documents found on the project page.")
            return
        
        print(f"\nFound {len(documents)} publicly accessible documents:")
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc['title']} ({doc['language']}) - {doc['type']}")
        
        print(f"\nAttempting to download {len(documents)} documents...")
        downloaded_count = 0
        
        for i, document in enumerate(documents, 1):
            print(f"\n{i}. Downloading: {document['title']}")
            print(f"   Language: {document['language']}")
            print(f"   Type: {document['type']}")
            
            if self.download_document(document):
                downloaded_count += 1
            
            time.sleep(2)  # Be respectful to the server
        
        print(f"\n" + "=" * 80)
        print(f"DOWNLOAD SUMMARY")
        print(f"=" * 80)
        print(f"Documents found: {len(documents)}")
        print(f"Successfully downloaded: {downloaded_count}")
        print(f"Failed downloads: {len(documents) - downloaded_count}")
        
        if downloaded_count > 0:
            print(f"\n✓ SUCCESS: Downloaded {downloaded_count} publicly accessible documents!")
            print(f"Files saved in: {self.downloads_dir}")
        else:
            print(f"\n✗ No documents were successfully downloaded.")

def main():
    """Main function."""
    downloader = PEL1187PublicDownloaderV2()
    downloader.download_public_documents()

if __name__ == "__main__":
    main()

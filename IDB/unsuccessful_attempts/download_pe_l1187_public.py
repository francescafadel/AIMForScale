#!/usr/bin/env python3
"""
Download Publicly Accessible Documents for PE-L1187
This script downloads the documents that are actually publicly available on the PE-L1187 project page.
"""

import requests
import time
from pathlib import Path
import os

class PEL1187PublicDownloader:
    def __init__(self):
        self.base_url = "https://www.iadb.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create downloads directory
        self.downloads_dir = Path("downloads/Peru")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
    def download_public_documents(self):
        """Download the publicly accessible documents for PE-L1187."""
        print("=" * 80)
        print("DOWNLOADING PUBLICLY ACCESSIBLE DOCUMENTS FOR PE-L1187")
        print("=" * 80)
        
        # Documents found in the project page HTML
        documents = [
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-4',
                'title': 'PERU Síntesis proyecto PES PE-L1187.pdf',
                'language': 'Spanish',
                'type': 'TC Abstract',
                'date': 'Mar. 28, 2018'
            },
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-5',
                'title': 'PERU - Project Synthesis SEP PE-L1187.pdf',
                'language': 'English',
                'type': 'TC Abstract',
                'date': 'Mar. 27, 2018'
            }
        ]
        
        print(f"Found {len(documents)} publicly accessible documents:")
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc['title']} ({doc['language']}) - {doc['type']}")
        
        print(f"\nAttempting to download {len(documents)} documents...")
        downloaded_count = 0
        
        for i, document in enumerate(documents, 1):
            print(f"\n{i}. Downloading: {document['title']}")
            print(f"   URL: {document['url']}")
            print(f"   Language: {document['language']}")
            print(f"   Type: {document['type']}")
            
            if self.download_document(document):
                downloaded_count += 1
                print(f"   ✓ Successfully downloaded")
            else:
                print(f"   ✗ Failed to download")
            
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
    
    def download_document(self, document):
        """Download a single document."""
        try:
            print(f"   Requesting document...")
            response = self.session.get(document['url'], timeout=30)
            
            if response.status_code == 200:
                # Check if we got a PDF or if we need to follow a redirect
                content_type = response.headers.get('content-type', '')
                
                if 'application/pdf' in content_type:
                    # Direct PDF download
                    filename = f"PE-L1187_{document['type'].replace(' ', '_')}_{document['language']}_{document['date'].replace(' ', '_').replace('.', '')}.pdf"
                    filename = filename.replace(' ', '_')
                    
                    filepath = self.downloads_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   Saved as: {filename}")
                    return True
                    
                elif 'text/html' in content_type:
                    # This might be a redirect page, try to extract the actual PDF URL
                    print(f"   Received HTML response, checking for redirect...")
                    
                    # Look for PDF links in the HTML
                    import re
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
                                pdf_response = self.session.get(pdf_url, timeout=30)
                                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', ''):
                                    filename = f"PE-L1187_{document['type'].replace(' ', '_')}_{document['language']}_{document['date'].replace(' ', '_').replace('.', '')}.pdf"
                                    filename = filename.replace(' ', '_')
                                    
                                    filepath = self.downloads_dir / filename
                                    
                                    with open(filepath, 'wb') as f:
                                        f.write(pdf_response.content)
                                    
                                    print(f"   Saved as: {filename}")
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

def main():
    """Main function."""
    downloader = PEL1187PublicDownloader()
    downloader.download_public_documents()

if __name__ == "__main__":
    main()

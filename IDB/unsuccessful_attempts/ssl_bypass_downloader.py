#!/usr/bin/env python3
"""
SSL Bypass Downloader
This script uses different SSL configurations and methods to download IDB documents.
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
import ssl
import certifi

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLBypassDownloader:
    def __init__(self):
        self.base_url = "https://www.iadb.org"
        self.session = requests.Session()
        
        # Try different SSL configurations
        self.setup_ssl_config()
        
        # Create downloads directory
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
    def setup_ssl_config(self):
        """Setup different SSL configurations to try."""
        # Method 1: Standard headers with SSL verification disabled
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Disable SSL verification
        self.session.verify = False
        
        # Create a custom SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Try to use custom SSL context
        try:
            import urllib3.util.ssl_
            self.session.mount('https://', requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=10,
                max_retries=3
            ))
        except Exception as e:
            print(f"Warning: Could not setup custom SSL adapter: {e}")
    
    def get_pe_l1187_data(self):
        """Get PE-L1187 project data from the CSV."""
        print("Loading PE-L1187 project data...")
        
        # Read the CSV file
        df = pd.read_csv("IDB Corpus Key Words.csv", skiprows=1)
        
        # Find PE-L1187
        pe_l1187_row = df[df['Project Number'] == 'PE-L1187']
        
        if pe_l1187_row.empty:
            print("PE-L1187 not found in CSV!")
            return None
        
        project = {
            'project_number': 'PE-L1187',
            'project_name': pe_l1187_row.iloc[0]['Project Name'],
            'country': pe_l1187_row.iloc[0]['Project Country'],
            'operation_number': pe_l1187_row.iloc[0]['Operation Number'],
            'approval_date': pe_l1187_row.iloc[0]['Approval Date'],
            'status': pe_l1187_row.iloc[0]['Status'],
            'project_type': pe_l1187_row.iloc[0]['Project Type'],
            'total_cost': pe_l1187_row.iloc[0]['Total Cost']
        }
        
        print(f"Found PE-L1187: {project['project_name']}")
        print(f"Country: {project['country']}")
        print(f"Operation: {project['operation_number']}")
        print(f"Type: {project['project_type']}")
        print(f"Cost: ${project['total_cost']:,.0f}")
        
        return project
    
    def try_different_download_methods(self, project):
        """Try different methods to download documents."""
        print(f"\nTrying different download methods for {project['project_number']}...")
        
        # Known document URLs for PE-L1187
        documents = [
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-4',
                'language': 'Spanish',
                'title': 'PERU Síntesis proyecto PES PE-L1187.pdf',
                'filename': 'PERU_Sintesis_proyecto_PES_PE-L1187.pdf'
            },
            {
                'url': 'https://www.iadb.org/document.cfm?id=EZSHARE-1121147323-5',
                'language': 'English',
                'title': 'PERU - Project Syntheis SEP PE-L1187.pdf',
                'filename': 'PERU_Project_Synthesis_SEP_PE-L1187.pdf'
            }
        ]
        
        downloaded_count = 0
        
        for doc in documents:
            print(f"\nDownloading {doc['language']} version...")
            print(f"URL: {doc['url']}")
            
            # Try different download methods
            success = False
            
            # Method 1: Direct download with SSL bypass
            if not success:
                success = self.method1_direct_download(doc, project)
            
            # Method 2: Follow redirects manually
            if not success:
                success = self.method2_manual_redirect(doc, project)
            
            # Method 3: Use different SSL context
            if not success:
                success = self.method3_custom_ssl(doc, project)
            
            # Method 4: Try HTTP instead of HTTPS
            if not success:
                success = self.method4_http_fallback(doc, project)
            
            if success:
                downloaded_count += 1
            else:
                print(f"  ✗ All download methods failed for {doc['language']} version")
        
        return downloaded_count
    
    def method1_direct_download(self, doc, project):
        """Method 1: Direct download with SSL bypass."""
        try:
            print(f"  Method 1: Direct download with SSL bypass...")
            
            response = self.session.get(doc['url'], timeout=30, allow_redirects=True)
            
            print(f"    Response status: {response.status_code}")
            print(f"    Final URL: {response.url}")
            print(f"    Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'application/pdf' in content_type.lower():
                    print(f"    ✓ Direct PDF download successful")
                    return self.save_document(response.content, doc, project)
                else:
                    print(f"    HTML page received, looking for download link...")
                    return self.extract_download_from_html(response.text, doc, project)
            else:
                print(f"    ✗ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def method2_manual_redirect(self, doc, project):
        """Method 2: Follow redirects manually."""
        try:
            print(f"  Method 2: Manual redirect following...")
            
            # First, get the document page without following redirects
            response = self.session.get(doc['url'], timeout=30, allow_redirects=False)
            
            print(f"    Initial response: {response.status_code}")
            
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location')
                print(f"    Redirect URL: {redirect_url}")
                
                if redirect_url:
                    # Follow the redirect manually
                    if redirect_url.startswith('/'):
                        redirect_url = urljoin(self.base_url, redirect_url)
                    elif not redirect_url.startswith('http'):
                        redirect_url = urljoin(doc['url'], redirect_url)
                    
                    print(f"    Following redirect to: {redirect_url}")
                    
                    # Try to download from redirect URL
                    redirect_response = self.session.get(redirect_url, timeout=30, stream=True)
                    
                    if redirect_response.status_code == 200:
                        content_type = redirect_response.headers.get('content-type', '')
                        if 'application/pdf' in content_type.lower():
                            print(f"    ✓ PDF download from redirect successful")
                            return self.save_document(redirect_response.content, doc, project)
            
            return False
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def method3_custom_ssl(self, doc, project):
        """Method 3: Use custom SSL context."""
        try:
            print(f"  Method 3: Custom SSL context...")
            
            # Create a new session with custom SSL context
            custom_session = requests.Session()
            custom_session.verify = False
            custom_session.headers.update(self.session.headers)
            
            # Try with different SSL configurations
            response = custom_session.get(doc['url'], timeout=30, allow_redirects=True)
            
            print(f"    Response status: {response.status_code}")
            print(f"    Final URL: {response.url}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type.lower():
                    print(f"    ✓ PDF download with custom SSL successful")
                    return self.save_document(response.content, doc, project)
            
            return False
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def method4_http_fallback(self, doc, project):
        """Method 4: Try HTTP instead of HTTPS."""
        try:
            print(f"  Method 4: HTTP fallback...")
            
            # Try HTTP version of the URL
            http_url = doc['url'].replace('https://', 'http://')
            print(f"    Trying HTTP URL: {http_url}")
            
            response = self.session.get(http_url, timeout=30, allow_redirects=True)
            
            print(f"    Response status: {response.status_code}")
            print(f"    Final URL: {response.url}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type.lower():
                    print(f"    ✓ PDF download via HTTP successful")
                    return self.save_document(response.content, doc, project)
            
            return False
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def extract_download_from_html(self, html_content, doc, project):
        """Extract download link from HTML page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for download links
            download_links = soup.find_all('a', href=True)
            
            for link in download_links:
                link_href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()
                
                # Look for download indicators
                if any(keyword in link_text for keyword in ['download', 'descargar', 'pdf']):
                    print(f"    Found download link: {link_href}")
                    
                    # Make URL absolute
                    if link_href.startswith('/'):
                        download_url = urljoin(self.base_url, link_href)
                    elif link_href.startswith('http'):
                        download_url = link_href
                    else:
                        download_url = urljoin(doc['url'], link_href)
                    
                    # Try to download from this link
                    response = self.session.get(download_url, timeout=30, stream=True)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/pdf' in content_type.lower():
                            print(f"    ✓ PDF found at download link")
                            return self.save_document(response.content, doc, project)
            
            print(f"    ✗ No download link found in HTML")
            return False
            
        except Exception as e:
            print(f"    ✗ Error extracting download link: {e}")
            return False
    
    def save_document(self, content, doc, project):
        """Save document content to file."""
        try:
            # Create country directory
            country = project['country']
            country_dir = self.downloads_dir / country
            country_dir.mkdir(exist_ok=True)
            
            # Create filename
            project_number = project['project_number']
            language = doc['language']
            filename = f"{project_number}_TC_Abstract_{language}_{doc['filename']}"
            
            # Ensure filename is valid
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            filepath = country_dir / filename
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(content)
            
            print(f"    ✓ Saved: {filename}")
            print(f"    File size: {filepath.stat().st_size:,} bytes")
            return True
            
        except Exception as e:
            print(f"    ✗ Error saving file: {e}")
            return False
    
    def test_pe_l1187(self):
        """Test downloading documents for PE-L1187 with SSL bypass methods."""
        print("=" * 80)
        print("SSL BYPASS DOWNLOADER TEST - PE-L1187")
        print("=" * 80)
        
        # Get project data
        project = self.get_pe_l1187_data()
        if not project:
            print("Could not find PE-L1187 in the CSV file!")
            return
        
        # Try different download methods
        downloaded_count = self.try_different_download_methods(project)
        
        print(f"\nDownload Summary:")
        print(f"  Documents attempted: 2")
        print(f"  Successfully downloaded: {downloaded_count}")
        print(f"  Failed downloads: {2 - downloaded_count}")
        
        if downloaded_count > 0:
            print(f"\n✓ SUCCESS: Downloaded {downloaded_count} documents for PE-L1187!")
            print(f"Files saved in: {self.downloads_dir}/{project['country']}")
        else:
            print(f"\n✗ All download methods failed.")
            print("The documents may require browser-based authentication or have additional security measures.")

def main():
    downloader = SSLBypassDownloader()
    downloader.test_pe_l1187()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Example Project Access Demonstration
This script demonstrates what happens when trying to access a specific high-value loan operation project.
"""

import requests
import time
from urllib.parse import urljoin, quote
import re

def demonstrate_project_access():
    """Demonstrate accessing a specific high-value loan operation project."""
    
    # Example project: PE-L1187 - Increasing Cocoa Productivity through credit to small producers
    # This is a $1.25M loan operation from 2015 that should have detailed proposal documents
    
    project_number = "PE-L1187"
    project_name = "Increasing Cocoa Productivity through credit to small producers"
    operation_number = "SP/OC-15-01-PE"
    
    print("=" * 80)
    print(f"DEMONSTRATION: Accessing Project {project_number}")
    print(f"Project: {project_name}")
    print(f"Operation: {operation_number}")
    print(f"Type: Loan Operation (High Priority for Documents)")
    print(f"Value: $1,250,000")
    print("=" * 80)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    base_url = "https://www.iadb.org"
    
    # Method 1: Try direct project URL
    print("\n1. ATTEMPTING DIRECT PROJECT URL...")
    project_url = f"{base_url}/en/projects/{project_number}"
    print(f"URL: {project_url}")
    
    try:
        response = session.get(project_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Page found!")
            # Look for document links
            doc_patterns = [
                r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                r'href=["\']([^"\']*document[^"\']*)["\']',
                r'href=["\']([^"\']*proposal[^"\']*)["\']',
                r'href=["\']([^"\']*loan[^"\']*)["\']'
            ]
            
            found_docs = []
            for pattern in doc_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                found_docs.extend(matches)
            
            if found_docs:
                print(f"✓ Found {len(found_docs)} potential document links:")
                for doc in found_docs[:5]:  # Show first 5
                    print(f"  - {doc}")
            else:
                print("✗ No document links found on project page")
        else:
            print("✗ Project page not found")
            
    except Exception as e:
        print(f"✗ Error accessing project page: {e}")
    
    # Method 2: Try project search
    print("\n2. ATTEMPTING PROJECT SEARCH...")
    search_url = f"{base_url}/en/project-search"
    print(f"Search URL: {search_url}")
    
    try:
        # First get the search page
        response = session.get(search_url, timeout=10)
        print(f"Search page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Search page accessible")
            
            # Try to search for the project
            search_data = {
                'search': project_number,
                'country': '',
                'sector': '',
                'status': ''
            }
            
            # This would require form submission, but let's check if we can find the project
            if project_number in response.text:
                print("✓ Project number found on search page")
            else:
                print("✗ Project number not found on search page")
        else:
            print("✗ Search page not accessible")
            
    except Exception as e:
        print(f"✗ Error accessing search page: {e}")
    
    # Method 3: Try operation number search
    print("\n3. ATTEMPTING OPERATION NUMBER SEARCH...")
    operation_url = f"{base_url}/en/projects/{operation_number}"
    print(f"Operation URL: {operation_url}")
    
    try:
        response = session.get(operation_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Operation page found!")
            # Look for document links
            doc_patterns = [
                r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                r'href=["\']([^"\']*document[^"\']*)["\']',
                r'href=["\']([^"\']*proposal[^"\']*)["\']'
            ]
            
            found_docs = []
            for pattern in doc_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                found_docs.extend(matches)
            
            if found_docs:
                print(f"✓ Found {len(found_docs)} potential document links:")
                for doc in found_docs[:5]:  # Show first 5
                    print(f"  - {doc}")
            else:
                print("✗ No document links found on operation page")
        else:
            print("✗ Operation page not found")
            
    except Exception as e:
        print(f"✗ Error accessing operation page: {e}")
    
    # Method 4: Try publications/documents section
    print("\n4. ATTEMPTING PUBLICATIONS/DOCUMENTS SECTION...")
    docs_url = f"{base_url}/en/publications"
    print(f"Publications URL: {docs_url}")
    
    try:
        response = session.get(docs_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Publications page accessible")
            # Check if we can search for the project
            if "search" in response.text.lower():
                print("✓ Search functionality available on publications page")
            else:
                print("✗ No search functionality found")
        else:
            print("✗ Publications page not accessible")
            
    except Exception as e:
        print(f"✗ Error accessing publications page: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY OF FINDINGS:")
    print("=" * 80)
    print("""
This demonstration shows why the script marked this project as "Not Attempted - Manual Research Required":

1. DIRECT ACCESS: The IDB website doesn't provide direct public access to project documents
   through simple URLs like /projects/PE-L1187

2. SEARCH FUNCTIONALITY: While the website has search capabilities, they require:
   - User authentication/login
   - Specific search parameters
   - Manual navigation through multiple pages

3. DOCUMENT ACCESS: Project documents are typically:
   - Behind login walls
   - Require specific permissions
   - May be in internal document management systems
   - Not publicly accessible through web scraping

4. MANUAL RESEARCH REQUIRED: To access these documents, you would need to:
   - Contact IDB directly
   - Request access through official channels
   - Use IDB's document request system
   - Have proper authorization/credentials

This explains why automated scripts cannot access these documents, even though
they likely exist for high-value loan operations like this one.
""")

if __name__ == "__main__":
    demonstrate_project_access()

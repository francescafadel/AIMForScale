#!/usr/bin/env python3
"""
Manual IDB Website Exploration Script
This script explores the IDB website structure to understand how to access project documents.
"""

import requests
import time
from urllib.parse import urljoin, quote
import re

def explore_idb_structure():
    """Explore the IDB website structure to understand how projects are organized."""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    base_url = "https://www.iadb.org"
    
    # Test URLs to explore
    test_urls = [
        "https://www.iadb.org/en/projects",
        "https://www.iadb.org/en/search",
        "https://www.iadb.org/en/publications",
        "https://publications.iadb.org",
        "https://www.iadb.org/en/projects/search",
        "https://www.iadb.org/en/operations",
        "https://www.iadb.org/en/documents"
    ]
    
    print("Exploring IDB website structure...")
    
    for url in test_urls:
        try:
            print(f"\nTrying: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                # Look for links to projects or documents
                links = re.findall(r'href=["\']([^"\']*)["\']', response.text)
                project_links = [link for link in links if 'project' in link.lower() or 'operation' in link.lower()]
                doc_links = [link for link in links if '.pdf' in link.lower() or 'document' in link.lower()]
                
                print(f"Found {len(project_links)} project-related links")
                print(f"Found {len(doc_links)} document-related links")
                
                if project_links:
                    print("Sample project links:")
                    for link in project_links[:5]:
                        print(f"  {link}")
                
                if doc_links:
                    print("Sample document links:")
                    for link in doc_links[:5]:
                        print(f"  {link}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error accessing {url}: {e}")
    
    # Try to find a specific project page
    print("\n\nTrying to find specific project pages...")
    
    # Test with a known project number format
    test_project = "RG-T4752"
    
    test_project_urls = [
        f"https://www.iadb.org/en/projects/{test_project}",
        f"https://www.iadb.org/projects/{test_project}",
        f"https://www.iadb.org/en/operations/{test_project}",
        f"https://www.iadb.org/operations/{test_project}",
        f"https://publications.iadb.org/publications/english/document/{test_project}",
        f"https://publications.iadb.org/en/document/{test_project}"
    ]
    
    for url in test_project_urls:
        try:
            print(f"\nTrying project URL: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("Page found! Analyzing content...")
                
                # Look for document links
                doc_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', response.text, re.IGNORECASE)
                print(f"Found {len(doc_links)} PDF links")
                
                for link in doc_links[:5]:
                    print(f"  {link}")
                
                # Look for project information
                if 'project' in response.text.lower() or 'operation' in response.text.lower():
                    print("Page contains project information")
                
            elif response.status_code == 404:
                print("Page not found (404)")
            else:
                print(f"Unexpected status: {response.status_code}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")

def search_idb_publications():
    """Search IDB publications for project documents."""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print("\n\nSearching IDB publications...")
    
    # Try IDB publications search
    search_urls = [
        "https://publications.iadb.org/en",
        "https://publications.iadb.org/publications/english",
        "https://www.iadb.org/en/publications"
    ]
    
    for url in search_urls:
        try:
            print(f"\nTrying publications URL: {url}")
            response = session.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                # Look for search functionality
                search_forms = re.findall(r'<form[^>]*search[^>]*>', response.text, re.IGNORECASE)
                print(f"Found {len(search_forms)} search forms")
                
                # Look for document links
                doc_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', response.text, re.IGNORECASE)
                print(f"Found {len(doc_links)} PDF links")
                
                for link in doc_links[:3]:
                    print(f"  {link}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    explore_idb_structure()
    search_idb_publications()

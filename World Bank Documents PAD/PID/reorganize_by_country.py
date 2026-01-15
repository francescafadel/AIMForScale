#!/usr/bin/env python3
"""
Reorganize downloaded World Bank documents by country.

Moves all PID and PAD documents from the project-based structure to a 
country-based structure where all documents for each country are grouped together.
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

def find_country_directories(results_base_dir):
    """Recursively find all country directories in results."""
    country_dirs = []
    
    def search_directory(directory):
        """Recursively search for country directories."""
        for item in directory.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue
            
            # Check if this directory contains project directories (has PID/PAD subdirs)
            has_projects = False
            for subdir in item.iterdir():
                if subdir.is_dir():
                    if (subdir / "PID").exists() or (subdir / "PAD").exists():
                        has_projects = True
                        break
            
            if has_projects:
                # This is a country directory with projects
                country_dirs.append(item)
            else:
                # This might be a nested results directory, search deeper
                search_directory(item)
    
    search_directory(results_base_dir)
    return country_dirs

def reorganize_documents():
    """Reorganize documents from project-based to country-based structure."""
    
    # Define paths
    base_dir = Path(__file__).parent
    results_dir = base_dir / "results" / "full_downloads"
    new_base_dir = base_dir / "PAD" / "PID"
    
    # Create new directory structure
    new_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    stats = {
        'countries': set(),
        'pid_files': 0,
        'pad_files': 0,
        'errors': []
    }
    
    # Find all country directories recursively
    country_dirs = find_country_directories(results_dir)
    
    print(f"Found {len(country_dirs)} country directories")
    
    # Process each country
    for country_dir in country_dirs:
        country_name = country_dir.name
        stats['countries'].add(country_name)
        
        # Create country directory in new structure
        country_new_dir = new_base_dir / country_name
        country_new_dir.mkdir(exist_ok=True)
        pid_dir = country_new_dir / "PID"
        pad_dir = country_new_dir / "PAD"
        pid_dir.mkdir(exist_ok=True)
        pad_dir.mkdir(exist_ok=True)
        
        print(f"\nProcessing: {country_name}")
        
        # Find all project directories in this country
        project_dirs = [d for d in country_dir.iterdir() if d.is_dir()]
        
        # Process each project
        for project_dir in project_dirs:
            # Process PID directory
            pid_source = project_dir / "PID"
            if pid_source.exists():
                for pdf_file in pid_source.glob("*.pdf"):
                    try:
                        # Create unique filename if duplicate exists
                        dest_file = pid_dir / pdf_file.name
                        counter = 1
                        while dest_file.exists():
                            stem = pdf_file.stem
                            suffix = pdf_file.suffix
                            dest_file = pid_dir / f"{stem}_v{counter}{suffix}"
                            counter += 1
                        
                        shutil.copy2(pdf_file, dest_file)
                        stats['pid_files'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Error copying {pdf_file}: {e}")
            
            # Process PAD directory
            pad_source = project_dir / "PAD"
            if pad_source.exists():
                for pdf_file in pad_source.glob("*.pdf"):
                    try:
                        # Create unique filename if duplicate exists
                        dest_file = pad_dir / pdf_file.name
                        counter = 1
                        while dest_file.exists():
                            stem = pdf_file.stem
                            suffix = pdf_file.suffix
                            dest_file = pad_dir / f"{stem}_v{counter}{suffix}"
                            counter += 1
                        
                        shutil.copy2(pdf_file, dest_file)
                        stats['pad_files'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Error copying {pdf_file}: {e}")
    
    # Print statistics
    print("\n" + "="*60)
    print("REORGANIZATION COMPLETE")
    print("="*60)
    print(f"Countries processed: {len(stats['countries'])}")
    print(f"PID files copied: {stats['pid_files']}")
    print(f"PAD files copied: {stats['pad_files']}")
    print(f"Total files: {stats['pid_files'] + stats['pad_files']}")
    if stats['errors']:
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
    
    print(f"\nNew structure created at: {new_base_dir}")
    print("="*60)

if __name__ == "__main__":
    reorganize_documents()


#!/usr/bin/env python3
"""
Organize IDB Documents by Country
Moves all documents from downloads/ to IDB documents/ organized by country.
For Unknown folder, identifies countries from project codes.
"""

import os
import shutil
from pathlib import Path

# Country code mapping (expanded to include all codes found)
COUNTRY_CODES = {
    'PE': 'Peru', 'CO': 'Colombia', 'AR': 'Argentina', 'BR': 'Brazil',
    'MX': 'Mexico', 'CL': 'Chile', 'BO': 'Bolivia', 'EC': 'Ecuador',
    'PY': 'Paraguay', 'UY': 'Uruguay', 'VE': 'Venezuela', 'GT': 'Guatemala',
    'HN': 'Honduras', 'SV': 'El Salvador', 'NI': 'Nicaragua', 'CR': 'Costa Rica',
    'PA': 'Panama', 'DO': 'Dominican Republic', 'JM': 'Jamaica', 
    'TT': 'Trinidad and Tobago', 'BB': 'Barbados', 'GY': 'Guyana', 
    'SR': 'Suriname', 'HT': 'Haiti', 'RG': 'Regional',
    # Additional codes found in Unknown folder
    'BL': 'Belize', 'CH': 'Chile', 'DR': 'Dominican Republic',
    'ES': 'El Salvador', 'GU': 'Guatemala', 'HA': 'Haiti',
    'HO': 'Honduras', 'ME': 'Mexico', 'PR': 'Paraguay',
    'SU': 'Suriname', 'UR': 'Uruguay'
}

def get_country_from_filename(filename):
    """Extract country from filename based on project code."""
    # Extract project code (e.g., BL-L1041, CH-L1120)
    parts = filename.split('_')
    if parts:
        project_code = parts[0]
        if '-' in project_code:
            country_code = project_code.split('-')[0]
            return COUNTRY_CODES.get(country_code, None)
    return None

def sanitize_folder_name(name):
    """Sanitize folder name for filesystem compatibility."""
    # Replace problematic characters
    name = name.replace(';', '_')
    name = name.replace('/', '_')
    return name

def organize_documents():
    """Organize all documents by country."""
    base_dir = Path(__file__).parent
    downloads_dir = base_dir / "downloads"
    target_dir = base_dir / "IDB documents"
    
    # Create target directory
    target_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    unknown_count = 0
    other_count = 0
    
    print("=" * 80)
    print("ORGANIZING IDB DOCUMENTS BY COUNTRY")
    print("=" * 80)
    
    # Process all country folders in downloads
    for country_folder in downloads_dir.iterdir():
        if not country_folder.is_dir():
            continue
            
        country_name = country_folder.name
        
        # Skip if it's a system folder
        if country_name.startswith('.'):
            continue
        
        print(f"\nProcessing: {country_name}")
        
        # Handle Unknown folder specially
        if country_name == "Unknown":
            print("  Identifying countries from project codes...")
            for file in country_folder.iterdir():
                if file.is_file() and file.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    country = get_country_from_filename(file.name)
                    if country:
                        target_country_dir = target_dir / sanitize_folder_name(country)
                        target_country_dir.mkdir(exist_ok=True)
                        shutil.copy2(file, target_country_dir / file.name)
                        print(f"    {file.name} -> {country}")
                        moved_count += 1
                    else:
                        # Can't identify, put in Other
                        other_dir = target_dir / "Other"
                        other_dir.mkdir(exist_ok=True)
                        shutil.copy2(file, other_dir / file.name)
                        print(f"    {file.name} -> Other (unidentified)")
                        other_count += 1
        else:
            # Regular country folder - move all files
            target_country_dir = target_dir / sanitize_folder_name(country_name)
            target_country_dir.mkdir(exist_ok=True)
            
            files_moved = 0
            for file in country_folder.iterdir():
                if file.is_file() and file.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    shutil.copy2(file, target_country_dir / file.name)
                    files_moved += 1
                    moved_count += 1
            
            print(f"  Moved {files_moved} files to {country_name}")
    
    print(f"\n" + "=" * 80)
    print(f"ORGANIZATION COMPLETE")
    print(f"=" * 80)
    print(f"Total files moved: {moved_count}")
    print(f"Files identified from Unknown: {moved_count - other_count}")
    print(f"Files in Other folder: {other_count}")
    print(f"\nDocuments organized in: {target_dir}")
    
    # List all countries
    print(f"\nCountries with documents:")
    for country_dir in sorted(target_dir.iterdir()):
        if country_dir.is_dir():
            file_count = len(list(country_dir.glob("*.*")))
            if file_count > 0:
                print(f"  {country_dir.name}: {file_count} documents")

if __name__ == "__main__":
    organize_documents()


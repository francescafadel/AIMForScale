#!/usr/bin/env python3
"""
Fix File Organization Script
============================
This script fixes the file organization issue by properly sorting all downloaded
documents into their respective country folders.
"""

import pandas as pd
import re
from pathlib import Path
import shutil

class FileOrganizationFixer:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.tracking_file = "final_comprehensive_tracking.csv"
        self.tracking_data = []
        
    def load_tracking_data(self):
        """Load tracking data from CSV."""
        try:
            df = pd.read_csv(self.tracking_file)
            self.tracking_data = df.to_dict('records')
            print(f"Loaded tracking data for {len(self.tracking_data)} projects")
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            return False
        return True
    
    def organize_downloaded_files(self):
        """Organize downloaded files into country directories."""
        try:
            print("\nOrganizing downloaded files...")
            
            # Get all document files in the downloads directory (PDF, DOCX, etc.)
            document_extensions = ['*.pdf', '*.docx', '*.doc', '*.xlsx', '*.xls', 
                                 '*.PDF', '*.DOCX', '*.DOC', '*.XLSX', '*.XLS']
            all_files = []
            for ext in document_extensions:
                all_files.extend(list(self.downloads_dir.glob(ext)))
            
            print(f"Found {len(all_files)} document files to organize...")
            
            moved_count = 0
            skipped_count = 0
            error_count = 0
            
            for file_path in all_files:
                filename = file_path.name
                print(f"Processing: {filename}")
                
                # Try multiple patterns to extract project number or operation number
                project_number = None
                operation_number = None
                
                # Pattern 1: Standard project format (PE-L1187, CO-M1089, etc.)
                project_match = re.search(r'([A-Z]{2}-[A-Z]\d+)', filename)
                if project_match:
                    project_number = project_match.group(1)
                
                # Pattern 2: Operation number format (ATN_ME-14908-PR, ATN_ME-13560-CO, etc.)
                operation_match = re.search(r'(ATN_[A-Z]+-\d+-[A-Z]+)', filename)
                if operation_match:
                    operation_number = operation_match.group(1)
                
                # Pattern 3: Look for project numbers in the filename with different formats
                if not project_number:
                    patterns = [
                        r'([A-Z]{2}-[A-Z]\d+)',  # PE-L1187, CO-M1089
                        r'([A-Z]{2}-[A-Z]\d{4})',  # PE-L1187, CO-M1089
                        r'([A-Z]{2}-[A-Z]\d{3})',  # PE-L1187, CO-M1089
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, filename)
                        if match:
                            project_number = match.group(1)
                            break
                
                # Pattern 4: Look for project numbers in the filename without hyphens
                if not project_number:
                    match = re.search(r'([A-Z]{2}[A-Z]\d+)', filename)
                    if match:
                        raw_number = match.group(1)
                        if len(raw_number) >= 6:
                            project_number = f"{raw_number[:2]}-{raw_number[2:]}"
                
                if project_number:
                    print(f"  Extracted project number: {project_number}")
                    
                    # Find the project in our tracking data to get country
                    country = None
                    for project_data in self.tracking_data:
                        if project_data['project_number'] == project_number:
                            country = project_data['country']
                            break
                    
                    if country:
                        # Create country directory
                        country_dir = self.downloads_dir / country
                        country_dir.mkdir(exist_ok=True)
                        
                        # Move file to country directory
                        new_path = country_dir / filename
                        if not new_path.exists():
                            shutil.move(str(file_path), str(new_path))
                            print(f"  ✓ Moved {filename} to {country}/")
                            moved_count += 1
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                            skipped_count += 1
                    else:
                        print(f"  ❌ Could not determine country for {filename} (project: {project_number})")
                        error_count += 1
                
                elif operation_number:
                    print(f"  Extracted operation number: {operation_number}")
                    
                    # Find the project in our tracking data to get country
                    country = None
                    for project_data in self.tracking_data:
                        # Convert operation number format for comparison
                        # ATN_ME-14908-PR -> ATN/ME-14908-PR
                        normalized_op = operation_number.replace('_', '/')
                        if project_data['operation_number'] == normalized_op:
                            country = project_data['country']
                            break
                    
                    if country:
                        # Create country directory
                        country_dir = self.downloads_dir / country
                        country_dir.mkdir(exist_ok=True)
                        
                        # Move file to country directory
                        new_path = country_dir / filename
                        if not new_path.exists():
                            shutil.move(str(file_path), str(new_path))
                            print(f"  ✓ Moved {filename} to {country}/")
                            moved_count += 1
                        else:
                            print(f"  ⚠ File {filename} already exists in {country}/")
                            skipped_count += 1
                    else:
                        print(f"  ❌ Could not determine country for {filename} (operation: {operation_number})")
                        error_count += 1
                else:
                    print(f"  ❌ Could not extract project or operation number from {filename}")
                    error_count += 1
            
            print(f"\nOrganization Summary:")
            print(f"  ✓ Files moved: {moved_count}")
            print(f"  ⚠ Files skipped (already exists): {skipped_count}")
            print(f"  ❌ Files with errors: {error_count}")
                    
        except Exception as e:
            print(f"Error organizing files: {e}")
            import traceback
            traceback.print_exc()
    
    def show_current_organization(self):
        """Show current file organization status."""
        print("\nCurrent file organization status:")
        print("="*50)
        
        # Show files in main downloads directory
        main_files = []
        for ext in ['*.pdf', '*.docx', '*.doc', '*.xlsx', '*.xls', 
                   '*.PDF', '*.DOCX', '*.DOC', '*.XLSX', '*.XLS']:
            main_files.extend(list(self.downloads_dir.glob(ext)))
        
        if main_files:
            print(f"\nFiles in main downloads directory ({len(main_files)}):")
            for file_path in main_files:
                print(f"  - {file_path.name}")
        else:
            print("\nNo document files in main downloads directory")
        
        # Show files in country directories
        country_dirs = [d for d in self.downloads_dir.iterdir() if d.is_dir()]
        if country_dirs:
            print(f"\nFiles in country directories:")
            for country_dir in country_dirs:
                country_files = []
                for ext in ['*.pdf', '*.docx', '*.doc', '*.xlsx', '*.xls',
                           '*.PDF', '*.DOCX', '*.DOC', '*.XLSX', '*.XLS']:
                    country_files.extend(list(country_dir.glob(ext)))
                
                if country_files:
                    print(f"\n  {country_dir.name} ({len(country_files)} files):")
                    for file_path in country_files:
                        print(f"    - {file_path.name}")
                else:
                    print(f"\n  {country_dir.name} (empty)")

def main():
    fixer = FileOrganizationFixer()
    
    # Show current organization
    fixer.show_current_organization()
    
    # Load tracking data
    if not fixer.load_tracking_data():
        print("Failed to load tracking data. Exiting.")
        return
    
    # Organize files
    fixer.organize_downloaded_files()
    
    # Show final organization
    print("\n" + "="*50)
    fixer.show_current_organization()
    
    print("\nFile organization fix completed!")

if __name__ == "__main__":
    main()

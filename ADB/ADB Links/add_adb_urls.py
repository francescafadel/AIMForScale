#!/usr/bin/env python3
"""
Script to add ADB project URLs to the Final ADB Corpus CSV file.
Detects the Project ID column and creates hyperlinks to ADB project pages.
"""

import pandas as pd
import re
from pathlib import Path

def find_project_id_column(df):
    """
    Find the Project ID column in the DataFrame.
    First checks for a column explicitly named 'Project ID'.
    If not found, detects a column where most values match the pattern: ^\d{5}-\d{3}$
    """
    # Check for explicit 'Project ID' column
    if 'Project ID' in df.columns:
        return 'Project ID'
    
    # Pattern for ADB project IDs: 5 digits, dash, 3 digits
    pattern = re.compile(r'^\d{5}-\d{3}$')
    
    # Check each column
    for col in df.columns:
        # Skip columns with 'method' in the name (methodology descriptions)
        if 'method' in col.lower():
            continue
            
        # Count how many non-null values match the pattern
        non_null_values = df[col].dropna().astype(str)
        if len(non_null_values) == 0:
            continue
            
        matches = non_null_values.apply(lambda x: bool(pattern.match(x.strip())))
        match_ratio = matches.sum() / len(non_null_values)
        
        # If more than 80% of values match the pattern, consider it the Project ID column
        if match_ratio > 0.8:
            return col
    
    raise ValueError("Could not find a Project ID column. Please check your CSV file.")

def create_adb_url(project_id):
    """
    Create an ADB project URL from a project ID.
    Returns the URL if project_id matches the expected pattern, otherwise returns None.
    """
    if pd.isna(project_id):
        return None
    
    project_id_str = str(project_id).strip()
    
    # Check if it matches the expected pattern
    pattern = re.compile(r'^\d{5}-\d{3}$')
    if pattern.match(project_id_str):
        return f"https://www.adb.org/projects/{project_id_str}/main"
    else:
        return None

def main():
    # Define file paths
    input_file = Path(__file__).parent / "Final ADB Corpus - Sheet1.csv"
    output_file = Path(__file__).parent / "Final ADB Corpus - Sheet1_with_urls.csv"
    
    print(f"Loading CSV file: {input_file}")
    
    # Load the CSV file
    # The file has methodology text in the first 5 rows, so skip them
    df = pd.read_csv(input_file, skiprows=5, encoding='utf-8')
    
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    # Find the Project ID column
    project_id_col = find_project_id_column(df)
    print(f"\nDetected Project ID column: '{project_id_col}'")
    
    # Create the ADB URL column
    print("\nCreating ADB URL column...")
    df['ADB URL'] = df[project_id_col].apply(create_adb_url)
    
    # Count how many URLs were created
    url_count = df['ADB URL'].notna().sum()
    print(f"Created {url_count} URLs out of {len(df)} total rows")
    
    # Save to new CSV file
    print(f"\nSaving to: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("✓ File saved successfully!")
    
    # Display sample results
    print("\n" + "="*80)
    print("SAMPLE RESULTS (First 5 rows)")
    print("="*80)
    
    # Show only Project ID and ADB URL columns for clarity
    display_cols = [project_id_col, 'ADB URL']
    if 'Name' in df.columns:
        display_cols.insert(1, 'Name')
    
    print(df[display_cols].head().to_string(index=False))
    print("\n" + "="*80)
    print(f"✓ Complete! Check '{output_file.name}' for the full results.")

if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""
Test script to demonstrate keyword matching functionality.
This script creates sample data and shows how the keyword matching works.
"""

import pandas as pd
from pdf_keyword_scanner import load_keywords, find_keywords_in_text

def create_sample_data():
    """Create sample project data for testing."""
    sample_data = {
        'Project Name': [
            'Dairy Farm Development Project',
            'Beef Cattle Health Initiative',
            'Poultry Feed Efficiency Program',
            'Sustainable Agriculture Project',
            'Water Management System',
            'Livestock Market Access',
            'Goat Genetics Improvement',
            'Pasture Management Training'
        ],
        'Project Description': [
            'This project focuses on improving dairy production through modern farming techniques and milk processing facilities.',
            'Enhancing beef cattle health through veterinary services and disease prevention measures.',
            'Improving feed efficiency for poultry farms to reduce costs and increase protein production.',
            'General agricultural development with focus on crop production and soil health.',
            'Water conservation and irrigation systems for agricultural use.',
            'Connecting livestock farmers to markets and improving meat and dairy exports.',
            'Genetic improvement program for goat herds to increase milk and meat production.',
            'Training farmers in pasture management and grazing techniques for sustainable livestock farming.'
        ]
    }
    return pd.DataFrame(sample_data)

def test_keyword_matching():
    """Test the keyword matching functionality."""
    print("Testing PDF Keyword Scanner")
    print("=" * 50)
    
    # Load keywords
    keywords = load_keywords('keywords.txt')
    print(f"Loaded {len(keywords)} keywords")
    print(f"Keywords: {', '.join(keywords[:10])}...")
    print()
    
    # Create sample data
    df = create_sample_data()
    print("Sample Project Data:")
    print(df.to_string(index=False))
    print()
    
    # Test keyword matching
    print("Testing keyword matching on sample data:")
    print("-" * 50)
    
    for idx, (_, row) in enumerate(df.iterrows()):
        name_keywords = find_keywords_in_text(str(row['Project Name']), keywords)
        desc_keywords = find_keywords_in_text(str(row['Project Description']), keywords)
        
        print(f"Project {idx + 1}: {row['Project Name']}")
        print(f"  Keywords in Name: {name_keywords if name_keywords else 'None'}")
        print(f"  Keywords in Description: {desc_keywords if desc_keywords else 'None'}")
        print()
    
    # Add keyword columns to sample data
    df['Keywords Found in Project Name'] = df['Project Name'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    df['Keywords Found in Project Description'] = df['Project Description'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    
    print("Final DataFrame with Keyword Columns:")
    print(df[['Project Name', 'Keywords Found in Project Name', 'Keywords Found in Project Description']].to_string(index=False))
    
    # Save sample results
    df.to_csv('sample_results.csv', index=False)
    print(f"\nSample results saved to: sample_results.csv")

if __name__ == "__main__":
    test_keyword_matching() 
import pandas as pd
import PyPDF2
import tabula
import re
import sys
import os
from typing import List, Dict, Tuple

def load_keywords(keywords_file: str) -> List[str]:
    """
    Load keywords from a text file.
    
    Args:
        keywords_file (str): Path to the keywords file
        
    Returns:
        List[str]: List of keywords
    """
    try:
        with open(keywords_file, 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
        return keywords
    except FileNotFoundError:
        print(f"Error: Keywords file '{keywords_file}' not found.")
        return []

def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract tables from PDF using tabula-py.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[pd.DataFrame]: List of DataFrames extracted from the PDF
    """
    try:
        # Extract all tables from the PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
        return []

def find_keywords_in_text(text: str, keywords: List[str]) -> List[str]:
    """
    Find keywords in text with case-sensitive matching.
    
    Args:
        text (str): Text to search in
        keywords (List[str]): List of keywords to search for
        
    Returns:
        List[str]: List of found keywords
    """
    if not text or pd.isna(text):
        return []
    
    text_str = str(text)
    found_keywords = []
    
    for keyword in keywords:
        # Use word boundaries to match whole words only
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_str):
            found_keywords.append(keyword)
    
    return found_keywords

def process_pdf_data(pdf_path: str, keywords: List[str]) -> pd.DataFrame:
    """
    Process PDF data and add keyword columns.
    
    Args:
        pdf_path (str): Path to the PDF file
        keywords (List[str]): List of keywords to search for
        
    Returns:
        pd.DataFrame: DataFrame with original data and keyword columns
    """
    # Extract tables from PDF
    tables = extract_tables_from_pdf(pdf_path)
    
    if not tables:
        print("No tables found in the PDF.")
        return pd.DataFrame()
    
    # Find the table with Project Name and Project Description columns
    target_df = None
    for i, df in enumerate(tables):
        columns = [col.lower() for col in df.columns]
        if 'project name' in columns and 'project description' in columns:
            target_df = df.copy()
            print(f"Found table {i+1} with required columns")
            break
    
    if target_df is None:
        print("No table found with both 'Project Name' and 'Project Description' columns.")
        print("Available columns in tables:")
        for i, df in enumerate(tables):
            print(f"Table {i+1}: {list(df.columns)}")
        return pd.DataFrame()
    
    # Add keyword columns
    target_df['Keywords Found in Project Name'] = target_df['Project Name'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    
    target_df['Keywords Found in Project Description'] = target_df['Project Description'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    
    return target_df

def save_results(df: pd.DataFrame, output_path: str):
    """
    Save results to CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame to save
        output_path (str): Output file path
    """
    try:
        df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")

def main():
    """
    Main function to process PDF and find keywords.
    """
    if len(sys.argv) < 2:
        print("Usage: python pdf_keyword_scanner.py <pdf_file_path>")
        print("Example: python pdf_keyword_scanner.py projects.pdf")
        return
    
    pdf_path = sys.argv[1]
    keywords_file = "keywords.txt"
    
    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        return
    
    # Load keywords
    keywords = load_keywords(keywords_file)
    if not keywords:
        print("No keywords loaded. Please check the keywords.txt file.")
        return
    
    print(f"Loaded {len(keywords)} keywords: {', '.join(keywords)}")
    
    # Process PDF
    print(f"Processing PDF: {pdf_path}")
    result_df = process_pdf_data(pdf_path, keywords)
    
    if result_df.empty:
        print("No data to process.")
        return
    
    # Display results
    print(f"\nProcessed {len(result_df)} rows of data.")
    print("\nSample results:")
    print(result_df[['Project Name', 'Keywords Found in Project Name', 'Keywords Found in Project Description']].head())
    
    # Save results
    output_path = pdf_path.replace('.pdf', '_with_keywords.csv')
    save_results(result_df, output_path)
    
    # Summary statistics
    name_matches = result_df['Keywords Found in Project Name'].apply(len)
    desc_matches = result_df['Keywords Found in Project Description'].apply(len)
    
    print(f"\nSummary:")
    print(f"Projects with keywords in name: {sum(name_matches > 0)}")
    print(f"Projects with keywords in description: {sum(desc_matches > 0)}")
    print(f"Total keyword matches in names: {sum(name_matches)}")
    print(f"Total keyword matches in descriptions: {sum(desc_matches)}")

if __name__ == "__main__":
    main() 
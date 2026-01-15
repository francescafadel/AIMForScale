#!/usr/bin/env python3
"""
CSV Keyword Scanner - Enhanced livestock keyword detection for CSV files.
Processes existing CSV files and adds keyword columns with robust matching.
"""

import pandas as pd
import re
import sys
import os
import unicodedata
from typing import List, Dict

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

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent matching.
    """
    if not text or pd.isna(text):
        return ""
    
    text_str = str(text)
    
    # Unicode normalization
    text_str = unicodedata.normalize('NFKC', text_str)
    
    # Replace non-breaking spaces and hyphens
    text_str = text_str.replace('\u00A0', ' ')  # non-breaking space
    text_str = text_str.replace('\u2011', '-')  # non-breaking hyphen
    text_str = text_str.replace('–', '-')  # en dash
    text_str = text_str.replace('—', '-')  # em dash
    
    # Remove HTML tags
    text_str = re.sub(r'<br\s*/?>', ' ', text_str, flags=re.IGNORECASE)
    
    # Remove accents by decomposing and keeping only base characters
    text_str = ''.join(
        char for char in unicodedata.normalize('NFD', text_str)
        if not unicodedata.combining(char)
    )
    
    # Normalize separators (underscores, slashes) to spaces
    text_str = text_str.replace('_', ' ')
    text_str = text_str.replace('/', ' ')
    
    # Collapse whitespace
    text_str = re.sub(r'\s+', ' ', text_str)
    
    # Case fold for case-insensitive matching
    return text_str.casefold().strip()

def compile_keyword_patterns(keywords: List[str]) -> Dict[str, re.Pattern]:
    """
    Compile regex patterns for each keyword to handle PDF formatting issues.
    Enhanced to handle various separators and multi-word keywords.
    
    Args:
        keywords (List[str]): List of keywords
        
    Returns:
        Dict[str, re.Pattern]: Dictionary mapping original keywords to compiled patterns
    """
    patterns = {}
    
    for keyword in keywords:
        # Normalize the keyword
        normalized_keyword = normalize_text(keyword)
        
        # Enhanced pattern for better separator handling
        if ' ' in normalized_keyword:  # Multi-word keyword
            # Handle various separators between words
            words = normalized_keyword.split()
            pattern_parts = []
            for word in words:
                pattern_parts.append(r'\b' + re.escape(word) + r'\b')
            pattern_str = r'[\s\-_/]+'.join(pattern_parts)
        else:  # Single word keyword
            # Allow optional separators within the word
            pattern_parts = []
            for char in normalized_keyword:
                if char.isalnum():
                    pattern_parts.append(f"{re.escape(char)}[\\s\\u00A0\\-_/]*")
                else:
                    pattern_parts.append(re.escape(char))
            pattern_str = r'\b' + ''.join(pattern_parts) + r'\b'
        
        try:
            patterns[keyword] = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
        except re.error:
            # Fallback to simple pattern if complex pattern fails
            patterns[keyword] = re.compile(r'\b' + re.escape(normalized_keyword) + r'\b', re.IGNORECASE | re.UNICODE)
    
    return patterns

def find_keywords_in_text(text: str, keyword_patterns: Dict[str, re.Pattern]) -> List[str]:
    """
    Find keywords in text using compiled patterns for robust matching.
    
    Args:
        text (str): Text to search in
        keyword_patterns (Dict[str, re.Pattern]): Dictionary of compiled patterns
        
    Returns:
        List[str]: List of found keywords (original case preserved)
    """
    if not text or pd.isna(text):
        return []
    
    # Normalize the text for matching
    normalized_text = normalize_text(text)
    
    found_keywords = []
    
    for keyword, pattern in keyword_patterns.items():
        if pattern.search(normalized_text):
            found_keywords.append(keyword)  # Return original keyword case
    
    return found_keywords

def process_csv_keywords(csv_path: str, keywords: List[str], text_columns: List[str]) -> pd.DataFrame:
    """
    Process existing CSV file and add keyword columns.
    
    Args:
        csv_path (str): Path to the CSV file
        keywords (List[str]): List of keywords to search for
        text_columns (List[str]): List of column names to search in
        
    Returns:
        pd.DataFrame: DataFrame with original data and keyword columns
    """
    # Load CSV
    print(f"Loading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Compile keyword patterns
    keyword_patterns = compile_keyword_patterns(keywords)
    
    # Add keyword columns for each text column
    for col in text_columns:
        if col in df.columns:
            print(f"Processing column: {col}")
            df[f'Keywords Found in {col}'] = df[col].apply(
                lambda x: find_keywords_in_text(x, keyword_patterns)
            )
        else:
            print(f"Warning: Column '{col}' not found in CSV. Available columns: {list(df.columns)}")
            df[f'Keywords Found in {col}'] = [[]] * len(df)
    
    # Add union column
    keyword_cols = [f'Keywords Found in {col}' for col in text_columns if col in df.columns]
    if keyword_cols:
        print(f"Creating union column from: {keyword_cols}")
        df['Keywords Found (Any Column)'] = df.apply(
            lambda row: sorted(list(set(
                [kw for col in keyword_cols for kw in row[col]]
            ))), axis=1
        )
    else:
        df['Keywords Found (Any Column)'] = [[]] * len(df)
    
    return df

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

def analyze_results(df: pd.DataFrame, text_columns: List[str]):
    """
    Analyze and display keyword matching results.
    
    Args:
        df (pd.DataFrame): DataFrame with keyword results
        text_columns (List[str]): List of text columns that were searched
    """
    print("\n" + "=" * 60)
    print("📊 KEYWORD MATCHING ANALYSIS")
    print("=" * 60)
    
    # Calculate statistics for each column
    for col in text_columns:
        keyword_col = f'Keywords Found in {col}'
        if keyword_col in df.columns:
            matches = df[keyword_col].apply(len)
            rows_with_matches = sum(matches > 0)
            total_matches = sum(matches)
            print(f"\n{col}:")
            print(f"  Rows with keywords: {rows_with_matches}/{len(df)} ({rows_with_matches/len(df)*100:.1f}%)")
            print(f"  Total keyword matches: {total_matches}")
    
    # Overall statistics
    if 'Keywords Found (Any Column)' in df.columns:
        any_matches = df['Keywords Found (Any Column)'].apply(len)
        rows_with_any = sum(any_matches > 0)
        total_any_matches = sum(any_matches)
        print(f"\nOverall Results:")
        print(f"  Rows with any keywords: {rows_with_any}/{len(df)} ({rows_with_any/len(df)*100:.1f}%)")
        print(f"  Total unique keyword matches: {total_any_matches}")
    
    # Show top keywords found
    print(f"\n🔍 Top Keywords Found:")
    all_keywords = []
    for col in text_columns:
        keyword_col = f'Keywords Found in {col}'
        if keyword_col in df.columns:
            for keywords in df[keyword_col]:
                all_keywords.extend(keywords)
    
    if all_keywords:
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)
        for keyword, count in top_keywords:
            print(f"  {keyword}: {count} matches")
    
    # Show sample rows with matches
    print(f"\n📋 Sample Rows with Keywords:")
    if 'Keywords Found (Any Column)' in df.columns:
        rows_with_keywords = df[df['Keywords Found (Any Column)'].apply(len) > 0]
        if not rows_with_keywords.empty:
            sample_size = min(5, len(rows_with_keywords))
            sample_rows = rows_with_keywords.head(sample_size)
            
            for idx, row in sample_rows.iterrows():
                print(f"\nRow {idx + 1}:")
                for col in text_columns:
                    if col in df.columns:
                        keywords = row.get(f'Keywords Found in {col}', [])
                        if keywords:
                            print(f"  {col}: {keywords}")

def main():
    """
    Main function to process CSV and find keywords.
    """
    if len(sys.argv) < 2:
        print("Usage: python csv_keyword_scanner.py <csv_file_path> [text_columns...]")
        print("Example: python csv_keyword_scanner.py projects.csv 'Project Name' 'Description' 'Agency'")
        print("\nIf no text columns specified, will search all columns.")
        return
    
    csv_path = sys.argv[1]
    
    # Look for keywords file in updated/ folder first, then config/, then current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    keywords_file = None
    
    for path in [
        os.path.join(project_root, "updated", "keywords.txt"),
        os.path.join(project_root, "config", "keywords.txt"),
        "keywords.txt"
    ]:
        if os.path.exists(path):
            keywords_file = path
            break
    
    if not keywords_file:
        print("Error: keywords.txt not found in updated/, config/, or current directory.")
        return
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return
    
    # Load keywords
    keywords = load_keywords(keywords_file)
    if not keywords:
        print("No keywords loaded. Please check the keywords.txt file.")
        return
    
    print(f"Loaded {len(keywords)} keywords from {keywords_file}")
    
    # Determine which columns to search
    if len(sys.argv) > 2:
        text_columns = sys.argv[2:]
        print(f"Will search in specified columns: {text_columns}")
    else:
        # Load CSV to see available columns
        df_sample = pd.read_csv(csv_path, nrows=1)
        text_columns = list(df_sample.columns)
        print(f"No columns specified. Will search in all columns: {text_columns}")
    
    # Process CSV
    print(f"\nProcessing CSV: {csv_path}")
    result_df = process_csv_keywords(csv_path, keywords, text_columns)
    
    if result_df.empty:
        print("No data to process.")
        return
    
    # Analyze results
    analyze_results(result_df, text_columns)
    
    # Save results
    output_path = csv_path.replace('.csv', '_with_keywords.csv')
    save_results(result_df, output_path)
    
    print(f"\n✅ Processing complete!")
    print(f"📁 Original file: {csv_path}")
    print(f"📁 Output file: {output_path}")
    print(f"📊 Processed {len(result_df)} rows")

if __name__ == "__main__":
    main()

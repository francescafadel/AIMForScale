import pandas as pd
import PyPDF2
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

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using PyPDF2.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def parse_text_to_dataframe(text: str) -> pd.DataFrame:
    """
    Parse extracted text to find project data.
    This function looks for patterns that might indicate project names and descriptions.
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        pd.DataFrame: DataFrame with Project Name and Project Description columns
    """
    lines = text.split('\n')
    projects = []
    
    # Look for patterns that might indicate project data
    current_project = {"Project Name": "", "Project Description": ""}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # If we find a line that looks like a project name (shorter, might be in caps)
        if len(line) < 100 and not line.startswith(' ') and len(line.split()) <= 10:
            # Save previous project if we have one
            if current_project["Project Name"]:
                projects.append(current_project.copy())
            
            # Start new project
            current_project = {"Project Name": line, "Project Description": ""}
        
        # If we have a project name and this line looks like a description (longer)
        elif current_project["Project Name"] and len(line) > 20:
            if current_project["Project Description"]:
                current_project["Project Description"] += " " + line
            else:
                current_project["Project Description"] = line
    
    # Add the last project
    if current_project["Project Name"]:
        projects.append(current_project)
    
    # If we didn't find any projects with the pattern approach, try a different method
    if not projects:
        print("No projects found with pattern matching. Trying alternative approach...")
        return parse_text_alternative(text)
    
    return pd.DataFrame(projects)

def parse_text_alternative(text: str) -> pd.DataFrame:
    """
    Alternative parsing method that looks for specific keywords or patterns.
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        pd.DataFrame: DataFrame with Project Name and Project Description columns
    """
    # Split text into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    projects = []
    for i, para in enumerate(paragraphs):
        if len(para) > 20:  # Only consider substantial paragraphs
            # Use paragraph number as project name if we can't identify a clear name
            project_name = f"Project {i+1}"
            project_desc = para
            
            projects.append({
                "Project Name": project_name,
                "Project Description": project_desc
            })
    
    return pd.DataFrame(projects)

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
    # Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("No text extracted from the PDF.")
        return pd.DataFrame()
    
    print(f"Extracted {len(text)} characters of text.")
    
    # Parse text to DataFrame
    print("Parsing text to find project data...")
    df = parse_text_to_dataframe(text)
    
    if df.empty:
        print("No project data found in the PDF.")
        return pd.DataFrame()
    
    print(f"Found {len(df)} potential projects.")
    
    # Add keyword columns
    df['Keywords Found in Project Name'] = df['Project Name'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    
    df['Keywords Found in Project Description'] = df['Project Description'].apply(
        lambda x: find_keywords_in_text(x, keywords)
    )
    
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

def main():
    """
    Main function to process PDF and find keywords.
    """
    if len(sys.argv) < 2:
        print("Usage: python pdf_keyword_scanner_alternative.py <pdf_file_path>")
        print("Example: python pdf_keyword_scanner_alternative.py projects.pdf")
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
    
    print(f"Loaded {len(keywords)} keywords: {', '.join(keywords[:10])}...")
    
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
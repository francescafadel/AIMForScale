import pandas as pd
import PyPDF2
import re
import sys
import os
import unicodedata
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

def parse_table_structure(text: str) -> pd.DataFrame:
    """
    Parse the PDF text to extract table data with all columns.
    This function looks for the actual project data table structure.
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        pd.DataFrame: DataFrame with all original columns
    """
    lines = text.split('\n')
    
    # Look for the header row that contains column names
    header_found = False
    header_line = None
    data_start_line = None
    
    # Common World Bank project table headers
    expected_headers = [
        'Project Id', 'Region', 'Country', 'Project Status', 'Project Name', 
        'Project Development Objective', 'Implementing Agency', 'Project URL',
        'Disclosure Date', 'Board Approval Date', 'Effective Date', 'Project Closing Date',
        'Last Stage Reached', 'Financing Type', 'Total Project Cost $US', 'IBRD Commitment $US', 'IDA Commitment $US'
    ]
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check if this line contains multiple expected headers
        header_matches = sum(1 for header in expected_headers if header.lower() in line_clean.lower())
        if header_matches >= 3:  # If we find at least 3 expected headers, this is likely the header row
            header_found = True
            header_line = i
            data_start_line = i + 1
            print(f"Found header row at line {i}: {line_clean}")
            break
    
    if not header_found:
        print("Could not find standard table header. Trying alternative parsing...")
        return parse_text_alternative_improved(text)
    
    # Extract the header row and determine column positions
    header_text = lines[header_line] if header_line is not None else ""
    print(f"Header text: {header_text}")
    
    # Try to split the header into columns
    # Look for common delimiters or patterns
    columns = []
    
    # Try different splitting approaches
    if '\t' in header_text:
        columns = header_text.split('\t')
    elif '  ' in header_text:  # Multiple spaces
        columns = [col.strip() for col in re.split(r'\s{2,}', header_text)]
    else:
        # Try to identify columns by looking for common patterns
        columns = identify_columns_from_text(header_text)
    
    print(f"Identified columns: {columns}")
    
    # Extract and merge data rows
    start_line = data_start_line if data_start_line is not None else 0
    data_rows = merge_incomplete_rows(lines, start_line, columns)
    
    # Force use of alternative parsing method which handles the data better
    print("Using alternative parsing method for better data extraction...")
    df = parse_text_alternative_improved(text)
    
    # Validate and clean the DataFrame
    df = validate_dataframe_alignment(df)
    
    return df

def identify_columns_from_text(header_text: str) -> List[str]:
    """
    Try to identify column boundaries in header text.
    
    Args:
        header_text (str): The header row text
        
    Returns:
        List[str]: List of column names
    """
    # Look for common World Bank project table patterns
    patterns = [
        r'Project\s+Id',
        r'Region',
        r'Country',
        r'Project\s+Status',
        r'Project\s+Name',
        r'Project\s+Development\s+Objective',
        r'Implementing\s+Agency',
        r'Project\s+URL',
        r'Disclosure\s+Date',
        r'Board\s+Approval\s+Date',
        r'Effective\s+Date',
        r'Project\s+Closing\s+Date',
        r'Last\s+Stage\s+Reached',
        r'Financing\s+Type',
        r'Total\s+Project\s+Cost\s+\$US',
        r'IBRD\s+Commitment\s+\$US',
        r'IDA\s+Commitment\s+\$US'
    ]
    
    columns = []
    for pattern in patterns:
        match = re.search(pattern, header_text, re.IGNORECASE)
        if match:
            columns.append(match.group())
    
    if not columns:
        # Fallback: split by common delimiters
        if ',' in header_text:
            columns = [col.strip() for col in header_text.split(',')]
        else:
            columns = [header_text.strip()]
    
    return columns

def parse_row_data(row_text: str, expected_columns: int) -> List[str]:
    """
    Parse a data row into columns.
    
    Args:
        row_text (str): The row text
        expected_columns (int): Expected number of columns
        
    Returns:
        List[str]: List of column values
    """
    # Try different parsing strategies
    if ',' in row_text:
        return [col.strip() for col in row_text.split(',')]
    elif '\t' in row_text:
        return [col.strip() for col in row_text.split('\t')]
    else:
        # Split by multiple spaces
        return [col.strip() for col in re.split(r'\s{2,}', row_text)]

def clean_cell_text(text: str) -> str:
    """
    Clean cell text by replacing newlines and HTML tags with spaces.
    
    Args:
        text (str): Raw cell text
        
    Returns:
        str: Cleaned cell text
    """
    if not text or pd.isna(text):
        return ""
    
    text_str = str(text)
    
    # Replace newlines with spaces
    text_str = text_str.replace('\n', ' ')
    text_str = text_str.replace('\r', ' ')
    
    # Replace HTML <br> tags with spaces
    text_str = re.sub(r'<br\s*/?>', ' ', text_str, flags=re.IGNORECASE)
    
    # Collapse multiple spaces
    text_str = re.sub(r'\s+', ' ', text_str)
    
    return text_str.strip()

def merge_incomplete_rows(lines: List[str], start_line: int, columns: List[str]) -> List[List[str]]:
    """
    Extract and merge data rows, handling multi-line cells and incomplete rows.
    
    Args:
        lines (List[str]): All lines from the PDF
        start_line (int): Starting line for data extraction
        columns (List[str]): Column names
        
    Returns:
        List[List[str]]: List of complete data rows
    """
    data_rows = []
    current_row = [''] * len(columns)
    current_row_index = 0
    
    for i in range(start_line, len(lines)):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Skip methodology and instruction lines
        if any(skip_word in line.lower() for skip_word in ['methodology', 'open world bank', 'click', 'apply', 'download', 'filter']):
            continue
        
        # Check if this looks like a new row (has Project ID pattern)
        project_id_pattern = r'P\d{6}'
        has_project_id = bool(re.search(project_id_pattern, line))
        
        if has_project_id and current_row[0]:  # New row with Project ID, save previous row
            # Clean and save the previous row
            cleaned_row = [clean_cell_text(cell) for cell in current_row]
            if any(cell.strip() for cell in cleaned_row):  # Only add non-empty rows
                data_rows.append(cleaned_row)
            
            # Start new row
            current_row = [''] * len(columns)
            current_row_index = 0
        
        # Try to parse this line as a data row
        if '\t' in line:
            row_data = line.split('\t')
        elif '  ' in line:  # Multiple spaces
            row_data = [col.strip() for col in re.split(r'\s{2,}', line)]
        else:
            row_data = parse_row_data(line, len(columns))
        
        if has_project_id:  # Row with Project ID
            # Fill the new row with available data
            for j, value in enumerate(row_data):
                if j < len(current_row):
                    current_row[j] = value
                    current_row_index = j + 1
        
        else:  # Continuation of current row
            # Try to merge with the current row
            if current_row_index < len(current_row):
                # Append to the last non-empty cell
                if current_row[current_row_index - 1]:
                    current_row[current_row_index - 1] += " " + line
                else:
                    current_row[current_row_index - 1] = line
            else:
                # If we've filled all columns, append to the last column
                if current_row:
                    current_row[-1] += " " + line
    
    # Add the last row
    if current_row[0]:  # Only add if we have a Project ID
        cleaned_row = [clean_cell_text(cell) for cell in current_row]
        if any(cell.strip() for cell in cleaned_row):  # Only add non-empty rows
            data_rows.append(cleaned_row)
    
    return data_rows

def validate_dataframe_alignment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and fix DataFrame alignment issues.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        pd.DataFrame: Validated and cleaned DataFrame
    """
    if df.empty:
        return df
    
    print(f"Validating DataFrame alignment...")
    print(f"Original shape: {df.shape}")
    
    # Check for rows with missing Project ID but other data
    project_id_col = get_col(df, "Project Id")
    if project_id_col:
        blank_project_id_rows = df[df[project_id_col].str.strip() == '']
        if not blank_project_id_rows.empty:
            print(f"Found {len(blank_project_id_rows)} rows with blank Project ID but other data:")
            for idx, row in blank_project_id_rows.head(5).iterrows():
                print(f"  Row {idx}: {dict(row)}")
    
    # Remove completely blank rows
    df_cleaned = df.dropna(how='all')
    print(f"Removed {len(df) - len(df_cleaned)} completely blank rows")
    
    # Ensure all rows have the same number of columns
    expected_cols = len(df.columns)
    for idx, row in df_cleaned.iterrows():
        if len(row) != expected_cols:
            print(f"Row {idx} has {len(row)} columns, expected {expected_cols}")
    
    print(f"Final shape: {df_cleaned.shape}")
    return df_cleaned

def parse_text_alternative_improved(text: str) -> pd.DataFrame:
    """
    Alternative parsing method that properly handles table structure and merges multi-line cells.
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        pd.DataFrame: DataFrame with project data
    """
    lines = text.split('\n')
    
    # Look for the actual table data section
    data_start = None
    for i, line in enumerate(lines):
        if 'Project Id' in line and 'Region' in line and 'Country' in line:
            data_start = i + 1
            break
    
    if data_start is None:
        print("Could not find table header. Using fallback parsing...")
        return parse_text_fallback(text)
    
    # Define expected columns based on World Bank project table
    columns = [
        'Project Id', 'Region', 'Country', 'Project Status', 'Project Name', 
        'Project Development Objective', 'Implementing Agency', 'Project URL',
        'Disclosure Date', 'Board Approval Date', 'Effective Date', 'Project Closing Date',
        'Last Stage Reached', 'Financing Type', 'Total Project Cost $US', 'IBRD Commitment $US', 'IDA Commitment $US'
    ]
    
    projects = []
    current_project = None
    current_line_buffer = []
    
    for i in range(data_start, len(lines)):
        line = lines[i].strip()
        
        # Skip empty lines and methodology
        if not line or any(skip_word in line.lower() for skip_word in ['methodology', 'open world bank', 'click', 'apply', 'download', 'filter']):
            continue
        
        # Check if this line starts a new project (has Project ID pattern)
        project_id_match = re.search(r'P\d{6}', line)
        
        if project_id_match:
            # Save previous project if we have one
            if current_project:
                # Process the buffered lines for the previous project
                project_data = process_project_lines(current_line_buffer, columns)
                if project_data:
                    projects.append(project_data)
            
            # Start new project
            current_project = project_id_match.group()
            current_line_buffer = [line]
        
        elif current_project:
            # Continue building the current project
            current_line_buffer.append(line)
    
    # Process the last project
    if current_project and current_line_buffer:
        project_data = process_project_lines(current_line_buffer, columns)
        if project_data:
            projects.append(project_data)
    
    if not projects:
        print("No projects found with alternative parsing.")
        return pd.DataFrame()
    
    # Remove duplicates based on Project ID
    unique_projects = []
    seen_project_ids = set()
    
    for project in projects:
        project_id = project.get('Project Id', '')
        if project_id and project_id not in seen_project_ids:
            unique_projects.append(project)
            seen_project_ids.add(project_id)
    
    print(f"Found {len(projects)} total projects, {len(unique_projects)} unique projects")
    
    return pd.DataFrame(unique_projects)

def process_project_lines(lines: List[str], columns: List[str]) -> Dict[str, str]:
    """
    Process a list of lines for a single project and extract structured data.
    
    Args:
        lines (List[str]): Lines belonging to one project
        columns (List[str]): Expected column names
        
    Returns:
        Dict[str, str]: Project data dictionary
    """
    if not lines:
        return {}
    
    # Initialize project data
    project_data = {col: '' for col in columns}
    
    # Join all lines for this project
    full_text = ' '.join(lines)
    
    # Extract Project ID
    project_id_match = re.search(r'P\d{6}', full_text)
    if project_id_match:
        project_data['Project Id'] = project_id_match.group()
    
    # Try to extract other structured data
    # Look for region patterns
    region_patterns = [
        r'(Eastern and Southern Africa)',
        r'(Western and Central Africa)',
        r'(Latin America and Caribbean)',
        r'(South Asia)',
        r'(Middle East and North Africa)',
        r'(Europe and Central Asia)'
    ]
    
    for pattern in region_patterns:
        match = re.search(pattern, full_text)
        if match:
            project_data['Region'] = match.group(1)
            break
    
    # Look for country patterns
    country_pattern = r'\b(Republic of [A-Z][a-z]+|Republic of the [A-Z][a-z]+|[A-Z][a-z]+ Republic)\b'
    country_match = re.search(country_pattern, full_text)
    if country_match:
        project_data['Country'] = country_match.group(1)
    
    # Extract project name (usually shorter text)
    # Look for text that might be project name
    words = full_text.split()
    if len(words) > 3:
        # Try to find a reasonable project name length
        potential_name = ' '.join(words[:min(10, len(words))])
        if len(potential_name) < 200:  # Reasonable project name length
            project_data['Project Name'] = clean_cell_text(potential_name)
    
    # Extract project description (longer text)
    if len(full_text) > 100:
        project_data['Project Development Objective'] = clean_cell_text(full_text)
    
    # Look for implementing agency patterns
    agency_patterns = [
        r'(Ministry of [^,]+)',
        r'(Department of [^,]+)',
        r'([A-Z][a-z]+ Agency[^,]*)',
        r'([A-Z][a-z]+ Institute[^,]*)'
    ]
    
    for pattern in agency_patterns:
        match = re.search(pattern, full_text)
        if match:
            project_data['Implementing Agency'] = clean_cell_text(match.group(1))
            break
    
    return project_data

def parse_text_fallback(text: str) -> pd.DataFrame:
    """
    Fallback parsing method for when structured parsing fails.
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        pd.DataFrame: DataFrame with project data
    """
    lines = text.split('\n')
    
    # Simple pattern-based extraction
    project_pattern = r'P\d{6}'
    projects = []
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
            
        # Skip methodology and instruction lines
        if any(skip_word in line.lower() for skip_word in ['methodology', 'open world bank', 'click', 'apply', 'download', 'filter']):
            continue
        
        # Look for project ID pattern
        project_id_match = re.search(project_pattern, line)
        if project_id_match:
            project_data = {
                'Project Id': project_id_match.group(),
                'Project Name': '',
                'Project Description': clean_cell_text(line),
                'Implementing Agency': '',
                'Region': '',
                'Country': '',
                'Project Status': '',
                'Project URL': '',
                'Disclosure Date': '',
                'Board Approval Date': '',
                'Effective Date': '',
                'Project Closing Date': '',
                'Last Stage Reached': '',
                'Financing Type': '',
                'Total Project Cost $US': '',
                'IBRD Commitment $US': '',
                'IDA Commitment $US': ''
            }
            projects.append(project_data)
    
    return pd.DataFrame(projects)

def normalize_header(header: str) -> str:
    """
    Normalize header text for column matching:
    - casefold
    - collapse whitespace
    - strip
    
    Args:
        header (str): Header text to normalize
        
    Returns:
        str: Normalized header
    """
    if not header or pd.isna(header):
        return ""
    
    # Convert to string and casefold
    header_str = str(header).casefold()
    
    # Collapse whitespace and strip
    header_str = re.sub(r'\s+', ' ', header_str).strip()
    
    return header_str

def normalize_text(text: str) -> str:
    """
    Normalize text for robust keyword matching:
    - Convert to string
    - Unicode normalize NFKC
    - Replace non-breaking spaces with regular spaces
    - Replace non-breaking hyphen and en/em dashes with "-"
    - Remove HTML <br> tags
    - Collapse whitespace
    - casefold
    
    Args:
        text (str): Text to normalize
        
    Returns:
        str: Normalized text
    """
    if not text or pd.isna(text):
        return ""
    
    # Convert to string
    text_str = str(text)
    
    # Unicode normalize NFKC
    text_str = unicodedata.normalize('NFKC', text_str)
    
    # Replace non-breaking spaces (\u00A0) with regular spaces
    text_str = text_str.replace('\u00A0', ' ')
    
    # Replace non-breaking hyphen (\u2011) and en/em dashes with "-"
    text_str = text_str.replace('\u2011', '-')  # non-breaking hyphen
    text_str = text_str.replace('\u2013', '-')  # en dash
    text_str = text_str.replace('\u2014', '-')  # em dash
    
    # Remove HTML <br> tags
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
    
    # casefold (more aggressive than lower())
    text_str = text_str.casefold()
    
    return text_str.strip()

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
                # Allow underscores within words as well as between words
                word_pattern = re.escape(word).replace('\\_', '[\\s\\-_/]*')
                pattern_parts.append(r'\b' + word_pattern + r'\b')
            # Allow various separators between words (including underscores)
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

def get_col(df: pd.DataFrame, semantic_name: str) -> str:
    """
    Get a column by semantic name, ignoring case and extra spaces.
    
    Args:
        df (pd.DataFrame): DataFrame to search in
        semantic_name (str): Semantic name of the column
        
    Returns:
        str: Actual column name if found, empty string otherwise
    """
    normalized_target = normalize_header(semantic_name)
    
    for col in df.columns:
        normalized_col = normalize_header(col)
        if normalized_target in normalized_col or normalized_col in normalized_target:
            return col
    
    return ""

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
    df = parse_table_structure(text)
    
    if df.empty:
        print("No project data found in the PDF.")
        return pd.DataFrame()
    
    print(f"Found {len(df)} projects.")
    print(f"Columns found: {list(df.columns)}")
    
    # Compile keyword patterns
    print("Compiling keyword patterns for robust matching...")
    keyword_patterns = compile_keyword_patterns(keywords)
    
    # Find columns by semantic name
    print("Finding columns by semantic name...")
    project_name_col = get_col(df, "Project Name")
    project_desc_col = get_col(df, "Project Development Objective") or get_col(df, "Project Description")
    implementing_agency_col = get_col(df, "Implementing Agency")
    
    print(f"Found columns: Project Name='{project_name_col}', Project Description='{project_desc_col}', Implementing Agency='{implementing_agency_col}'")
    
    # Add keyword columns with robust matching
    if project_name_col:
        print(f"Searching for keywords in Project Name column: '{project_name_col}'")
        df['Keywords Found in Project Name'] = df.apply(
            lambda row: find_keywords_in_text(row[project_name_col], keyword_patterns) 
            if project_name_col in df.columns and str(row[project_name_col]).strip() else [], 
            axis=1
        )
    else:
        df['Keywords Found in Project Name'] = [[]] * len(df)
    
    if project_desc_col:
        print(f"Searching for keywords in Project Description column: '{project_desc_col}'")
        df['Keywords Found in Project Description'] = df.apply(
            lambda row: find_keywords_in_text(row[project_desc_col], keyword_patterns) 
            if project_desc_col in df.columns and str(row[project_desc_col]).strip() else [], 
            axis=1
        )
    else:
        df['Keywords Found in Project Description'] = [[]] * len(df)
    
    if implementing_agency_col:
        print(f"Searching for keywords in Implementing Agency column: '{implementing_agency_col}'")
        df['Keywords Found in Implementing Agency'] = df.apply(
            lambda row: find_keywords_in_text(row[implementing_agency_col], keyword_patterns) 
            if implementing_agency_col in df.columns and str(row[implementing_agency_col]).strip() else [], 
            axis=1
        )
    else:
        df['Keywords Found in Implementing Agency'] = [[]] * len(df)
    
    # Add union column with sorted unique keywords from all three columns
    print("Creating union column with all keywords...")
    df['Keywords Found (Any Column)'] = df.apply(
        lambda row: sorted(list(set(
            row['Keywords Found in Project Name'] + 
            row['Keywords Found in Project Description'] + 
            row['Keywords Found in Implementing Agency']
        ))), axis=1
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

def debug_project(df: pd.DataFrame, project_id: str, keyword_patterns: Dict[str, re.Pattern]):
    """
    Debug helper to verify keyword detection for a specific project.
    
    Args:
        df (pd.DataFrame): DataFrame with project data
        project_id (str): Project ID to debug
        keyword_patterns (Dict[str, re.Pattern]): Compiled keyword patterns
    """
    # Find the project
    project_row = df[df['Project Id'] == project_id]
    
    if project_row.empty:
        print(f"Project {project_id} not found in the dataset.")
        return
    
    row = project_row.iloc[0]
    
    print(f"\n=== DEBUG: Project {project_id} ===")
    
    # Get column names
    project_name_col = get_col(df, "Project Name")
    project_desc_col = get_col(df, "Project Development Objective") or get_col(df, "Project Description")
    implementing_agency_col = get_col(df, "Implementing Agency")
    
    # Show original and normalized text for each column
    columns_to_check = [
        ("Project Name", project_name_col),
        ("Project Description", project_desc_col),
        ("Implementing Agency", implementing_agency_col)
    ]
    
    for col_name, col_actual in columns_to_check:
        if col_actual and col_actual in df.columns:
            original_text = str(row[col_actual])
            normalized_text = normalize_text(original_text)
            
            print(f"\n{col_name} ({col_actual}):")
            print(f"  Original: '{original_text}'")
            print(f"  Normalized: '{normalized_text}'")
            
            # Find keywords in this column
            found_keywords = find_keywords_in_text(original_text, keyword_patterns)
            print(f"  Keywords found: {found_keywords}")
            
            # Show specific matches for livestock-related keywords
            livestock_keywords = ['livestock', 'dairy', 'beef', 'poultry', 'animal', 'health', 'market']
            for keyword in livestock_keywords:
                if keyword in found_keywords:
                    print(f"    ✓ Found '{keyword}' in {col_name}")
    
    # Show final results
    print(f"\nFinal Results:")
    print(f"  Keywords in Project Name: {row.get('Keywords Found in Project Name', [])}")
    print(f"  Keywords in Project Description: {row.get('Keywords Found in Project Description', [])}")
    print(f"  Keywords in Implementing Agency: {row.get('Keywords Found in Implementing Agency', [])}")
    print(f"  Keywords Found (Any Column): {row.get('Keywords Found (Any Column)', [])}")
    print("=" * 50)

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

def main():
    """
    Main function to process PDF and find keywords.
    """
    if len(sys.argv) < 2:
        print("Usage: python pdf_keyword_scanner_improved.py <pdf_file_path>")
        print("Example: python pdf_keyword_scanner_improved.py projects.pdf")
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
    print(f"Columns in output: {list(result_df.columns)}")
    
    # Show sample results
    print("\nSample results:")
    sample_cols = ['Project Id', 'Project Name', 'Keywords Found in Project Name', 'Keywords Found in Project Description']
    available_cols = [col for col in sample_cols if col in result_df.columns]
    if available_cols:
        print(result_df[available_cols].head())
    
    # Save results
    output_path = pdf_path.replace('.pdf', '_with_keywords_improved.csv')
    save_results(result_df, output_path)
    
    # Summary statistics
    name_matches = result_df['Keywords Found in Project Name'].apply(len)
    desc_matches = result_df['Keywords Found in Project Description'].apply(len)
    agency_matches = result_df['Keywords Found in Implementing Agency'].apply(len)
    any_matches = result_df['Keywords Found (Any Column)'].apply(len)
    
    print(f"\nSummary:")
    print(f"Projects with keywords in name: {sum(name_matches > 0)}")
    print(f"Projects with keywords in description: {sum(desc_matches > 0)}")
    print(f"Projects with keywords in implementing agency: {sum(agency_matches > 0)}")
    print(f"Projects with keywords in any column: {sum(any_matches > 0)}")
    print(f"Total keyword matches in names: {sum(name_matches)}")
    print(f"Total keyword matches in descriptions: {sum(desc_matches)}")
    print(f"Total keyword matches in implementing agencies: {sum(agency_matches)}")
    print(f"Total unique keyword matches: {sum(any_matches)}")
    
    # Debug specific projects if requested
    debug_projects = ["P151978", "P147674"]  # Add more project IDs here to debug
    print(f"\nDebugging specific projects: {debug_projects}")
    
    # Compile patterns for debug function
    keyword_patterns = compile_keyword_patterns(keywords)
    
    for project_id in debug_projects:
        debug_project(result_df, project_id, keyword_patterns)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Pivot Table Generator for Project Data

This script processes project data from Numbers file and generates:
1. Intervention category pivot table (with counts)
2. Outcome primary category pivot table (with counts)
3. Outcome primary-to-subcategory pivot table (with counts)

All pivot tables show the count of occurrences, not just binary presence.
"""

import os

import pandas as pd
from collections import defaultdict
from numbers_parser import Document

# Directory containing this script (so paths work regardless of cwd)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# IDB source: "IDB Objective, Intervention, and Outcome" (Numbers file on disk)
IDB_NUMBERS_FILE = os.path.join(
    _SCRIPT_DIR, "IDB Objectives, Interventions, Outcomes copy 2.numbers"
)
# Prefix for CSV outputs from this source (avoids overwriting World Bank runs)
IDB_OUTPUT_PREFIX = "idb_"


def load_and_filter(df):
    """
    Load CSV and filter out objective rows.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame without objective rows
    """
    print(f"Number of input rows: {len(df)}")
    
    # Filter out objectives
    df_filtered = df[df['type'] != 'objective'].copy()
    print(f"Number after filtering objectives: {len(df_filtered)}")
    
    return df_filtered


def get_taxonomy_mapping():
    """
    Return mapping of duplicate/variant category names to canonical names.
    Merges: Advisory variants, Behavior Change variants, Technology/R&D variants.
    """
    return {
        # Advisory & Extension variants (merge "and" vs "&")
        'Advisory and Extension': 'Advisory & Extension',
        # Behavior Change variants (merge both to canonical form)
        'Behavior Communication Change & Social Programs': 'Behavior Change & Social Programs',
        # Technology/R&D variants (merge R&D and Technology into Technology & R&D)
        'R&D': 'Technology & R&D',
        'Technology': 'Technology & R&D',
        # Crop Management variants
        'Crop Management & Technology': 'Crop Management',
    }


def normalize_taxonomy(df):
    """
    Merge duplicate taxonomy columns to canonical names.
    Applied to 'category' and 'primary_category' before pivot creation.
    """
    mapping = get_taxonomy_mapping()
    
    def normalize(cat):
        if pd.isna(cat) or cat == '':
            return cat
        return mapping.get(str(cat).strip(), cat)
    
    df['category'] = df['category'].apply(normalize)
    if 'primary_category' in df.columns:
        df.loc[df['primary_category'].notna(), 'primary_category'] = (
            df.loc[df['primary_category'].notna(), 'primary_category'].apply(normalize)
        )
    
    return df


def clean_and_split_categories(df):
    """
    Clean and split category columns.
    Standardizes separators (both , and ;), splits, trims, and drops empty values.
    
    Args:
        df: DataFrame with category column
        
    Returns:
        DataFrame with cleaned and split categories
    """
    def split_categories(category_str):
        """Split category string by comma or semicolon, trim, and filter empty."""
        if pd.isna(category_str) or category_str == '':
            return []
        
        # Replace semicolons with commas for standardization
        standardized = str(category_str).replace(';', ',')
        
        # Split by comma
        categories = [cat.strip() for cat in standardized.split(',')]
        
        # Filter out empty strings
        categories = [cat for cat in categories if cat]
        
        return categories
    
    # Apply splitting function
    df['category'] = df['category'].apply(split_categories)
    
    # Explode so each row has one category
    df_exploded = df.explode('category', ignore_index=True)
    
    # Drop rows where category is empty/NaN
    df_exploded = df_exploded[df_exploded['category'].notna()].copy()
    df_exploded = df_exploded[df_exploded['category'] != ''].copy()
    
    print(f"Number after exploding categories: {len(df_exploded)}")
    
    return df_exploded


def parse_outcome_hierarchy(df):
    """
    Parse hierarchical outcome categories.
    Creates primary_category and subcategory columns for outcome rows.
    
    Args:
        df: DataFrame with category column
        
    Returns:
        DataFrame with primary_category and subcategory columns
    """
    # Initialize columns
    df['parsed_primary_category'] = None
    df['subcategory'] = None
    
    # Process outcome rows
    outcome_mask = df['type'] == 'outcome'
    
    def parse_hierarchy(row):
        """Parse hierarchical category into primary and subcategory."""
        category_str = row['category']
        specific_outcome = row.get('specific_outcome', None) if 'specific_outcome' in row else None
        
        if pd.isna(category_str) or category_str == '':
            return None, None
        
        category_str = str(category_str).strip()
        
        # First, check if category itself has hierarchical separators
        separators = [' - ', ':', ' > ']
        
        for sep in separators:
            if sep in category_str:
                parts = category_str.split(sep, 1)  # Split only on first occurrence
                primary = parts[0].strip()
                sub = parts[1].strip() if len(parts) > 1 else ''
                return primary, sub
        
        # No separator in category - check if we have specific_outcome to use as subcategory
        if pd.notna(specific_outcome) and str(specific_outcome).strip() != '':
            # Use category as primary, specific_outcome as subcategory
            return category_str, str(specific_outcome).strip()
        
        # No separator and no specific_outcome - treat entire value as primary
        return category_str, None
    
    # Apply parsing to outcome rows
    outcome_df = df.loc[outcome_mask].copy()
    parsed = outcome_df.apply(parse_hierarchy, axis=1)
    df.loc[outcome_mask, 'parsed_primary_category'] = parsed.apply(lambda x: x[0])
    df.loc[outcome_mask, 'subcategory'] = parsed.apply(lambda x: x[1])
    
    # For intervention rows, use category as primary (no hierarchy)
    intervention_mask = df['type'] == 'intervention'
    df.loc[intervention_mask, 'parsed_primary_category'] = df.loc[intervention_mask, 'category']
    
    # Rename for consistency
    df['primary_category'] = df['parsed_primary_category']
    df = df.drop(columns=['parsed_primary_category'], errors='ignore')
    
    return df


def create_project_labels(df):
    """
    Create project labels based on country associations.
    
    Rule:
    - If project_id has exactly one unique country: PROJECT_ID (Country)
    - If project_id has more than one country: PROJECT_ID (multiple)
    
    Args:
        df: DataFrame with project_id and country columns
        
    Returns:
        DataFrame with project_label column
    """
    # Get unique project-country pairs
    project_countries = df.groupby('project_id')['country'].nunique()
    
    # Create mapping
    project_labels = {}
    for project_id in df['project_id'].unique():
        # Handle NaN project_ids
        if pd.isna(project_id):
            project_labels[project_id] = "Unknown (multiple)"
        else:
            unique_countries = df[df['project_id'] == project_id]['country'].unique()
            unique_countries = [c for c in unique_countries if pd.notna(c)]
            
            if len(unique_countries) == 1:
                project_labels[project_id] = f"{project_id} ({unique_countries[0]})"
            else:
                project_labels[project_id] = f"{project_id} (multiple)"
    
    # Add project_label column
    df['project_label'] = df['project_id'].map(project_labels)
    
    return df


def get_all_project_labels(df):
    """
    One stable-ordered project_label per project_id (entire portfolio in df).
    Used so pivot tables include every project, with zeros where a type has no rows.
    """
    sub = df[['project_id', 'project_label']].copy()
    sub = sub.dropna(subset=['project_id'])
    sub = sub.drop_duplicates(subset=['project_id'], keep='first')
    return sub.sort_values('project_label')['project_label'].tolist()


def create_intervention_pivot(df, all_project_labels):
    """
    Create intervention category pivot table.
    
    Args:
        df: DataFrame with intervention rows
        all_project_labels: Ordered list of every project_label to include (zeros if no interventions)
        
    Returns:
        Pivot table DataFrame
    """
    intervention_df = df[df['type'] == 'intervention'].copy()
    
    if len(intervention_df) == 0:
        print("Warning: No intervention rows found")
        out = pd.DataFrame({'project_label': all_project_labels})
        out['Total'] = 0
        totals_row = pd.DataFrame(
            [['Total'] + [0] * (len(out.columns) - 1)],
            columns=out.columns,
        )
        return pd.concat([out, totals_row], ignore_index=True)
    
    # Create pivot: project_label x category, count occurrences
    pivot = intervention_df.pivot_table(
        index='project_label',
        columns='category',
        values='project_id',  # Use any column for aggregation
        aggfunc='count',
        fill_value=0
    )
    
    # Keep as counts (don't convert to binary)
    pivot = pivot.astype(int)
    # Every project in the portfolio, even with zero interventions
    pivot = pivot.reindex(all_project_labels, fill_value=0)
    
    # Add row totals (sum across columns for each project)
    pivot['Total'] = pivot.sum(axis=1)
    
    # Reset index to make project_label a column
    pivot = pivot.reset_index()
    
    # Add column totals (sum down rows for each category)
    # Get numeric columns (exclude project_label)
    numeric_cols = [col for col in pivot.columns if col != 'project_label']
    totals_row = pd.DataFrame([['Total'] + [pivot[col].sum() for col in numeric_cols]], 
                               columns=['project_label'] + numeric_cols)
    
    # Append totals row
    pivot = pd.concat([pivot, totals_row], ignore_index=True)
    
    return pivot


def create_outcome_primary_pivot(df, all_project_labels):
    """
    Create outcome primary category pivot table.
    
    Args:
        df: DataFrame with outcome rows
        all_project_labels: Every project_label to include (zeros if no outcomes)
        
    Returns:
        Pivot table DataFrame
    """
    outcome_df = df[df['type'] == 'outcome'].copy()
    outcome_df = outcome_df[outcome_df['primary_category'].notna()].copy()
    
    if len(outcome_df) == 0:
        print("Warning: No outcome rows with primary_category found")
        out = pd.DataFrame({'project_label': all_project_labels})
        out['Total'] = 0
        totals_row = pd.DataFrame(
            [['Total'] + [0] * (len(out.columns) - 1)],
            columns=out.columns,
        )
        return pd.concat([out, totals_row], ignore_index=True)
    
    # Create pivot: project_label x primary_category, count occurrences
    pivot = outcome_df.pivot_table(
        index='project_label',
        columns='primary_category',
        values='project_id',
        aggfunc='count',
        fill_value=0
    )
    
    # Keep as counts (don't convert to binary)
    pivot = pivot.astype(int)
    pivot = pivot.reindex(all_project_labels, fill_value=0)
    
    # Add row totals (sum across columns for each project)
    pivot['Total'] = pivot.sum(axis=1)
    
    # Reset index
    pivot = pivot.reset_index()
    
    # Add column totals (sum down rows for each category)
    # Get numeric columns (exclude project_label)
    numeric_cols = [col for col in pivot.columns if col != 'project_label']
    totals_row = pd.DataFrame([['Total'] + [pivot[col].sum() for col in numeric_cols]], 
                               columns=['project_label'] + numeric_cols)
    
    # Append totals row
    pivot = pd.concat([pivot, totals_row], ignore_index=True)
    
    return pivot


def create_outcome_subcategory_pivot(df, all_project_labels):
    """
    Create outcome primary-to-subcategory pivot table.
    
    Args:
        df: DataFrame with outcome rows
        all_project_labels: Every project_label to include (zeros if no subcategory outcomes)
        
    Returns:
        Pivot table DataFrame
    """
    outcome_df = df[df['type'] == 'outcome'].copy()
    outcome_df = outcome_df[outcome_df['subcategory'].notna()].copy()
    outcome_df = outcome_df[outcome_df['subcategory'] != ''].copy()
    
    if len(outcome_df) == 0:
        print("Warning: No outcome rows with subcategory found")
        out = pd.DataFrame({'project_label': all_project_labels})
        out['Total'] = 0
        totals_row = pd.DataFrame(
            [['Total'] + [0] * (len(out.columns) - 1)],
            columns=out.columns,
        )
        return pd.concat([out, totals_row], ignore_index=True)
    
    # Create combined label: Primary::Subcategory
    outcome_df['combined_category'] = (
        outcome_df['primary_category'].astype(str) + '::' + 
        outcome_df['subcategory'].astype(str)
    )
    
    # Create pivot: project_label x combined_category, count occurrences
    pivot = outcome_df.pivot_table(
        index='project_label',
        columns='combined_category',
        values='project_id',
        aggfunc='count',
        fill_value=0
    )
    
    # Keep as counts (don't convert to binary)
    pivot = pivot.astype(int)
    pivot = pivot.reindex(all_project_labels, fill_value=0)
    
    # Add row totals (sum across columns for each project)
    pivot['Total'] = pivot.sum(axis=1)
    
    # Reset index
    pivot = pivot.reset_index()
    
    # Add column totals (sum down rows for each category)
    # Get numeric columns (exclude project_label)
    numeric_cols = [col for col in pivot.columns if col != 'project_label']
    totals_row = pd.DataFrame([['Total'] + [pivot[col].sum() for col in numeric_cols]], 
                               columns=['project_label'] + numeric_cols)
    
    # Append totals row
    pivot = pd.concat([pivot, totals_row], ignore_index=True)
    
    return pivot


def create_intervention_outcome_cooccurrence_matrix(df):
    """
    Create Intervention × Outcome co-occurrence matrix.
    
    Project-level join: for each project, get its intervention categories and
    outcome categories. Each cell = number of projects where that intervention
    and outcome both appear (at least once each).
    
    Rows = intervention categories
    Columns = outcome primary categories
    """
    intervention_df = df[df['type'] == 'intervention'].copy()
    outcome_df = df[df['type'] == 'outcome'].copy()
    outcome_df = outcome_df[outcome_df['primary_category'].notna()].copy()
    outcome_df = outcome_df[outcome_df['primary_category'] != ''].copy()
    
    if len(intervention_df) == 0 or len(outcome_df) == 0:
        print("Warning: Need both intervention and outcome rows for co-occurrence matrix")
        return pd.DataFrame()
    
    # Get unique interventions and outcomes per project (sets)
    project_interventions = (
        intervention_df.groupby('project_label')['category']
        .apply(lambda x: set(x.dropna().unique()))
        .to_dict()
    )
    project_outcomes = (
        outcome_df.groupby('project_label')['primary_category']
        .apply(lambda x: set(x.dropna().unique()))
        .to_dict()
    )
    
    # Projects that have both interventions and outcomes
    project_labels = sorted(set(project_interventions.keys()) & set(project_outcomes.keys()))
    
    # Build co-occurrence counts
    cooccur = defaultdict(lambda: defaultdict(int))
    
    for plabel in project_labels:
        interv_set = project_interventions.get(plabel, set())
        outcome_set = project_outcomes.get(plabel, set())
        for interv in interv_set:
            for outcome in outcome_set:
                cooccur[interv][outcome] += 1
    
    # Convert to DataFrame
    interventions = sorted(cooccur.keys())
    outcomes = sorted(set(o for row in cooccur.values() for o in row.keys()))
    
    matrix = []
    for interv in interventions:
        row = [cooccur[interv].get(o, 0) for o in outcomes]
        matrix.append(row)
    
    pivot = pd.DataFrame(matrix, index=interventions, columns=outcomes)
    pivot = pivot.astype(int)
    
    # Add row totals
    pivot['Total'] = pivot.sum(axis=1)
    
    # Add column totals
    pivot.loc['Total'] = pivot.sum(axis=0)
    
    # Reset index so intervention becomes a column
    pivot = pivot.reset_index()
    pivot = pivot.rename(columns={'index': 'Intervention'})
    
    return pivot


def generate_category_dictionary(df):
    """
    Generate category dictionary with counts.
    
    Args:
        df: Exploded DataFrame
        
    Returns:
        DataFrame with category and count columns
    """
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    category_counts = category_counts.sort_values('category')
    
    return category_counts


def print_statistics(df):
    """
    Print QA statistics to console.
    
    Args:
        df: Processed DataFrame
    """
    print("\n=== Statistics ===")
    print(f"Number of unique projects total: {df['project_id'].nunique()}")
    print(f"Number of intervention projects: {df[df['type'] == 'intervention']['project_id'].nunique()}")
    print(f"Number of outcome projects: {df[df['type'] == 'outcome']['project_id'].nunique()}")
    print(f"Number of unique categories: {df['category'].nunique()}")
    
    outcome_df = df[df['type'] == 'outcome']
    if len(outcome_df) > 0:
        print(f"Number of unique primary outcome categories: {outcome_df['primary_category'].nunique()}")
        subcategories = outcome_df[outcome_df['subcategory'].notna()]['subcategory']
        print(f"Number of unique outcome subcategories: {subcategories.nunique()}")
    else:
        print("Number of unique primary outcome categories: 0")
        print("Number of unique outcome subcategories: 0")


def load_numbers_file(filename):
    """
    Load a Numbers file and convert to pandas DataFrame.
    
    Args:
        filename: Path to .numbers file
        
    Returns:
        DataFrame with the data from the first table
    """
    print(f"Loading {filename}...")
    doc = Document(filename)
    
    # Get the first sheet and first table
    sheet = doc.sheets[0]
    table = sheet.tables[0]
    
    # Get all rows
    rows = list(table.rows())
    
    # Get headers from first row (convert to string and strip)
    headers = []
    for cell in rows[0]:
        val = cell.value
        if val is None:
            val = ''
        else:
            val = str(val).strip()
        headers.append(val)
    
    # If headers are empty, try using first data row as headers
    if all(h == '' for h in headers) and len(rows) > 1:
        headers = []
        for cell in rows[1]:
            val = cell.value
            if val is None:
                val = ''
            else:
                val = str(val).strip()
            headers.append(val)
        start_row = 2
    else:
        start_row = 1
    
    # Get data from remaining rows
    data = []
    for row in rows[start_row:]:
        row_data = []
        for cell in row:
            val = cell.value
            if val is None:
                val = ''
            else:
                val = str(val).strip() if isinstance(val, str) else val
            row_data.append(val)
        data.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=headers)
    
    # Remove empty column names
    df = df.loc[:, df.columns != '']
    
    return df


def main():
    """Main function to orchestrate the pivot table generation."""
    
    # Load input Numbers file (IDB Objectives, Interventions, and Outcomes)
    df = load_numbers_file(IDB_NUMBERS_FILE)
    
    # Map column names if needed
    # The file uses 'item_type' instead of 'type'
    if 'item_type' in df.columns and 'type' not in df.columns:
        df['type'] = df['item_type']
    
    # Use 'primary_category' as the category column (contains comma/semicolon separated categories)
    if 'category' not in df.columns:
        if 'primary_category' in df.columns:
            df['category'] = df['primary_category'].fillna('')
        else:
            raise ValueError("Could not find 'category' or 'primary_category' column in the data")
    
    # Step 1: Filter out objectives
    df = load_and_filter(df)
    
    # Step 2: Clean and split categories
    df = clean_and_split_categories(df)
    
    # Step 3: Parse outcome hierarchy
    df = parse_outcome_hierarchy(df)
    
    # Step 4: Taxonomy cleaning - merge duplicate columns before pivots
    df = normalize_taxonomy(df)
    print(f"Number of unique categories after taxonomy merge: {df['category'].nunique()}")
    
    # Step 5: Create project labels
    df = create_project_labels(df)
    
    # Full portfolio: every project appears on project × category pivots (zeros where empty)
    all_project_labels = get_all_project_labels(df)
    print(f"Projects in pivot tables (all rows): {len(all_project_labels)}")
    
    # Step 6: Generate pivot tables
    print("\nGenerating pivot tables...")
    
    intervention_pivot = create_intervention_pivot(df, all_project_labels)
    outcome_primary_pivot = create_outcome_primary_pivot(df, all_project_labels)
    outcome_subcategory_pivot = create_outcome_subcategory_pivot(df, all_project_labels)
    cooccurrence_matrix = create_intervention_outcome_cooccurrence_matrix(df)
    
    # Step 7: Generate category dictionary
    category_dict = generate_category_dictionary(df)
    
    # Step 8: Export results
    print("\nExporting results...")
    out = lambda name: os.path.join(_SCRIPT_DIR, f"{IDB_OUTPUT_PREFIX}{name}")
    intervention_pivot.to_csv(out("intervention_category_pivot.csv"), index=False)
    outcome_primary_pivot.to_csv(out("outcome_primary_category_pivot.csv"), index=False)
    outcome_subcategory_pivot.to_csv(out("outcome_primary_subcategory_pivot.csv"), index=False)
    cooccurrence_matrix.to_csv(out("intervention_outcome_cooccurrence.csv"), index=False)
    category_dict.to_csv(out("category_dictionary.csv"), index=False)
    
    print("\nExported files (IDB):")
    print(f"  - {out('intervention_category_pivot.csv')}")
    print(f"  - {out('outcome_primary_category_pivot.csv')}")
    print(f"  - {out('outcome_primary_subcategory_pivot.csv')}")
    print(f"  - {out('intervention_outcome_cooccurrence.csv')}")
    print(f"  - {out('category_dictionary.csv')}")
    
    # Step 9: Print statistics
    print_statistics(df)
    
    print("\nDone!")


if __name__ == '__main__':
    main()


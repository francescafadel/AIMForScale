#!/usr/bin/env python3
"""
Analyze Download Results
This script analyzes the results from the SSL-fixed document downloader to provide comprehensive statistics.
"""

import pandas as pd
import os
from pathlib import Path
from collections import Counter

def analyze_download_results():
    """Analyze the download results and provide comprehensive statistics."""
    
    # Load the tracking data
    df = pd.read_csv("data/ssl_fixed_document_tracking.csv")
    
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS OF IDB DOCUMENT DOWNLOAD RESULTS")
    print("=" * 80)
    
    # Basic statistics
    total_projects = len(df)
    projects_with_documents = len(df[df['Total_Documents'] > 0])
    total_documents_found = df['Total_Documents'].sum()
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Total Projects Processed: {total_projects}")
    print(f"   Projects with Documents: {projects_with_documents}")
    print(f"   Projects without Documents: {total_projects - projects_with_documents}")
    print(f"   Total Documents Found: {total_documents_found}")
    print(f"   Success Rate: {(projects_with_documents/total_projects)*100:.1f}%")
    
    # Document type analysis
    loan_proposal_count = len(df[df['Loan_Proposal_Document'] == 'Yes'])
    project_proposal_count = len(df[df['Project_Proposal_Document'] == 'Yes'])
    project_abstract_count = len(df[df['Project_Abstract_Document'] == 'Yes'])
    
    print(f"\n📄 DOCUMENT TYPE ANALYSIS:")
    print(f"   Loan Proposal Documents: {loan_proposal_count}")
    print(f"   Project Proposal Documents: {project_proposal_count}")
    print(f"   Project Abstract Documents: {project_abstract_count}")
    
    # Language analysis
    downloads_dir = Path("downloads")
    english_files = list(downloads_dir.rglob("*English*.pdf"))
    spanish_files = list(downloads_dir.rglob("*Spanish*.pdf"))
    other_files = []
    
    for pdf_file in downloads_dir.rglob("*.pdf"):
        if "English" not in pdf_file.name and "Spanish" not in pdf_file.name:
            other_files.append(pdf_file)
    
    print(f"\n🌐 LANGUAGE ANALYSIS:")
    print(f"   English Documents: {len(english_files)}")
    print(f"   Spanish Documents: {len(spanish_files)}")
    print(f"   Other Documents: {len(other_files)}")
    print(f"   Total Downloaded: {len(english_files) + len(spanish_files) + len(other_files)}")
    
    # Country analysis
    country_docs = {}
    for pdf_file in downloads_dir.rglob("*.pdf"):
        country = pdf_file.parent.name
        if country not in country_docs:
            country_docs[country] = 0
        country_docs[country] += 1
    
    print(f"\n🌍 COUNTRY ANALYSIS:")
    print(f"   Countries with Documents: {len(country_docs)}")
    
    # Sort countries by document count
    sorted_countries = sorted(country_docs.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n   Top Countries by Document Count:")
    for i, (country, count) in enumerate(sorted_countries[:10], 1):
        print(f"   {i:2d}. {country}: {count} documents")
    
    # Project type analysis
    project_types = df['Project_Type'].value_counts()
    
    print(f"\n🏗️ PROJECT TYPE ANALYSIS:")
    for project_type, count in project_types.items():
        print(f"   {project_type}: {count} projects")
    
    # Projects with documents by type
    projects_with_docs = df[df['Total_Documents'] > 0]
    project_types_with_docs = projects_with_docs['Project_Type'].value_counts()
    
    print(f"\n📋 PROJECT TYPES WITH DOCUMENTS:")
    for project_type, count in project_types_with_docs.items():
        print(f"   {project_type}: {count} projects with documents")
    
    # Status analysis
    status_counts = df['Status'].value_counts()
    
    print(f"\n📈 PROJECT STATUS ANALYSIS:")
    for status, count in status_counts.items():
        print(f"   {status}: {count} projects")
    
    # Projects with documents by status
    status_with_docs = projects_with_docs['Status'].value_counts()
    
    print(f"\n📊 PROJECT STATUS WITH DOCUMENTS:")
    for status, count in status_with_docs.items():
        print(f"   {status}: {count} projects with documents")
    
    # Year analysis
    df['Year'] = pd.to_datetime(df['Approval_Date'], errors='coerce').dt.year
    year_counts = df['Year'].value_counts().sort_index()
    
    print(f"\n📅 YEAR ANALYSIS:")
    for year, count in year_counts.items():
        if pd.notna(year):
            print(f"   {int(year)}: {count} projects")
    
    # Years with documents
    years_with_docs = projects_with_docs['Year'].value_counts().sort_index()
    
    print(f"\n📅 YEARS WITH DOCUMENTS:")
    for year, count in years_with_docs.items():
        if pd.notna(year):
            print(f"   {int(year)}: {count} projects with documents")
    
    # Document size analysis
    total_size = 0
    file_sizes = []
    
    for pdf_file in downloads_dir.rglob("*.pdf"):
        try:
            size = pdf_file.stat().st_size
            total_size += size
            file_sizes.append(size)
        except:
            pass
    
    avg_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
    
    print(f"\n💾 STORAGE ANALYSIS:")
    print(f"   Total Size: {total_size / (1024*1024):.1f} MB")
    print(f"   Average File Size: {avg_size / (1024*1024):.1f} MB")
    print(f"   Largest File: {max(file_sizes) / (1024*1024):.1f} MB" if file_sizes else "N/A")
    print(f"   Smallest File: {min(file_sizes) / (1024*1024):.1f} MB" if file_sizes else "N/A")
    
    # Success rate by country
    print(f"\n🎯 SUCCESS RATE BY COUNTRY:")
    for country, doc_count in sorted_countries:
        country_projects = len(df[df['Country'].str.contains(country, na=False)])
        if country_projects > 0:
            success_rate = (doc_count / country_projects) * 100
            print(f"   {country}: {doc_count}/{country_projects} projects ({success_rate:.1f}%)")
    
    print(f"\n" + "=" * 80)
    print(f"ANALYSIS COMPLETE")
    print(f"=" * 80)

if __name__ == "__main__":
    analyze_download_results()


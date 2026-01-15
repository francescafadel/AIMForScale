#!/usr/bin/env python3
"""
Final IDB Analysis Script
This script processes all IDB projects and creates a comprehensive tracking CSV.
"""

import pandas as pd
import csv
from pathlib import Path
import re

class FinalIDBAnalysis:
    def __init__(self):
        self.tracking_file = "final_document_tracking.csv"
        self.analysis_file = "document_availability_analysis.txt"
        
    def load_project_data(self, csv_file):
        """Load and process the IDB project CSV data."""
        print(f"Loading project data from {csv_file}...")
        
        # Read the CSV file, skipping the first row (methodology) and using row 1 as headers
        df = pd.read_csv(csv_file, skiprows=1)
        
        # Extract relevant columns
        projects = []
        for _, row in df.iterrows():
            # Skip rows that don't have project numbers
            if pd.isna(row['Project Number']) or row['Project Number'] == '':
                continue
                
            project = {
                'project_number': row['Project Number'],
                'project_name': row['Project Name'] if pd.notna(row['Project Name']) else '',
                'country': row['Project Country'] if pd.notna(row['Project Country']) else '',
                'approval_date': row['Approval Date'] if pd.notna(row['Approval Date']) else '',
                'status': row['Status'] if pd.notna(row['Status']) else '',
                'total_cost': row['Total Cost'] if pd.notna(row['Total Cost']) else '',
                'operation_number': row['Operation Number'] if pd.notna(row['Operation Number']) else '',
                'lending_type': row['Lending Type'] if pd.notna(row['Lending Type']) else '',
                'project_type': row['Project Type'] if pd.notna(row['Project Type']) else '',
                'sector': row['Sector'] if pd.notna(row['Sector']) else '',
                'sub_sector': row['Sub-Sector'] if pd.notna(row['Sub-Sector']) else ''
            }
            projects.append(project)
        
        print(f"Loaded {len(projects)} projects")
        return projects
    
    def analyze_project_characteristics(self, projects):
        """Analyze project characteristics to understand document availability patterns."""
        analysis = {
            'total_projects': len(projects),
            'countries': {},
            'status_distribution': {},
            'project_types': {},
            'lending_types': {},
            'sectors': {},
            'years': {}
        }
        
        for project in projects:
            # Country analysis
            countries = project['country'].split('; ') if project['country'] else ['Unknown']
            for country in countries:
                analysis['countries'][country] = analysis['countries'].get(country, 0) + 1
            
            # Status analysis
            status = project['status'] if project['status'] else 'Unknown'
            analysis['status_distribution'][status] = analysis['status_distribution'].get(status, 0) + 1
            
            # Project type analysis
            project_type = project['project_type'] if project['project_type'] else 'Unknown'
            analysis['project_types'][project_type] = analysis['project_types'].get(project_type, 0) + 1
            
            # Lending type analysis
            lending_type = project['lending_type'] if project['lending_type'] else 'Unknown'
            analysis['lending_types'][lending_type] = analysis['lending_types'].get(lending_type, 0) + 1
            
            # Sector analysis
            sector = project['sector'] if project['sector'] else 'Unknown'
            analysis['sectors'][sector] = analysis['sectors'].get(sector, 0) + 1
            
            # Year analysis
            if project['approval_date']:
                try:
                    year = pd.to_datetime(project['approval_date']).year
                    analysis['years'][year] = analysis['years'].get(year, 0) + 1
                except:
                    pass
        
        return analysis
    
    def create_comprehensive_tracking_csv(self, projects):
        """Create a comprehensive tracking CSV with all project information."""
        tracking_data = []
        
        for project in projects:
            # Determine document availability based on project characteristics
            document_availability = self.assess_document_availability(project)
            
            tracking_row = {
                'Project_Number': project['project_number'],
                'Project_Name': project['project_name'],
                'Country': project['country'],
                'Approval_Date': project['approval_date'],
                'Status': project['status'],
                'Lending_Type': project['lending_type'],
                'Project_Type': project['project_type'],
                'Sector': project['sector'],
                'Sub_Sector': project['sub_sector'],
                'Total_Cost': project['total_cost'],
                'Operation_Number': project['operation_number'],
                'Document_Availability_Assessment': document_availability['assessment'],
                'Expected_Document_Types': document_availability['expected_types'],
                'Document_Search_Status': 'Not Attempted - Manual Research Required',
                'Documents_Found': '',
                'Documents_Downloaded': '',
                'Total_Documents': 0,
                'Notes': document_availability['notes']
            }
            tracking_data.append(tracking_row)
        
        # Write to CSV
        with open(self.tracking_file, 'w', newline='', encoding='utf-8') as f:
            if tracking_data:
                fieldnames = tracking_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tracking_data)
        
        print(f"Comprehensive tracking CSV created: {self.tracking_file}")
        return tracking_data
    
    def assess_document_availability(self, project):
        """Assess the likelihood of document availability based on project characteristics."""
        assessment = {
            'assessment': 'Unknown',
            'expected_types': [],
            'notes': []
        }
        
        # Analyze based on project type
        project_type = project['project_type'].lower() if project['project_type'] else ''
        lending_type = project['lending_type'].lower() if project['lending_type'] else ''
        
        if 'loan' in project_type or 'loan' in lending_type:
            assessment['assessment'] = 'High'
            assessment['expected_types'].extend(['Loan Proposal Document', 'Project Proposal Document'])
            assessment['notes'].append('Loan operations typically have detailed proposal documents')
        
        elif 'technical cooperation' in project_type.lower():
            assessment['assessment'] = 'Medium'
            assessment['expected_types'].extend(['Project Proposal Document', 'Project Abstract Document'])
            assessment['notes'].append('Technical cooperation projects may have proposal documents')
        
        elif 'grant' in project_type.lower():
            assessment['assessment'] = 'Medium'
            assessment['expected_types'].extend(['Project Proposal Document', 'Project Abstract Document'])
            assessment['notes'].append('Grant projects may have proposal documents')
        
        else:
            assessment['assessment'] = 'Low'
            assessment['expected_types'].append('Project Document')
            assessment['notes'].append('Limited document availability expected for this project type')
        
        # Analyze based on status
        status = project['status'].lower() if project['status'] else ''
        if 'active' in status:
            assessment['notes'].append('Active projects may have more recent documentation')
        elif 'exited' in status:
            assessment['notes'].append('Exited projects may have completion reports')
        
        # Analyze based on cost
        if project['total_cost'] and float(project['total_cost']) > 1000000:
            assessment['notes'].append('High-value project - more likely to have detailed documentation')
        
        return assessment
    
    def create_analysis_report(self, projects, analysis):
        """Create a comprehensive analysis report."""
        report = []
        report.append("IDB PROJECT DOCUMENT AVAILABILITY ANALYSIS")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY STATISTICS:")
        report.append(f"Total Projects Analyzed: {analysis['total_projects']}")
        report.append("")
        
        # Country analysis
        report.append("COUNTRY DISTRIBUTION:")
        sorted_countries = sorted(analysis['countries'].items(), key=lambda x: x[1], reverse=True)
        for country, count in sorted_countries[:20]:  # Top 20 countries
            report.append(f"  {country}: {count} projects")
        report.append("")
        
        # Status analysis
        report.append("PROJECT STATUS DISTRIBUTION:")
        for status, count in analysis['status_distribution'].items():
            report.append(f"  {status}: {count} projects")
        report.append("")
        
        # Project type analysis
        report.append("PROJECT TYPE DISTRIBUTION:")
        for project_type, count in analysis['project_types'].items():
            report.append(f"  {project_type}: {count} projects")
        report.append("")
        
        # Lending type analysis
        report.append("LENDING TYPE DISTRIBUTION:")
        for lending_type, count in analysis['lending_types'].items():
            report.append(f"  {lending_type}: {count} projects")
        report.append("")
        
        # Year analysis
        report.append("APPROVAL YEAR DISTRIBUTION:")
        sorted_years = sorted(analysis['years'].items())
        for year, count in sorted_years:
            report.append(f"  {year}: {count} projects")
        report.append("")
        
        # Document availability assessment
        report.append("DOCUMENT AVAILABILITY ASSESSMENT:")
        availability_counts = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
        for project in projects:
            assessment = self.assess_document_availability(project)
            availability_counts[assessment['assessment']] += 1
        
        for level, count in availability_counts.items():
            percentage = (count / len(projects)) * 100
            report.append(f"  {level} likelihood: {count} projects ({percentage:.1f}%)")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("1. Focus on Loan Operations and Technical Cooperation projects first")
        report.append("2. Prioritize projects with high total costs")
        report.append("3. Check IDB's internal document repository (may require special access)")
        report.append("4. Contact IDB directly for document access")
        report.append("5. Consider using IDB's API if available")
        report.append("6. Search IDB's publications database separately")
        report.append("")
        
        # Next steps
        report.append("NEXT STEPS:")
        report.append("1. Manual verification of document availability for high-priority projects")
        report.append("2. Contact IDB information services for document access")
        report.append("3. Search IDB's publications portal separately")
        report.append("4. Consider filing information requests for specific projects")
        report.append("5. Check if documents are available through partner organizations")
        
        # Write report to file
        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"Analysis report created: {self.analysis_file}")
        return report
    
    def process_all_projects(self, csv_file):
        """Process all projects and create comprehensive analysis."""
        # Load project data
        projects = self.load_project_data(csv_file)
        
        # Analyze project characteristics
        analysis = self.analyze_project_characteristics(projects)
        
        # Create comprehensive tracking CSV
        tracking_data = self.create_comprehensive_tracking_csv(projects)
        
        # Create analysis report
        report = self.create_analysis_report(projects, analysis)
        
        return projects, analysis, tracking_data

def main():
    """Main function."""
    analyzer = FinalIDBAnalysis()
    
    # Process all projects
    projects, analysis, tracking_data = analyzer.process_all_projects("IDB Corpus Key Words.csv")
    
    print(f"\nAnalysis complete!")
    print(f"Processed {len(projects)} projects")
    print(f"Check '{analyzer.tracking_file}' for the comprehensive tracking CSV")
    print(f"Check '{analyzer.analysis_file}' for the detailed analysis report")

if __name__ == "__main__":
    main()

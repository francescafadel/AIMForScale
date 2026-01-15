#!/usr/bin/env python3
"""
World Bank Document Downloader

A standalone Python module/CLI that downloads Project Information Documents (PID) 
and Project/Program Appraisal Documents (PAD) from the World Bank WDS API.

Usage:
    python wb_downloader.py --projects projects.csv \
        --id-col "Project Id" --country-col Country --title-col "Project Name" \
        --languages en --out-dir downloads --latest-only false

For more options, see the argument parser below.
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import requests
from urllib.parse import urlparse


class WorldBankDownloader:
    """Main class for downloading World Bank project documents."""
    
    def __init__(self, out_dir: str = "downloads", languages: str = "en", 
                 latest_only: bool = False, dry_run: bool = False):
        self.out_dir = Path(out_dir)
        self.languages = languages
        self.latest_only = latest_only
        self.dry_run = dry_run
        
        # API configuration
        self.base_url = "https://search.worldbank.org/api/v2/wds"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WorldBank-Downloader/1.0'
        })
        
        # Document type patterns
        self.pid_pattern = re.compile(
            r'(?i)\bproject information document\b|\bpid\b|pid\s*\/\s*isds|(concept|appraisal)\s*stage'
        )
        self.pad_pattern = re.compile(
            r'(?i)\b(project|program)\s+appraisal\s+document\b|\bpad\b'
        )
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_projects': 0,
            'projects_with_pid': 0,
            'projects_with_pad': 0,
            'downloads_successful': 0,
            'downloads_skipped': 0,
            'downloads_failed': 0
        }
        
        # Manifest data
        self.manifest_data = []
        
    def slug(self, text: str, max_length: int = 120) -> str:
        """Convert text to URL-friendly slug."""
        import unicodedata
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Convert to lowercase and replace spaces/non-alphanumerics with hyphens
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text)
        
        # Remove leading/trailing hyphens and limit length
        text = text.strip('-')
        if len(text) > max_length:
            text = text[:max_length].rstrip('-')
            
        return text
    
    def call_wds_api(self, project_id: str, offset: int = 0) -> Dict:
        """Call the WDS API with pagination and retry logic."""
        params = {
            'format': 'json',
            'includepublicdocs': '1',
            'rows': '200',
            'os': str(offset),
            'proid': project_id,
            'fl': 'docna,docty,docdt,lang,repnb,url,pdfurl,projn,proid,countryshortname,countryname'
        }
        
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(self.base_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limited, retrying in {delay}s...")
                    time.sleep(delay)
                elif response.status_code >= 500:
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(f"Server error {response.status_code}, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"API call failed with status {response.status_code}")
                    return {}
                    
            except requests.RequestException as e:
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Request failed, retrying in {delay}s: {e}")
                time.sleep(delay)
        
        self.logger.error(f"Failed to call WDS API for project {project_id} after {max_retries} attempts")
        return {}
    
    def get_project_documents(self, project_id: str) -> List[Dict]:
        """Get all documents for a project using pagination."""
        all_docs = []
        offset = 0
        
        while True:
            response = self.call_wds_api(project_id, offset)
            
            if not response:
                break
            
            # Handle both old and new API response formats
            if 'response' in response:
                docs = response['response'].get('docs', [])
            elif 'documents' in response:
                # New API format: documents is a dict with doc IDs as keys
                docs_dict = response.get('documents', {})
                docs = list(docs_dict.values()) if isinstance(docs_dict, dict) else []
            else:
                break
                
            if not docs:
                break
                
            all_docs.extend(docs)
            offset += 200
            
            # Safety check to prevent infinite loops
            if len(docs) < 200:
                break
        
        return all_docs
    
    def detect_document_type(self, doc: Dict) -> Optional[str]:
        """Detect if document is PID or PAD based on docty and docna fields."""
        docty = doc.get('docty', '').lower()
        
        # Handle nested docna structure in new API format
        docna_field = doc.get('docna', '')
        if isinstance(docna_field, dict):
            # New API format: docna is nested
            docna = ''
            if '0' in docna_field and 'docna' in docna_field['0']:
                docna = docna_field['0']['docna'].lower()
        else:
            # Old API format: docna is a string
            docna = docna_field.lower()
        
        # Check docty first, then fallback to docna
        if self.pid_pattern.search(docty) or self.pid_pattern.search(docna):
            return 'PID'
        elif self.pad_pattern.search(docty) or self.pad_pattern.search(docna):
            return 'PAD'
        
        return None
    
    def filter_documents(self, docs: List[Dict]) -> Dict[str, List[Dict]]:
        """Filter documents by type and organize by language."""
        filtered = {'PID': [], 'PAD': []}
        
        for doc in docs:
            doc_type = self.detect_document_type(doc)
            if doc_type:
                filtered[doc_type].append(doc)
        
        return filtered
    
    def select_documents_by_language(self, docs: List[Dict]) -> List[Dict]:
        """Select documents based on language preference."""
        if self.languages == 'all':
            return docs
        
        # Find English documents first
        english_docs = [doc for doc in docs if doc.get('lang', '').lower() == 'en']
        
        if english_docs:
            return english_docs
        elif docs:
            # Return first available if no English
            return [docs[0]]
        
        return []
    
    def select_latest_documents(self, docs: List[Dict]) -> List[Dict]:
        """Select only the most recent documents if latest_only is True."""
        if not self.latest_only:
            return docs
        
        # Group by language and select latest by date
        by_lang = {}
        for doc in docs:
            lang = doc.get('lang', 'xx').lower()
            if lang not in by_lang:
                by_lang[lang] = []
            by_lang[lang].append(doc)
        
        latest_docs = []
        for lang_docs in by_lang.values():
            # Sort by date (newest first) and take the first
            sorted_docs = sorted(
                lang_docs,
                key=lambda x: x.get('docdt', '0000-00-00'),
                reverse=True
            )
            latest_docs.append(sorted_docs[0])
        
        return latest_docs
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        if not file_path.exists():
            return ""
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def download_pdf(self, url: str, file_path: Path) -> Tuple[bool, str, str]:
        """Download a PDF file with idempotent behavior."""
        if self.dry_run:
            return True, "dry_run", ""
        
        # Check if file already exists
        if file_path.exists():
            return True, "skipped_existing", self.get_file_hash(file_path)
        
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file was downloaded
            if file_path.exists() and file_path.stat().st_size > 0:
                file_hash = self.get_file_hash(file_path)
                return True, "downloaded", file_hash
            else:
                return False, "failed", ""
                
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return False, "failed", ""
    
    def generate_filename(self, doc: Dict, doc_type: str) -> str:
        """Generate filename for a document."""
        # Extract components
        doc_date = doc.get('docdt', '0000-00-00')
        if 'T' in doc_date:  # Handle ISO format date
            doc_date = doc_date.split('T')[0]
        
        repnb = doc.get('repnb', 'NO-REPNB')
        
        # Handle nested docna structure
        docna_field = doc.get('docna', 'Unknown')
        if isinstance(docna_field, dict):
            # New API format: docna is nested
            if '0' in docna_field and 'docna' in docna_field['0']:
                docna = docna_field['0']['docna']
            else:
                docna = 'Unknown'
        else:
            # Old API format: docna is a string
            docna = docna_field
        
        lang = doc.get('lang', 'xx').lower()
        
        # Clean and slug the document name
        docna_slug = self.slug(docna)
        
        # Format: YYYY-MM-DD_REPNB_slug_lang.pdf
        filename = f"{doc_date}_{repnb}_{docna_slug}_{lang}.pdf"
        
        return filename
    
    def process_project(self, project_id: str, country: str, project_name: str) -> Dict:
        """Process a single project and download its documents."""
        self.logger.info(f"Processing project {project_id}: {project_name}")
        
        # Get all documents for the project
        docs = self.get_project_documents(project_id)
        if not docs:
            self.logger.warning(f"No documents found for project {project_id}")
            return self._create_project_summary(project_id, country, project_name, False, False, 0, 0, [], [])
        
        # Filter documents by type
        filtered_docs = self.filter_documents(docs)
        
        # Process each document type
        pid_paths = []
        pad_paths = []
        
        for doc_type, type_docs in filtered_docs.items():
            if not type_docs:
                continue
            
            # Select documents by language preference
            selected_docs = self.select_documents_by_language(type_docs)
            
            # Select latest documents if requested
            if self.latest_only:
                selected_docs = self.select_latest_documents(selected_docs)
            
            # Download each selected document
            for doc in selected_docs:
                success, status, file_hash = self._download_document(
                    doc, doc_type, project_id, country, project_name
                )
                
                if success and status == "downloaded":
                    self.stats['downloads_successful'] += 1
                elif success and status == "skipped_existing":
                    self.stats['downloads_skipped'] += 1
                else:
                    self.stats['downloads_failed'] += 1
                
                # Track paths for summary
                if doc_type == 'PID':
                    pid_paths.append(str(self._get_document_path(doc, doc_type, project_id, country, project_name)))
                else:
                    pad_paths.append(str(self._get_document_path(doc, doc_type, project_id, country, project_name)))
        
        # Create project summary
        has_pid = len(filtered_docs['PID']) > 0
        has_pad = len(filtered_docs['PAD']) > 0
        
        if has_pid:
            self.stats['projects_with_pid'] += 1
        if has_pad:
            self.stats['projects_with_pad'] += 1
        
        return self._create_project_summary(
            project_id, country, project_name, has_pid, has_pad,
            len(filtered_docs['PID']), len(filtered_docs['PAD']),
            pid_paths, pad_paths
        )
    
    def _download_document(self, doc: Dict, doc_type: str, project_id: str, 
                          country: str, project_name: str) -> Tuple[bool, str, str]:
        """Download a single document and update manifest."""
        # Generate file path
        file_path = self._get_document_path(doc, doc_type, project_id, country, project_name)
        
        # Determine download URL
        pdf_url = doc.get('pdfurl')
        if not pdf_url:
            # Try to extract PDF URL from regular URL
            url = doc.get('url')
            if url and 'pdf' in url.lower():
                pdf_url = url
            else:
                self.logger.warning(f"No PDF URL found for document {doc.get('docna', 'Unknown')}")
                return False, "failed", ""
        
        # Download the file
        success, status, file_hash = self.download_pdf(pdf_url, file_path)
        
        # Extract document name for manifest
        docna_field = doc.get('docna', 'Unknown')
        if isinstance(docna_field, dict):
            if '0' in docna_field and 'docna' in docna_field['0']:
                docna = docna_field['0']['docna']
            else:
                docna = 'Unknown'
        else:
            docna = docna_field
        
        # Handle date format
        doc_date = doc.get('docdt', '0000-00-00')
        if 'T' in doc_date:
            doc_date = doc_date.split('T')[0]
        
        # Add to manifest
        manifest_row = {
            'country': country,
            'project_id': project_id,
            'project_title': project_name,
            'doc_type': doc_type,
            'doc_date': doc_date,
            'repnb': doc.get('repnb', 'NO-REPNB'),
            'language': doc.get('lang', 'xx'),
            'source_url': doc.get('url', ''),
            'pdf_url': pdf_url,
            'saved_path': str(file_path),
            'status': status,
            'sha256': file_hash
        }
        self.manifest_data.append(manifest_row)
        
        return success, status, file_hash
    
    def _get_document_path(self, doc: Dict, doc_type: str, project_id: str, 
                          country: str, project_name: str) -> Path:
        """Generate the file path for a document."""
        # Create project directory
        project_slug = self.slug(project_name)
        project_dir = self.out_dir / country / f"{project_id}_{project_slug}"
        
        # Create type subdirectory
        type_dir = project_dir / doc_type
        
        # Generate filename
        filename = self.generate_filename(doc, doc_type)
        
        return type_dir / filename
    
    def _create_project_summary(self, project_id: str, country: str, project_name: str,
                               has_pid: bool, has_pad: bool, pid_count: int, pad_count: int,
                               pid_paths: List[str], pad_paths: List[str]) -> Dict:
        """Create a summary entry for a project."""
        return {
            'country': country,
            'project_id': project_id,
            'project_title': project_name,
            'has_pid': has_pid,
            'has_pad': has_pad,
            'pid_count': pid_count,
            'pad_count': pad_count,
            'pid_paths': ';'.join(pid_paths),
            'pad_paths': ';'.join(pad_paths)
        }
    
    def write_manifest(self):
        """Write or append to the manifest CSV file."""
        manifest_path = self.out_dir / "manifest.csv"
        
        fieldnames = [
            'country', 'project_id', 'project_title', 'doc_type', 'doc_date',
            'repnb', 'language', 'source_url', 'pdf_url', 'saved_path', 'status', 'sha256'
        ]
        
        # Check if file exists to determine if we need headers
        file_exists = manifest_path.exists()
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would write {len(self.manifest_data)} rows to {manifest_path}")
            return
        
        # Create directory if it doesn't exist
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'a' if file_exists else 'w'
        with open(manifest_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(self.manifest_data)
        
        self.logger.info(f"Wrote {len(self.manifest_data)} rows to manifest: {manifest_path}")
    
    def write_summary(self, summary_data: List[Dict], summary_path: Optional[str] = None):
        """Write the summary CSV file."""
        if summary_path:
            summary_file = Path(summary_path)
        else:
            summary_file = self.out_dir / "summary.csv"
        
        fieldnames = [
            'country', 'project_id', 'project_title', 'has_pid', 'has_pad',
            'pid_count', 'pad_count', 'pid_paths', 'pad_paths'
        ]
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would write summary to {summary_file}")
            return
        
        # Create directory if it doesn't exist
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_data)
        
        self.logger.info(f"Wrote summary to: {summary_file}")
    
    def run(self, projects_file: str, id_col: str = "Project Id", 
            country_col: str = "Country", title_col: str = "Project Name",
            summary_out: Optional[str] = None) -> int:
        """Main execution method."""
        self.logger.info(f"Starting World Bank document downloader")
        self.logger.info(f"Projects file: {projects_file}")
        self.logger.info(f"Output directory: {self.out_dir}")
        self.logger.info(f"Languages: {self.languages}")
        self.logger.info(f"Latest only: {self.latest_only}")
        self.logger.info(f"Dry run: {self.dry_run}")
        
        # Read projects CSV
        try:
            with open(projects_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                projects = list(reader)
        except Exception as e:
            self.logger.error(f"Failed to read projects file: {e}")
            return 1
        
        if not projects:
            self.logger.error("No projects found in CSV file")
            return 1
        
        self.logger.info(f"Found {len(projects)} projects to process")
        
        # Validate required columns
        required_cols = [id_col, country_col, title_col]
        missing_cols = [col for col in required_cols if col not in projects[0]]
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return 1
        
        # Process each project
        summary_data = []
        failed_projects = []
        
        for i, project in enumerate(projects, 1):
            project_id = project[id_col].strip()
            country = project[country_col].strip()
            project_name = project[title_col].strip()
            
            if not project_id:
                self.logger.warning(f"Skipping project {i}: empty project ID")
                continue
            
            try:
                summary = self.process_project(project_id, country, project_name)
                summary_data.append(summary)
                self.stats['total_projects'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process project {project_id}: {e}")
                failed_projects.append(project_id)
        
        # Write outputs
        self.write_manifest()
        self.write_summary(summary_data, summary_out)
        
        # Print statistics
        self.logger.info("Processing complete!")
        self.logger.info(f"Total projects processed: {self.stats['total_projects']}")
        self.logger.info(f"Projects with PID: {self.stats['projects_with_pid']}")
        self.logger.info(f"Projects with PAD: {self.stats['projects_with_pad']}")
        self.logger.info(f"Downloads successful: {self.stats['downloads_successful']}")
        self.logger.info(f"Downloads skipped: {self.stats['downloads_skipped']}")
        self.logger.info(f"Downloads failed: {self.stats['downloads_failed']}")
        
        if failed_projects:
            self.logger.error(f"Failed projects: {failed_projects}")
            return 1
        
        return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download World Bank project documents (PID/PAD) from WDS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wb_downloader.py --projects projects.csv
  python wb_downloader.py --projects projects.csv --languages all --latest-only true
  python wb_downloader.py --projects projects.csv --dry-run --out-dir test_downloads
        """
    )
    
    parser.add_argument('--projects', required=True,
                       help='CSV file with project data')
    parser.add_argument('--id-col', default='Project Id',
                       help='Column name for project ID (default: Project Id)')
    parser.add_argument('--country-col', default='Country',
                       help='Column name for country (default: Country)')
    parser.add_argument('--title-col', default='Project Name',
                       help='Column name for project title (default: Project Name)')
    parser.add_argument('--languages', choices=['en', 'all'], default='en',
                       help='Language preference: en (English only) or all (default: en)')
    parser.add_argument('--latest-only', type=str, choices=['true', 'false'], default='false',
                       help='Keep only latest PID/PAD per language (default: false)')
    parser.add_argument('--out-dir', default='downloads',
                       help='Output directory (default: downloads)')
    parser.add_argument('--summary-out',
                       help='Summary CSV file path (default: {out-dir}/summary.csv)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would happen without downloading')
    
    args = parser.parse_args()
    
    # Convert latest_only string to boolean
    latest_only = args.latest_only.lower() == 'true'
    
    # Create downloader and run
    downloader = WorldBankDownloader(
        out_dir=args.out_dir,
        languages=args.languages,
        latest_only=latest_only,
        dry_run=args.dry_run
    )
    
    exit_code = downloader.run(
        projects_file=args.projects,
        id_col=args.id_col,
        country_col=args.country_col,
        title_col=args.title_col,
        summary_out=args.summary_out
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

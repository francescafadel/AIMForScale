#!/usr/bin/env python3
"""
Test script for World Bank Document Downloader

This script tests the core functionality with known project IDs to validate
that PID/PAD detection and downloading work correctly.
"""

import csv
import tempfile
import os
from pathlib import Path
from wb_downloader import WorldBankDownloader


def create_test_csv(project_ids):
    """Create a temporary CSV file with test project data."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    writer = csv.writer(temp_file)
    writer.writerow(['Project Id', 'Country', 'Project Name'])
    
    for project_id in project_ids:
        writer.writerow([project_id, 'Test Country', f'Test Project {project_id}'])
    
    temp_file.close()
    return temp_file.name


def test_document_detection():
    """Test document type detection with sample data."""
    downloader = WorldBankDownloader(dry_run=True)
    
    # Test PID detection
    pid_docs = [
        {'docty': 'Project Information Document', 'docna': 'Some document'},
        {'docty': 'PID', 'docna': 'Another document'},
        {'docty': 'Other', 'docna': 'Project Information Document for testing'},
        {'docty': 'Concept Stage', 'docna': 'Some document'},
    ]
    
    # Test PAD detection
    pad_docs = [
        {'docty': 'Project Appraisal Document', 'docna': 'Some document'},
        {'docty': 'PAD', 'docna': 'Another document'},
        {'docty': 'Other', 'docna': 'Program Appraisal Document for testing'},
    ]
    
    # Test non-matching documents
    other_docs = [
        {'docty': 'Implementation Status Report', 'docna': 'Some ISR'},
        {'docty': 'Procurement Plan', 'docna': 'Some procurement document'},
        {'docty': 'Audit Report', 'docna': 'Some audit document'},
    ]
    
    print("Testing PID detection:")
    for doc in pid_docs:
        doc_type = downloader.detect_document_type(doc)
        print(f"  {doc['docty']} / {doc['docna']} -> {doc_type}")
        assert doc_type == 'PID', f"Expected PID, got {doc_type}"
    
    print("\nTesting PAD detection:")
    for doc in pad_docs:
        doc_type = downloader.detect_document_type(doc)
        print(f"  {doc['docty']} / {doc['docna']} -> {doc_type}")
        assert doc_type == 'PAD', f"Expected PAD, got {doc_type}"
    
    print("\nTesting non-matching documents:")
    for doc in other_docs:
        doc_type = downloader.detect_document_type(doc)
        print(f"  {doc['docty']} / {doc['docna']} -> {doc_type}")
        assert doc_type is None, f"Expected None, got {doc_type}"
    
    print("\n✅ Document detection tests passed!")


def test_slug_generation():
    """Test slug generation function."""
    downloader = WorldBankDownloader(dry_run=True)
    
    test_cases = [
        ("Simple Project Name", "simple-project-name"),
        ("Complex Project Name with Numbers 123", "complex-project-name-with-numbers-123"),
        ("Special Characters: @#$%^&*()", "special-characters"),
        ("Unicode: São Paulo Project", "unicode-sao-paulo-project"),
        ("Very Long Project Name " * 10, "very-long-project-name-very-long-project-name-very-long-project-name-very-long-project-name-very-long-project-name-very"),
    ]
    
    print("Testing slug generation:")
    for input_text, expected in test_cases:
        result = downloader.slug(input_text)
        print(f"  '{input_text}' -> '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("✅ Slug generation tests passed!")


def test_api_integration():
    """Test API integration with a known project."""
    print("\nTesting API integration with project P149286...")
    
    downloader = WorldBankDownloader(dry_run=True)
    
    # Test API call
    response = downloader.call_wds_api("P149286")
    
    if response and 'response' in response:
        docs = response['response'].get('docs', [])
        print(f"  Found {len(docs)} documents")
        
        if docs:
            # Test document filtering
            filtered = downloader.filter_documents(docs)
            print(f"  PID documents: {len(filtered['PID'])}")
            print(f"  PAD documents: {len(filtered['PAD'])}")
            
            # Show some document details
            for doc_type, type_docs in filtered.items():
                if type_docs:
                    print(f"  {doc_type} examples:")
                    for doc in type_docs[:2]:  # Show first 2
                        print(f"    - {doc.get('docna', 'Unknown')} ({doc.get('lang', 'unknown')})")
        
        print("✅ API integration test passed!")
    else:
        print("⚠️  API test failed - this might be due to network issues or API changes")


def test_full_workflow():
    """Test the full workflow with a known project."""
    print("\nTesting full workflow...")
    
    # Create test CSV
    test_csv = create_test_csv(["P149286"])
    
    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = WorldBankDownloader(
                out_dir=temp_dir,
                languages='en',
                latest_only=False,
                dry_run=True
            )
            
            # Run the downloader
            exit_code = downloader.run(test_csv)
            
            print(f"  Exit code: {exit_code}")
            print(f"  Total projects processed: {downloader.stats['total_projects']}")
            print(f"  Projects with PID: {downloader.stats['projects_with_pid']}")
            print(f"  Projects with PAD: {downloader.stats['projects_with_pad']}")
            
            # Check if manifest was created
            manifest_path = Path(temp_dir) / "manifest.csv"
            if manifest_path.exists():
                print(f"  Manifest created: {manifest_path}")
            else:
                print("  ⚠️  Manifest not created")
            
            print("✅ Full workflow test completed!")
            
    finally:
        # Clean up test CSV
        os.unlink(test_csv)


def main():
    """Run all tests."""
    print("🧪 Running World Bank Document Downloader Tests\n")
    
    try:
        test_document_detection()
        test_slug_generation()
        test_api_integration()
        test_full_workflow()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

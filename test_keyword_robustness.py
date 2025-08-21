#!/usr/bin/env python3
"""
Test script for robust keyword matching functionality.
Tests all acceptance criteria for the enhanced keyword search.
"""

import re
import unicodedata
from typing import List, Dict

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent matching.
    """
    if not text:
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
    """
    if not text:
        return []
    
    # Normalize the text for matching
    normalized_text = normalize_text(text)
    
    found_keywords = []
    
    for keyword, pattern in keyword_patterns.items():
        if pattern.search(normalized_text):
            found_keywords.append(keyword)  # Return original keyword case
    
    return found_keywords

def test_keyword_robustness():
    """Test all acceptance criteria for keyword matching."""
    print("🧪 Testing Keyword Robustness")
    print("=" * 60)
    
    # Test keywords
    keywords = [
        "cow", "climate smart livestock", "climate-smart livestock", 
        "feed conversion ratio", "zoonosis", "pasture"
    ]
    
    # Test cases with expected results
    test_cases = [
        # Case-insensitive tests
        ("Cow health program", ["cow"], "Case-insensitive matching"),
        ("COW health program", ["cow"], "Case-insensitive matching (uppercase)"),
        ("cow health program", ["cow"], "Case-insensitive matching (lowercase)"),
        
        # Separator-tolerant tests - each keyword should match its own pattern
        ("climate-smart livestock", ["climate smart livestock", "climate-smart livestock"], "Separator-tolerant (hyphen)"),
        ("climate smart livestock", ["climate smart livestock"], "Separator-tolerant (space)"),
        ("climate_smart livestock", ["climate smart livestock"], "Separator-tolerant (underscore)"),
        ("climate/smart livestock", ["climate smart livestock"], "Separator-tolerant (slash)"),
        
        # Accent normalization tests
        ("zoonósis control", ["zoonosis"], "Accent normalization"),
        ("zoonosis control", ["zoonosis"], "Accent normalization (no accent)"),
        
        # Word boundary tests
        ("scowl", [], "Word boundary protection"),
        ("coward", [], "Word boundary protection"),
        ("cow", ["cow"], "Word boundary (exact match)"),
        
        # Multiword boundary tests
        ("feed-conversion ratio", ["feed conversion ratio"], "Multiword boundary (hyphen)"),
        ("feed conversion ratio", ["feed conversion ratio"], "Multiword boundary (space)"),
        ("feed_conversion ratio", ["feed conversion ratio"], "Multiword boundary (underscore)"),
        
        # Duplicate handling tests - each occurrence should be found once
        ("pasture pasture", ["pasture"], "Duplicate handling (finds each keyword once)"),
        ("pasture and pasture", ["pasture"], "Duplicate handling (finds each keyword once)"),
        
        # Complex real-world examples
        ("Climate-smart livestock farming in Africa", ["climate smart livestock", "climate-smart livestock"], "Complex real-world example"),
        ("Cow health and zoonósis prevention", ["cow", "zoonosis"], "Complex real-world example with accents"),
        ("Feed conversion ratio optimization", ["feed conversion ratio"], "Complex real-world example"),
    ]
    
    # Compile patterns
    keyword_patterns = compile_keyword_patterns(keywords)
    
    # Run tests
    passed = 0
    failed = 0
    
    for text, expected, description in test_cases:
        found = find_keywords_in_text(text, keyword_patterns)
        
        # Check if results match expected (allowing for order differences)
        success = set(found) == set(expected)
        
        if success:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"{status} {description}")
        print(f"   Text: '{text}'")
        print(f"   Expected: {expected}")
        print(f"   Found: {found}")
        print()
    
    # Summary
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Keyword matching is robust.")
    else:
        print("⚠️  Some tests failed. Review the patterns above.")
    
    return failed == 0

def test_specific_keywords():
    """Test specific keywords from the new comprehensive list."""
    print("\n🔍 Testing Specific Keywords from New List")
    print("=" * 60)
    
    # Load keywords from file
    try:
        with open('keywords.txt', 'r') as f:
            keywords = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ keywords.txt not found. Run the main script first to create it.")
        return False
    
    print(f"Loaded {len(keywords)} keywords from keywords.txt")
    
    # Test specific challenging keywords
    test_keywords = [
        "African swine fever",
        "climate smart livestock", 
        "climate-smart livestock",
        "feed conversion ratio",
        "community based breeding",
        "goat meat",
        "herd health",
        "manure management",
        "waste management",
        "women in livestock"
    ]
    
    # Verify these keywords are in our list
    missing_keywords = [kw for kw in test_keywords if kw not in keywords]
    if missing_keywords:
        print(f"❌ Missing keywords: {missing_keywords}")
        return False
    
    print("✅ All test keywords found in keywords.txt")
    
    # Test pattern compilation
    try:
        patterns = compile_keyword_patterns(test_keywords)
        print(f"✅ Successfully compiled patterns for {len(patterns)} keywords")
    except Exception as e:
        print(f"❌ Pattern compilation failed: {e}")
        return False
    
    # Test specific matching scenarios
    test_scenarios = [
        ("African swine fever outbreak", ["African swine fever"]),
        ("climate-smart livestock program", ["climate smart livestock", "climate-smart livestock"]),
        ("feed conversion ratio improvement", ["feed conversion ratio"]),
        ("community based breeding initiative", ["community based breeding"]),
        ("goat meat production", ["goat meat"]),
        ("herd health management", ["herd health"]),
        ("manure management system", ["manure management"]),
        ("waste management program", ["waste management"]),
        ("women in livestock training", ["women in livestock"]),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_scenarios:
        found = find_keywords_in_text(text, patterns)
        success = set(found) == set(expected)
        
        if success:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"
        
        print(f"{status} '{text}' → {found}")
    
    print(f"\n📊 Specific keyword tests: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    print("🚀 Starting Keyword Robustness Tests")
    print("=" * 60)
    
    # Run basic robustness tests
    basic_tests_passed = test_keyword_robustness()
    
    # Run specific keyword tests
    specific_tests_passed = test_specific_keywords()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 60)
    
    if basic_tests_passed and specific_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Keyword matching is robust and ready for production use.")
        print("✅ Ready to process your CSV file with enhanced keyword detection.")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("❌ Please review the failed tests above before proceeding.")
    
    print("\n📝 Next steps:")
    print("1. Place your CSV file in the project directory")
    print("2. Run: python csv_keyword_scanner.py your_file.csv")
    print("3. Check the output CSV for keyword matches")

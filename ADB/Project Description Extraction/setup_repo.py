"""
Script to organize files into ADB/Project Description Extraction/ structure.

Run from the folder that contains the root project files (e.g. "ADB Project Description Extraction").
Creates ADB/Project Description Extraction/ and copies scripts, tests, data, docs, utils into it.
"""

import shutil
from pathlib import Path

# Base directory: parent of the folder containing this script (Project Description Extraction)
THIS_DIR = Path(__file__).parent.resolve()
BASE_DIR = THIS_DIR.parent  # "ADB Project Description Extraction"
TARGET_DIR = THIS_DIR  # we're already inside Project Description Extraction

# File organization mapping: (source_file, (target_subdir, target_filename))
FILE_MAPPING = {
    "extract_descriptions_test_3_fixed.py": ("scripts/", "adb_description_extractor.py"),
    "scrape_adb_descriptions.py": ("scripts/", None),
    "extract_descriptions_test_5.py": ("tests/", None),
    "extract_descriptions_test_batch.py": ("tests/", None),
    "scrape_adb_descriptions_test.py": ("tests/", None),
    "test_single_url.py": ("tests/", None),
    "add_description_column_header.py": ("utils/", None),
    "ISSUES_ANALYSIS.md": ("docs/", None),
    "TEST_RESULTS.md": ("docs/", None),
    "USAGE.md": ("docs/", None),
    "README.md": ("", None),
    "requirements.txt": ("", None),
}

# Data files (relative to BASE_DIR)
DATA_FILES = [
    "Copy of Final ADB Corpus - Link Extraction File.csv",
    "Final ADB Corpus - Link Extraction File.csv",
    "Final ADB Corpus - Sheet1_with_urls.csv",
    "Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv",
    "Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv",
    "ADB Working document.csv",
    "Final ADB Corpus - Link Extraction File .numbers",
    "Final ADB Corpus, Insert to Cursor.numbers",
]


def main():
    (TARGET_DIR / "scripts").mkdir(exist_ok=True)
    (TARGET_DIR / "tests").mkdir(exist_ok=True)
    (TARGET_DIR / "data").mkdir(exist_ok=True)
    (TARGET_DIR / "docs").mkdir(exist_ok=True)
    (TARGET_DIR / "utils").mkdir(exist_ok=True)

    for filename, (subdir, new_name) in FILE_MAPPING.items():
        source = BASE_DIR / filename
        if source.exists():
            dest_dir = TARGET_DIR / subdir if subdir else TARGET_DIR
            dest_dir.mkdir(parents=True, exist_ok=True)
            target_filename = new_name or filename
            shutil.copy2(source, dest_dir / target_filename)
            print(f"Copied {filename} -> {subdir or '.'}{target_filename}")

    for filename in DATA_FILES:
        source = BASE_DIR / filename
        if source.exists():
            shutil.copy2(source, TARGET_DIR / "data" / filename)
            print(f"Copied {filename} -> data/")

    print(f"\nDone. Target: {TARGET_DIR}")


if __name__ == "__main__":
    main()

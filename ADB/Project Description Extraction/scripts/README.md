# Scripts folder contents

This folder holds the main Python scripts that run the ADB project description extraction. Below is what each file contains.

---

**adb_description_extractor.py**  
Primary extraction script. Reads project URLs from the working CSV in the data folder, visits each ADB project page, and writes the scraped description into the Description column. Uses direct navigation to the /pds URL when possible, then falls back to force-clicking the Project Data Sheet tab. Extracts text from table rows or dt/dd elements. Skips duplicate project IDs and uses configurable test size (TEST_SIZE) for partial runs. Run from the project root; input and output CSVs are in the data folder.

**scrape_adb_descriptions.py**  
Alternative scraper that uses pandas to load the CSV and detect the URL column automatically. Navigates to each project URL, clicks Project Data Sheet when available, and extracts the description using the same table and dt/dd strategies. Appends a Description column and saves the result. Uses different wait and navigation settings than adb_description_extractor.py. Expects input and output CSV filenames (e.g. Sheet1_with_urls, Sheet1_with_urls_and_descriptions) in the data folder.

**extract_descriptions_test_3_fixed.py**  
Standalone version of the main extractor with the same extraction logic (direct /pds navigation, force click, table and dt/dd extraction). Uses paths relative to the Project Description Extraction folder and the data subfolder. Intended to be run from the project root so CSV paths resolve correctly. Use this when you want the same behavior as adb_description_extractor.py with a separate entry point or path setup.

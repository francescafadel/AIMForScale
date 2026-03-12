# Utils folder contents

This folder holds helper scripts used to prepare or maintain the Project Description Extraction pipeline. Below is what each file contains.

---

**add_description_column_header.py**  
Adds a Description column to the working CSV (Copy of Final ADB Corpus - Link Extraction File.csv) in the data folder if that column is missing. Finds the header row by the Project ID column, appends "Description" to the header, and pads all data rows so they have the same number of columns. Run once before the first extraction if your CSV does not yet have a Description column. Reads and writes the file in the data folder.

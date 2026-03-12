# Data folder contents

This folder holds the CSV and Numbers files used and produced by the Project Description Extraction pipeline. Below is what each file contains.

---

## CSV files

**Copy of Final ADB Corpus - Link Extraction File.csv**  
Working corpus used by the main extraction script. Contains project metadata (Project ID, Name, Country, Financing, Sector, etc.), a Project Link column (URLs in the form `https://www.adb.org/projects/{Project ID}/main`), and a Description column that the scraper fills by visiting each URL and extracting the description from the Project Data Sheet. This file is both the primary input and the primary output for the extraction run.

**Final ADB Corpus - Link Extraction File.csv**  
Source export from the link-extraction workflow. Includes methodology lines at the top (how the ADB Sovereign Projects CSV was obtained), then a header row and project rows. Columns include Project ID, Name, Country, Financing, Project Type, Status, Approval details, Sector, Department, Executing Agency, Project Officer, and Summary. No Project Link or Description columns. Used as the base to create the "Copy of" working file.

**Final ADB Corpus - Sheet1_with_urls.csv**  
Corpus of ADB projects with a URL column added (project page links). Same metadata as the Link Extraction File plus a column of project URLs. Used as an alternative input by the pandas-based scraper. May contain duplicate project IDs across rows.

**Final ADB Corpus - Sheet1_with_urls_and_descriptions.csv**  
Output of a full (or partial) description extraction run. Same structure as Sheet1_with_urls plus a Description column populated with text scraped from each project’s Project Data Sheet. One row per project row in the source; descriptions are blank where extraction failed or was not run.

**Final ADB Corpus - Sheet1_with_urls_and_descriptions_TEST.csv**  
Same structure as Sheet1_with_urls_and_descriptions but containing only the subset of rows used in a test run (e.g. first N URLs). Used to verify the pipeline without processing the full corpus.

**ADB Working document.csv**  
Deduplicated version of the project corpus. Same kind of project and URL columns as the other corpora, with duplicate rows removed. Can be used as a cleaner input for analysis or for a separate extraction run.

---

## Numbers files

**Final ADB Corpus - Link Extraction File .numbers**  
Apple Numbers workbook containing the same underlying data as the CSV "Final ADB Corpus - Link Extraction File.csv". Used for manual editing or review before exporting to CSV.

**Final ADB Corpus, Insert to Cursor.numbers**  
Apple Numbers workbook used to prepare or curate the corpus for use in Cursor (e.g. filtering, column setup, or exporting). Content aligns with the other Final ADB Corpus files; the name indicates it was prepared for insertion into Cursor workflows.

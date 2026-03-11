# ADB Links

This folder is for the **ADB project corpus and URL generation** used in the AIMForScale project.

## What goes here

| Item | Description |
|------|-------------|
| **Final ADB Corpus - Sheet1.csv** | Base CSV corpus of ADB projects (project IDs and metadata). |
| **Final ADB Corpus - Sheet1_with_urls.csv** | Same corpus with an added column of project page URLs: `https://www.adb.org/projects/{Project ID}/main`. |
| **add_adb_urls.py** | Script that generates the URL column from the Project ID column. |

If you have these files from another location (e.g. your Desktop or the Project Description Extraction data folder), you can copy them here so the ADB Links folder in the repo is self-contained.

## Relation to Project Description Extraction

The **Project Description Extraction** pipeline (in the parent repo: `ADB/Project Description Extraction/`) uses similar corpora that include a **Project Link** column. Those working files live in `ADB/Project Description Extraction/data/` (e.g. **Copy of Final ADB Corpus - Link Extraction File.csv**). This **ADB Links** folder holds the canonical corpus and the script that builds the URL column; the extractor can use files from either place depending on your workflow.

# Docs folder contents

This folder holds documentation for the Project Description Extraction pipeline. Below is what each file contains.

---

**USAGE.md**  
Step-by-step instructions for running the ADB description scraper. Covers installing dependencies (pandas, playwright, Playwright browser), how to run the script, what progress output to expect, where input and output files live, and troubleshooting (timeouts, missing Project Data Sheet link, network errors). Use this when you need to run the extraction locally.

**ISSUES_ANALYSIS.md**  
Technical analysis of problems encountered with the extraction script. Describes navigation wait strategy (domcontentloaded vs networkidle), missing wait after clicking the Project Data Sheet tab, Cloudflare handling, selector and count-check behavior, and suggested fixes. Intended for developers debugging or improving the scraper.

**TEST_RESULTS.md**  
Summary of test runs of the scraper. Includes test date, script and dataset used, number of URLs tested, success rate, an example of a successfully extracted description, what works, known limitations, output file names, and next steps (full run, parameter changes, investigating failed URLs). Use this to understand how the pipeline has performed in testing.

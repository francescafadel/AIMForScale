# World Bank Document Downloader

A standalone Python module/CLI that downloads Project Information Documents (PID) and Project/Program Appraisal Documents (PAD) from the World Bank WDS API.

## Features

- **API Integration**: Uses the World Bank WDS API (no browser automation)
- **Document Detection**: Automatically detects PID and PAD documents using regex patterns
- **Idempotent Downloads**: Skips existing files, handles duplicates gracefully
- **Language Support**: Download English documents or all available languages
- **Latest Only Option**: Keep only the most recent PID/PAD per language
- **Comprehensive Outputs**: Manifest CSV with download tracking and summary statistics
- **Error Handling**: Retry logic, graceful failure handling, non-zero exit codes

## Installation

1. Clone or download the files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python wb_downloader.py --projects projects.csv
```

### Advanced Usage

```bash
python wb_downloader.py --projects projects.csv \
    --id-col "Project Id" --country-col Country --title-col "Project Name" \
    --languages en --out-dir downloads --latest-only false
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--projects` | **Required** | CSV file with project data |
| `--id-col` | `Project Id` | Column name for project ID |
| `--country-col` | `Country` | Column name for country |
| `--title-col` | `Project Name` | Column name for project title |
| `--languages` | `en` | Language preference: `en` (English only) or `all` |
| `--latest-only` | `false` | Keep only latest PID/PAD per language: `true` or `false` |
| `--out-dir` | `downloads` | Output directory |
| `--summary-out` | `{out-dir}/summary.csv` | Summary CSV file path |
| `--dry-run` | `false` | Show what would happen without downloading |

## Input CSV Format

The input CSV should have at least these columns (configurable via CLI options):

```csv
Project Id,Country,Project Name
P149286,India,Second Karnataka State Highway Improvement Project
P123456,Kenya,Urban Water and Sanitation Project
```

## Output Structure

### File Organization

```
downloads/
├── manifest.csv
├── summary.csv
└── {Country}/
    └── {ProjectId}_{slug(ProjectName)}/
        ├── PID/
        │   └── {YYYY-MM-DD}_{repnb}_{slug(docna)}_{lang}.pdf
        └── PAD/
            └── {YYYY-MM-DD}_{repnb}_{slug(docna)}_{lang}.pdf
```

### Manifest CSV

Tracks all download attempts with columns:
- `country`, `project_id`, `project_title`
- `doc_type`, `doc_date`, `repnb`, `language`
- `source_url`, `pdf_url`, `saved_path`
- `status` (downloaded/skipped_existing/failed), `sha256`

### Summary CSV

Per-project statistics with columns:
- `country`, `project_id`, `project_title`
- `has_pid`, `has_pad` (boolean)
- `pid_count`, `pad_count` (integer)
- `pid_paths`, `pad_paths` (semicolon-separated file paths)

## Examples

### Download English documents only
```bash
python wb_downloader.py --projects projects.csv --languages en
```

### Download all languages
```bash
python wb_downloader.py --projects projects.csv --languages all
```

### Keep only latest documents per language
```bash
python wb_downloader.py --projects projects.csv --latest-only true
```

### Preview mode (no downloads)
```bash
python wb_downloader.py --projects projects.csv --dry-run
```

### Custom output directory
```bash
python wb_downloader.py --projects projects.csv --out-dir my_downloads
```

### Custom column names
```bash
python wb_downloader.py --projects projects.csv \
    --id-col "WB_ID" --country-col "Nation" --title-col "Project_Title"
```

## Document Detection

The tool uses regex patterns to detect document types:

### PID (Project Information Document)
- `(?i)\bproject information document\b|\bpid\b|pid\s*\/\s*isds|(concept|appraisal)\s*stage`

### PAD (Project/Program Appraisal Document)
- `(?i)\b(project|program)\s+appraisal\s+document\b|\bpad\b`

## Error Handling

- **API Failures**: Automatic retry with exponential backoff for 429/5xx errors
- **Missing Files**: Graceful handling of missing PDF URLs
- **Duplicate Files**: Appends version numbers (-v2, -v3) for same-name files with different content
- **Exit Codes**: Returns non-zero exit code if any downloads fail

## Testing

Use the included sample file to test the tool:

```bash
python wb_downloader.py --projects sample_projects.csv --dry-run
```

## API Endpoint

The tool uses the World Bank WDS API:
```
https://search.worldbank.org/api/v2/wds?format=json&includepublicdocs=1&rows=200&os={offset}&proid={PROJECT_ID}&fl=docna,docty,docdt,lang,repnb,url,pdfurl,projn,proid,countryshortname,countryname
```

## Requirements

- Python 3.6+
- requests library

## License

This tool is provided as-is for educational and research purposes.

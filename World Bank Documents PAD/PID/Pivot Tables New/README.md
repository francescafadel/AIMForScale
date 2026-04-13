# make_pivot_table

Reads a World Bank livestock projects CSV and generates binary pivot tables and a co-occurrence heatmap showing which interventions and outcomes appear across projects.

## Outputs
- `livestock_pivot_tables.xlsx` — 3 sheets: Interventions Pivot, Outcomes Pivot, and Co-occurrence Table
- `intervention_outcome_heatmap.png` — heatmap of intervention vs outcome co-occurrences

Both files are saved to the same directory as your input CSV.

## How to use

**1. Install dependencies**
```bash
pip install pandas openpyxl matplotlib
```

**2. Set your file path** — open `make_pivot_table.py` and update this line at the top:
```python
INPUT_CSV_PATH = "/path/to/your/file.csv"
```

**3. Run the script**
```bash
python make_pivot_table.py
```
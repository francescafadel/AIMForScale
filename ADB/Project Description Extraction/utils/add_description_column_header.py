import csv

# File paths
input_file = "Copy of Final ADB Corpus - Link Extraction File.csv"
output_file = "Copy of Final ADB Corpus - Link Extraction File.csv"

# Read the CSV file
rows = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

# Find the header row
header_row_index = None
for i, row in enumerate(rows):
    if len(row) > 0 and row[0].strip() == "Project ID":
        header_row_index = i
        break

if header_row_index is None:
    print("Error: Could not find header row with 'Project ID'")
    exit(1)

# Add "Description" column if it doesn't exist
if "Description" not in rows[header_row_index]:
    rows[header_row_index].append("Description")
    print("Added 'Description' column header")
else:
    print("'Description' column already exists")

# Ensure all data rows have enough columns
for i in range(header_row_index + 1, len(rows)):
    while len(rows[i]) <= len(rows[header_row_index]) - 1:
        rows[i].append("")

# Write the updated CSV file
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print(f"Updated {output_file}")


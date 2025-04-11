import pandas as pd
import re

# Input and output files
input_file = 'my_output_USER.csv'    # The spool output file
output_file = 'oracle_output.xlsx'   # The Excel file to create

# Read the entire file
with open(input_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

sheets = {}
current_table = None
headers = []
rows = []

for line in lines:
    line = line.strip()

    # New table section
    if line.startswith('-- '):
        # Save previous table
        if current_table and headers:
            df = pd.DataFrame(rows, columns=headers)
            sheets[current_table] = df

        # Reset for new table
        current_table = line[3:].strip().replace('.', '_')
        headers = []
        rows = []

    elif line.startswith('"') and not headers:
        # CSV header row
        headers = [h.strip('"') for h in line.split(',')]

    elif line.startswith('['):
        # Skipped, Error, or No data — log as empty DataFrame
        if current_table:
            sheets[current_table] = pd.DataFrame()
        current_table = None
        headers = []
        rows = []

    elif headers and line:
        # CSV data row
        row = re.findall(r'(?:"((?:[^"]|"")*)"|([^,]*))(?:,|$)', line)
        row = [r[0].replace('""', '"') if r[0] else r[1] for r in row]
        rows.append(row)

# Add the final table
if current_table and headers:
    df = pd.DataFrame(rows, columns=headers)
    sheets[current_table] = df

# Write to Excel
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    for sheet_name, df in sheets.items():
        safe_name = sheet_name[:31]  # Excel sheet name max length
        df.to_excel(writer, index=False, sheet_name=safe_name)

print(f"Excel file created: {output_file}")

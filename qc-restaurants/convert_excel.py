import pandas as pd
import os

# Get the absolute path to the data files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, 'Outscraper-20250306082041s8b.xlsx')
CSV_FILE = os.path.join(BASE_DIR, 'restaurants.xlsx.csv')

# Read the Excel file
print(f"Reading Excel file from: {EXCEL_FILE}")
df = pd.read_excel(EXCEL_FILE)

# Save as CSV
print(f"Saving CSV file to: {CSV_FILE}")
df.to_csv(CSV_FILE, index=False, encoding='utf-8')
print("Conversion complete!") 
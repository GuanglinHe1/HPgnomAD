#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import sys

# Check command line arguments
if len(sys.argv) != 3:
    print("Usage: python 2_tsv_df.py <input_tsv_file> <output_dir>")
    sys.exit(1)

# Input file and output directory
input_file = sys.argv[1]
output_dir = sys.argv[2]
os.makedirs(output_dir, exist_ok=True)

# Sample name (used to overwrite QRY_TAG)
file_name   = os.path.basename(input_file)
sample_name = file_name.replace('_vs_ref.snps.tsv', '')

# 1. Read all non-empty lines
with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = [ln.strip() for ln in f if ln.strip()]

# 2. Locate the index of header line starting with “[P1]”
try:
    header_idx = next(i for i, ln in enumerate(lines) if ln.startswith('[P1]'))
except StopIteration:
    sys.exit('ERROR: Cannot find header line starting with "[P1]" in the file.')

# 3. Parse all data lines starting from the line after the header
data_lines = lines[header_idx + 1:]
records = []
for ln in data_lines:
    # Skip any comment or extra bracket lines
    if ln.startswith('[') or ln.startswith('/'):
        continue
    parts = ln.split()  # Split by whitespace
    # Expect at least 12 columns: P1, SUB_REF, SUB_ALT, P2, BUFF, DIST, LEN_R, LEN_Q,
    #                             FRM_ref, FRM_qry, REF_TAG, QRY_TAG
    if len(parts) < 12:
        continue
    records.append(parts[:12])

# 4. Build DataFrame and name columns
columns = [
    'P1',
    'SUB_REF',
    'SUB_ALT',
    'P2',
    'BUFF',
    'DIST',
    'LEN_R',
    'LEN_Q',
    'FRM_ref',
    'FRM_qry',
    'REF_TAG',
    'QRY_TAG'
]
df = pd.DataFrame(records, columns=columns)

# 5. Split FRM_ref and FRM_qry into Ref_dir and Samp_dir
df['Ref_dir']  = df['FRM_ref']
df['Samp_dir'] = df['FRM_qry']
df = df.drop(columns=['FRM_ref', 'FRM_qry'])

# 6. Overwrite QRY_TAG with the sample name
df['QRY_TAG'] = sample_name

# 7. Save as CSV
output_file = os.path.join(output_dir, f"{sample_name}.csv")
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"Processing completed. Output file: {output_file}")

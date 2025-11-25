
import pandas as pd
import os
import sys

if len(sys.argv) != 3:
    print("Usage: python 2_tsv_df.py <input_tsv_file> <output_dir>")
    sys.exit(1)

input_file = sys.argv[1]
output_dir = sys.argv[2]
os.makedirs(output_dir, exist_ok=True)

file_name   = os.path.basename(input_file)
sample_name = file_name.replace('_vs_ref.snps.tsv', '')

with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = [ln.strip() for ln in f if ln.strip()]

try:
    header_idx = next(i for i, ln in enumerate(lines) if ln.startswith('[P1]'))
except StopIteration:
    sys.exit("ERROR: Cannot find the header line starting with \"[P1]\" in the file.")

data_lines = lines[header_idx + 1:]
records = []
for ln in data_lines:
    if ln.startswith('[') or ln.startswith('/'):
        continue
    if len(parts) < 12:
        continue
    records.append(parts[:12])

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

df['Ref_dir']  = df['FRM_ref']
df['Samp_dir'] = df['FRM_qry']
df = df.drop(columns=['FRM_ref', 'FRM_qry'])

df['QRY_TAG'] = sample_name

output_file = os.path.join(output_dir, f"{sample_name}.csv")
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"File processing completed! Output file: {output_file}")

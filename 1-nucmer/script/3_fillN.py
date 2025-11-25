#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script uses the coord file to modify CSV and add N positions,
# distinguishing non-variant bases from uncovered bases.
# Expected output format:
# P1,P2,SUB_REF,SUB_ALT,REF_TAG,QRY_TAG,REAL_REF,BUFF,DIST,LEN_R,LEN_Q,Ref_dir,Samp_dir
# 100,101,A,G,ref1,qry1,A,5,10,100,100,0,0
# 150,151,T,C,ref1,qry1,T,5,10,100,100,0,0
# 200,201,G,N,ref1,qry1,G,1,1,1,1,1,1   #todo First added N site, N represents uncovered base
# 300,301,C,N,ref1,qry1,C,1,1,1,1,1,1   #todo Second added N site, N represents uncovered base
import os
import argparse
import pandas as pd

def process(sample_id, coords_file, reference_csv, final_csv_file, output_dir):
    # 1. Read coords file and filter aligned == 'N'
    coords = pd.read_csv(coords_file, usecols=['pos','aligned'])
    n_positions = coords.loc[coords['aligned']=='N','pos']

    # 2. Read reference bases
    ref = pd.read_csv(reference_csv, usecols=['pos','base'])
    ref_n = pd.merge(pd.DataFrame({'pos':n_positions}),
                     ref, on='pos', how='inner')

    # 3. Read original variant CSV
    orig = pd.read_csv(final_csv_file)
    cols = orig.columns

    # 4. Vectorized construction of N positions
    df_n = pd.DataFrame('N', index=range(len(ref_n)), columns=cols)
    df_n['P1']      = ref_n['pos'].values
    df_n['SUB_REF'] = ref_n['base'].values
    df_n['SUB_ALT'] = 'N'

    # 5. Merge and sort
    df = pd.concat([orig, df_n], ignore_index=True)
    # First convert column P1 to numeric (non-numeric parts become NaN)
    df['P1'] = pd.to_numeric(df['P1'], errors='coerce')
    # Then sort directly by P1
    df.sort_values(by='P1', inplace=True)
    # 6. Update fields for rows with SUB_ALT == 'N'
    mask = df['SUB_ALT']=='N'
    ref_tag = orig['REF_TAG'].iat[0]
    qry_tag = orig['QRY_TAG'].iat[0]

    df.loc[mask, 'REF_TAG']  = ref_tag
    df.loc[mask, 'QRY_TAG']  = qry_tag
    df.loc[mask, 'REAL_REF'] = df.loc[mask, 'SUB_REF']
    for c in ['P2','BUFF','DIST','LEN_R','LEN_Q','Ref_dir','Samp_dir']:
        df.loc[mask, c] = 1


    # 8. Write output
    os.makedirs(output_dir, exist_ok=True)
    out_csv = os.path.join(output_dir, f"{sample_id}.csv")
    df.to_csv(out_csv, index=False, encoding='utf-8')
    print(f"[{sample_id}] -> {out_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Fill N sites and generate CSV for VCF conversion")
    parser.add_argument('--coords-file',    required=True,
                        help="*_vs_ref.coords.csv file")
    parser.add_argument('--reference-csv',  required=True,
                        help="Reference base CSV")
    parser.add_argument('--final-csv-dir',  required=True,
                        help="Directory containing original .csv files")
    parser.add_argument('--output-dir',     required=True,
                        help="Output CSV directory")
    args = parser.parse_args()

    # Extract sample_id from file name
    base = os.path.basename(args.coords_file)
    sample_id = base.replace('_vs_ref.coords.csv','')

    # Build path to original variant CSV
    final_csv_file = os.path.join(args.final_csv_dir,
                                  f"{sample_id}.csv")
    if not os.path.exists(final_csv_file):
        raise FileNotFoundError(f"Original CSV not found: {final_csv_file}")

    process(sample_id,
            args.coords_file,
            args.reference_csv,
            final_csv_file,
            args.output_dir)

if __name__=='__main__':
    main()

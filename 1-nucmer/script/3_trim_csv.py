#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import sys
from Bio import SeqIO

def process_csv(input_file, output_dir, fasta_path):
    # Extract sample name
    file_name   = os.path.basename(input_file)
    sample_name = file_name.replace('.csv', '')

    # Read reference sequence
    record   = SeqIO.read(fasta_path, "fasta")
    sequence = str(record.seq)
    # Build reference position-to-base table
    positions = list(range(1, len(sequence) + 1))
    bases     = list(sequence)
    ref_df    = pd.DataFrame({"P1": positions, "REAL_REF": bases})

    # Read CSV, ensure P1 is integer
    df_hp = pd.read_csv(input_file, dtype={"P1": int})

    # Keep required columns and merge reference bases
    df_trim = df_hp[['P1','SUB_REF','SUB_ALT','REF_TAG','QRY_TAG']].merge(
                  ref_df, on='P1', how='left')

    # —— Insertion events (SUB_REF == '.') aggregation and rewrite
    ins = df_trim[df_trim['SUB_REF'] == '.']
    if not ins.empty:
        proc_ins = ins.groupby('P1').agg({
            'SUB_REF': 'first',
            'SUB_ALT': ''.join,
            'REF_TAG': 'first',
            'QRY_TAG': 'first',
            'REAL_REF': 'first'
        }).reset_index()
        proc_ins['SUB_REF'] = proc_ins['REAL_REF']
        proc_ins['SUB_ALT'] = proc_ins['REAL_REF'] + proc_ins['SUB_ALT']
    else:
        proc_ins = pd.DataFrame(columns=df_trim.columns)

    # —— Deletion events (SUB_ALT == '.') handling
    delet = df_trim[df_trim['SUB_ALT'] == '.'].sort_values('P1')
    
    if not delet.empty:
        # Identify contiguous deletion regions
        deletion_groups = []
        current_group = [delet.iloc[0]]
        
        for i in range(1, len(delet)):
            # If current position is contiguous with previous, keep in same group
            if delet.iloc[i]['P1'] == current_group[-1]['P1'] + 1:
                current_group.append(delet.iloc[i])
            else:
                # Otherwise start a new group
                deletion_groups.append(current_group)
                current_group = [delet.iloc[i]]
        deletion_groups.append(current_group)
        
        # Process each deletion region
        proc_del_list = []
        for group in deletion_groups:
            # Take the first position as representative
            first_row = group[0].copy()
            
            if len(group) == 1:
                # Single-base deletion: keep SUB_REF as is, SUB_ALT as '.'
                # No change needed; keep original format
                pass
            else:
                # Multi-base deletion: concatenate all deleted bases
                deleted_seq = ''.join([row['SUB_REF'] for row in group])
                first_row['SUB_REF'] = deleted_seq
            
            # Convert to standard VCF: REF contains deleted bases, ALT keeps reference base
            first_row['SUB_REF'] = first_row['REAL_REF'] + first_row['SUB_REF']
            first_row['SUB_ALT'] = first_row['REAL_REF']
            proc_del_list.append(first_row)
        
        proc_del = pd.DataFrame(proc_del_list)
    else:
        proc_del = pd.DataFrame(columns=df_trim.columns)

    # —— Other events (SNP/substitution) kept as is
    other = df_trim[(df_trim['SUB_REF'] != '.') & (df_trim['SUB_ALT'] != '.')]

    # Combine three event types
    dataframes_to_concat = []
    if not other.empty:
        dataframes_to_concat.append(other)
    if not proc_ins.empty:
        dataframes_to_concat.append(proc_ins)
    if not proc_del.empty:
        dataframes_to_concat.append(proc_del)
    
    if dataframes_to_concat:
        final_data = pd.concat(dataframes_to_concat, ignore_index=True)
    else:
        # If there are no variant events, create empty DataFrame
        final_data = pd.DataFrame(columns=df_trim.columns)

    # Fill back original additional columns
    # First drop variant columns from original df_hp
    df_hp.drop(['SUB_REF','SUB_ALT','REF_TAG','QRY_TAG'], axis=1, inplace=True)
    # Then merge final_data with original df_hp to keep all original columns
    df_out = final_data.merge(df_hp, on='P1', how='left') \
                       .drop_duplicates(subset='P1') \
                       .sort_values(by='P1')

    # Save as CSV
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, file_name)
    df_out.to_csv(out_path, index=False, encoding='utf-8')
    print(f"Processing completed, output: {out_path}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 3_trim_csv.py <input_csv> <output_dir> <fasta_path>")
        sys.exit(1)
    process_csv(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()

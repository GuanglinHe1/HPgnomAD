#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(
        description="Transpose FST.txt, extract the first column (renamed to 'Fst'), and export as CSV."
    )
    parser.add_argument(
        "--base_dir",
        required=True,
        help="Directory containing FST.txt; the CSV will be written in the same folder."
    )
    args = parser.parse_args()
    base_dir = args.base_dir

    df_result = pd.read_csv(f'{base_dir}/FST.txt', sep='\t')
    df_result = df_result.T
    df_result = df_result.rename(columns={0: 'Fst'})
    df_result = df_result.reset_index()
    df_result = df_result.loc[:, ['Fst']]
    df_result.to_csv(f'{base_dir}/Processed_FST.csv', header=True, index_label='Location')

if __name__ == "__main__":
    main()

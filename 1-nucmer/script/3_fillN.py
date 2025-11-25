import os
import argparse
import pandas as pd

def process(sample_id, coords_file, reference_csv, final_csv_file, output_dir):
    coords = pd.read_csv(coords_file, usecols=['pos','aligned'])
    n_positions = coords.loc[coords['aligned']=='N','pos']

    ref = pd.read_csv(reference_csv, usecols=['pos','base'])
    ref_n = pd.merge(pd.DataFrame({'pos':n_positions}),
                     ref, on='pos', how='inner')

    orig = pd.read_csv(final_csv_file)
    cols = orig.columns

    df_n = pd.DataFrame('N', index=range(len(ref_n)), columns=cols)
    df_n['P1']      = ref_n['pos'].values
    df_n['SUB_REF'] = ref_n['base'].values
    df_n['SUB_ALT'] = 'N'

    df = pd.concat([orig, df_n], ignore_index=True)
    df['P1'] = pd.to_numeric(df['P1'], errors='coerce')
    df.sort_values(by='P1', inplace=True)
    mask = df['SUB_ALT']=='N'
    ref_tag = orig['REF_TAG'].iat[0]
    qry_tag = orig['QRY_TAG'].iat[0]

    df.loc[mask, 'REF_TAG']  = ref_tag
    df.loc[mask, 'QRY_TAG']  = qry_tag
    df.loc[mask, 'REAL_REF'] = df.loc[mask, 'SUB_REF']
    for c in ['P2','BUFF','DIST','LEN_R','LEN_Q','Ref_dir','Samp_dir']:
        df.loc[mask, c] = 1


    os.makedirs(output_dir, exist_ok=True)
    out_csv = os.path.join(output_dir, f"{sample_id}.csv")
    df.to_csv(out_csv, index=False, encoding='utf-8')
    print(f"[{sample_id}] -> {out_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Fill N and generate CSV for VCF conversion")
    parser.add_argument('--coords-file',    required=True,
                        help="*_vs_ref.coords.csv file")
    parser.add_argument('--reference-csv',  required=True,
                        help="Reference base CSV")
    parser.add_argument('--final-csv-dir',  required=True,
                        help="Directory containing original .csv files")
    parser.add_argument('--output-dir',     required=True,
                        help="Directory to output CSV")
    args = parser.parse_args()

    base = os.path.basename(args.coords_file)
    sample_id = base.replace('_vs_ref.coords.csv','')

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from aquarel import load_theme

def main():
    parser = argparse.ArgumentParser(
        description="Compute empirical quantiles for F_ST values and draw a histogram with 99th/99.5th percentiles and a threshold line."
    )
    parser.add_argument(
        "--input_csv", "-i",
        required=True,
        help="Processed FST CSV path (must contain a 'Fst' column), e.g., /path/Processed_FST.csv"
    )
    parser.add_argument(
        "--output_png", "-o",
        required=True,
        help="Destination PNG path, e.g., /path/FST_percentile_distribution.png"
    )

    args = parser.parse_args()
    input_csv = args.input_csv
    output_png = args.output_png

    # Load plotting theme
    theme = load_theme('arctic_light')
    theme.apply()
    plt.rcParams['font.family'] = 'Arial'
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42

    # 1. Read CSV (expecting columns 'Location' and 'Fst')
    df = pd.read_csv(input_csv, header=0, encoding='utf-8')
    if "Fst" not in df.columns:
        raise KeyError("Column 'Fst' is missing from the processed CSV. Check the file format.")

    # 2. Extract Fst values
    fst_vals = df["Fst"].values

    # 3. Total number of sites
    total_sites = len(fst_vals)

    # 4. Empirical percentiles
    p99  = np.percentile(fst_vals, 99)
    p995 = np.percentile(fst_vals, 99.5)

    # 5. Define threshold (99th percentile)
    threshold = p99

    # 6. Print summary
    print(
        f"Genome-wide total of {total_sites} sites. 99th percentile F_ST ≈ {p99:.2f} "
        f"(99.5th percentile ≈ {p995:.2f}). F_ST > {threshold:.2f} is considered highly differentiated."
    )

    # 7. Plot distribution
    plt.figure(figsize=(8, 5))
    plt.hist(fst_vals, bins=100, color='#71A48D', edgecolor='black', alpha=0.7)
    plt.xlabel("Fst value")
    plt.ylabel("Count")
    plt.title("Genome-wide Fst distribution (empirical quantiles)")

    plt.axvline(x=p99,  color='red',   linestyle='--', linewidth=1.5, label=f"99th percentile = {p99:.2f}")
    plt.axvline(x=p995, color='orange',linestyle='--', linewidth=1.5, label=f"99.5th percentile = {p995:.2f}")
    plt.axvline(x=threshold, color='blue', linestyle='-',  linewidth=1.5, label=f"Threshold = {threshold:.2f}")

    plt.legend(loc="upper right", fontsize=10)
    plt.tight_layout()

    plt.savefig(output_png, dpi=300)
    plt.close()

    print(f"Histogram saved to: {output_png}")

if __name__ == "__main__":
    main()

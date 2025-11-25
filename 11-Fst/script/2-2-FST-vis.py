#!/usr/bin/env python3
# Example:
# python 2-2-FST-vis.py \
#     --base_dir "${BASE_DIR}" \
#     --limitation 0.2 \
#     --gff_file "path/to/NC_000915.gff"

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from aquarel import load_theme

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "FST visualization and annotation workflow:\n"
            "1) Draw stacked scatter plots (bottom and top panels rasterized, axes and annotations remain vector).\n"
            "2) Annotate sites with Fst > limitation using CDS features from the GFF file.\n"
            "3) Export the annotated plot and a text file listing annotations."
        )
    )
    parser.add_argument(
        "--base_dir", "-b",
        required=True,
        help="Base directory containing Processed_FST.csv; outputs are written alongside it."
    )
    parser.add_argument(
        "--limitation", "-l",
        type=float,
        required=True,
        help="Fst cutoff between 0 and 1; points above this value are annotated and the split line uses the same threshold."
    )
    parser.add_argument(
        "--gff_file", "-g",
        required=True,
        help="Path to the NC_000915.gff file providing CDS coordinates and product annotations."
    )
    return parser.parse_args()

def read_cds_list(gff_path):
    """
    Extract CDS entries from the GFF file and return a list of tuples:
    [(start1, end1, product1), ...]
    """
    cds_list = []
    with open(gff_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            cols = line.strip().split("\t")
            # Expect at least 9 columns; the third column must be "CDS"
            if len(cols) >= 9 and cols[2] == "CDS":
                try:
                    start = int(cols[3])
                    end   = int(cols[4])
                except ValueError:
                    # Skip malformed entries
                    continue
                annotation_field = cols[8]
                # Parse annotation; assume the last field carries product info
                fields = annotation_field.split(";")
                last_field = fields[-1].strip()
                if last_field.startswith("product="):
                    product_info = last_field[len("product="):]
                else:
                    product_info = last_field
                cds_list.append((start, end, product_info))
    return cds_list

def annotate_sites(data_df, cds_list, threshold, ax_top, txt_output_path):
    """
    For rows with Fst > threshold:
    1) Annotate the top subplot if the site falls within a CDS range.
    2) Record annotation details into txt_output_path.
    """
    annotate_df = data_df[data_df["Fst"] > threshold].copy()
    results = []

    # Iterate through candidate sites
    for idx, row in annotate_df.iterrows():
        pos = int(row["Location"])
        fst_value = float(row["Fst"])
        # Check whether the position falls inside a CDS interval
        for (start, end, product_info) in cds_list:
            if start <= pos <= end:
                # Annotate figure using vector text with arrows
                ax_top.annotate(
                    product_info,
                    xy=(pos, fst_value),
                    xytext=(pos, min(fst_value + 0.03, 1.0)),
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.5),
                    fontsize=8
                )
                results.append(f"Position: {pos}, Fst: {fst_value:.4f}, CDS product: {product_info}")
                break

    # Write annotations to disk
    with open(txt_output_path, "w", encoding="utf-8") as out_fh:
        for line in results:
            out_fh.write(line + "\n")

    return len(results)

def main():
    args = parse_args()
    BASE_DIR = args.base_dir.rstrip("/")
    limitation = args.limitation
    gff_file = args.gff_file

    fst_csv_path = os.path.join(BASE_DIR, "Processed_FST.csv")
    if not os.path.exists(fst_csv_path):
        raise FileNotFoundError(f"Fst data file not found: {fst_csv_path}")
    if not os.path.exists(gff_file):
        raise FileNotFoundError(f"GFF file not found: {gff_file}")

    data = pd.read_csv(fst_csv_path, header=0, encoding="utf-8")
    if "Location" not in data.columns or "Fst" not in data.columns:
        raise KeyError(f"CSV file must contain 'Location' and 'Fst': {fst_csv_path}")

    theme = load_theme("arctic_light")
    theme.apply()
    plt.rcParams["font.family"]     = "Arial"
    plt.rcParams["pdf.fonttype"]    = 42
    plt.rcParams["ps.fonttype"]     = 42

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1,
        figsize=(12, 6),
        sharex=True,
        gridspec_kw={"height_ratios": [6, 1]}
    )
    plt.subplots_adjust(hspace=0)

    scatter_bottom = ax_bottom.scatter(
        data["Location"],
        data["Fst"],
        c="#71A48D",
        alpha=1,
        s=7,
        rasterized=True
    )
    ax_bottom.set_ylim(0, limitation)
    ax_bottom.get_yaxis().set_visible(False)
    ax_bottom.set_ylabel("Fst", fontsize=10)
    ax_bottom.grid(False)

    scatter_top = ax_top.scatter(
        data["Location"],
        data["Fst"],
        c="#AB5962",
        alpha=1,
        s=7,
        rasterized=True
    )
    ax_top.set_ylim(limitation, 1)
    ax_top.set_ylabel("Fst", fontsize=10)
    ax_top.grid(False)

    ax_top.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
    ax_top.spines["bottom"].set_visible(False)

    # Draw a bold line at the cutoff value
    ax_top.axhline(
        y=limitation,
        color="black",
        linewidth=4,
        alpha=1,
        linestyle="-"
    )

    ax_bottom.set_xlabel("Location (Position)", fontsize=10)
    ax_bottom.set_title("")
    ax_bottom.set_xlim(left=0, right=data["Location"].max() + 10000)
    ax_bottom.ticklabel_format(style="plain", axis="x")

    cds_list = read_cds_list(gff_file)
    txt_out = os.path.join(BASE_DIR, "FST_annotations.txt")
    n_hits = annotate_sites(data, cds_list, limitation, ax_top, txt_out)
    print(f"Annotated {n_hits} sites with Fst > {limitation}. Details saved to: {txt_out}")

    theme.apply_transforms()
    pdf_out = os.path.join(BASE_DIR, "FST_annotations.pdf")
    plt.savefig(pdf_out, dpi=500)
    plt.close(fig)
    print(f"Annotated PDF saved to: {pdf_out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage:
  python3 coords_to_csv.py <input_coords_tsv> <output_directory>

Traverse a single coords.tsv file, mark unaligned positions on the reference
genome based on alignment intervals, and output a same-named .csv file to the
specified directory, keeping only rows with aligned == 'N'.
"""

import os
import csv
import sys

def parse_coords(coords_path):
    """
    Parse show-coords -rclT output, extract all reference alignment intervals
    (s1, e1), and obtain reference sequence length LEN R from the first data row.
    """
    blocks = []
    ref_len = None
    with open(coords_path, 'r') as f:
        # Locate header line
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('[S1]'):
                header = line.split('\t')
                idx_s1   = header.index('[S1]')
                idx_e1   = header.index('[E1]')
                idx_lenr = header.index('[LEN R]')
                break
        else:
            raise RuntimeError("coords file missing [S1] header line")
        # Read subsequent data lines
        for line in f:
            line = line.strip()
            if not line or line.startswith('['):
                continue
            cols = line.split('\t')
            s1 = int(cols[idx_s1])
            e1 = int(cols[idx_e1])
            blocks.append((s1, e1))
            if ref_len is None:
                ref_len = int(cols[idx_lenr])
    if ref_len is None:
        raise RuntimeError("Unable to obtain reference sequence length from coords file")
    return blocks, ref_len

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 coords_to_csv.py <coords_tsv> <output_dir>")
        sys.exit(1)

    coords_tsv = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    # Parse coords
    blocks, ref_length = parse_coords(coords_tsv)

    # Mark unaligned positions (1-based)
    covered = [False] * (ref_length + 1)
    for s, e in blocks:
        start = max(1, s)
        end   = min(ref_length, e)
        for pos in range(start, end + 1):
            covered[pos] = True

    # Build output file path: same name, suffix .tsv -> .csv
    base = os.path.basename(coords_tsv)
    name = base.rsplit('.', 1)[0]  # strip .tsv
    out_path = os.path.join(output_dir, f"{name}.csv")

    # Write CSV, keeping only aligned == 'N'
    with open(out_path, 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(['pos', 'aligned'])
        for pos in range(1, ref_length + 1):
            if not covered[pos]:
                writer.writerow([pos, 'N'])

    print(f"Generated: {out_path}")

if __name__ == '__main__':
    main()

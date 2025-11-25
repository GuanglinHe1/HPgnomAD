#!/usr/bin/env bash

set -euo pipefail

# --- Modify these lines as needed ---
REF="../conf/GCF_014672775.1.fasta"
DATA_DIR="../data/fasta/" # Folder containing all fasta files to be aligned, each file is a sample, may contain multiple contigs
OUTDIR="../output/"
JOBS=16                      # Number of parallel jobs
# -----------------------------------

MUMMER_BIN="../../bin/" # Set the directory of MUMmer here
DELTA_DIR="$OUTDIR/Delta_files"
COORDS_DIR="$OUTDIR/Coords_files"
OTHER_DIR="$OUTDIR/Other_files"


mkdir -p "$DELTA_DIR" "$COORDS_DIR" "$OTHER_DIR"


################################################################
## Write the actual work as a function, to be exported for parallel to call
################################################################
process_fasta() {
    local query="$1"                     # Absolute path of fasta file
    local sample
    sample=$(basename "$query" .fasta)   # e.g. 3800
    local prefix="${sample}_vs_ref"

    echo "[Start]  $sample"

    # 1. NUCmer
    "$MUMMER_BIN/nucmer" --maxmatch \
        --prefix="$DELTA_DIR/$prefix" \
        "$REF" "$query"

    # 2. delta-filter
    "$MUMMER_BIN/delta-filter" -r -q \
        "$DELTA_DIR/${prefix}.delta" \
        >"$DELTA_DIR/${prefix}.cluster.delta"

    # 3. show-coords
    "$MUMMER_BIN/show-coords" -rclT \
        "$DELTA_DIR/${prefix}.cluster.delta" \
        >"$COORDS_DIR/${prefix}.coords.tsv"

    # 4. show-snps
    "$MUMMER_BIN/show-snps" -ClrT \
        "$DELTA_DIR/${prefix}.cluster.delta" \
        >"$OTHER_DIR/${prefix}.snps.tsv"

    echo "[Done]  $sample"
}


################################################################
## Export function and required environment variables for parallel to see in subprocesses
################################################################
export -f process_fasta
export REF MUMMER_BIN DELTA_DIR COORDS_DIR OTHER_DIR


echo "Processing *.fasta in parallel (jobs = $JOBS)..."

find "$DATA_DIR" -type f -name '*.fasta' | \
    parallel --bar -j "$JOBS" process_fasta {}

echo "All tasks completed!"
# python3 ../../test_mail.py "1-nucmer.sh job completion notification" "<p>1-nucmer.sh analysis is complete, please check the result directory.</p>"

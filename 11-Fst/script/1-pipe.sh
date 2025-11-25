#!/bin/bash
set -euo pipefail

# Resolve directories relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configure input/output locations
META_CSV="${SCRIPT_DIR}/conf/META.csv"
FASTA_DIR="${SCRIPT_DIR}/input/FASTA_DIR"
WORK_DIR="${SCRIPT_DIR}/work_dir"
ALIGNMENT_FILE="${WORK_DIR}/temp.aln"
OUTPUT_DIR="${SCRIPT_DIR}/output"
FST_TXT="${OUTPUT_DIR}/FST.txt"
PROCESSED_DIR="${OUTPUT_DIR}"
FST_PNG="${OUTPUT_DIR}/FST_percentile_distribution.png"

mkdir -p "$WORK_DIR" "$OUTPUT_DIR"

Rscript "${SCRIPT_DIR}/2-0-FST_BATCH.r" \
  "$META_CSV" \
  "$FASTA_DIR" \
  "$ALIGNMENT_FILE" \
  "$WORK_DIR" \
  "$FST_TXT"

python3 "${SCRIPT_DIR}/2-1-trans.py" \
  --base_dir "$PROCESSED_DIR"

python3 "${SCRIPT_DIR}/2-1-threshold.py" \
  --input_csv "${PROCESSED_DIR}/Processed_FST.csv" \
  --output_png "$FST_PNG"

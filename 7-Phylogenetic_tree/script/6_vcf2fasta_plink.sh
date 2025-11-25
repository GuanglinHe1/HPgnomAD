#!/bin/bash


# Exit on error: exit immediately if any command fails
set -euo pipefail

# ================== Configuration parameters ==================
VCF_PATH="./output/Archive/merge/merged_clean_filtered.N_removehot.vcf.gz"
OUT_PREFIX="./output/Archive/merge_fasta/merged_clean_filtered.N_removehot"
PYTHON_PATH="python3"
SCRIPT_PATH="./script/6_vcf2fasta_plink.py"
MAPPING_FILE="./data/quality_control_ID_Hap.tsv" # Optional parameter, see rename_fasta_ids function
THREADS=32

# ================== Function definitions ==================

function run_plink() {
    echo "[INFO] Processing VCF file with PLINK..."
    plink --vcf "$VCF_PATH" \
        --threads "$THREADS" \
        --recode \
        --double-id \
        --out "$OUT_PREFIX"
    echo "[INFO] PLINK processing completed!"
}

function ped_to_fasta() {
    local ped_file="${OUT_PREFIX}.ped"
    local fasta_file="${OUT_PREFIX}.fasta"

    echo "[INFO] Converting PED file to FASTA format..."
    awk '{
        printf(">%s\n", $1);
        seq = "";
        for (i = 7; i <= NF; i += 2) {
            seq = seq $i;
        }
        printf("%s\n", seq);
    }' "$ped_file" > "$fasta_file"
    echo "[INFO] PED successfully converted to FASTA!"
}

function rename_fasta_ids() {
    local input_fasta="${OUT_PREFIX}.fasta"
    local output_fasta="${OUT_PREFIX}_rename.fasta"

    echo "[INFO] Renaming FASTA sequence IDs using Python script..."
    "$PYTHON_PATH" "$SCRIPT_PATH" \
        --mapping "$MAPPING_FILE" \
        --input_fasta "$input_fasta" \
        --output_fasta "$output_fasta"
    echo "[INFO] FASTA sequence renaming completed!"
}

# ================== Main workflow execution ==================

run_plink
ped_to_fasta
# rename_fasta_ids
rm "$OUT_PREFIX".ped
rm "$OUT_PREFIX".map
rm "$OUT_PREFIX".log
rm "$OUT_PREFIX".nosex
echo "[DONE] All steps completed."

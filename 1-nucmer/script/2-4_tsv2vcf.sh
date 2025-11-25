# : '
# Script Name: 2-4_tsv2vcf.sh
#
# Function Overview:
# This script is used for batch processing of genome alignment and variant detection workflows, automating multiple steps from NUCmer alignment results to VCF file generation. Main steps include directory creation, TSV/CSV file processing, data trimming, coordinate conversion, missing value filling, and final VCF file generation. Supports multithreaded parallel processing for efficiency.
#
# Main Steps:
# 1. Set required paths (script directory, reference sequence, Python environment, working directory, etc.).
# 2. Create various output directories (Delta, VCF, CSV, Final CSV, Final CSV N, VCF output, Coords).
# 3. (Optional) Run NUCmer and show-snps in parallel for alignment and variant detection.
# 4. Run 2_tsv_df.py in parallel to convert TSV files to CSV.
# 5. Run 3_trim_csv.py in parallel to trim and standardize CSV files.
# 6. Run 3_coord_csv.py in parallel to process coordinate-related CSV files.
# 7. Run 3_fillN.py in parallel to fill missing (N) information and generate final CSV.
# 8. Run 4_vcf.py in parallel to convert final CSV files to VCF format.
# 9. Output processing progress and completion information.
#
# Usage:
# - Please modify the path variables at the beginning of the script as needed (e.g., reference sequence, Python environment, etc.).
# - Prepare the required Python scripts in advance (2_tsv_df.py, 3_trim_csv.py, 3_coord_csv.py, 3_fillN.py, 4_vcf.py).
# - Install GNU parallel and the required Python environment.
# - Adjust the number of parallel threads (-j parameter) according to server performance.
#
# Notes:
# - If the path contains Chinese characters or spaces, ensure the shell can recognize them correctly.
# - Some steps are commented out; enable or adjust as needed.
# - The reference sequence CSV file can be generated using ../src/fasta_to_csv.py.
#
# Author: LLT
# Date: 2025-07-03
# '
#!/bin/bash


# Set paths
# TODO: Please modify the following paths as needed
SCRIPT_DIR="../"
# TODO: Reference FASTA file path
REFERENCE="../conf/NC_000915.fasta"
# TODO: Reference CSV file path. If you do not have this CSV file, you can generate it using ../src/fasta_to_csv.py
REFERENCE_CSV="../conf/NC_000915.fasta"
# TODO: Python environment path
PYTHON_ENV="python3"
# TODO: Working directory
WORK_DIR="../output/"


NUCMER_DIR="$WORK_DIR/Delta_files" #! Do not modify this path
VCF_DIR="$WORK_DIR/Other_files" #! Do not modify this path
CSV_DIR="$WORK_DIR/CSV_files" #! Do not modify this path
FINAL_CSV_DIR="$WORK_DIR/Final_CSV_files" #! Do not modify this path
FINAL_CSV_N_DIR="$WORK_DIR/Final_CSV_N_files" #! Do not modify this path
VCF_OUTPUT_DIR="$WORK_DIR/VCF_files" #! Do not modify this path
COORDS_DIR="$WORK_DIR/Coords_files" #! Do not modify this path


# Create working directories
mkdir -p "$NUCMER_DIR"
mkdir -p "$VCF_DIR"
mkdir -p "$CSV_DIR"
mkdir -p "$FINAL_CSV_DIR"
mkdir -p "$VCF_OUTPUT_DIR"
mkdir -p "$FINAL_CSV_N_DIR"
mkdir -p "$COORDS_DIR"



# Step 1: Run nucmer and show-snps scripts in parallel
# If you have already parallelized this part, you can keep or adjust it
# The following is an example using parallel for nucmer and show-snps based on your previous script

# 2-nucmer run/

# Step 2: Run 2_tsv_df.py in parallel
echo "Start processing TSV files in parallel..."
find "$VCF_DIR" -type f -name '*.tsv' | parallel -j 8 \
  ${PYTHON_ENV} \
  "${SCRIPT_DIR}/3-AB/script/2_tsv_df.py" {} \
  "$CSV_DIR"

echo "TSV file processing completed!"

# Step 3: Run 3_trim_csv.py in parallel
echo "Start processing CSV files in parallel..."
find "$CSV_DIR" -type f -name '*.csv' | parallel  -j 8   ${PYTHON_ENV} \
    ${SCRIPT_DIR}/3-AB/script/3_trim_csv.py {} "$FINAL_CSV_DIR" "$REFERENCE"

echo "CSV file processing completed!"


# Step 4: Run 3_coord_csv.py in parallel
find "$COORDS_DIR" -type f -name '*.tsv' | parallel -j 16 ${PYTHON_ENV} \
    ${SCRIPT_DIR}/3-AB/script/3_coord_csv.py {} "$COORDS_DIR" 

# Step 5: Run 3_fillN.py in parallel
# Parallel call

find "$COORDS_DIR" -name '*_vs_ref.coords.csv' | \
  parallel --jobs 8 \
     ${PYTHON_ENV} ${SCRIPT_DIR}/3-AB/script/3_fillN.py \
      --coords-file {} \
      --reference-csv "$REFERENCE_CSV" \
      --final-csv-dir "$FINAL_CSV_DIR" \
      --output-dir "$FINAL_CSV_N_DIR"

# Step 6: Run 4_vcf.py in parallel
# If you want to keep non-variant sites, uncomment the 4_vcf.py section.
echo "Start processing Final CSV files in parallel..."
find "$FINAL_CSV_N_DIR" -type f -name '*.csv' | parallel -j 16 \
   ${PYTHON_ENV} \
  ${SCRIPT_DIR}/3-AB/script/4_vcf.py {} "$VCF_OUTPUT_DIR" "${REFERENCE_CSV}"

echo "Final CSV file processing completed!"
echo "All scripts completed!"
echo "In the vcf file, if ALT=N and GT=0/0, it means the site has no variant; if ALT=N and GT=1/1, it means the site is not covered."
echo "Subsequent merge scripts will fill non-variant sites as 0/0, and uncovered sites as:"
echo "ALT=N,GT=1/1"
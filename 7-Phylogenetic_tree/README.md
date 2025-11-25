# Phylogenetic Tree Pipeline

This directory contains scripts and resources for generating phylogenetic trees from VCF files using PLINK and related tools.

## Directory Structure

- `script/` : Contains all scripts for VCF to FASTA conversion, ID renaming, and workflow automation.
- `conf/`   : Configuration files (if any).

## Main Workflow

1. **VCF to PED Conversion**
   - Uses PLINK to convert VCF files to PED format.
   - Example script: `6_vcf2fasta_通过plink.sh`

2. **PED to FASTA Conversion**
   - Converts PED files to FASTA format using `awk`.

3. **FASTA ID Renaming (Optional)**
   - Uses a Python script to update sequence IDs in the FASTA file based on a mapping TSV file.

## Key Scripts

- `6_vcf2fasta_通过plink.sh`  : Main shell script to automate the conversion process.
- `6_vcf2fasta_通过plink.py`   : Python script for renaming FASTA sequence IDs.
- `6_vcf2fasta_通过plink_0toN.py` : Python script to replace '0' with 'N' in FASTA sequences.

## Usage

1. Edit the configuration variables in the shell script as needed (input/output paths, thread count, etc.).
2. Run the shell script:
   ```bash
   bash script/6_vcf2fasta_通过plink.sh
   ```
3. (Optional) Use the Python scripts for further FASTA processing.

## Requirements

- PLINK (installed and available in PATH)
- Python 3
- Biopython, pandas (for Python scripts)

## Notes

- All scripts are written in English and use relative paths for portability.
- For details on each script, see the comments within the script files.

#!/bin/bash
# -----------------------------------------------------------------------------
# Script purpose: remove ambiguous bases in VCF files to keep them Beagle-friendly
# Usage: ./0-clean_vcf.sh
# -----------------------------------------------------------------------------

set -euo pipefail

# Set up paths relative to the script directory
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
INPUT_DIR="${BASE_DIR}/EXAMPLE"
DATA_DIR="${BASE_DIR}/data"
OUTPUT_DIR="${BASE_DIR}/data/cleaned"

# Create the output directory
mkdir -p "${OUTPUT_DIR}"

echo "[$(date +'%F %T')] Starting ambiguous-base cleanup for VCF files..."

# Clean the target-sample VCF
echo "Cleaning the target-sample VCF..."
INPUT_VCF="${INPUT_DIR}/EXAMPLE.vcf.gz"
OUTPUT_VCF="${OUTPUT_DIR}/EXAMPLE.cleaned.vcf.gz"

# Use bcftools to drop any sites that contain ambiguous bases
# Only keep sites whose REF and ALT values contain A, C, T, G, N, or *
bcftools view -Oz \
  --include 'REF~"^[ACTGN*]+$" && ALT~"^[ACTGN*,]+$"' \
  "${INPUT_VCF}" > "${OUTPUT_VCF}"

# Build an index
bcftools index "${OUTPUT_VCF}"

# Clean each reference-panel VCF
for REF_FILE in "HP_panel.vcf.gz" "HP_panel.T2T.vcf.gz"; do
  if [[ -f "${DATA_DIR}/${REF_FILE}" ]]; then
    echo "Cleaning reference panel ${REF_FILE}..."
    OUTPUT_REF="${OUTPUT_DIR}/${REF_FILE%.vcf.gz}.cleaned.vcf.gz"
    
    bcftools view -Oz \
      --include 'REF~"^[ACTGN*]+$" && ALT~"^[ACTGN*,]+$"' \
      "${DATA_DIR}/${REF_FILE}" > "${OUTPUT_REF}"
    
    # Build an index
    bcftools index "${OUTPUT_REF}"
  fi
done

echo "[$(date +'%F %T')] VCF cleanup complete! Clean files saved to: ${OUTPUT_DIR}"
echo "Use the cleaned files for the downstream Beagle analysis."

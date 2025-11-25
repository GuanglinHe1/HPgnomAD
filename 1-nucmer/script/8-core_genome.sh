#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# -----------------------------------------------------------------------------
# Script Description:
# 1. Perform quality filtering on VCF files, including allele frequency and missing rate.
# 2. Use bcftools stats to calculate statistics for original and filtered files.
# Use case: SNP data preprocessing before population genetics analysis to ensure data quality.
# -----------------------------------------------------------------------------


# 1. Define paths (hard-coded variables)
BASE_DIR="../Archive"
INPUT_VCF="${BASE_DIR}/merged_clean.SNP.vcf.gz"
OUTPUT_VCF="${BASE_DIR}/merged_clean.SNP.maf01.mms99.WGS.vcf.gz"
STATS_ORIGINAL="${BASE_DIR}/merged_clean.SNP.stats.txt"
STATS_FILTERED="${BASE_DIR}/merged_clean.SNP.maf01.mms99.WGS.stats.txt"

# Define color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# Check whether bcftools is available
if ! command -v bcftools &> /dev/null; then
    log_error "bcftools not found, please install it first"
    exit 1
fi

# 2. Check input file
if [[ ! -f "${INPUT_VCF}" ]]; then
    log_error "Input file does not exist: ${INPUT_VCF}"
    exit 1
fi

log_info "Starting VCF quality filtering..."
log_info "Input file: ${INPUT_VCF}"
log_info "Output file: ${OUTPUT_VCF}"


# 4. Apply filtering: MAF ≥ 0.01, missing rate ≤ 1%
log_info "Applying filters (MAF ≥ 0.01, missing rate ≤ 1%)..."
bcftools view "${INPUT_VCF}" \
    --min-af 0.01 \
    -i 'F_MISSING<0.01' \
    -O z \
    --threads 32 \
    -o "${OUTPUT_VCF}"

# 5. Create index
log_info "Creating index file..."
bcftools index "${OUTPUT_VCF}"

# 6. Statistics
log_info "Collecting stats for original file..."
bcftools stats "${INPUT_VCF}" > "${STATS_ORIGINAL}"
log_info "Collecting stats for filtered file..."
bcftools stats "${OUTPUT_VCF}" > "${STATS_FILTERED}"

# 7. Print summary
log_info "Filtering completed! Summary:"
echo "----------------------------------------"
echo "Original SNP count: $(grep -E '^SN.*number of SNPs:' "${STATS_ORIGINAL}" | cut -f4)"
echo "Filtered SNP count: $(grep -E '^SN.*number of SNPs:' "${STATS_FILTERED}" | cut -f4)"
echo "----------------------------------------"

log_info "Output files:"
log_info "  - Filtered VCF: ${OUTPUT_VCF}"
log_info "  - Index file: ${OUTPUT_VCF}.csi"
log_info "  - Original stats: ${STATS_ORIGINAL}"
log_info "  - Filtered stats: ${STATS_FILTERED}"


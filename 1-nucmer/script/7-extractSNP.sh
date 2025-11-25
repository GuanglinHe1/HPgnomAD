#!/bin/bash

INPUT_FILE="../Archive/merged_clean.vcf.gz"
OUTPUTDIR="../Archive"
OUTSNP="${OUTPUTDIR}/merged_clean.SNP.vcf.gz"



# 1. Extract SNPs and output compressed VCF
bcftools view -v snps \
  -Oz \
  -o \
  ${OUTSNP} \
  ${INPUT_FILE}

# 2. Index the generated VCF (optional but recommended for fast querying)
bcftools index \
  ${OUTSNP}

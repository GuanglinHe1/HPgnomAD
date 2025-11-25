#!/bin/bash
# -----------------------------------------------------------------------------
# Script purpose: expand ambiguous bases into multi-allelic representation
#                 so their information is retained while staying Beagle-friendly
# Usage: ./0-convert_ambiguous.sh
# -----------------------------------------------------------------------------

set -euo pipefail

# Paths relative to the script location
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
INPUT_DIR="${BASE_DIR}/EXAMPLE"
DATA_DIR="${BASE_DIR}/data"
OUTPUT_DIR="${BASE_DIR}/data/converted"

mkdir -p "${OUTPUT_DIR}"

echo "[$(date +'%F %T')] Starting ambiguous-base conversion..."

# Create the helper conversion script
cat > "${OUTPUT_DIR}/convert_ambiguous.py" << 'EOF'
#!/usr/bin/env python3
"""
Convert ambiguous bases in a VCF file into multi-allelic entries.
For example: M (A or C) -> represented as A,C in the site.
"""

import sys
import gzip
import re

# Mapping from ambiguous bases to canonical bases
AMBIGUOUS_MAP = {
    'R': ['A', 'G'],  # puRine
    'Y': ['C', 'T'],  # pYrimidine  
    'S': ['C', 'G'],  # Strong
    'W': ['A', 'T'],  # Weak
    'K': ['G', 'T'],  # Keto
    'M': ['A', 'C'],  # aMino
    'B': ['C', 'G', 'T'],  # not A
    'D': ['A', 'G', 'T'],  # not C
    'H': ['A', 'C', 'T'],  # not G
    'V': ['A', 'C', 'G'],  # not T
    'N': ['A', 'C', 'G', 'T']  # aNy
}

def convert_ambiguous_line(line):
    """Convert ambiguous bases in a single VCF record"""
    if line.startswith('#'):
        return line
    
    fields = line.strip().split('\t')
    if len(fields) < 5:
        return line
    
    ref = fields[3]
    alt = fields[4]
    
    # Skip sites whose REF is ambiguous
    if ref in AMBIGUOUS_MAP:
        return None
    
    # Handle ambiguous bases in ALT
    alt_alleles = alt.split(',')
    new_alt_alleles = []
    
    for allele in alt_alleles:
        if allele in AMBIGUOUS_MAP:
            # Expand the ambiguous base into possible bases
            possible_bases = AMBIGUOUS_MAP[allele]
            # Only keep bases different from REF
            for base in possible_bases:
                if base != ref and base not in new_alt_alleles:
                    new_alt_alleles.append(base)
        else:
            # Keep non-ambiguous alleles as-is
            if allele not in new_alt_alleles:
                new_alt_alleles.append(allele)
    
    if new_alt_alleles:
        fields[4] = ','.join(new_alt_alleles)
        return '\t'.join(fields)
    else:
        # Skip the site if no valid ALT alleles remain
        return None

def convert_vcf(input_file, output_file):
    """Convert the entire VCF file"""
    open_func = gzip.open if input_file.endswith('.gz') else open
    
    with open_func(input_file, 'rt') as infile:
        with gzip.open(output_file, 'wt') if output_file.endswith('.gz') else open(output_file, 'w') as outfile:
            for line in infile:
                converted_line = convert_ambiguous_line(line)
                if converted_line is not None:
                    outfile.write(converted_line + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 convert_ambiguous.py input.vcf.gz output.vcf.gz")
        sys.exit(1)
    
    input_vcf = sys.argv[1]
    output_vcf = sys.argv[2]
    
    print(f"Converting {input_vcf} to {output_vcf}")
    convert_vcf(input_vcf, output_vcf)
    print("Conversion completed!")
EOF

chmod +x "${OUTPUT_DIR}/convert_ambiguous.py"

# Convert the target-sample VCF
echo "Converting the target-sample VCF..."
python3 "${OUTPUT_DIR}/convert_ambiguous.py" \
  "${INPUT_DIR}/EXAMPLE.vcf.gz" \
  "${OUTPUT_DIR}/EXAMPLE.converted.vcf.gz"

# Build an index
bcftools index "${OUTPUT_DIR}/EXAMPLE.converted.vcf.gz"

# Convert each reference-panel VCF
for REF_FILE in "HP_panel.vcf.gz" "HP_panel.T2T.vcf.gz"; do
  if [[ -f "${DATA_DIR}/${REF_FILE}" ]]; then
    echo "Converting reference panel ${REF_FILE}..."
    python3 "${OUTPUT_DIR}/convert_ambiguous.py" \
      "${DATA_DIR}/${REF_FILE}" \
      "${OUTPUT_DIR}/${REF_FILE%.vcf.gz}.converted.vcf.gz"
    
    bcftools index "${OUTPUT_DIR}/${REF_FILE%.vcf.gz}.converted.vcf.gz"
  fi
done

echo "[$(date +'%F %T')] Ambiguous-base conversion completed!"

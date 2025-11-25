#!/usr/bin/env python3
import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Generate Bugwas genotype input files by mapping 0/1/2/3 codes to A/T/C/G"
    )
    parser.add_argument(
        "input_file", 
        help="Path to the input file (for example: input/tmp2.txt)"
    )
    parser.add_argument(
        "--output_file", 
        help="Output file path. If omitted, a default is derived from the biallelic setting",
        default=None
    )
    # Keep only biallelic variants by default; use --no-biallelic to keep all variants
    parser.add_argument(
        "--no-biallelic", 
        dest="biallelic", 
        action="store_false", 
        help="Disable the biallelic filter and keep all variants"
    )
    parser.set_defaults(biallelic=True)

    args = parser.parse_args()
    input_file = args.input_file
    biallelic = args.biallelic

    # If no output file is given, derive one next to the input file based on the biallelic option
    if args.output_file:
        output_file = args.output_file
    else:
        base_dir = os.path.dirname(os.path.abspath(input_file))
        output_name = "geno_biallelic_SNP.txt" if biallelic else "geno_multiallelic_SNP.txt"
        output_file = os.path.join(base_dir, output_name)

    header = []          # Header info: first element is marker id column, second is sample names
    positions = []       # SNP identifiers
    genotype_data = []   # Converted genotype rows

    try:
        with open(input_file, 'r') as f:
            for line_number, line in enumerate(f, start=1):
                tokens = line.strip().split()
                if not tokens:
                    continue  # Skip empty rows

                # First row is header
                if line_number == 1:
                    if len(tokens) < 4:
                        raise ValueError("Header must contain at least 4 columns (marker, Ref, Alt, samples)")
                    header = [tokens[0], tokens[3:]]  # First column is marker, sample names start at column 4
                    continue

                # Data rows must contain at least 4 columns
                if len(tokens) < 4:
                    print(f"Warning: Skipped line {line_number} because it lacks enough columns")
                    continue

                pos_id = tokens[0]
                ref_allele = tokens[1]
                alt_alleles = tokens[2].split(",")
                genotypes = tokens[3:]

                # Skip if biallelic is required but the alternative allele count is not 1
                if biallelic and len(alt_alleles) != 1:
                    continue

                # Convert genotype codes to nucleotide bases
                try:
                    converted_genotypes = [
                        ref_allele if g == '0' else alt_alleles[int(g) - 1]
                        for g in genotypes
                    ]
                except (ValueError, IndexError) as e:
                    print(f"Error processing line {line_number}: {e}. Content: {tokens}")
                    continue

                positions.append(pos_id)
                genotype_data.append(converted_genotypes)
                # Progress message
                print(f"Processed line {line_number}")
    except Exception as e:
        print(f"Error reading input file {input_file}: {e}")
        sys.exit(1)

    try:
        with open(output_file, 'w') as f_out:
            # Write header
            f_out.write(header[0] + '\t' + '\t'.join(header[1]) + '\n')
            # Write each data row
            for pos, geno in zip(positions, genotype_data):
                f_out.write(pos + '\t' + '\t'.join(geno) + '\n')
    except Exception as e:
        print(f"Error writing output file {output_file}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

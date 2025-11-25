import os
import csv
import sys
import subprocess

def csv_to_vcf(input_csv, output_vcf, ref_genome_path):
    # Define valid bases, including 'N'
    valid_bases = {'A', 'T', 'C', 'G', 'N'}
    
    # Read reference genome information
    ref_genome = {}
    try:
        with open(ref_genome_path, mode='r', encoding='utf-8') as ref_file:
            reader = csv.reader(ref_file)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    pos = int(row[0])
                    base = row[1].upper().strip()
                    ref_genome[pos] = base
    except FileNotFoundError:
        print(f"Warning: reference genome file {ref_genome_path} not found")
        ref_genome = {}

    # Read CSV file, collect all data rows and unique TAG values
    data_rows = []
    unique_tags = set()
    existing_positions = set()  # 记录已存在的位点
    
    with open(input_csv, mode='r', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            data_rows.append(row)
            unique_tags.add(row['QRY_TAG'])
            existing_positions.add(int(row['P1']))
    
    # Sort sample names to ensure consistency
    sorted_tags = sorted(unique_tags)
    
    # VCF header (can be extended as needed)
    vcf_header = [
        "##fileformat=VCFv4.2",
        "##source=CSV_to_VCF_Script",
        "##FORMAT=<ID=GT,Number=1,Type=String,Description=\"Genotype\">",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
    ]
    
    # Add sample names to header
    if sorted_tags:
        sample_header = "\t".join(sorted_tags)
        vcf_header[-1] += "\t" + sample_header
    
    with open(output_vcf, mode='w', encoding='utf-8') as fout:
        # Write VCF header
        for line in vcf_header:
            fout.write(line + "\n")
        
        # Collect all position records to output
        all_vcf_lines = []
        
        # Process original CSV data row by row
        for row in data_rows:
            chrom = row["REF_TAG"]
            pos = int(row["P1"])
            var_id = "."
            ref_base = row["SUB_REF"].upper().strip()
            alt_base = row["SUB_ALT"].upper().strip()
            
            # If SUB_ALT is '.', set ALT to 'N'
            if alt_base == ".":
                alt_base = "N"
            
            qual = "."
            filter_flag = "PASS"
            
            # INFO field is empty
            info_str = "."
            
            # Build sample genotype fields
            genotype_dict = {tag: "0/0" for tag in sorted_tags}
            #? When ALT is strictly 'N', 0/0 could denote no variant and 1/1 uncovered;
            #? since the coord file distinguishes no variant and uncovered, we simplify here.
            if alt_base == "N":
                genotype_dict[row['QRY_TAG']] = "1/1"
            else:
                genotype_dict[row['QRY_TAG']] = "1/1"
            genotype_list = [genotype_dict[tag] for tag in sorted_tags]
            genotype_str = "\t".join(genotype_list)
            
            # Build a single VCF-formatted line
            vcf_line_data = {
                'pos': pos,
                'line': f"{chrom}\t{pos}\t{var_id}\t{ref_base}\t{alt_base}\t{qual}\t{filter_flag}\t{info_str}\tGT\t{genotype_str}\n"
            }
            all_vcf_lines.append(vcf_line_data)
        
        # Fill in missing reference genome positions
        if ref_genome and data_rows:
            chrom = data_rows[0]["REF_TAG"]  # Use chromosome name from the first row
            for pos, base in ref_genome.items():
                if pos not in existing_positions:
                    # Position missing in CSV, needs to be added
                    var_id = "."
                    ref_base = base
                    alt_base = "."
                    qual = "."
                    filter_flag = "PASS"
                    info_str = "."
                    
                    # All samples: genotype set to 0/0 (no variant)
                    genotype_dict = {tag: "0/0" for tag in sorted_tags}
                    genotype_list = [genotype_dict[tag] for tag in sorted_tags]
                    genotype_str = "\t".join(genotype_list)
                    
                    vcf_line_data = {
                        'pos': pos,
                        'line': f"{chrom}\t{pos}\t{var_id}\t{ref_base}\t{alt_base}\t{qual}\t{filter_flag}\t{info_str}\tGT\t{genotype_str}\n"
                    }
                    all_vcf_lines.append(vcf_line_data)
        
        # Sort by position and write to file
        all_vcf_lines.sort(key=lambda x: x['pos'])
        for vcf_data in all_vcf_lines:
            fout.write(vcf_data['line'])

def main():
    # Check command line arguments
    if len(sys.argv) != 4:
        print("Usage: python 4_vcf.py <input_csv_file> <output_vcf_dir> <ref_genome_csv>")
        print("Example: python 4_vcf.py input.csv output_dir/ /path/to/NC_000915.csv")
        sys.exit(1)
    
    # Input file, output directory, and reference genome path from CLI arguments
    input_csv = sys.argv[1]
    output_dir = sys.argv[2]
    ref_genome_path = sys.argv[3]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output VCF file path
    file_name = os.path.basename(input_csv)
    output_vcf = os.path.join(output_dir, file_name.replace('.csv', '.vcf'))
    
    # Convert CSV to VCF
    csv_to_vcf(input_csv, output_vcf, ref_genome_path)
    
    # Compress and index VCF file
    if os.path.isfile(output_vcf):
        try:
            subprocess.run(['bgzip', '-c', output_vcf], check=True, stdout=open(f"{output_vcf}.gz", 'wb'))
            subprocess.run(['tabix', '-p', 'vcf', f"{output_vcf}.gz"], check=True)
            # Delete uncompressed VCF (optional)
            os.remove(output_vcf)
            print(f"VCF processing completed. Output file: {output_vcf}.gz")
        except subprocess.CalledProcessError as e:
            print(f"Error compressing or indexing VCF: {e}")
    else:
        print(f"Failed to generate VCF file: {output_vcf}")

if __name__ == "__main__":
    main()

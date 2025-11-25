: '
Script Name: 5-2_merge.sh

Function Overview:
This script is used for batch merging multiple VCF files, and performs indexing and basic information statistics on the merged VCF file. It is mainly applicable to genome variant analysis workflows to integrate VCF results from multiple samples.

Main Steps:
1. Check if the input VCF file list exists and is non-empty.
2. Check if each VCF file in the list exists.
3. Count the number of VCF files to be merged.
4. Use bcftools merge command to merge all VCF files, output as compressed format (.vcf.gz).
5. Automatically create an index file (.csi) for the merged VCF file after successful merging.
6. Output basic information of the merged VCF file, including file size, number of variant sites, and number of samples.

Parameter Description:
- input_list: List file containing paths of VCF files to be merged, one VCF file path per line, supporting comments and empty lines.
- output_file: Path of the merged VCF compressed file.

Dependency Tools:
- bcftools (must support subcommands like merge, index, view, query, etc.)
- bash shell

Usage:
1. Edit the input_list file, ensuring each line is a valid VCF file path.
2. Modify output_file to the desired output path.
3. Run this script: bash 5-2_merge.sh

Notes:
- All VCF files to be merged must have a consistent format, and sample names cannot be repeated.
- The merging process requires large memory and CPU resources; it is recommended to run it in a high-performance computing environment.
- If merging or indexing fails, the script will output an error message and terminate.

Author: LLT
Date: 2025-07-03
'
#!/bin/bash

# Configuration paths
input_list='../conf/VCF2merge.list.txt'
output_file='../merged.vcf.gz'

# Check whether the input file exists
if [ ! -f "$input_list" ]; then
    echo "Error: Input file list does not exist: $input_list"
    exit 1
fi

# Check whether the input file is empty
if [ ! -s "$input_list" ]; then
    echo "Error: Input file list is empty: $input_list"
    exit 1
fi

# Create the output directory if missing
output_dir=$(dirname "$output_file")
mkdir -p "$output_dir"

# Verify that all VCF files in the list exist
echo "Checking whether VCF files exist..."
while IFS= read -r vcf_file; do
    # Skip empty lines and comments
    [[ -z "$vcf_file" || "$vcf_file" =~ ^[[:space:]]*# ]] && continue
    
    if [ ! -f "$vcf_file" ]; then
        echo "Error: VCF file does not exist: $vcf_file"
        exit 1
    fi
    echo "  ✓ $vcf_file"
done < "$input_list"

# Count the number of files to merge
vcf_count=$(grep -v '^[[:space:]]*$\|^[[:space:]]*#' "$input_list" | wc -l)
echo "Preparing to merge $vcf_count VCF files"

# Merge VCF files with bcftools
echo "Starting VCF merge..."
echo "Output file: $output_file"

# Merge command
bcftools merge \
    --file-list "$input_list" \
    --output-type z \
    --output "$output_file" \
    --threads 32

# Check whether merging succeeded
if [ $? -eq 0 ]; then
    echo "✓ VCF merge succeeded: $output_file"
    
    # Create index file
    echo "Creating index file..."
    bcftools index "$output_file" --threads 32
    
    if [ $? -eq 0 ]; then
        echo "✓ Index file created successfully"
    else
        echo "Warning: Index file creation failed"
    fi
    
    # Show basic information of the merged file
    echo "Merged file info:"
    echo "  File size: $(du -h "$output_file" | cut -f1)"
else
    echo "Error: VCF merge failed"
    exit 1
fi

echo "Merge completed!"

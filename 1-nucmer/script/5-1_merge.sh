#!/bin/bash
# ---------------------------------------------

# ------------------ Parameter Configuration ------------------
INPUT_DIR="../VCF_files"
OUTPUT_DIR="../Archive"
BATCH_SIZE=500         # Number of VCF files to merge per batch, can be adjusted according to server configuration and file size
THREADS=4             # Number of threads used by bcftools merge and index
PARALLEL_JOBS=8        # Number of concurrent merge tasks running simultaneously, adjusted according to server resources


# ------------------ Directory Check ------------------
cd "$INPUT_DIR" || { echo "Failed to enter directory $INPUT_DIR"; exit 1; }

# ------------------ Step 1: Collect All VCF Files ------------------
VCF_LIST="$OUTPUT_DIR/vcf_list.txt"
# Create directory to store batch files
BATCH_DIR="$OUTPUT_DIR/batch_files"
mkdir -p "$BATCH_DIR"
echo "Generating VCF file list to $VCF_LIST ..."
find "$INPUT_DIR" -type f -name "*.vcf.gz" | awk -F '/' '{print $NF"\t"$0}' | sort | uniq -f 0 -D | cut -f1 | sort | uniq > "$OUTPUT_DIR/dup.txt"
find "$INPUT_DIR" -type f -name "*.vcf.gz" | awk -F '/' '{print $NF"\t"$0}' | grep -v -F -f "$OUTPUT_DIR/dup.txt" | cut -f2 >"$OUTPUT_DIR/vcf_list.txt"

# ------------------ Step 2: Group Files by Batch and Merge with parallel ------------------
echo "Starting batch merging of VCF files..."



batch_counter=0
file_counter=0
current_batch_file="$BATCH_DIR/current_batch_list.txt"
> "$current_batch_file"  # Clear or create current batch file

while IFS= read -r vcf; do
    echo "$vcf" >> "$current_batch_file"
    ((file_counter++))

    # When the current batch reaches BATCH_SIZE, rename it as an independent batch file
    if [ "$file_counter" -eq "$BATCH_SIZE" ]; then
        ((batch_counter++))
        mv "$current_batch_file" "$BATCH_DIR/batch_${batch_counter}.txt"
        # Create a new current batch file
        > "$current_batch_file"
        file_counter=0
    fi
done < "$VCF_LIST"

# Save the remaining files as a batch if they do not make a full batch
if [ "$file_counter" -ne 0 ]; then
    ((batch_counter++))
    mv "$current_batch_file" "$BATCH_DIR/batch_${batch_counter}.txt"
else
    rm -f "$current_batch_file"
fi

# Define a function to merge a single batch
merge_batch() {
    batch_file="$1"
    # Extract batch number (assuming filename format batch_<number>.txt)
    batch_number=$(basename "$batch_file" | sed 's/[^0-9]*\([0-9]\+\).*/\1/')
    partial_merged="$OUTPUT_DIR/partial_${batch_number}.vcf.gz"

    echo "  -> Merging batch ${batch_number} VCFs (file list: $batch_file)..."
    bcftools merge --threads "$THREADS" --file-list "$batch_file" --missing-to-ref --force-samples -Oz -o "$partial_merged"
    if [ $? -ne 0 ]; then
        echo "  !! Batch ${batch_number} merge failed."
        exit 1
    fi

    # Index the partially merged file
    bcftools index --threads "$THREADS" "$partial_merged"
}

# Export necessary variables and functions so GNU parallel can access them
export -f merge_batch
export THREADS
export OUTPUT_DIR

# Use GNU parallel to process each batch file concurrently
parallel --jobs "$PARALLEL_JOBS" merge_batch ::: "$BATCH_DIR"/batch_*.txt
if [ $? -ne 0 ]; then
    echo "An error occurred during parallel merging."
    exit 1
fi

# Clean up batch directory
rm -rf "$BATCH_DIR"

# ------------------ Step 3: Merge All Partial Files ------------------
echo "Starting merge of all partial_*.vcf.gz..."
ls "$OUTPUT_DIR"/partial_*.vcf.gz > "$OUTPUT_DIR/partial_list.txt"
bcftools merge --force-samples \
    --missing-to-ref  \
    --threads "$THREADS" \
    --file-list "$OUTPUT_DIR/partial_list.txt" \
    -Oz -o "$OUTPUT_DIR/merged.vcf.gz"
if [ $? -ne 0 ]; then
    echo "Merging all partial files failed."
    exit 1
fi

# Index the final merged result
echo "Indexing the final merged VCF..."
bcftools index --threads "$THREADS" "$OUTPUT_DIR/merged.vcf.gz"
if [ $? -ne 0 ]; then
    echo "Index creation for merged VCF failed."
    exit 1
fi

echo "VCF files merged: $OUTPUT_DIR/merged.vcf.gz"

rm "$OUTPUT_DIR"/partial_*

echo "Partial VCF files removed"

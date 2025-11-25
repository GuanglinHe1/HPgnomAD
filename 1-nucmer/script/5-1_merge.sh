#!/bin/bash
# ---------------------------------------------

# ------------------ 参数设置 ------------------
INPUT_DIR="../VCF_files"
OUTPUT_DIR="../Archive"
BATCH_SIZE=500         # Number of VCF files to merge per batch, can be adjusted according to server configuration and file size
THREADS=4             # Number of threads used by bcftools merge and index
PARALLEL_JOBS=8        # Number of concurrent merge tasks running simultaneously, adjusted according to server resources


# ------------------ 目录检查 ------------------
cd "$INPUT_DIR" || { echo "Failed to enter directory $INPUT_DIR"; exit 1; }

# ------------------ 步骤1：收集所有VCF文件 ------------------
VCF_LIST="$OUTPUT_DIR/vcf_list.txt"
# Create directory to store batch files
BATCH_DIR="$OUTPUT_DIR/batch_files"
mkdir -p "$BATCH_DIR"
echo "Generating VCF file list to $VCF_LIST ..."
find "$INPUT_DIR" -type f -name "*.vcf.gz" | awk -F '/' '{print $NF"\t"$0}' | sort | uniq -f 0 -D | cut -f1 | sort | uniq > "$OUTPUT_DIR/dup.txt"
find "$INPUT_DIR" -type f -name "*.vcf.gz" | awk -F '/' '{print $NF"\t"$0}' | grep -v -F -f "$OUTPUT_DIR/dup.txt" | cut -f2 >"$OUTPUT_DIR/vcf_list.txt"

# ------------------ 步骤2：按批次分组文件，并使用parallel合并 ------------------
echo "开始分批次合并 VCF 文件..."



batch_counter=0
file_counter=0
current_batch_file="$BATCH_DIR/current_batch_list.txt"
> "$current_batch_file"  # 清空或新建当前批次文件

while IFS= read -r vcf; do
    echo "$vcf" >> "$current_batch_file"
    ((file_counter++))

    # 当当前批次文件数达到BATCH_SIZE时，重命名当前批次文件为独立批次文件
    if [ "$file_counter" -eq "$BATCH_SIZE" ]; then
        ((batch_counter++))
        mv "$current_batch_file" "$BATCH_DIR/batch_${batch_counter}.txt"
        # 重新建立一个新的当前批次文件
        > "$current_batch_file"
        file_counter=0
    fi
done < "$VCF_LIST"

# 如果最后剩余的文件不足一批，也保存为一个批次
if [ "$file_counter" -ne 0 ]; then
    ((batch_counter++))
    mv "$current_batch_file" "$BATCH_DIR/batch_${batch_counter}.txt"
else
    rm -f "$current_batch_file"
fi

# 定义一个函数用于合并单个批次
merge_batch() {
    batch_file="$1"
    # 提取批次编号（假定文件名格式为 batch_数字.txt）
    batch_number=$(basename "$batch_file" | sed 's/[^0-9]*\([0-9]\+\).*/\1/')
    partial_merged="$OUTPUT_DIR/partial_${batch_number}.vcf.gz"

    echo "  -> 合并第 ${batch_number} 批 VCF（使用文件列表：$batch_file）..."
    bcftools merge --threads "$THREADS" --file-list "$batch_file" --missing-to-ref --force-samples -Oz -o "$partial_merged"
    if [ $? -ne 0 ]; then
        echo "  !! 第 ${batch_number} 批合并失败。"
        exit 1
    fi

    # 对部分合并文件建立索引
    bcftools index --threads "$THREADS" "$partial_merged"
}

# 导出必要的变量和函数，保证 GNU parallel 可以访问
export -f merge_batch
export THREADS
export OUTPUT_DIR

# 使用 GNU parallel 并行处理每个批次文件
parallel --jobs "$PARALLEL_JOBS" merge_batch ::: "$BATCH_DIR"/batch_*.txt
if [ $? -ne 0 ]; then
    echo "并行合并过程中发生错误。"
    exit 1
fi

# 清理批次目录
rm -rf "$BATCH_DIR"

# ------------------ 步骤3：合并所有部分文件 ------------------
echo "开始合并所有 partial_*.vcf.gz..."
ls "$OUTPUT_DIR"/partial_*.vcf.gz > "$OUTPUT_DIR/partial_list.txt"
bcftools merge --force-samples \
    --missing-to-ref  \
    --threads "$THREADS" \
    --file-list "$OUTPUT_DIR/partial_list.txt" \
    -Oz -o "$OUTPUT_DIR/merged.vcf.gz"
if [ $? -ne 0 ]; then
    echo "所有部分文件合并失败。"
    exit 1
fi

# 为最终合并结果建立索引
echo "为最终合并的 VCF 建立索引..."
bcftools index --threads "$THREADS" "$OUTPUT_DIR/merged.vcf.gz"
if [ $? -ne 0 ]; then
    echo "合并后的VCF索引建立失败。"
    exit 1
fi

echo "VCF文件已合并完成：$OUTPUT_DIR/merged.vcf.gz"

rm "$OUTPUT_DIR"/partial_*

echo "已删除部分VCF文件"
#!/usr/bin/env python3
# python3 <path_to_test_mail.py>/test_mail.py "2-nucmer运行/3-AB/script/5-1_merge.sh Task Completion Notification" "<p>2-nucmer运行/3-AB/script/5-1_merge.sh analysis completed, please check the result directory.</p>"

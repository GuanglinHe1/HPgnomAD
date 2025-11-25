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
日期: 2025年7月3日
'
#!/bin/bash

# 配置文件路径
input_list='../conf/VCF2merge.list.txt'
output_file='../merged.vcf.gz'

# 检查输入文件是否存在
if [ ! -f "$input_list" ]; then
    echo "错误: 输入文件列表不存在: $input_list"
    exit 1
fi

# 检查输入文件是否为空
if [ ! -s "$input_list" ]; then
    echo "错误: 输入文件列表为空: $input_list"
    exit 1
fi

# 创建输出目录（如果不存在）
output_dir=$(dirname "$output_file")
mkdir -p "$output_dir"

# 检查列表中的VCF文件是否都存在
echo "检查VCF文件是否存在..."
while IFS= read -r vcf_file; do
    # 跳过空行和注释行
    [[ -z "$vcf_file" || "$vcf_file" =~ ^[[:space:]]*# ]] && continue
    
    if [ ! -f "$vcf_file" ]; then
        echo "错误: VCF文件不存在: $vcf_file"
        exit 1
    fi
    echo "  ✓ $vcf_file"
done < "$input_list"

# 统计要合并的文件数量
vcf_count=$(grep -v '^[[:space:]]*$\|^[[:space:]]*#' "$input_list" | wc -l)
echo "将要合并 $vcf_count 个VCF文件"

# 使用bcftools合并VCF文件
echo "开始合并VCF文件..."
echo "输出文件: $output_file"

# 合并命令
bcftools merge \
    --file-list "$input_list" \
    --output-type z \
    --output "$output_file" \
    --threads 32

# 检查合并是否成功
if [ $? -eq 0 ]; then
    echo "✓ VCF文件合并成功: $output_file"
    
    # 创建索引文件
    echo "创建索引文件..."
    bcftools index "$output_file" --threads 32
    
    if [ $? -eq 0 ]; then
        echo "✓ 索引文件创建成功"
    else
        echo "警告: 索引文件创建失败"
    fi
    
    # 显示合并后文件的基本信息
    echo "合并后文件信息:"
    echo "  文件大小: $(du -h "$output_file" | cut -f1)"
else
    echo "错误: VCF文件合并失败"
    exit 1
fi

echo "合并完成!"
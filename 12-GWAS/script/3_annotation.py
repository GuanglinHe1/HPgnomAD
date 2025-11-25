#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import numpy as np

def extract_product(attr_str):
    parts = attr_str.split("product=")
    return parts[1].split(";")[0] if len(parts) > 1 else None

def gwas_analysis(gwas_file, gff_file, output_dir, logp_threshold=5, dist_threshold=1000,
                  gwas_sep="\t", gff_sep="\t", gwas_header=0, gff_header=None):
    """
    读取 GWAS 和 GFF 文件，对数据进行处理并输出结果。
    
    :param gwas_file: GWAS结果文件路径
    :param gff_file:  GFF注释文件路径
    :param output_dir: 结果输出目录
    :param logp_threshold: 筛选显著SNP时使用的 -log10(p-value) 阈值
    :param dist_threshold: 判断相邻SNP是否紧邻时的距离阈值（单位：bp）
    :param gwas_sep: GWAS文件的分隔符
    :param gff_sep: GFF文件的分隔符
    :param gwas_header: GWAS文件的header参数
    :param gff_header: GFF文件的header参数（无表头时传入None）
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 1. 读入 GWAS 数据
    gwas_data = pd.read_csv(gwas_file, sep=gwas_sep, header=gwas_header)
    print("Columns in GWAS data:", gwas_data.columns.tolist())

    # 2. 处理 -log10(p-value) 信息
    if 'negLog10' in gwas_data.columns:
        gwas_data['logp'] = gwas_data['negLog10']
    elif 'pvalue' in gwas_data.columns:
        gwas_data['logp'] = -np.log10(gwas_data['pvalue'])
    else:
        raise ValueError("输入文件中既没有 'negLog10' 列也没有 'pvalue' 列，请检查输入文件。")

    # 3. 确认存在 SNP 位置的列 'ps'
    if 'ps' not in gwas_data.columns:
        raise ValueError("找不到 'ps' 列作为 SNP 的位置信息，请检查输入文件。")

    # 4. 筛选 -log10(p-value) 大于阈值且不为 Inf 的显著 SNP
    gwas_data.replace([np.inf, -np.inf], np.nan, inplace=True)
    sig = gwas_data.loc[(gwas_data['logp'] > logp_threshold) & (gwas_data['logp'].notna())].copy()

    # 5. 按 SNP 的位置排序，并计算相邻 SNP 之间的距离，筛选距离小于阈值的 SNP
    sig.sort_values('ps', inplace=True)
    sig.reset_index(drop=True, inplace=True)
    sig['delta'] = sig['ps'].diff().abs().fillna(0)
    sig = sig.loc[sig['delta'] < dist_threshold].drop(columns='delta')

    # 6. 读入 CDS 注释文件（GFF格式）
    gff_CDS = pd.read_csv(gff_file, sep=gff_sep, header=gff_header,
                            names=['seqid', 'source', 'type', 'start', 'end', 'score',
                                   'strand', 'phase', 'attributes'])

    # 7. 对于每个显著 SNP，根据其位置在 CDS 注释中进行匹配，并记录对应的 negLog10
    sig_CDS_list = []
    for idx, snp_row in sig.iterrows():
        pos = snp_row['ps']
        current_logp = snp_row['logp']  # 记录当前 SNP 的 negLog10 值
        matched = gff_CDS.loc[(gff_CDS['start'] < pos) & (gff_CDS['end'] > pos)]
        if not matched.empty:
            matched = matched.copy()
            matched['negLog10'] = current_logp
            sig_CDS_list.append(matched)
    if sig_CDS_list:
        # 合并所有匹配结果
        sigCDS_all = pd.concat(sig_CDS_list, ignore_index=True)
    else:
        sigCDS_all = pd.DataFrame(columns=list(gff_CDS.columns) + ['negLog10'])

    # 8. 从 CDS 的 attributes 字段中提取 product 信息
    sigCDS_all['product'] = sigCDS_all['attributes'].apply(extract_product)

    # 9. 如果同一 CDS（由 start, end, product 唯一确定）被多个 SNP匹配，则取最大的 negLog10
    sigCDS_grouped = sigCDS_all.groupby(['start', 'end', 'product'], as_index=False)['negLog10'].max()

    # 按 CDS 的起始位置排序，并输出 CDS 信息（包含 start, end, product, negLog10 四列）
    sigCDS_sorted = sigCDS_grouped.sort_values('start')
    cds_output_path = os.path.join(output_dir, "significantCDS.csv")
    sigCDS_sorted.to_csv(cds_output_path, index=False, header=False, sep=",")

    # 10. 输出显著 SNP 的详细信息
    snp_output_path = os.path.join(output_dir, "significantSNPs.txt")
    sig.to_csv(snp_output_path, sep='\t', index=False)

    print("分析完成！结果已输出至：", output_dir)

def main():
    parser = argparse.ArgumentParser(description="GWAS分析脚本，通过shell传入变量")
    parser.add_argument("--gwas_file", type=str, required=True, help="GWAS结果文件路径")
    parser.add_argument("--gff_file", type=str, required=True, help="CDS注释GFF文件路径")
    parser.add_argument("--output_dir", type=str, required=True, help="结果输出目录")
    parser.add_argument("--logp_threshold", type=float, default=5, help="-log10(p-value)筛选阈值，默认5")
    parser.add_argument("--dist_threshold", type=int, default=1000, help="相邻SNP距离阈值（bp），默认1000")
    parser.add_argument("--gwas_sep", type=str, default="\t", help="GWAS文件分隔符，默认制表符")
    parser.add_argument("--gff_sep", type=str, default="\t", help="GFF文件分隔符，默认制表符")
    parser.add_argument("--gwas_header", type=int, default=0, help="GWAS文件header行参数，默认0")
    parser.add_argument("--gff_header", type=str, default="None", help="GFF文件header参数，无表头传入 None 或不传入")
    args = parser.parse_args()

    # 处理 gff_header 参数，如果传入 "None" 则转换为 None
    gff_header = None if args.gff_header == "None" else int(args.gff_header)

    gwas_analysis(
        gwas_file=args.gwas_file,
        gff_file=args.gff_file,
        output_dir=args.output_dir,
        logp_threshold=args.logp_threshold,
        dist_threshold=args.dist_threshold,
        gwas_sep=args.gwas_sep,
        gff_sep=args.gff_sep,
        gwas_header=args.gwas_header,
        gff_header=gff_header
    )

if __name__ == "__main__":
    main()

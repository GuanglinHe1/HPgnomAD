import pysam
import os
import argparse

parser = argparse.ArgumentParser(description="清理VCF文件，删除ALT中的N等位基因")
parser.add_argument("input_vcf", help="输入VCF文件路径（可为bgzip压缩的.vcf.gz）")
parser.add_argument("output_vcf", help="输出VCF文件路径（将自动bgzip压缩）")
args = parser.parse_args()

input_vcf = args.input_vcf
output_vcf = args.output_vcf

in_vcf = pysam.VariantFile(input_vcf, "r")
out_vcf = pysam.VariantFile(output_vcf, "wz", header=in_vcf.header)

def build_index_map(alts):
    if alts is None:
        return [], {0: 0}
    n_pos = {i for i, a in enumerate(alts, start=1) if a.upper() == "N"}
    new_alts = [a for a in alts if a.upper() != "N"]

    index_map = {0: 0}
    new_i = 1
    for old_i in range(1, len(alts) + 1):
        if old_i in n_pos:
            index_map[old_i] = None
        else:
            index_map[old_i] = new_i
            new_i += 1
    return new_alts, index_map

def remap_gt(gt_tuple, index_map, set_missing_if_all_N=True):
    if gt_tuple is None:
        return None
    alleles = list(gt_tuple)
    if len(alleles) == 0:
        return gt_tuple

    all_n = True
    new_alleles = []
    for a in alleles:
        if a is None or a < 0:
            new_alleles.append(None)
            all_n = False
            continue
        mapped = index_map.get(a, a)
        if mapped is None:
            new_alleles.append(None)
        else:
            new_alleles.append(mapped)
            all_n = False

    if set_missing_if_all_N and all_n:
        return tuple(None for _ in new_alleles)
    return tuple(new_alleles)

for rec in in_vcf:
    original_alts = list(rec.alts) if rec.alts is not None else None
    new_alts, index_map = build_index_map(original_alts)

    if len(new_alts) == 0:
        continue

    for s in rec.samples:
        gt = rec.samples[s].get("GT")
        new_gt = remap_gt(gt, index_map, set_missing_if_all_N=True)
        rec.samples[s]["GT"] = new_gt

    rec.alts = tuple(new_alts)
    out_vcf.write(rec)

in_vcf.close()
out_vcf.close()

try:
    pysam.tabix_index(output_vcf, preset="vcf", force=True)
except Exception as e:
    print("Indexing note:", e)

print(f"Completed: {output_vcf}")

"""
用法:
  python3 coords_to_csv.py <input_coords_tsv> <output_directory>

遍历单个 coords.tsv 文件，根据对齐区间标记参考基因组未对齐位点，
输出同名 .csv 到指定目录，只保留 aligned == 'N' 的行。
"""

import os
import csv
import sys

def parse_coords(coords_path):
    """
    解析 show-coords -rclT 输出文件，提取所有参考序列对齐区间 (s1,e1)，
    并从首条数据行获取参考序列长度 LEN R。
    """
    blocks = []
    ref_len = None
    with open(coords_path, 'r') as f:
        # 定位表头行
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('[S1]'):
                header = line.split('\t')
                idx_s1   = header.index('[S1]')
                idx_e1   = header.index('[E1]')
                idx_lenr = header.index('[LEN R]')
                break
        else:
            raise RuntimeError("coords 文件缺少 [S1] 表头行")
        # 读取后续数据行
        for line in f:
            line = line.strip()
            if not line or line.startswith('['):
                continue
            cols = line.split('\t')
            s1 = int(cols[idx_s1])
            e1 = int(cols[idx_e1])
            blocks.append((s1, e1))
            if ref_len is None:
                ref_len = int(cols[idx_lenr])
    if ref_len is None:
        raise RuntimeError("无法从 coords 文件中获取参考序列长度")
    return blocks, ref_len

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 coords_to_csv.py <coords_tsv> <output_dir>")
        sys.exit(1)

    coords_tsv = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    blocks, ref_length = parse_coords(coords_tsv)

    covered = [False] * (ref_length + 1)
    for s, e in blocks:
        start = max(1, s)
        end   = min(ref_length, e)
        for pos in range(start, end + 1):
            covered[pos] = True

    base = os.path.basename(coords_tsv)
    out_path = os.path.join(output_dir, f"{name}.csv")

    with open(out_path, 'w', newline='') as fo:
        writer = csv.writer(fo)
        writer.writerow(['pos', 'aligned'])
        for pos in range(1, ref_length + 1):
            if not covered[pos]:
                writer.writerow([pos, 'N'])

    print(f"Generated: {out_path}")

if __name__ == '__main__':
    main()


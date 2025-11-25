#!/usr/bin/env bash
###############################################################################
# 脚本名称：query.sh
# 脚本说明：
#   本脚本用于进行幽门螺旋杆菌 VCF 数据的碱基统计与分群频率分析。
# 使用方式：
#   在项目根目录下：
#     source .venv/bin/activate
#     ./query.sh <site_pos> [out_dir]
#
# 依赖：
#   Python 环境（已激活的虚拟环境或 .venv）需安装 pandas、pysam、argparse 等。
#
###############################################################################
set -euo pipefail

# -----------------------------------------------------------------------
# 1. 项目目录与 Python 可执行文件检测
# -----------------------------------------------------------------------
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [[ -x "$BASE_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$BASE_DIR/.venv/bin/python"
else
  echo "Error: 找不到 Python，可先创建并激活虚拟环境，或确保 $BASE_DIR/.venv/bin/python 存在。" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# 2. 参数解析
# -----------------------------------------------------------------------
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <site_pos> [out_dir]" >&2
  exit 1
fi
SITE_POS="$1"
# 可选输出目录
if [[ $# -ge 2 ]]; then
  OUT_DIR="$2"
else
  OUT_DIR="$BASE_DIR/output"
fi
mkdir -p "$OUT_DIR"

# -----------------------------------------------------------------------
# 3. 子目录定义
# -----------------------------------------------------------------------
SCRIPT_DIR="$BASE_DIR/script"
DATA_DIR="$BASE_DIR/data"
CONF_DIR="$BASE_DIR/conf"

# -----------------------------------------------------------------------
# 4. 输入／输出文件
# -----------------------------------------------------------------------
VCF_FILE="$DATA_DIR/biallelic_snp_noinfo_fixed_core.vcf.gz"
META_FILE="$CONF_DIR/META_revised.csv"

ALLELE_TABLE="$OUT_DIR/allele_table.tsv"
OUT_CHROMO="$OUT_DIR/base_by_chromopainter4.tsv"
OUT_MAIN="$OUT_DIR/base_by_main_population.tsv"
OUT_COUNTRY="$OUT_DIR/base_by_chromopainter4_country.tsv"
OUT_CONTINENT="$OUT_DIR/base_by_main_population_continent.tsv"

# -----------------------------------------------------------------------
# 5. 执行分析步骤
# -----------------------------------------------------------------------
echo "[1/3] 查询位点 $SITE_POS 的碱基数量..."
"$PYTHON_BIN" "$SCRIPT_DIR/1-1-查询碱基数量.py" \
    --vcf "$VCF_FILE" --pos "$SITE_POS" > "$ALLELE_TABLE"

echo "[2/3] 计算分群频率..."
"$PYTHON_BIN" "$SCRIPT_DIR/1-2-各种分群频率计算.py" \
    --allele "$ALLELE_TABLE" --meta "$META_FILE" \
    --out_chromo "$OUT_CHROMO" --out_main "$OUT_MAIN"

echo "[3/3] 计算国家与大陆频率..."
"$PYTHON_BIN" "$SCRIPT_DIR/1-2-1-国家大陆频率计算.py" \
    --allele "$ALLELE_TABLE" --meta "$META_FILE" \
    --out_country "$OUT_COUNTRY" --out_continent "$OUT_CONTINENT"

echo "✅ 分析完成，结果保存在 $OUT_DIR 目录下。"

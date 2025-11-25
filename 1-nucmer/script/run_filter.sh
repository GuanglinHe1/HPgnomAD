#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: run_filter.sh <input VCF[.gz]> <output VCF.gz> [threads]" >&2
    exit 1
fi

INPUT=$1
OUTPUT=$2
THREADS=${3:-$(nproc)}

if [[ ! -f "$INPUT" ]]; then
    echo "Input file not found: $INPUT" >&2
    exit 1
fi

for tool in bgzip tabix; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing dependency: $tool" >&2
        exit 1
    fi
done

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
FILTER_BIN="$SCRIPT_DIR/N值处理"
if [[ ! -x "$FILTER_BIN" ]]; then
    echo "Executable not found: $FILTER_BIN, please compile N_value_processing.cpp first" >&2
    exit 1
fi

TMP_PARENT=${TMPDIR_OVERRIDE:-$(dirname "$OUTPUT")}
if [[ ! -d "$TMP_PARENT" ]]; then
    echo "Temporary directory does not exist: $TMP_PARENT" >&2
    exit 1
fi

if [[ "$INPUT" == *.gz ]]; then
    READ_CMD=(bgzip -dc -- "$INPUT")
else
    READ_CMD=(cat "$INPUT")
fi

TMP_OUT=$(mktemp -p "$TMP_PARENT" n_filter.XXXXXX.vcf.gz)
trap 'rm -f "$TMP_OUT" "$TMP_OUT.tbi"' EXIT

"${READ_CMD[@]}" | "$FILTER_BIN" -t "$THREADS" | bgzip -@ "$THREADS" -c >"$TMP_OUT"
tabix -f -p vcf "$TMP_OUT"
mv "$TMP_OUT" "$OUTPUT"
mv "$TMP_OUT.tbi" "$OUTPUT.tbi"

echo "Completed: $OUTPUT"

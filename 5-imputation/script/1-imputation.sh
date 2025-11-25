#!/bin/bash
# -----------------------------------------------------------------------------
# Script purpose: run Beagle for phasing & imputation of low-coverage samples
#                 and benchmark two reference panels (Large Panel and T2T Panel)
# Usage: save as run_impute.sh, grant execute permission (chmod +x run_impute.sh),
#        then run from the project root: ./run_impute.sh
# -----------------------------------------------------------------------------

set -euo pipefail
# -e: abort when any command returns non-zero
# -u: abort when referencing undefined variables
# -o pipefail: fail when any command in a pipeline fails

# -------------------------- Resource guardrails --------------------------
# Warn if available memory is under 1.5 GB
AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
if [ "${AVAILABLE_MEM}" -lt 1500 ]; then
    echo "Warning: only ${AVAILABLE_MEM}MB available memory (need at least 1.5 GB)"
    echo "Attempting to free up memory..."
    # Drop page cache
    sync
    echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || true
    sleep 2
fi

# Set a per-process memory limit (avoid OOM lockups)
ulimit -v 1800000  # 1.8 GB virtual memory cap

# Periodically monitor memory usage
monitor_memory() {
    while true; do
        MEM_USAGE=$(free | awk 'NR==2{printf "%.1f", $3/$2*100}')
        if (( $(echo "${MEM_USAGE} > 90" | bc -l) )); then
            echo "Warning: memory usage is ${MEM_USAGE}% — pausing for 5 seconds..."
            sleep 5
        fi
        sleep 10
    done
}

# Start monitoring in the background
monitor_memory &
MONITOR_PID=$!

# -------------------------- User-configurable parameters --------------------------
# Base directory relative to this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
# Input/output resources
INPUT_VCF="${BASE_DIR}/EXAMPLE/EXAMPLE.vcf.gz"
REF_DIR="${BASE_DIR}/data"
OUT_DIR="${BASE_DIR}/output/"
# Beagle JAR path
BEAGLE_JAR="${BASE_DIR}/func/beagle.27Feb25.75f.jar"

# Java heap upper bound (800 MB to leave headroom)
MEM="800m"
# Thread count (single-thread to avoid CPU contention)
THREADS=1
# Reference sequence/chromosome name
CHROM="NC_000915.1"
# Chunk size (keeps per-run loci manageable)
CHUNK_SIZE=1000
# Sliding window size (Beagle parameter to reduce memory usage)
WINDOW_SIZE=100

# ----------------------------------------------------------------------

# Create the output directory (-p avoids errors if it exists)
mkdir -p "${OUT_DIR}"

# Reference panels and their output suffixes
declare -A PANELS
PANELS=(
  ["HP_panel.vcf.gz"]="phased"
  ["HP_panel.T2T.vcf.gz"]="T2Tphased"
)

# Loop over each panel, run phasing/imputation, and assess results
for REF_FILE in "${!PANELS[@]}"; do
  SUFFIX=${PANELS[$REF_FILE]}
  REF_PATH="${REF_DIR}/${REF_FILE}" 
  OUT_PREFIX="${OUT_DIR}/HP_Imputated.${SUFFIX}"

  # Check system resources and let things settle
  echo "[$(date +'%F %T')] Checking system resource status..."
  free -h
  sleep 5  # allow the system to stabilize

  # -----------------------------------------------------------------------------
  # Step 1: run Beagle for phasing & imputation (optimized settings)
  # Tweaks:
  #   window=       sliding-window size to tame memory usage
  #   overlap=      window overlap for accuracy
  #   ne=           effective population size to lower complexity
  #   cluster=      similarity threshold to boost efficiency
  # -----------------------------------------------------------------------------
  echo "[$(date +'%F %T')] Running Beagle (low-resource mode) with panel ${REF_FILE}..."
  
  # Favor memory-friendly JVM GC options
  JAVA_OPTS="-Xmx${MEM} -XX:+UseG1GC -XX:G1HeapRegionSize=16m -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication"
  
  # Lower CPU priority to stay courteous to other workloads
  nice -n 10 java ${JAVA_OPTS} -jar "${BEAGLE_JAR}" \
    gt="${INPUT_VCF}" \
    ref="${REF_PATH}" \
    chrom="${CHROM}" \
    impute=true \
    gp=true \
    out="${OUT_PREFIX}" \
    nthreads="${THREADS}" \
    window="${WINDOW_SIZE}" \
    overlap=10 \
    ne=1000 \
    cluster=0.005
  
  # Provide breathing room for system resources
  echo "[$(date +'%F %T')] Task complete, waiting for resource cooldown..."
  sleep 10
  
  # Optional cache drop
  echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

done

# Stop memory-monitor process
kill ${MONITOR_PID} 2>/dev/null || true

echo "All runs completed! Outputs are under: ${OUT_DIR}"

# Final cleanup
echo "Cleaning up temporary files and cache..."
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
echo "Cleanup finished."

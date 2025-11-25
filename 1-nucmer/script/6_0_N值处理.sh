#!/usr/bin/env bash


PYTHON3="python3"
PY_PROCESS_N="./6_0_N值处理.py"
INPUT="<path_to_input_vcf>/merged.vcf.gz"
OUTPUT="<path_to_output_vcf>/merged_clean.vcf.gz"

${PYTHON3} \
    ${PY_PROCESS_N} \
    ${INPUT} \
    ${OUTPUT}

# python3 <path_to_test_mail.py>/test_mail.py "2-nucmer运行/3-AB/script/6_0_N值处理.sh Task Completion Notification" "<p>2-nucmer运行/3-AB/script/6_0_N值处理.sh analysis completed, please check the result directory.</p>"

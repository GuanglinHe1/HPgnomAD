#!/bin/bash

#? It is recommended to use the following version, especially for large-scale data processing; the C++ version usually performs better.
#? For details, read 2-nucmer运行/N值处理/README.md

# cd <relative_path_to_N_value_processing_directory>
cd ../N值处理/

./run_filter.sh \
    <path_to_input_vcf>/merged.vcf.gz \
    <path_to_output_vcf>/merged_clean_C++.vcf.gz \
    64

# python3 <path_to_test_mail.py>/test_mail.py "2-nucmer运行/3-AB/script/6_0_N值处理新版C++.sh Task Completion Notification" "<p>2-nucmer运行/3-AB/script/6_0_N值处理新版C++.sh analysis completed, please check the result directory.</p>"

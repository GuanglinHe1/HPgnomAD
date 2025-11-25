#!/bin/bash

#? It is recommended to use the following version, especially for large-scale data processing; the C++ version usually performs better.


# cd <relative_path_to_N_value_processing_directory>


./run_filter.sh \
    <path_to_input_vcf>/merged.vcf.gz \
    <path_to_output_vcf>/merged_clean_C++.vcf.gz \
    64

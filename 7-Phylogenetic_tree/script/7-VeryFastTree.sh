#!/bin/bash

#! install VeryFastTree
#! conda install VeryFastTree
#! conda install -c bioconda snp-sites 
#! conda install -c conda-forge seqmagick

seqmagick convert \
    --include-from-file List_to_bulid_tree.txt \
    All_WGS.fasta \
    List_to_bulid_tree.fasta

snp-sites -c -o List_to_bulid_tree_snp-sites.fasta \
    List_to_bulid_tree.fasta


VeryFastTree \
    -nt -gtr < List_to_bulid_tree_snp-sites.fasta \
    > WGS.tree
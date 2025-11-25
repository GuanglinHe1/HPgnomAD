#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UMAP dimensionality reduction script
---------------------------------------
This script does the following:
1. Read the first n principal components (PCs) per sample from a PLINK .eigenvec file.
2. Run UMAP on the selected PCs to reduce them to two dimensions.
3. Compute and print the variance and variance explained for the two dimensions (V1, V2).
4. Optionally save the results to CSV.

Example usage:
    python hpglobal_umap.py \
        --input /path/to/hpglobal_LD_PCA.eigenvec \
        --n_pcs 10 \
        --n_neighbors 10 \
        --min_dist 0.1 \
        --output result.csv
"""
# Input file sample, raw PLINK .eigenvec output without further edits:
# SAMPLE1 SAMPLE1 0.123456 0.234567 0.345678 ...
# SAMPLE2 SAMPLE2 0.234567 0.345678 0.456789 ...
# SAMPLE3 SAMPLE3 0.345678 0.456789 0.567890 ...

import argparse
import logging
import warnings

import numpy as np
import pandas as pd
from umap import UMAP


def parse_args():
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Namespaces containing file paths, principal component count, UMAP args, etc.
    """
    parser = argparse.ArgumentParser(
        description="Read principal components from a .eigenvec file and perform UMAP"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Input .eigenvec file path (PLINK output)"
    )
    parser.add_argument(
        "--n_pcs", "-k", type=int, default=10,
        help="Number of principal components to feed to UMAP (default 10)"
    )
    parser.add_argument(
        "--n_neighbors", type=int, default=10,
        help="UMAP n_neighbors parameter (default 10)"
    )
    parser.add_argument(
        "--min_dist", type=float, default=0.1,
        help="UMAP min_dist parameter (default 0.1)"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Optional CSV output path"
    )
    return parser.parse_args()


def read_eigenvec(path: str) -> pd.DataFrame:
    """
    Read a PLINK .eigenvec file and add column names.

    Parameters
    ----------
    path : str
        Path to the .eigenvec file.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ['FID', 'IID', 'PC1', 'PC2', …].
    """
    # First two columns are FID/IID, remaining columns are PCs
    df = pd.read_csv(path, delim_whitespace=True, header=None)
    n_pcs = df.shape[1] - 2
    cols = ['FID', 'IID'] + [f'PC{i}' for i in range(1, n_pcs + 1)]
    df.columns = cols
    logging.info(
        f"Loaded {path} with {df.shape[0]} samples and {n_pcs} principal components"
    )
    return df


def run_umap(
    X: np.ndarray,
    n_neighbors: int = 10,
    min_dist: float = 0.1,
    random_state: int = 42
) -> np.ndarray:
    """
    Run UMAP on matrix X and reduce to two dimensions.

    Parameters
    ----------
    X : numpy.ndarray
        Input matrix with shape (n_samples, n_features).
    n_neighbors : int
        UMAP n_neighbors parameter.
    min_dist : float
        UMAP min_dist parameter.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    numpy.ndarray
        Array of reduced coordinates with shape (n_samples, 2).
    """
    reducer = UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        metric='euclidean',
        init='spectral',
        random_state=random_state
    )
    embedding = reducer.fit_transform(X)
    logging.info("UMAP dimensionality reduction finished")
    return embedding


def compute_variance_explained(embedding: np.ndarray) -> tuple:
    """
    Compute the variance and variance explained for the two UMAP dimensions.

    Parameters
    ----------
    embedding : numpy.ndarray
        UMAP coordinates with shape (n_samples, 2).

    Returns
    -------
    tuple
        (v1_var, v2_var, ratio1, ratio2) where each variance explained value is a percentage.
    """
    v1_var = np.var(embedding[:, 0])
    v2_var = np.var(embedding[:, 1])
    tot = v1_var + v2_var
    ratio1 = v1_var / tot * 100
    ratio2 = v2_var / tot * 100
    logging.info(
        f"V1 variance={v1_var:.6f}, V2 variance={v2_var:.6f}, "
        f"variance explained V1={ratio1:.2f}%, V2={ratio2:.2f}%"
    )
    return v1_var, v2_var, ratio1, ratio2


def main():
    """
    Main entry point to read data, run UMAP, and print the results.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    # Ignore FutureWarning and UMAP UserWarning
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    args = parse_args()

    # Load data
    df = read_eigenvec(args.input)

    # Select the first k principal components
    pcs = [f'PC{i}' for i in range(1, args.n_pcs + 1)]
    X = df.loc[:, pcs].values

    # Run UMAP
    embedding = run_umap(
        X,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist
    )

    # Build the output DataFrame
    out_df = pd.DataFrame({
        'FID': df['FID'],
        'IID': df['IID'],
        'V1': embedding[:, 0],
        'V2': embedding[:, 1]
    })

    # Compute variance explained
    v1_var, v2_var, ratio1, ratio2 = compute_variance_explained(embedding)

    # Print results and optionally save
    print(out_df.to_string(index=False))
    print(f"\nV1 variance: {v1_var:.6f}, V2 variance: {v2_var:.6f}")
    print(f"Variance explained: V1: {ratio1:.2f}%, V2: {ratio2:.2f}%")

    if args.output:
        out_df.to_csv(args.output, index=False)
        logging.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()

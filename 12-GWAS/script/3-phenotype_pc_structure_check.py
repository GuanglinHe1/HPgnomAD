#!/usr/bin/env python
import os
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import statsmodels.api as sm

base_dir = os.getenv('GWAS_BASE_DIR', 'PATH_TO_PROJECT')
meta_path = os.path.join(base_dir, 'META/clinical_metadata.csv')
mat_path = os.path.join(base_dir, 'data/geno_binary_matrix.tsv')
lead_base = os.path.join(base_dir, 'data/lead_hits')
out_dir = os.path.join(base_dir, 'output/structure_check')
os.makedirs(out_dir, exist_ok=True)

score_traits = {'AtrophyScore', 'IMScore'}

meta = pd.read_csv(meta_path)

traits = [d for d in os.listdir(lead_base) if os.path.isdir(os.path.join(lead_base, d))]

# Load binary matrix and compute PCA
mat = pd.read_csv(mat_path, sep='\t')
if 'site' not in mat.columns:
    raise ValueError('geno_binary_matrix.tsv must contain site column')

mat = mat.set_index('site')
mat = mat.replace('NA', np.nan).astype(float)

# Mean-impute missing values by site
mat = mat.apply(lambda row: row.fillna(row.mean()), axis=1)

X = mat.T  # samples x sites

pca = PCA(n_components=10, svd_solver='randomized', random_state=1)
pcs = pca.fit_transform(X.values)

pc_cols = [f'PC{i+1}' for i in range(pcs.shape[1])]
pcs_df = pd.DataFrame(pcs, index=X.index, columns=pc_cols)
pcs_df = pcs_df.reset_index().rename(columns={'index': 'ID'})
pcs_df.to_csv(os.path.join(out_dir, 'pc_scores.csv'), index=False)

explained = pd.DataFrame({
    'PC': pc_cols,
    'explained_variance_ratio': pca.explained_variance_ratio_,
})
explained.to_csv(os.path.join(out_dir, 'pc_explained_variance.csv'), index=False)

# Merge with meta
merged = meta.merge(pcs_df, on='ID', how='inner')

results = []

for trait in traits:
    if trait not in merged.columns:
        continue

    y_raw = merged[trait]
    if trait in score_traits:
        y = y_raw.astype(float)
        model_type = 'OLS'
    else:
        y = y_raw.astype(float)
        # Ensure binary
        y = y.where(y.isin([0, 1]))
        model_type = 'Logit'

    df = merged[['ID'] + pc_cols].copy()
    df['y'] = y
    df = df.dropna(subset=['y'])

    if df['y'].nunique() < 2:
        continue

    X_model = sm.add_constant(df[pc_cols])

    try:
        if model_type == 'Logit':
            fit = sm.Logit(df['y'], X_model).fit(disp=0)
        else:
            fit = sm.OLS(df['y'], X_model).fit()
    except Exception:
        try:
            fit = sm.GLM(df['y'], X_model, family=sm.families.Binomial()).fit()
            model_type = 'GLM-Binomial'
        except Exception:
            continue

    for term in fit.params.index:
        if term == 'const':
            continue
        results.append({
            'Trait': trait,
            'term': term,
            'coef': fit.params[term],
            'p_value': fit.pvalues[term],
            'model_type': model_type,
            'N': int(df.shape[0]),
        })

res_df = pd.DataFrame(results)
res_df.to_csv(os.path.join(out_dir, 'phenotype_pc_results.csv'), index=False)

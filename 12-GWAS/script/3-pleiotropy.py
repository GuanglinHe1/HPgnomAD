#!/usr/bin/env python
import os
import math
import textwrap
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BASE_DIR = os.getenv('GWAS_BASE_DIR', 'PATH_TO_PROJECT')
META_PATH = os.path.join(BASE_DIR, 'META/clinical_metadata.csv')
GENO_PATH = os.path.join(BASE_DIR, 'data/geno_biallelic_SNP.txt')
GFF_PATH = os.path.join(BASE_DIR, 'conf/reference.gff')
LEAD_ALL_PATH = os.path.join(BASE_DIR, 'output/lead_hits_firth/all_traits_lead_hits_firth_adjusted.csv')
OUT_BASE = os.path.join(BASE_DIR, 'output/pleiotropy')

Q_THRESHOLD = 0.25
DROP_TRAITS = {'TRAIT_TETRACYCLINE'}
WINDOW_SIZE = 5000
Q_SIG = 0.10
Q_SUG = 0.20

TRAIT_LABELS = {
    'TRAIT_PEPTIC_ULCER': 'Peptic ulcer',
    'TRAIT_ATROPHY': 'Atrophy',
    'TRAIT_ATROPHY_SCORE': 'Atrophy score',
    'TRAIT_IM': 'Intestinal metaplasia',
    'TRAIT_IM_SCORE': 'IM score',
    'TRAIT_AMOX': 'Amoxicillin resistance',
    'TRAIT_TETRACYCLINE': 'Tetracycline resistance',
    'TRAIT_MTZ': 'Metronidazole resistance',
    'TRAIT_LEV': 'Levofloxacin resistance',
    'TRAIT_CLR': 'Clarithromycin resistance',
    'TRAIT_RIF': 'Rifampicin resistance'
}

plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42


def bh_adjust(pvals):
    pvals = np.asarray(pvals, dtype=float)
    out = np.full_like(pvals, np.nan, dtype=float)
    mask = ~np.isnan(pvals)
    n = int(mask.sum())
    if n == 0:
        return out
    p = pvals[mask]
    order = np.argsort(p)
    p_sorted = p[order]
    q_sorted = np.minimum.accumulate((p_sorted * n / np.arange(1, n + 1))[::-1])[::-1]
    q_sorted = np.minimum(q_sorted, 1.0)
    q = np.empty_like(p)
    q[order] = q_sorted
    out[mask] = q
    return out


def load_gff_genes(gff_path):
    genes = []
    with open(gff_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 9:
                continue
            try:
                start = int(parts[3])
                end = int(parts[4])
            except ValueError:
                continue
            attrs = parts[8]
            gene = None
            for item in attrs.split(';'):
                if '=' not in item:
                    continue
                key, val = item.split('=', 1)
                if key == 'gene' and val:
                    gene = val
                    break
            if gene is None:
                for item in attrs.split(';'):
                    if '=' not in item:
                        continue
                    key, val = item.split('=', 1)
                    if key in ('Name', 'locus_tag') and val:
                        gene = val
                        break
            if gene is None:
                continue
            genes.append((start, end, gene))
    return genes


def find_gene(pos, genes):
    for start, end, gene in genes:
        if start <= pos <= end:
            return gene
    return None


def make_group_id(pos, gene):
    if gene:
        return f'gene:{gene}'
    win_start = (pos // WINDOW_SIZE) * WINDOW_SIZE
    win_end = win_start + WINDOW_SIZE - 1
    return f'window:{win_start}-{win_end}'


def build_heatmap(df, trait_mapping, out_pdf, out_png):
    if df.empty:
        return
    df = df[df['Trait'].isin(trait_mapping.keys())].copy()
    if df.empty:
        return
    df['Trait'] = df['Trait'].map(trait_mapping)

    heatmap_data = df.pivot_table(
        index='Trait',
        columns='Location',
        values='p_value',
        aggfunc='min'
    )
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.index))
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)

    colors = ['#562054', '#602251', '#90465C', '#C9D4C3', '#6BA18A', '#45837A', '#013A38']
    cmap = LinearSegmentedColormap.from_list('custom_pvalue', colors, N=256)
    cmap.set_bad(color='lightgray')

    fig_w = max(8, heatmap_data.shape[1] * 0.25)
    fig, ax = plt.subplots(figsize=(fig_w, 3.5))
    masked = np.ma.masked_invalid(heatmap_data.values)
    x = np.arange(heatmap_data.shape[1] + 1)
    y = np.arange(heatmap_data.shape[0] + 1)
    mesh = ax.pcolormesh(x, y, masked, cmap=cmap, shading='auto')
    fig.colorbar(mesh, ax=ax, label='p-value')
    ax.set_xticks(np.arange(heatmap_data.shape[1]) + 0.5)
    ax.set_xticklabels(heatmap_data.columns, rotation=90, fontsize=6)
    ax.set_yticks(np.arange(heatmap_data.shape[0]) + 0.5)
    ax.set_yticklabels(heatmap_data.index, fontsize=8)
    ax.set_xlabel('Position')
    ax.set_ylabel('Clinical condition')
    ax.invert_yaxis()
    ax.set_title('P-values by SNP and clinical condition')
    fig.tight_layout()
    fig.savefig(out_pdf, bbox_inches='tight')
    fig.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.close(fig)


def main():
    os.makedirs(OUT_BASE, exist_ok=True)
    lead = pd.read_csv(LEAD_ALL_PATH)
    lead = lead[lead['q_value_all'] <= Q_THRESHOLD].copy()
    lead = lead[~lead['Trait'].isin(DROP_TRAITS)].copy()
    if lead.empty:
        raise SystemExit('No lead variants after filtering.')

    traits = sorted(lead['Trait'].unique().tolist())
    lead = lead.sort_values('q_value_all')
    lead_best = lead.groupby('Location', as_index=False).first()

    genes = load_gff_genes(GFF_PATH)
    lead_best['Gene'] = lead_best['Location'].apply(lambda x: find_gene(int(x), genes))
    lead_best['group_id'] = lead_best.apply(lambda r: make_group_id(int(r['Location']), r['Gene']), axis=1)
    clumped = lead_best.sort_values('q_value_all').groupby('group_id', as_index=False).first()

    lead_out = os.path.join(OUT_BASE, 'lead_variants.tsv')
    clumped[['Location', 'Gene', 'group_id', 'q_value_all', 'Trait']].to_csv(
        lead_out, sep='\t', index=False
    )

    traits_path = os.path.join(OUT_BASE, 'traits.txt')
    with open(traits_path, 'w', encoding='utf-8') as f:
        for t in traits:
            f.write(t + '\n')

    r_script_path = os.path.join(OUT_BASE, 'run_pleio_firth.R')
    r_script = textwrap.dedent("""
        suppressPackageStartupMessages({
          if (!requireNamespace('logistf', quietly = TRUE)) {
            install.packages('logistf', repos = 'https://cloud.r-project.org')
          }
          library(logistf)
        })

        args <- commandArgs(trailingOnly = TRUE)
        meta_path <- args[1]
        geno_path <- args[2]
        lead_path <- args[3]
        traits_path <- args[4]
        out_path <- args[5]

        meta <- read.csv(meta_path, stringsAsFactors = FALSE, check.names = FALSE)
        if (!'Gender' %in% names(meta) && 'Sex' %in% names(meta)) meta$Gender <- meta$Sex
        if ('Gender' %in% names(meta)) meta$Gender <- as.factor(meta$Gender)
        if ('Ethnicity' %in% names(meta)) meta$Ethnicity <- as.factor(meta$Ethnicity)
        if ('City' %in% names(meta)) meta$City <- as.factor(meta$City)

        disease_candidates <- c('DiseaseType', 'DiseaseSubtype', 'EndoscopicFindings', 'EndoscopicFindingsAlt')
        disease_col <- disease_candidates[disease_candidates %in% colnames(meta)]
        disease_col <- if (length(disease_col) > 0) disease_col[1] else NA_character_
        if (!is.na(disease_col)) {
          meta[[disease_col]] <- as.factor(meta[[disease_col]])
        }

        score_traits <- c('AtrophyScore', 'IMScore')

        lead <- read.delim(lead_path, stringsAsFactors = FALSE, check.names = FALSE)
        traits <- readLines(traits_path)

        geno <- read.table(geno_path, header = TRUE, sep = '\\t', stringsAsFactors = FALSE, check.names = FALSE)
        if (!'ps' %in% colnames(geno)) {
          stop('geno_biallelic_SNP.txt must contain ps column.')
        }
        geno$ps <- as.integer(geno$ps)

        results <- list()

        for (i in seq_len(nrow(lead))) {
          ps <- as.integer(lead$Location[i])
          gene <- lead$Gene[i]
          sub <- geno[geno$ps == ps, , drop = FALSE]
          if (nrow(sub) == 0) {
            next
          }
          row <- sub[1, , drop = FALSE]
          sample_ids <- colnames(row)[colnames(row) != 'ps']
          alleles <- as.character(unlist(row[1, sample_ids]))

          keep_idx <- !is.na(alleles) & alleles != ''
          alleles <- alleles[keep_idx]
          sample_ids <- sample_ids[keep_idx]

          uniq <- unique(alleles)
          if (length(uniq) != 2) {
            next
          }

          tab <- sort(table(alleles), decreasing = TRUE)
          major <- names(tab)[1]
          minor <- names(tab)[2]

          df <- data.frame(ID = sample_ids, allele = alleles, stringsAsFactors = FALSE)
          df <- merge(df, meta, by = 'ID', all.x = TRUE)
          df$geno_minor <- ifelse(df$allele == minor, 1, 0)

          for (trait in traits) {
            if (!trait %in% colnames(df)) {
              results[[length(results) + 1]] <- data.frame(
                Location = ps,
                Gene = gene,
                Trait = trait,
                Allele_major = major,
                Allele_minor = minor,
                N = NA_integer_,
                N_case = NA_integer_,
                N_control = NA_integer_,
                OR = NA_real_,
                CI_lower = NA_real_,
                CI_upper = NA_real_,
                p_value = NA_real_,
                converged = FALSE,
                stringsAsFactors = FALSE
              )
              next
            }
            df$pheno_raw <- df[[trait]]
            if (trait %in% score_traits) {
              df$pheno <- ifelse(df$pheno_raw > 0, 1, 0)
            } else {
              df$pheno <- df$pheno_raw
            }

            req_cols <- c('pheno', 'geno_minor', 'Age', 'Gender', 'Ethnicity', 'City')
            if (!is.na(disease_col) && disease_col != trait) {
              req_cols <- c(req_cols, disease_col)
            }
            req_cols <- req_cols[req_cols %in% names(df)]
            df_sub <- df[complete.cases(df[, req_cols, drop = FALSE]), , drop = FALSE]

            if (nrow(df_sub) < 10 || length(unique(df_sub$pheno)) < 2) {
              results[[length(results) + 1]] <- data.frame(
                Location = ps,
                Gene = gene,
                Trait = trait,
                Allele_major = major,
                Allele_minor = minor,
                N = nrow(df_sub),
                N_case = sum(df_sub$pheno == 1),
                N_control = sum(df_sub$pheno == 0),
                OR = NA_real_,
                CI_lower = NA_real_,
                CI_upper = NA_real_,
                p_value = NA_real_,
                converged = FALSE,
                stringsAsFactors = FALSE
              )
              next
            }

            covars <- c('Age', 'Gender', 'Ethnicity', 'City')
            if (!is.na(disease_col) && disease_col != trait) {
              covars <- c(covars, disease_col)
            }
            covars_keep <- c()
            for (cv in covars) {
              if (!cv %in% colnames(df_sub)) next
              if (length(unique(df_sub[[cv]])) > 1) {
                covars_keep <- c(covars_keep, cv)
              }
            }

            if (length(covars_keep) > 0) {
              terms <- c('geno_minor', covars_keep)
            } else {
              terms <- c('geno_minor')
            }
            safe_terms <- sapply(terms, function(x) {
              if (grepl('[^A-Za-z0-9_.]', x)) {
                paste0('`', x, '`')
              } else {
                x
              }
            })
            fmla <- as.formula(paste('pheno ~', paste(safe_terms, collapse = ' + ')))

            fit <- try(logistf(fmla, data = df_sub), silent = TRUE)
            if (inherits(fit, 'try-error')) {
              results[[length(results) + 1]] <- data.frame(
                Location = ps,
                Gene = gene,
                Trait = trait,
                Allele_major = major,
                Allele_minor = minor,
                N = nrow(df_sub),
                N_case = sum(df_sub$pheno == 1),
                N_control = sum(df_sub$pheno == 0),
                OR = NA_real_,
                CI_lower = NA_real_,
                CI_upper = NA_real_,
                p_value = NA_real_,
                converged = FALSE,
                stringsAsFactors = FALSE
              )
              next
            }

            beta <- fit$coefficients['geno_minor']
            pval <- fit$prob['geno_minor']
            ci <- try(confint(fit), silent = TRUE)
            if (inherits(ci, 'try-error')) {
              ci_low <- NA_real_
              ci_high <- NA_real_
            } else {
              ci_low <- ci['geno_minor', 'Lower 95%']
              ci_high <- ci['geno_minor', 'Upper 95%']
            }

            results[[length(results) + 1]] <- data.frame(
              Location = ps,
              Gene = gene,
              Trait = trait,
              Allele_major = major,
              Allele_minor = minor,
              N = nrow(df_sub),
              N_case = sum(df_sub$pheno == 1),
              N_control = sum(df_sub$pheno == 0),
              OR = exp(beta),
              CI_lower = exp(ci_low),
              CI_upper = exp(ci_high),
              p_value = pval,
              converged = TRUE,
              stringsAsFactors = FALSE
            )
          }
        }

        if (length(results) == 0) {
          write.csv(data.frame(), out_path, row.names = FALSE)
        } else {
          res_df <- do.call(rbind, results)
          write.csv(res_df, out_path, row.names = FALSE)
        }
    """).strip() + "\n"

    with open(r_script_path, 'w', encoding='utf-8') as f:
        f.write(r_script)

    out_csv = os.path.join(OUT_BASE, 'pleiotropy_results_raw.csv')
    subprocess.run(
        ['Rscript', r_script_path, META_PATH, GENO_PATH, lead_out, traits_path, out_csv],
        check=True,
        text=True
    )

    res = pd.read_csv(out_csv)
    if res.empty:
        raise SystemExit('No Firth results generated.')

    res['q_value_all'] = bh_adjust(res['p_value'].values)
    res['q_value_by_variant'] = np.nan
    for loc, idx in res.groupby('Location').groups.items():
        res.loc[idx, 'q_value_by_variant'] = bh_adjust(res.loc[idx, 'p_value'].values)

    res_out = os.path.join(OUT_BASE, 'pleiotropy_results.csv')
    res.to_csv(res_out, index=False)

    summary_rows = []
    for loc in res['Location'].unique():
        sub = res[res['Location'] == loc].copy()
        gene = sub['Gene'].iloc[0] if 'Gene' in sub.columns else None
        sub_valid = sub[~sub['p_value'].isna()].copy()
        sig_traits = sub_valid[sub_valid['q_value_all'] <= Q_SIG]['Trait'].tolist()
        sug_traits = sub_valid[sub_valid['q_value_all'] <= Q_SUG]['Trait'].tolist()
        if sub_valid.empty:
            best_row = None
        else:
            best_row = sub_valid.sort_values('q_value_all').iloc[0]

        directional = 'NA'
        nom = sub_valid[(sub_valid['p_value'] < 0.05) & (~sub_valid['OR'].isna())]
        if not nom.empty:
            all_pos = (nom['OR'] > 1).all()
            all_neg = (nom['OR'] < 1).all()
            if all_pos:
                directional = 'All OR>1'
            elif all_neg:
                directional = 'All OR<1'
            else:
                directional = 'Mixed'

        summary_rows.append({
            'Location': loc,
            'Gene': gene,
            'n_traits_q<=0.10': len(sig_traits),
            'traits_q<=0.10': ';'.join([TRAIT_LABELS.get(t, t) for t in sig_traits]),
            'n_traits_q<=0.20': len(sug_traits),
            'traits_q<=0.20': ';'.join([TRAIT_LABELS.get(t, t) for t in sug_traits]),
            'best_trait': TRAIT_LABELS.get(best_row['Trait'], best_row['Trait']) if best_row is not None else None,
            'best_OR': best_row['OR'] if best_row is not None else None,
            'best_CI_lower': best_row['CI_lower'] if best_row is not None else None,
            'best_CI_upper': best_row['CI_upper'] if best_row is not None else None,
            'best_p_value': best_row['p_value'] if best_row is not None else None,
            'best_q_value_all': best_row['q_value_all'] if best_row is not None else None,
            'direction_consistency': directional
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_out = os.path.join(OUT_BASE, 'pleiotropy_summary.csv')
    summary_df.to_csv(summary_out, index=False)

    heatmap_pdf = os.path.join(OUT_BASE, 'pleiotropy_heatmap.pdf')
    heatmap_png = os.path.join(OUT_BASE, 'pleiotropy_heatmap.png')
    build_heatmap(res, TRAIT_LABELS, heatmap_pdf, heatmap_png)

    print('Done. Outputs:', OUT_BASE)


if __name__ == '__main__':
    main()

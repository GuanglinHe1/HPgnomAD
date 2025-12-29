#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  if (!requireNamespace('logistf', quietly = TRUE)) {
    install.packages('logistf', repos = 'https://cloud.r-project.org')
  }
  library(logistf)
})

base_dir <- 'Version2'
meta_path <- file.path(base_dir, 'META/Clinical.csv')
geno_path <- file.path(base_dir, 'data/geno_biallelic_SNP.txt')
lead_base <- file.path(base_dir, 'data/lead_hits')
out_base <- file.path(base_dir, 'output/lead_hits_firth')

dir.create(out_base, recursive = TRUE, showWarnings = FALSE)

traits <- list.dirs(lead_base, full.names = FALSE, recursive = FALSE)
if (length(traits) == 0) {
  stop('No lead_hits directories found.')
}

meta <- read.csv(meta_path, stringsAsFactors = FALSE, check.names = FALSE)
meta$Gender <- as.factor(meta$Gender)
meta$Ethnicity <- as.factor(meta$Ethnicity)
meta$City <- as.factor(meta$City)

score_traits <- c('Atrophyscore', 'Intestinalmetaplasiascore')

message('Loading genotype matrix...')
geno <- read.table(geno_path, header = TRUE, sep = '\t', stringsAsFactors = FALSE, check.names = FALSE)
if (!'ps' %in% colnames(geno)) {
  stop('geno_biallelic_SNP.txt must contain ps column.')
}
geno$ps <- as.integer(geno$ps)

all_results <- list()

for (trait in traits) {
  lead_file <- file.path(lead_base, trait, 'GWAS和FST交集位点.csv')
  if (!file.exists(lead_file)) {
    warning('Missing lead hits file for trait: ', trait)
    next
  }

  lead <- read.csv(lead_file)
  if (!'Location' %in% colnames(lead)) {
    warning('Lead hits missing Location column for trait: ', trait)
    next
  }

  sites <- unique(as.integer(lead$Location))
  sub <- geno[geno$ps %in% sites, , drop = FALSE]
  if (nrow(sub) == 0) {
    warning('No matching genotype sites for trait: ', trait)
    next
  }

  trait_out_dir <- file.path(out_base, trait)
  dir.create(trait_out_dir, recursive = TRUE, showWarnings = FALSE)

  trait_results <- list()

  for (i in seq_len(nrow(sub))) {
    ps <- sub$ps[i]
    row <- sub[i, , drop = FALSE]
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

    if (!trait %in% colnames(df)) {
      warning('Trait column not found in meta: ', trait)
      next
    }

    df$pheno_raw <- df[[trait]]
    if (trait %in% score_traits) {
      df$pheno <- ifelse(df$pheno_raw > 0, 1, 0)
      pheno_note <- 'score>0 as case'
    } else {
      df$pheno <- df$pheno_raw
      pheno_note <- 'binary'
    }

    df <- df[df$allele %in% c(major, minor), ]
    df$geno_minor <- ifelse(df$allele == minor, 1, 0)

    df <- df[complete.cases(df[, c('pheno', 'geno_minor', 'Age', 'Gender', 'Ethnicity', 'City')]), ]

    if (nrow(df) < 10) {
      next
    }

    if (length(unique(df$pheno)) < 2) {
      next
    }

    covars <- c('Age', 'Gender', 'Ethnicity', 'City')
    covars_keep <- c()
    for (cv in covars) {
      if (!cv %in% colnames(df)) next
      if (is.factor(df[[cv]]) || is.character(df[[cv]])) {
        if (length(unique(df[[cv]])) > 1) covars_keep <- c(covars_keep, cv)
      } else {
        if (length(unique(df[[cv]])) > 1) covars_keep <- c(covars_keep, cv)
      }
    }

    if (length(covars_keep) > 0) {
      fmla <- as.formula(paste('pheno ~ geno_minor +', paste(covars_keep, collapse = ' + ')))
    } else {
      fmla <- pheno ~ geno_minor
    }

    fit <- try(logistf(fmla, data = df), silent = TRUE)
    if (inherits(fit, 'try-error')) {
      next
    }

    beta <- fit$coefficients['geno_minor']
    pval <- fit$prob['geno_minor']
    ci <- confint(fit)
    ci_low <- ci['geno_minor', 'Lower 95%']
    ci_high <- ci['geno_minor', 'Upper 95%']

    n_case <- sum(df$pheno == 1)
    n_ctrl <- sum(df$pheno == 0)

    trait_results[[length(trait_results) + 1]] <- data.frame(
      Trait = trait,
      Location = ps,
      Allele_major = major,
      Allele_minor = minor,
      N = nrow(df),
      N_case = n_case,
      N_control = n_ctrl,
      OR = exp(beta),
      CI_lower = exp(ci_low),
      CI_upper = exp(ci_high),
      p_value = pval,
      pheno_note = pheno_note,
      stringsAsFactors = FALSE
    )
  }

  if (length(trait_results) == 0) {
    warning('No results for trait: ', trait)
    next
  }

  trait_df <- do.call(rbind, trait_results)
  trait_df$q_value <- p.adjust(trait_df$p_value, method = 'BH')

  out_file <- file.path(trait_out_dir, 'lead_hits_firth_adjusted.csv')
  write.csv(trait_df, out_file, row.names = FALSE)

  all_results[[length(all_results) + 1]] <- trait_df
}

if (length(all_results) > 0) {
  all_df <- do.call(rbind, all_results)
  all_df$q_value_all <- p.adjust(all_df$p_value, method = 'BH')
  write.csv(all_df, file.path(out_base, 'all_traits_lead_hits_firth_adjusted.csv'), row.names = FALSE)
}

message('Done.')

#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  if (!requireNamespace('logistf', quietly = TRUE)) {
    install.packages('logistf', repos = 'https://cloud.r-project.org')
  }
  library(logistf)
})

base_dir <- Sys.getenv('GWAS_BASE_DIR', 'PATH_TO_PROJECT')
meta_path <- file.path(base_dir, 'META/clinical_metadata.csv')
geno_path <- file.path(base_dir, 'data/geno_biallelic_SNP.txt')
lead_all_path <- file.path(base_dir, 'output/lead_hits_firth/all_traits_lead_hits_firth_adjusted.csv')
lead_path <- file.path(base_dir, 'output/pleiotropy/lead_variants.tsv')
pc_path <- file.path(base_dir, 'output/structure_check/pc_scores.csv')
out_base <- file.path(base_dir, 'output/interaction_analysis')

dir.create(out_base, recursive = TRUE, showWarnings = FALSE)

bh_adjust <- function(pvals) {
  out <- rep(NA_real_, length(pvals))
  ok <- !is.na(pvals)
  if (any(ok)) {
    out[ok] <- p.adjust(pvals[ok], method = 'BH')
  }
  out
}

meta <- read.csv(meta_path, stringsAsFactors = FALSE, check.names = FALSE)

if ('City' %in% names(meta)) {
  city_raw <- meta$City
} else if ('Isolation_area' %in% names(meta)) {
  city_raw <- meta$Isolation_area
} else {
  stop('No City or Isolation_area column found for altitude definition.')
}

site_a <- Sys.getenv('SITE_A_LABEL', 'SITE_A')
site_b <- Sys.getenv('SITE_B_LABEL', 'SITE_B')
altitude_bin <- ifelse(grepl(site_a, city_raw, ignore.case = TRUE), 1,
                       ifelse(grepl(site_b, city_raw, ignore.case = TRUE), 0, NA))
meta$altitude <- altitude_bin

if (all(is.na(meta$altitude))) {
  stop('Altitude mapping failed: no site labels found.')
}

if ('Gender' %in% names(meta)) meta$Gender <- as.factor(meta$Gender)
if ('Ethnicity' %in% names(meta)) meta$Ethnicity <- as.factor(meta$Ethnicity)
if ('City' %in% names(meta)) meta$City <- as.factor(meta$City)

disease_candidates <- c('DiseaseType', 'DiseaseSubtype', 'EndoscopicFindings', 'EndoscopicFindingsAlt')
disease_col <- disease_candidates[disease_candidates %in% colnames(meta)]
disease_col <- if (length(disease_col) > 0) disease_col[1] else NA_character_
if (!is.na(disease_col)) {
  meta[[disease_col]] <- as.factor(meta[[disease_col]])
}

pc_cols <- character(0)
if (file.exists(pc_path)) {
  pcs <- read.csv(pc_path, stringsAsFactors = FALSE, check.names = FALSE)
  pc_cols <- intersect(paste0('PC', 1:10), names(pcs))
  meta <- merge(meta, pcs, by = 'ID', all.x = TRUE)
}

lead_all <- read.csv(lead_all_path, stringsAsFactors = FALSE, check.names = FALSE)
lead_all <- lead_all[lead_all[['q_value_all']] <= 0.25, , drop = FALSE]
lead_all <- lead_all[!lead_all[['Trait']] %in% c('TRAIT_TETRACYCLINE'), , drop = FALSE]
traits <- sort(unique(lead_all[['Trait']]))

if (!file.exists(lead_path)) {
  stop('Missing lead_variants.tsv. Please run pleiotropy pipeline first.')
}
lead <- read.delim(lead_path, stringsAsFactors = FALSE, check.names = FALSE)
if (!'Location' %in% names(lead)) {
  stop('lead_variants.tsv must contain Location column.')
}

sites <- unique(as.integer(lead[['Location']]))
lead_map <- lead[, c('Location', 'Gene'), drop = FALSE]

score_traits <- c('AtrophyScore', 'IMScore')

message('Loading genotype matrix...')
geno <- read.table(geno_path, header = TRUE, sep = '\t', stringsAsFactors = FALSE, check.names = FALSE)
if (!'ps' %in% colnames(geno)) {
  stop('geno_biallelic_SNP.txt must contain ps column.')
}
geno$ps <- as.integer(geno$ps)
geno <- geno[geno$ps %in% sites, , drop = FALSE]

if (nrow(geno) == 0) {
  stop('No matching variants found in geno_biallelic_SNP.txt for lead set.')
}

run_interaction <- function(label) {
  out_dir <- file.path(out_base, label)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  results <- list()
  variant_filters <- list()
  first_error <- NULL
  run_stats <- data.frame(
    label = label,
    variants_total = nrow(geno),
    variants_pass_mac = 0,
    tests_trait_present = 0,
    tests_pass_filter = 0,
    tests_fit_success = 0,
    stringsAsFactors = FALSE
  )

  for (i in seq_len(nrow(geno))) {
    ps <- geno$ps[i]
    row <- geno[i, , drop = FALSE]

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
    df$geno_minor <- ifelse(df$allele == minor, 1, 0)
    df <- merge(df, meta, by = 'ID', all.x = TRUE)

    mac_total <- sum(df$geno_minor, na.rm = TRUE)
    mac_low <- sum(df$geno_minor[df$altitude == 0], na.rm = TRUE)
    mac_high <- sum(df$geno_minor[df$altitude == 1], na.rm = TRUE)

    pass_mac <- !is.na(mac_total) && mac_total >= 10 && mac_low >= 5 && mac_high >= 5
    variant_filters[[length(variant_filters) + 1]] <- data.frame(
      Location = ps,
      Allele_major = major,
      Allele_minor = minor,
      MAC_total = mac_total,
      MAC_low = mac_low,
      MAC_high = mac_high,
      pass_mac = pass_mac,
      stringsAsFactors = FALSE
    )

    if (!pass_mac) {
      next
    }
    run_stats$variants_pass_mac <- run_stats$variants_pass_mac + 1

    for (trait in traits) {
      if (!trait %in% colnames(df)) {
        next
      }
      run_stats$tests_trait_present <- run_stats$tests_trait_present + 1

      df$pheno_raw <- df[[trait]]
      if (trait %in% score_traits) {
        df$pheno <- ifelse(as.numeric(df$pheno_raw) > 0, 1, 0)
        pheno_note <- 'score>0 as case'
      } else {
        df$pheno <- df$pheno_raw
        pheno_note <- 'binary'
      }

      if (!all(df$pheno %in% c(0, 1, NA))) {
        df$pheno <- ifelse(df$pheno %in% c(0, 1), df$pheno, NA)
      }

      covars <- c('Age', 'Gender', 'Ethnicity')
      if (!is.na(disease_col) && disease_col != trait) {
        covars <- c(covars, disease_col)
      }
      if (length(pc_cols) > 0) {
        covars <- c(covars, pc_cols)
      }

      covars_keep <- c()
      for (cv in covars) {
        if (!cv %in% names(df)) next
        vals <- df[[cv]]
        vals <- vals[!is.na(vals)]
        if (length(unique(vals)) > 1) {
          covars_keep <- c(covars_keep, cv)
        }
      }

      req_cols <- unique(c('pheno', 'geno_minor', 'altitude', covars_keep))
      sub <- df[req_cols]
      sub <- sub[complete.cases(sub), , drop = FALSE]

      if (nrow(sub) < 10) {
        next
      }

      n_case <- sum(sub$pheno == 1)
      n_ctrl <- sum(sub$pheno == 0)
      if (n_case < 10) {
        next
      }
      if (length(unique(sub$pheno)) < 2) {
        next
      }
      run_stats$tests_pass_filter <- run_stats$tests_pass_filter + 1

      covars_keep <- c()
      for (cv in covars) {
        if (!cv %in% names(sub)) next
        if (length(unique(sub[[cv]])) > 1) {
          covars_keep <- c(covars_keep, cv)
        }
      }

      quote_name <- function(x) {
        if (make.names(x) != x) {
          paste0('`', x, '`')
        } else {
          x
        }
      }
      covars_formula <- vapply(covars_keep, quote_name, character(1))
      rhs_full <- c('geno_minor', 'altitude', 'geno_minor:altitude', covars_formula)
      rhs_red <- c('geno_minor', 'altitude', covars_formula)
      f_full <- as.formula(paste('pheno ~', paste(rhs_full, collapse = ' + ')))
      f_red <- as.formula(paste('pheno ~', paste(rhs_red, collapse = ' + ')))

      fit_full <- try(logistf(f_full, data = sub), silent = TRUE)
      if (inherits(fit_full, 'try-error')) {
        if (is.null(first_error)) {
          first_error <- as.character(fit_full)
        }
        next
      }
      fit_red <- try(logistf(f_red, data = sub), silent = TRUE)
      if (inherits(fit_red, 'try-error')) {
        if (is.null(first_error)) {
          first_error <- as.character(fit_red)
        }
        next
      }
      run_stats$tests_fit_success <- run_stats$tests_fit_success + 1

      term_int <- names(fit_full$coefficients)[grepl('geno_minor:altitude|altitude:geno_minor', names(fit_full$coefficients))]
      if (length(term_int) == 0) {
        next
      }
      term_int <- term_int[1]

      beta_g <- fit_full$coefficients['geno_minor']
      beta_int <- fit_full$coefficients[term_int]
      or_int <- exp(beta_int)
      ci_low <- fit_full$ci.lower[term_int]
      ci_high <- fit_full$ci.upper[term_int]

      or_low <- exp(beta_g)
      or_high <- exp(beta_g + beta_int)

      ll_full <- fit_full$loglik['full']
      ll_red <- fit_red$loglik['full']
      lrt_stat <- 2 * (ll_full - ll_red)
      if (is.na(lrt_stat) || lrt_stat < 0) {
        p_int <- NA_real_
      } else {
        p_int <- pchisq(lrt_stat, df = 1, lower.tail = FALSE)
      }

      p_wald <- fit_full$prob[term_int]

      sub_low <- sub[sub$altitude == 0, , drop = FALSE]
      sub_high <- sub[sub$altitude == 1, , drop = FALSE]

      strat_fit <- function(dat) {
        if (nrow(dat) < 10) {
          return(list(or = NA_real_, ci_low = NA_real_, ci_high = NA_real_, p = NA_real_, n = nrow(dat)))
        }
        if (length(unique(dat$pheno)) < 2) {
          return(list(or = NA_real_, ci_low = NA_real_, ci_high = NA_real_, p = NA_real_, n = nrow(dat)))
        }
        covars_keep_strat <- c()
        for (cv in covars_keep) {
          if (!cv %in% names(dat)) next
          if (length(unique(dat[[cv]])) > 1) {
            covars_keep_strat <- c(covars_keep_strat, cv)
          }
        }
        covars_formula_strat <- vapply(covars_keep_strat, quote_name, character(1))
        rhs_strat <- c('geno_minor', covars_formula_strat)
        f_strat <- as.formula(paste('pheno ~', paste(rhs_strat, collapse = ' + ')))
        fit_strat <- try(logistf(f_strat, data = dat), silent = TRUE)
        if (inherits(fit_strat, 'try-error')) {
          return(list(or = NA_real_, ci_low = NA_real_, ci_high = NA_real_, p = NA_real_, n = nrow(dat)))
        }
        beta <- fit_strat$coefficients['geno_minor']
        ci_low_s <- fit_strat$ci.lower['geno_minor']
        ci_high_s <- fit_strat$ci.upper['geno_minor']
        p_s <- fit_strat$prob['geno_minor']
        list(or = exp(beta), ci_low = exp(ci_low_s), ci_high = exp(ci_high_s), p = p_s, n = nrow(dat))
      }

      low_fit <- strat_fit(sub_low)
      high_fit <- strat_fit(sub_high)

      results[[length(results) + 1]] <- data.frame(
        Location = ps,
        Trait = trait,
        Allele_major = major,
        Allele_minor = minor,
        N = nrow(sub),
        N_case = n_case,
        N_control = n_ctrl,
        MAC_total = mac_total,
        MAC_low = mac_low,
        MAC_high = mac_high,
        OR_int = or_int,
        CI_int_lower = exp(ci_low),
        CI_int_upper = exp(ci_high),
        p_int = p_int,
        p_wald = p_wald,
        OR_low = or_low,
        OR_high = or_high,
        N_low = low_fit$n,
        N_high = high_fit$n,
        OR_low_strat = low_fit$or,
        CI_low_strat = low_fit$ci_low,
        CI_high_strat = low_fit$ci_high,
        p_low_strat = low_fit$p,
        OR_high_strat = high_fit$or,
        CI_low_high_strat = high_fit$ci_low,
        CI_high_high_strat = high_fit$ci_high,
        p_high_strat = high_fit$p,
        pheno_note = pheno_note,
        covar_set = label,
        stringsAsFactors = FALSE
      )
    }
  }

  res_df <- if (length(results) > 0) do.call(rbind, results) else data.frame()
  filt_df <- if (length(variant_filters) > 0) do.call(rbind, variant_filters) else data.frame()

  if (nrow(res_df) > 0) {
    res_df$q_int_global <- bh_adjust(res_df$p_int)
    res_df$q_int_within <- ave(res_df$p_int, res_df$Location, FUN = bh_adjust)
    res_df <- merge(res_df, lead_map, by = 'Location', all.x = TRUE)
  }

  write.csv(res_df, file.path(out_dir, 'interaction_results.csv'), row.names = FALSE)
  write.csv(filt_df, file.path(out_dir, 'variant_mac_summary.csv'), row.names = FALSE)
  write.csv(run_stats, file.path(out_dir, 'run_summary.csv'), row.names = FALSE)
  if (!is.null(first_error)) {
    writeLines(first_error, con = file.path(out_dir, 'run_error_first.txt'))
  }
  invisible(res_df)
}

main_res <- run_interaction('main')
message('Done.')

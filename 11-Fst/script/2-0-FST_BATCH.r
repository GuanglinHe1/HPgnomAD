#!/usr/bin/env Rscript
# Usage:
# Rscript script.R <csv_file_path> <src_directory> <dest_alignment_file> <popgen_working_directory> <popgen_output_path>

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 5) {
  cat("Usage: Rscript script.R <csv_file_path> <src_directory> <dest_alignment_file> <popgen_working_directory> <popgen_output_path>\n")
  quit(status = 1)
}

csv_file_path        <- args[1]
src_directory        <- args[2]
dest_alignment_file  <- args[3]
popgen_working_dir   <- args[4]
popgen_output_path   <- args[5]

# Merge FASTA files listed in the metadata CSV
mergeFastaFiles <- function(csv_file, src_dir, dest_file, id_column = "strain") {
  # Load the CSV file; it must contain a strain ID column (default: "strain")
  strains_info <- read.csv(csv_file, header = TRUE, stringsAsFactors = FALSE)
  if (!(id_column %in% names(strains_info))) {
    stop(paste("Column does not exist in CSV:", id_column))
  }
  ids <- strains_info[[id_column]]
  
  # Build absolute paths for each FASTA file
  fasta_files <- file.path(src_dir, paste0(ids, ".fasta"))
  
  # Keep only the files that exist
  existing_files <- fasta_files[file.exists(fasta_files)]
  if (length(existing_files) == 0) {
    stop("No FASTA files were found based on the metadata list.")
  }
  
  # Remove the destination file if it already exists
  if (file.exists(dest_file)) {
    file.remove(dest_file)
  }
  
  # Concatenate files via shell to keep the process simple
  cmd <- paste("cat", paste(shQuote(existing_files), collapse = " "), ">", shQuote(dest_file))
  cat("Running command:\n", cmd, "\n")
  
  # Execute merge command
  system(cmd)
}

# Run PopGenome and compute FST
performFSTAnalysis <- function(csv_file, popgen_input_dir, popgen_working_dir, popgen_output_file) {
  # Set working directory for PopGenome
  setwd(popgen_working_dir)
  
  # Load PopGenome
  if (!requireNamespace("PopGenome", quietly = TRUE)) {
    stop("The PopGenome package is required. Please install it before running.")
  }
  library(PopGenome)
  
  # Load metadata
  meta <- read.table(csv_file, sep = ",", header = TRUE, stringsAsFactors = FALSE)
  if (!("fs_pop" %in% names(meta))) {
    stop("Column 'fs_pop' is missing from the CSV file.")
  }
  # Keep only hsp1 and hsp2
  meta <- meta[meta$fs_pop %in% c("hsp1", "hsp2"), ]
  
  # Load FASTA alignment (directory should contain a single .aln file)
  data <- readData(popgen_input_dir,
                   populations = FALSE,
                   outgroup = FALSE,
                   include.unknown = FALSE,
                   gffpath = FALSE,
                   format = "fasta",
                   parallized = FALSE,
                   progress_bar_switch = FALSE,
                   FAST = TRUE,
                   big.data = TRUE,
                   SNP.DATA = FALSE)
  
  # Basic summaries
  cat("Individuals:\n")
  print(get.individuals(data))
  
  cat("Slot structure:\n")
  show.slots(data)
  
  cat("Data summary:\n")
  print(get.sum.data(data))
  
  # Configure populations
  if (!("strain" %in% names(meta))) {
    stop("Column 'strain' is missing from the CSV file.")
  }
  pop1 <- meta$strain[meta$fs_pop == "hsp1"]
  pop2 <- meta$strain[meta$fs_pop == "hsp2"]
  data <- set.populations(data, list(pop1, pop2))
  
  # Sliding window transform for site-wise FST
  slide.data <- sliding.window.transform(data,
                                         width = 1,
                                         jump = 1,
                                         type = 2,
                                         start.pos = FALSE,
                                         end.pos = FALSE,
                                         whole.data = TRUE)
  
  # Compute nucleotide FST per site
  slide.data <- F_ST.stats(slide.data, mode = "nucleotide")
  cat("Structure of FST output:\n")
  str(slide.data@nuc.F_ST.pairwise)
  fst_values <- slide.data@nuc.F_ST.pairwise
  
  # Ensure the destination file exists before writing
  if (!file.exists(popgen_output_file)) {
    if (!file.create(popgen_output_file)) {
      stop("Unable to create file:", popgen_output_file)
    }
  }
  
  write.table(fst_values, file = popgen_output_file, sep = "\t", row.names = FALSE)
  cat("FST results saved to:", popgen_output_file, "\n")
}

# Orchestrate the pipeline
runFSTPipeline <- function(csv_file, src_dir, dest_file, popgen_working_dir, popgen_output_file) {
  mergeFastaFiles(csv_file, src_dir, dest_file)
  
  # PopGenome expects the .aln file in its directory
  popgen_input_dir <- dirname(dest_file)
  performFSTAnalysis(csv_file, popgen_input_dir, popgen_working_dir, popgen_output_file)
}

# Execute pipeline
runFSTPipeline(csv_file_path, src_directory, dest_alignment_file, popgen_working_dir, popgen_output_path)

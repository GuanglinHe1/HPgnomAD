import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Merge multiple FASTA files into a single output file")
    parser.add_argument("list_file", help="List file containing target IDs")
    parser.add_argument("fasta_dir", help="Directory that stores FASTA files")
    parser.add_argument("output_file", help="Path to the merged output file")
    args = parser.parse_args()

    list_file = args.list_file
    fasta_dir = args.fasta_dir
    output_file = args.output_file

    # Read target ID list
    try:
        with open(list_file, 'r') as f:
            target_ids = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error: Unable to read list file {list_file}: {e}")
        sys.exit(1)

    # Open output file (overwrite mode)
    try:
        with open(output_file, 'w') as fout:
            # Iterate through all target IDs
            for tid in target_ids:
                fasta_file = os.path.join(fasta_dir, tid + ".fasta")
                # Check whether the corresponding FASTA file exists
                if os.path.exists(fasta_file):
                    with open(fasta_file, 'r') as fin:
                        # Read line by line and write directly to the output file
                        for line in fin:
                            fout.write(line)
                    fout.flush()  # Flush buffer after each file
                else:
                    print(f"Warning: File {fasta_file} does not exist")
    except IOError as e:
        print(f"Error: Unable to write to output file {output_file}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

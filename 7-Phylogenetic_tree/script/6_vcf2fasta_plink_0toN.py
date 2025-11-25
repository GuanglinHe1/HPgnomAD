def replace_zeros_with_n(input_file_path, output_file_path):
    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    # Used to store the modified content
    modified_lines = []

    for line in lines:
        line = line.strip()

        if line.startswith(">"):  # 这是标题行，不做修改
        if line.startswith(">"):  # This is a header line, do not modify
            modified_lines.append(line)
        else:
            # Replace '0' with 'N' in the sequence
            modified_sequence = line.replace('0', 'N')
            modified_lines.append(modified_sequence)

    # 将修改后的内容写入新的文件
    # Write the modified content to a new file
    with open(output_file_path, 'w') as output_file:
        for modified_line in modified_lines:
            output_file.write(modified_line + "\n")

    print(f"File has been processed and saved to: {output_file_path}")

# 使用示例
input_file_path = 'input.fasta'  
output_file_path = 'output.fasta' 
replace_zeros_with_n(input_file_path, output_file_path)

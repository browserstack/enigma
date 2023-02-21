
# Set the names of the input files
file1 = 'requirements.txt'
file2 = 'Access/access_modules/requirements.txt'

# Set the name of the output file
output_file = 'merged_requirements.txt'

# Read the requirements from the first file
with open(file1, 'r') as f1:
    requirements1 = f1.readlines()

# Read the requirements from the second file
with open(file2, 'r') as f2:
    requirements2 = f2.readlines()

# Merge the requirements
merged_requirements = list(set(requirements1 + requirements2))

# Write the merged requirements to the output file
with open(output_file, 'w') as out_file:
    for requirement in sorted(merged_requirements):
        out_file.write(requirement)

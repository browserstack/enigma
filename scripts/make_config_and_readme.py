import shutil
import os

# Set the names of the input and output files
sample_file = 'config.json.sample'
output_file = 'config.json'

# Check if the output file exists, and create it if it doesn't
if not os.path.exists(output_file):
    open(output_file, 'w').close()
    # Copy the sample file to the output file
    shutil.copy(sample_file, output_file)


# Set the name of the file to be created
filename = 'README.md'

# Check if the file already exists
if os.path.exists(filename):
    print(f"{filename} already exists.")
else:
    # Create the file and write some content to it
    with open(filename, 'w') as f:
        f.write('# Engima\n\n')
        f.write('Central Codebase for access management tool.\n')
        f.write('## Installation\n\n')
        f.write('To install this project, follow these steps:\n\n')
        f.write('1. Clone the repository.\n')
        f.write('2. Run `brew install docker docker-compose`\n\n')
        f.write('2. Run `brew install colima`\n\n')
        f.write('2. Run `colima start`\n\n')
        f.write('## Usage\n\n')
        f.write('To use this project, run the following command:\n\n')
        f.write('```\n')
        f.write('make dev\n')
        f.write('```\n\n')
        f.write('## License\n\n')
        f.write('This project is licensed under the MIT License - see the LICENSE file for details.\n')
        print(f"{filename} created successfully!")



import os
import shutil
import sys
import importlib.util
import django
import json

sys.path.append(os.path.abspath('./'))

django.setup()

from Access.helpers import get_available_access_modules

directory = "Access/access_modules"

access_module_paths = []
# Walk through the directory and its subdirectories and print the path of each folder.
for path, subdirs, files in os.walk(directory):
    for name in files:

        file_name = (os.path.join(path, name)).split('/')[-1]
        curr_path_array = (os.path.join(path, name)).split('/')[:-1]

        if file_name == 'config.json.sample':
            sample_file = 'config.json.sample'
            output_file = 'config.json'
            sample_file_path = (os.path.join('/'.join(curr_path_array) , sample_file))
            output_file_path = (os.path.join('/'.join(curr_path_array) , output_file))
            access_module_paths.append(output_file_path)
            
            if not os.path.exists(output_file_path):
               open(output_file_path, 'w').close()
               shutil.copy(sample_file_path, output_file_path)
    

access_module_tags = []
# print(get_available_access_modules())
for key in get_available_access_modules():
   access_module_tags.append(get_available_access_modules()[key].tag())
access_module_paths = sorted(access_module_paths)


index = 0
merged_access_module= {}
for access_module_path in access_module_paths:
    with open(access_module_path) as f:
          config_dict = json.load(f)
    conig_dict_with_tag = { 
        access_module_tags[index] : config_dict
     }
    merged_access_module.update(conig_dict_with_tag)
    index += 1




# load config.json from root directory
with open('config.json') as f:
    config_dict = json.load(f)
    
    for tag in merged_access_module:
        # print(tag , merged_access_module[tag])
        config_dict['access_modules'][tag] = merged_access_module[tag]

# convert into json
config_dict_json = (json.dumps(config_dict))
with open("config.json", "w") as f:
    json.dump(config_dict, f)
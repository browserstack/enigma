import json
import sys
import shutil
from git import Repo
import os

print("Starting cloning setup")
try:
    f = open("./config.json", "r")
    config = json.load(f)
    urls = config["access_modules"]["git_urls"]

    for each_access_module in os.listdir('Access/access_modules'):
        path_to_remove = "Access/access_modules/%s" % each_access_module
        print("Deleting %s" % path_to_remove)
        try:
            if os.path.isdir(path_to_remove):
                shutil.rmtree(path_to_remove)
        except Exception as e:
            print("Got Error while deleting the path %s. Error: %s" % (path_to_remove, str(e)))
    shutil.copyfile('Access/base_email_access/access_modules_init.py', "Access/access_modules/__init__.py")

    requirements_file = 'Access/access_modules/requirements.txt'
    if not os.path.exists(requirements_file):
          open(requirements_file, 'w').close()

    print("All urls: %s" % (",".join(urls)))
    for url in urls:
        specified_branch = None
        if "#" in url:
            specified_branch = url.split("#")[1]
            url = url.split("#")[0]
        folder_name = url.split("/").pop()[:-4]
        folder_path = "./Access/access_modules/" + folder_name
        try:
            if specified_branch:
                Repo.clone_from(url, folder_path, branch=specified_branch)
            else:
                Repo.clone_from(url, folder_path)
            # move all folders, not files in the cloned repo to the access_modules
            # folder except the .git, .github and secrets folder
            for file in os.listdir(folder_path):
                if (
                        os.path.isdir(folder_path + "/" + file)
                        and file != ".git"
                        and file != ".github"
                        and file != "secrets"
                    ) :
                    try :
                        os.rename(
                            folder_path + "/" + file, "./Access/access_modules/" + file
                        )
                    except:
                         print("File is already present.")
                            
                if(file == "requirements.txt"):
                    current_requirements_file = folder_path + "/" + file
                    #Read the requirements
                    with open(requirements_file, 'r') as f1:
                             requirements1 = f1.readlines()

                    with open(current_requirements_file, 'r') as f1:
                             requirements2 = f1.readlines()

                    # Merge the requirements
                    merged_requirements = list(set(requirements1 + requirements2))
                       
                    #update the requirements.txt
                    with open(requirements_file, 'w') as out_file:
                        for requirement in sorted(merged_requirements):
                             out_file.write(requirement)
                       
            print("Cloning successful!")
        except Exception as e:
           print("error-->",e)
           print("failed cloning " + folder_name + ".")

        # remove the cloned repo folder entirely with all its contents which
        # includes folders and files using shutil.rmtree()
        # shutil.rmtree() sometimes throws an error on windows,
        # so we use try and except to ignore the error
        try:
            shutil.rmtree(folder_path)
        except Exception as e:
            print(e)
            print("failed to remove " + folder_path + " folder.")
        
except Exception as e:
    print("Access module cloning failed!")
    print(str(e))
    sys.exit(1)

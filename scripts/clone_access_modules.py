import json
import sys
import shutil
from git import Repo
import os

try:
    f = open("./config.json", "r")
    config = json.load(f)
    urls = config["access_modules"]["git_urls"]
    for url in urls:
        folder_name = url.split("/").pop()[:-4]
        folder_path = "./Access/access_modules/" + folder_name
        try:
            if os.path.exists(folder_path):
                Repo(folder_path).remotes.origin.pull()
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
                    ):
                        os.rename(
                            folder_path + "/" + file, "./Access/access_modules/" + file
                        )

                # remove the cloned repo folder entirely with all its contents which
                # includes folders and files using shutil.rmtree()
                # shutil.rmtree() sometimes throws an error on windows,
                # so we use try and except to ignore the error
                try:
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(e)
                    print("failed to remove " + folder_path + " folder.")

            print("Cloning successful!")

        except Exception as e:
            print(e)
            print("failed cloning " + folder_name + ".")
except Exception as e:
    print("Access module cloning failed!")
    print(str(e))
    sys.exit(1)

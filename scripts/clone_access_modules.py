import json
import sys
from git import Repo
import os

try:
  f = open("./config.json","r")
  config = json.load(f)
  urls = config["access_modules"]["git_urls"]
  for url in urls:
    folder_name = url.split("/").pop()[:-4]
    try:
      if os.path.exists("./Access/access_modules/"+folder_name):
        Repo("./Access/access_modules/"+folder_name).remotes.origin.pull()
      else:
        Repo.clone_from(url, "./Access/access_modules/"+folder_name)
    except Exception as e:
      print("failed cloning "+folder_name+".")
except Exception as e:
  print("Access module cloning failed!")
  print(str(e))
  sys.exit(1)

import json
import sys
from git import Repo

try:
  f = open("config.json","r")
  config = json.load(f)
  urls = config["access_modules"]["git_urls"]
  for url in urls:
    folder_name = url.split("/").pop()[:-4]
    Repo.clone_from(url, "./Access/access_modules/"+folder_name)
except Exception as e:
  print("Access module cloning failed!")
  print(str(e))
  sys.exit(1)

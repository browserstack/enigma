import json
import os
import sys
from jsonschema import validate

try:
  f = open("schema.json","r")
  schema = json.load(f)
  f = open(sys.argv[1], "r")
  config = json.load(f)
  modules = [ f.path for f in os.scandir("./Access/access_modules") if f.is_dir() ]
  for module in modules:
    f = open(module+"/schema.json")
    module_schema = json.load(f)
    schema["properties"].update(module_schema["properties"])
    schema["required"] += module_schema["required"]
  validate(instance=config, schema=schema)  
  print("Schema validation passed!")
except Exception as e:
  print("Schema validation failed!")
  print(str(e))
  sys.exit(1)
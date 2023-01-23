import json
import os
import sys
from jsonschema import validate

try:
    config_file = "config.json" if len(sys.argv) <= 1 else sys.argv[1]
    f = open("./schema.json", "r")
    schema = json.load(f)
    f = open("./" + config_file, "r")
    config = json.load(f)
    root_folders = [f.path for f in os.scandir("./Access/access_modules") if f.is_dir()]
    for folder in root_folders:
        modules = [f.path for f in os.scandir(folder) if f.is_dir()]
        for module in modules:
            if os.path.exists(module + "/schema.json"):
                f = open(module + "/schema.json")
                module_schema = json.load(f)
                schema["properties"].update(module_schema["properties"])
                schema["required"] += module_schema["required"]
    validate(instance=config, schema=schema)
    print("Schema validation passed!")
except Exception as e:
    print("Schema validation failed!")
    print(e)
    sys.exit(1)

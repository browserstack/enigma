import json
import os
import sys
import traceback
import logging
from jsonschema import validate

logger = logging.getLogger(__name__)

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
    logger.info("Schema validation passed!")
except Exception as e:
    logger.error("Schema validation failed! Error is: " + e)
    traceback.format_exc()
    sys.exit(1)

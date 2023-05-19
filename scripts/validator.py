""" Script to validare the config.json file against the schema.json file. """
import logging
import os
import sys
from jsonschema import validate

from scripts.helpers import read_json_from_file

logger = logging.getLogger(__name__)


def validate_schema():
    """ Core function to validate """

    schema = read_json_from_file("./schema.json")

    config_file = "config.json" if len(sys.argv) <= 1 else sys.argv[1]
    config = read_json_from_file("./" + config_file)

    root_folders = [f.path for f in os.scandir("./Access/access_modules") if f.is_dir()]
    for folder in root_folders:
        modules = [f.path for f in os.scandir(folder) if f.is_dir()]
        for module in modules:
            if os.path.exists(module + "/schema.json"):
                module_schema = read_json_from_file(module + "/schema.json")
                schema["properties"].update(module_schema["properties"])
                schema["required"] += module_schema["required"]
    validate(instance=config, schema=schema)
    logger.info("Schema validation passed!")


def __main__():
    try:
        validate_schema()
    except Exception as exception:
        logger.exception("Schema validation failed! Error is: %s", exception)
        sys.exit(1)

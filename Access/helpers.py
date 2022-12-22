from os.path import dirname, basename, isfile, join
import glob
import re
import logging

logger = logging.getLogger(__name__)
available_accesses = []
cached_accesses = []

def getAvailableAccessModules():
    global available_accesses
    if len(available_accesses) > 0:
        return available_accesses
    available_accesses = [access for access in getAccessModules() if access.available]
    return available_accesses

def getAccessModules():
    global cached_accesses
    if len(cached_accesses) > 0:
        return cached_accesses
    access_modules_dirs = glob.glob(join(dirname(__file__), "access_modules", "*"))
    for each_dir in access_modules_dirs:
        if re.search(r"/(base_|__pycache__)", each_dir):
            access_modules_dirs.remove(each_dir)
    access_modules_dirs.sort()
    cached_accesses = [ globals()[basename(f)].access.get_object() for f in access_modules_dirs if not isfile(f)]
    return cached_accesses

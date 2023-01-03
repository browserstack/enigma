from os.path import dirname, basename, isfile, join
import glob
import re
import logging
import time, datetime
from Access.access_modules import *
from django.template import loader

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
    cached_accesses = \
        [globals()[basename(f)].access.get_object() for f in access_modules_dirs if not isfile(f)]
    return cached_accesses

def check_user_permissions(user, permissions):
    if hasattr(user, 'user'):
        permission_labels = [permission.label for permission in user.user.permissions]
        if type(permissions) == list:
            if len(set(permissions).intersection(permission_labels)) > 0:
                return True
        else:
            if permissions in permission_labels:
                return True
    return False

def getAccessDetails(eachAccess):
    accessDetails = {}
    access_label = eachAccess.access_label
    logger.debug(accessDetails)
    for eachAccessModule in getAccessModules():
        if eachAccess.access_tag == eachAccessModule.tag():
            accessDetails['accessType'] = eachAccessModule.access_desc()
            accessDetails['accessCategory'] = eachAccessModule.get_label_desc(access_label)
            accessDetails['accessMeta'] = eachAccessModule.get_label_meta(access_label)

            if eachAccess.access_tag == "other" and "grant_emails" in eachAccess.access_label and type(eachAccess.access_label["grant_emails"])==list:
                accessDetails['revokeOwner'] = ",".join(eachAccess.access_label["grant_emails"])
                accessDetails['grantOwner']  = accessDetails['revokeOwner']
            else:
                accessDetails['revokeOwner'] = ",".join(eachAccessModule.revoke_owner())
                accessDetails['grantOwner'] = ",".join(eachAccessModule.grant_owner())
    logger.debug(accessDetails)
    return accessDetails
    
def sla_breached(requested_on):
    diff = datetime.datetime.now().replace(tzinfo=None) - requested_on.replace(tzinfo=None)
    duration_in_s = diff.total_seconds()
    hours = divmod(duration_in_s, 3600)[0]
    return hours >= 24

def generateStringFromTemplate(filename, **kwargs):
    template = loader.get_template(filename)
    vals = {}
    for key, value in kwargs.items():
        vals[key] = value
    return template.render(vals)

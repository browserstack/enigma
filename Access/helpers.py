from django.template import loader
from os.path import dirname, basename, isfile, join
import glob
import logging
import re
import datetime

from Access.access_modules import * # NOQA
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS

logger = logging.getLogger(__name__)

available_accesses = []
cached_accesses = []

modules = {}


def get_available_access_modules():
    available_accesses = getAvailableAccessModules()
    for access in available_accesses:
        modules.update({access.tag(): access})
    return modules


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
    # create a deepcopy copy of the list so we can remove items from the original list
    access_modules_dirs_copy = access_modules_dirs[:]
    for each_dir in access_modules_dirs_copy:
        if re.search(r"/(base_|__pycache__|secrets)", each_dir):
            access_modules_dirs.remove(each_dir)
    access_modules_dirs.sort()
    cached_accesses = [
        globals()[basename(f)].access.get_object()
        for f in access_modules_dirs
        if not isfile(f)
    ]
    return cached_accesses


def check_user_permissions(user, permissions):
    if hasattr(user, "user"):
        permission_labels = [permission.label for permission in user.user.permissions]
        if type(permissions) == list:
            if len(set(permissions).intersection(permission_labels)) > 0:
                return True
        else:
            if permissions in permission_labels:
                return True
    return False


def sla_breached(requested_on):
    diff = datetime.datetime.now().replace(tzinfo=None) - requested_on.replace(
        tzinfo=None
    )
    duration_in_s = diff.total_seconds()
    hours = divmod(duration_in_s, 3600)[0]
    return hours >= 24


def generateStringFromTemplate(filename, **kwargs):
    template = loader.get_template(filename)
    vals = {}
    for key, value in kwargs.items():
        vals[key] = value
    return template.render(vals)


def getPossibleApproverPermissions():
    all_approver_permissions = [PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]]
    for each_module in getAvailableAccessModules():
        approver_permissions = each_module.fetch_approver_permissions()
        all_approver_permissions.extend(approver_permissions.values())
    return list(set(all_approver_permissions))


def get_access_details(each_access):
    access_details = {}
    access_label = each_access.access_label
    for each_access_module in getAccessModules():
        if each_access.access_tag == each_access_module.tag():
            access_details['accessType'] = each_access_module.access_desc()
            access_details['accessCategory'] = each_access_module.get_label_desc(access_label)
            access_details['accessMeta'] = each_access_module.get_label_meta(access_label)

            if (each_access.access_tag == "other" and
                "grant_emails" in each_access.access_label and
                    type(each_access.access_label["grant_emails"]) == list):
                access_details['revokeOwner'] = ",".join(each_access.access_label["grant_emails"])
                access_details['grantOwner'] = access_details['revokeOwner']
            else:
                access_details['revokeOwner'] = ",".join(each_access_module.revoke_owner())
                access_details['grantOwner'] = ",".join(each_access_module.grant_owner())
    return access_details


def split_access_details(original_details):
    split_details = []
    for each_category in original_details['accessCategory'].split(';'):
        split_details.append({
            'accessType': original_details['accessType'],
            'accessCategory': each_category,
            'accessMeta': original_details['accessMeta']
        })
    return split_details

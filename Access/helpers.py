from django.template import loader
from os.path import dirname, basename, isfile, join
import glob
import logging
import re
import datetime
import random

from Access.access_modules import *  # NOQA
from enigma_automation.settings import PERMISSION_CONSTANTS
from Access.models import User

logger = logging.getLogger(__name__)

available_accesses = []
cached_accesses = []


def get_available_access_module_from_tag(tag):
    all_modules = get_available_access_modules()
    if tag in all_modules:
        return get_available_access_modules()[tag]
    return None

def get_available_access_module_desc():
    access_descriptions = []
    for tag, each_module in get_available_access_modules().items():
        access_descriptions.append(each_module.access_desc())
    
    return access_descriptions


def get_available_access_type():
    available_accesses_type = [access.access_desc() for access in _get_modules_on_disk()]
    return available_accesses_type


def get_available_access_modules():
    global available_accesses
    if len(available_accesses) > 0:
        return available_accesses.copy()

    available_accesses = {
        access.tag(): access for access in _get_modules_on_disk() if access.available
    }
    return available_accesses.copy()


def _get_modules_on_disk():
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
    for each_tag, each_module in get_available_access_modules().items():
        approver_permissions = each_module.fetch_approver_permissions()
        all_approver_permissions.extend(approver_permissions.values())
    return list(set(all_approver_permissions))


def get_approvers():
    emails = [
        user.email
        for user in User.get_active_users_with_permission(
            permission_label=PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]
        )
    ]
    if not emails:
        raise Exception("No user found with approver roles")
    primary_approver = random.choice(emails)

    emails.remove(primary_approver)
    other_approver = emails
    if not other_approver:
        other_approver = None
    else:
        other_approver = ", ".join(other_approver)
    return primary_approver, other_approver

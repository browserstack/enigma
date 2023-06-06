""" module contains helper methods """
from os.path import dirname, basename, isfile, join
import glob
import logging
import re
import datetime
import random
from typing import Dict
from django.template import loader
from Access.access_modules import *  # NOQA
from Access.models import User
from enigma_automation.settings import PERMISSION_CONSTANTS

logger = logging.getLogger(__name__)

MAP_ACCESSES: Dict[str, list[object]] = {}


def get_available_access_module_from_tag(tag):
    """ method to get available access module from tag """
    all_modules = get_available_access_modules()
    if tag in all_modules:
        return get_available_access_modules()[tag]
    return None


def get_available_access_type():
    """ method to get available access type """
    available_accesses_type = [access.access_desc() for access in _get_modules_on_disk()]
    return available_accesses_type


def get_available_access_modules():
    """ method to get available access modules """
    if MAP_ACCESSES.get("AVAILABLE_ACCESSES"):
        return MAP_ACCESSES.get("AVAILABLE_ACCESSES").copy()

    available_accesses = {
        access.tag(): access for access in _get_modules_on_disk() if access.available
    }
    MAP_ACCESSES["AVAILABLE_ACCESSES"] = available_accesses
    return available_accesses.copy()


def _get_modules_on_disk():
    if MAP_ACCESSES.get("CACHED_ACCESSES"):
        return MAP_ACCESSES.get("CACHED_ACCESSES")

    access_modules_dirs = glob.glob(join(dirname(__file__), "access_modules", "*"))
    # create a deepcopy copy of the list, so we can remove items from the original list
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
    MAP_ACCESSES["CACHED_ACCESSES"] = cached_accesses
    return cached_accesses


def check_user_permissions(user, permissions):
    """ method to check user permission """
    if hasattr(user, "user"):
        permission_labels = [permission.label for permission in user.user.permissions]
        if isinstance(permissions, list):
            if len(set(permissions).intersection(permission_labels)) > 0:
                return True
        else:
            if permissions in permission_labels:
                return True
    return False


def sla_breached(requested_on):
    """ method to handle sla breach """
    diff = datetime.datetime.now().replace(tzinfo=None) - requested_on.replace(
        tzinfo=None
    )
    duration_in_s = diff.total_seconds()
    hours = divmod(duration_in_s, 3600)[0]
    return hours >= 24


def generate_string_from_template(filename, **kwargs):
    """ method to generate string from template """
    template = loader.get_template(filename)
    vals = {}
    for key, value in kwargs.items():
        vals[key] = value
    return template.render(vals)


def get_possible_approver_permissions():
    """ method to get possible approver permissions """
    all_approver_permissions = [PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]]
    for _each_tag, each_module in get_available_access_modules().items():
        approver_permissions = each_module.fetch_approver_permissions()
        all_approver_permissions.extend(approver_permissions.values())
    return list(set(all_approver_permissions))


def get_approvers():
    """ method to get approvers """
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

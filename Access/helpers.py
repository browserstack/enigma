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

# One Access request will contain Accesses to one component at a time.
def getAccessRequestDetails(eachAccessRequest):
    access_request_data = {}
    access = [eachAccessRequest.access]
    access_tags = [eachAccessRequest.access.access_tag]
    access_labels = [eachAccessRequest.access.access_label]

    access_tag = access_tags[0]
    # code metadata
    access_request_data["access_tag"] = access_tag
    # ui metadata
    access_request_data["userEmail"] = eachAccessRequest.user.email
    access_request_data["requestId"] = eachAccessRequest.request_id
    access_request_data['accessReason'] = eachAccessRequest.request_reason
    access_request_data['requested_on'] = eachAccessRequest.requested_on

    for eachAccessModule in getAccessModules():
        if access_tag == eachAccessModule.tag():
            access_request_data["accessType"] = eachAccessModule.access_desc()
            access_request_data["accessCategory"] = eachAccessModule.combine_labels_desc(access_labels)
            access_request_data["accessMeta"] = eachAccessModule.combine_labels_meta(access_labels)
    
    return access_request_data
from Access import helpers, views_helper, accessrequest_helper
from Access.models import User, UserAccessMapping, SshPublicKey
import threading
import json
from Access.background_task_manager import background_task
import logging
from . import helpers as helper
from django.db import transaction

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PERMISSION_VIEW_USER_LIST = "VIEW_USER_LIST"
PERMISSION_ALLOW_USER_OFFBOARD = "ALLOW_USER_OFFBOARD"

EXCEPTION_USER_UNAUTHORIZED = "Unauthorized to list users"
ERROR_MESSAGE = "Error in request not found OR Invalid request type"

NEW_IDENTITY_CREATE_SUCCESS_MESSAGE = {
    "title": "Identity Updated",
    "msg": "Identity Updated for {modulename}",
}

NEW_IDENTITY_CREATE_ERROR_MESSAGE = {
    "title": "Identity could not be updated",
    "msg": "Identity could not be updated for {modulename}. Please connect with admin",
}

IDENTITY_UNCHANGED_ERROR_MESSAGE = {
    "title": "Identity value not changed",
    "msg": "Identity could not be updated for {modulename}. The new identity is same as the old identity",
}


class IdentityNotChangedException(Exception):
    def __init__(self):
            self.message = "Identity Unchanged"
            super().__init__(self.message)    


def get_identity_templates(auth_user):
    user_identities = auth_user.user.get_all_active_identity()
    context = {}
    context["configured_identity_template"] = []
    context["unconfigured_identity_template"] = []
    all_modules = helper.get_available_access_modules()
    for user_identity in user_identities:
        is_identity_configured = _is_valid_identity_json(identity=user_identity.identity)
        if is_identity_configured:
            module = all_modules[user_identity.access_tag]
            context["configured_identity_template"].append(
                {
                    "accessUserTemplatePath": module.get_identity_template(), 
                    "identity" : user_identity.identity
                }            
            )
            all_modules.pop(user_identity.access_tag)
            
    for mod in all_modules.values():
        context["unconfigured_identity_template"].append(
            {
                "accessUserTemplatePath": mod.get_identity_template(), 
            }
        )
    # context["aws_username"] = "some name"
    return context

def _is_valid_identity_json(identity):
    try:
        identity_json = json.loads(json.dumps(identity))
        identity_dict = dict(identity_json)
        if len(identity_dict)>0:
            return True
        return False
    except Exception:
        return False

def create_identity(user_identity_form, auth_user):
    user = auth_user.user
    mod_name = user_identity_form.get("modname")
    selected_access_module = helper.get_available_access_modules()[mod_name]
    context = {}
    if selected_access_module:
        new_module_identity_json = selected_access_module.verify_identity(
            user_identity_form, user.email
        )
        existing_user_identity = user.get_active_identity(
            access_tag=selected_access_module.tag()
        )
        if new_module_identity_json == existing_user_identity.identity:
            raise IdentityNotChangedException()
        existing_user_access_mapping = None

        # get useraccess if an identity already exists
        if existing_user_identity:
            existing_user_access_mapping = (
                existing_user_identity.get_active_access_mapping()
            )

        # create identity json  # call this verify identity
        new_user_access_mapping = __change_identity_and_transfer_membership(
            user=user,
            access_tag=selected_access_module.tag(),
            existing_user_identity=existing_user_identity,
            existing_user_access_mapping=existing_user_access_mapping,
            new_module_identity=new_module_identity_json,
        )
        if True:
            for access_mapping in existing_user_access_mapping:
                # Create celery task for revoking old access
                # mod.revoke(membership)
                if access_mapping.status.lower() == "processing":
                    raise Exception("Not Implemented")

            for access_mapping in new_user_access_mapping:
                # Create celery task for approval
                # mod.approve(membership)
                raise Exception("Not Implemented")

   
    context["status"] = {
        "title": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["title"],
        "msg": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["msg"].format(
            modulename=selected_access_module.tag()
        ),
    }
    return context


@transaction.atomic
def __change_identity_and_transfer_membership(
    user,
    access_tag,
    existing_user_identity,
    existing_user_access_mapping,
    new_module_identity,
):
    # deactivate old identity and create new
    if existing_user_identity:
        existing_user_identity.deactivate()
    # create new User Identity
    new_user_identity = user.create_new_identity(
        access_tag=access_tag, identity=new_module_identity
    )
    # replicate the memberships with new identity
    if existing_user_access_mapping:
        return new_user_identity.replicate_active_access_membership_for_module(
            existing_access=existing_user_access_mapping
        )


def getallUserList(request):
    try:
        if not (
            helpers.check_user_permissions(request.user, PERMISSION_VIEW_USER_LIST)
        ):
            raise Exception(EXCEPTION_USER_UNAUTHORIZED)

        allowOffboarding = request.user.user.has_permission(
            PERMISSION_ALLOW_USER_OFFBOARD
        )

        dataList = []
        for each_user in User.objects.all():
            dataList.append(
                {
                    "name": each_user.name,
                    "first_name": each_user.user.first_name,
                    "last_name": each_user.user.last_name,
                    "email": each_user.email,
                    "username": each_user.user.username,
                    # "git_username": each_user.gitusername,
                    "is_active": each_user.user.is_active,
                    "offbaord_date": each_user.offbaord_date,
                    "state": each_user.current_state(),
                }
            )
        context = {}
        context["dataList"] = dataList
        context["viewDetails"] = {
            "numColumns": 8 if allowOffboarding else 7,
            "allowOffboarding": allowOffboarding,
        }
        return context
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response["error"] = {"error_msg": str(e), "msg": ERROR_MESSAGE}
        return json_response

def bulk_approve(request, access_tag):
    context = {}
    user=User.objects.get(user__username=request.user)
    accesses = UserAccessMapping.objects.filter(status__in=["Processing", "Approved", "GrantFailed"],access__access_tag__in=[access_tag], user=user)
    if accesses:
      for access in accesses:
          access.status = "Processing"
          access.save()
          requestid = access.request_id
          requestObject =  UserAccessMapping.objects.get(request_id=access.request_id,user=user)
          accessAcceptThread = threading.Thread(target=views_helper.run_access_grant, args=(requestid, requestObject, requestObject.access.access_tag, requestObject.user, requestObject.approver_1.user.username))
          accessAcceptThread.start()

    if len(accesses) >= 1:
      list = []
      for tags in access_tag:
        if (len(tags.split('_')[0])>3): list.append(tags.split('_')[0].capitalize())
        else: list.append(tags.split('_')[0].upper())

      context['status'] = {'title':'Regranted all the previous requests for: ' + ','.join(list) , 'msg': 'Details updated.'}
    else:
      context['status'] = {'title':'No granted accesses found. Please request access for required modules. ' , 'msg': 'Request access. No details found.'}

    return context


def update_user(request):
    context = {}
    try:
        userInfo = []
        userInfo.append(('confluenceusername', request.POST.get("confluenceusername")))
        userInfo.append(('slackusername', request.POST.get("slackusername")))
        userInfo.append(('zoomusername', request.POST.get("zoomusername")))
        userInfo.append(('awsusername', request.POST.get("awsusername")))
        userInfo.append(('opsgenieusername', request.POST.get("opsgenieusername")))
        userInfo.append(('gcpusername', request.POST.get("gcpusername")))
        userInfo.append(('gitusername', request.POST.get("gitusername")))
        userInfo.append(('ssh_public_key', request.POST.get("ssh_pub_key")))

        user=User.objects.get(user__username=request.user)
        msg = ''
        for info in userInfo:
          key = info[0]
          value = info[1]
          msg = update(user, key, value, msg)

        context = {}
        context['status'] = {'title':'Details Updated', 'msg': msg}
        return context
    except Exception as e:
        logger.exception(e)
        context['error'] = {'error':'Error ocurred while updating details.'}
        return context

def update(user, key, value, msg):
    if key=='ssh_public_key':
        if not user.has_module_credentials[key] or value != user.has_module_credentials[key]['key']:
            new_ssh_key = SshPublicKey.objects.create(key = value).__dict__
            if user.ssh_public_key:
                user.ssh_public_key.status = "Revoked"
                user.ssh_public_key.save()
            user.update_module_credentials(key, new_ssh_key['key'])
            msg += "SSH Key updated.\n"
    else:
        if value and value != user.has_module_credentials[key]:
            if user.has_module_credentials[key] != None:
                #mark old accesses as grantfailed
                accesses = UserAccessMapping.objects.filter(status__in=["Approved", "Processing"],access__access_tag="github_access", user=user)
                for access in accesses:
                    access.status = "GrantFailed"
                    access.save()
            user.update_module_credentials(key, value)
            if (len(key.split('username')[0])>3): key = key.split('username')[0].capitalize()
            else:  key = key.split('username')[0].upper()

            msg += key + " Username updated.\n"

    return msg

def offboard_user(request):
    if not (request.user.user.has_permission("VIEW_USER_LIST") and request.user.user.has_permission("ALLOW_USER_OFFBOARD")):
        raise Exception("Requested User is unauthorised to offboard user.")
    try:
        offboard_user_email = request.POST.get("offboard_email")
        if not offboard_user_email:
            raise Exception("Invalid request, attribute not found")
        
        user = User.objects.filter(email=offboard_user_email).first()
        if not user:
            raise Exception("User not found")

    except Exception as e:
        logger.debug("Error in request, not found or Invalid request type")
        logger.exception(str(e))
        return {"error": ERROR_MESSAGE}
    
    user.offboard(request.user.user)
    
    module_identities = user.get_all_active_identity()

    for module_identity in module_identities:  
        module_identity.decline_all_non_approved_access_mappings()
        access_mappings = module_identity.get_all_granted_access_mappings()

        for access_mapping in access_mappings:
            module_identity.offboarding_approved_access_mapping(access_mapping.access)
            background_task("run_access_revoke", json.dumps({"request_id": access_mapping.request_id, "revoker_email": request.user.user.email}))
        
        module_identity.deactivate()
    
    user.revoke_all_memberships()

    return {"message": "Successfully initiated Offboard user"}


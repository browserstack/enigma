from Access import helpers
from Access.models import User
import logging, datetime
from . import helpers as helper
from django.db import transaction

logger = logging.getLogger(__name__)

PERMISSION_VIEW_USER_LIST = "VIEW_USER_LIST"
PERMISSION_ALLOW_USER_OFFBOARD = "ALLOW_USER_OFFBOARD"

EXCEPTION_USER_UNAUTHORIZED = "Unauthorized to list users"
ERROR_MESSAGE = "Error in request not found OR Invalid request type"

NEW_IDENTITY_CREATE_SUCCESS_MESSAGE  = {
    "title" : "Identity Updated",
    "msg": "Identity Updated for {modulename}",
}

NEW_IDENTITY_CREATE_ERROR_MESSAGE  = {
    "title" : "Identity could not be updated",
    "msg": "Identity could not be updated for {modulename}. Please connect with admin",
}


ERROR_INVALID_ACCESS_MODULE = {
    "title" : "Invalid Access Module",
    "msg": "Invalid Access Module - {modulename}",
}

def get_identity_templates():
    context = {}
    templates = []    
    for mod in helper.get_available_access_modules().values():
        templates.append(mod.get_identity_template())
        
    context["identity_templates"] = templates
    return context


def create_identity(user_identity_form, auth_user):
    user=auth_user.user
    mod_name = user_identity_form.get("modname")
    selected_access_module = helper.get_available_access_modules()[mod_name]
    
    if selected_access_module:
        new_module_identity = selected_access_module.verify_identity(user_identity_form, user.email)
        existing_user_identity = user.get_active_identity(access_tag = selected_access_module.tag())
        existing_user_access_mapping = None
        
        # get useraccess if an identity already exists
        if existing_user_identity:
            existing_user_access_mapping = existing_user_identity.get_active_access()
        
        #create identity json  # call this verify identity     
        new_user_access_mapping = __change_identity_and_transfer_membership(user=user, 
                                                                            access_tag = selected_access_module.tag(), 
                                                                            existing_user_identity=existing_user_identity,
                                                                            existing_user_access_mapping=existing_user_access_mapping,
                                                                            new_module_identity=new_module_identity)
        if True:
            for access_mapping in existing_user_access_mapping:
                #Create celery task for revoking old access
                # mod.revoke(membership)
                if access_mapping.status.lower() == "processing":
                    raise Exception("Not Implemented")

            for access_mapping in new_user_access_mapping:
                #Create celery task for approval
                # mod.approve(membership)
                raise Exception("Not Implemented")
                                
    context = {}
    context["status"] = {
        "title": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["title"],
        "msg": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["msg"].format(modulename = selected_access_module.tag()),
    }            
    return context

@transaction.atomic            
def __change_identity_and_transfer_membership(user, access_tag, existing_user_identity, existing_user_access_mapping, new_module_identity):
    #deactivate old identity and create new
    if existing_user_identity:
        existing_user_identity.deactivate()
    #create new User Identity
    new_user_identity = user.create_new_identity(access_tag = access_tag, identity = new_module_identity)
    #replicate the memberships with new identity
    if existing_user_access_mapping:
        return new_user_identity.replicate_active_access_membership_for_module(existing_access = existing_user_access_mapping)
            
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
                    "git_username": each_user.gitusername,
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

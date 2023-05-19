import json
from Access import helpers
from Access.background_task_manager import (
    background_task,
    accept_request,
    revoke_request,
)
from Access.models import User, ApprovalType
import logging
from . import helpers as helper
from django.db import transaction

logger = logging.getLogger(__name__)

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

OFFBOARDING_SUCCESS_MESSAGE = {"message": "Successfully initiated Offboard user"}


class IdentityNotChangedException(Exception):
    def __init__(self):
        self.message = "Identity Unchanged"
        super().__init__(self.message)


def get_identity_templates(auth_user):
    user_identities = auth_user.user.get_all_active_identity()
    context = {}
    context["identity_template"] = []
    all_modules = helper.get_available_access_modules()
    for user_identity in user_identities:
        is_identity_configured = _is_valid_identity_json(
            identity=user_identity.identity
        )
        if is_identity_configured:
            module = all_modules[user_identity.access_tag]
            context["identity_template"].append(
                {
                    "accessUserTemplatePath": module.get_identity_template(),
                    "identity": user_identity.identity,
                }
            )
            all_modules.pop(user_identity.access_tag)

    for mod in all_modules.values():
        if not mod.get_identity_template():
            if not auth_user.user.get_active_identity(mod.tag()):
                auth_user.user.create_new_identity(
                    access_tag=mod.tag(), identity={}
                )
            continue
        context["identity_template"].append(
            {
                "accessUserTemplatePath": mod.get_identity_template(),
            }
        )
    return context


def _is_valid_identity_json(identity):
    try:
        identity_json = json.loads(json.dumps(identity))
        identity_dict = dict(identity_json)
        if len(identity_dict) > 0:
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
        if not new_module_identity_json:
            raise Exception("Failed to verify identity")

        existing_user_identity = user.get_active_identity(
            access_tag=selected_access_module.tag()
        )
        existing_user_access_mapping = None

        # get useraccess if an identity already exists
        if existing_user_identity:
            if new_module_identity_json == existing_user_identity.identity:
                raise IdentityNotChangedException()
            existing_user_access_mapping = (
                existing_user_identity.get_active_access_mapping()
            )

        # create identity json  # call this verify identity
        try:
            __change_identity_and_transfer_access_mapping(
                user=user,
                access_tag=selected_access_module.tag(),
                existing_user_identity=existing_user_identity,
                existing_user_access_mapping=existing_user_access_mapping,
                new_module_identity=new_module_identity_json,
            )
        except Exception as ex:
            raise (ex)

    context["status"] = {
        "title": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["title"],
        "msg": NEW_IDENTITY_CREATE_SUCCESS_MESSAGE["msg"].format(
            modulename=selected_access_module.tag()
        ),
    }
    return context


@transaction.atomic
def __change_identity_and_transfer_access_mapping(
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
    new_user_access_mapping = []
    if existing_user_identity:
        if existing_user_access_mapping:
            new_user_access_mapping = (
                new_user_identity.replicate_active_access_membership_for_module(
                    existing_user_access_mapping=existing_user_access_mapping
                )
            )
        system_user = User.get_system_user()

        for mapping in existing_user_access_mapping:
            if mapping.is_approved():
                revoke_request(user_access_mapping=mapping, revoker=system_user)

        existing_user_identity.decline_all_non_approved_access_mappings("Identity Updated")

    for mapping in new_user_access_mapping:
        if mapping.is_processing() or mapping.is_grantfailed():
            if mapping.approver_2:
                accept_request(user_access_mapping=mapping)
            elif mapping.approver_1:
                accept_request(user_access_mapping=mapping)
            else:
                logger.fatal(
                    "migration failed for request_id:%s mapping is approved but approvers are missing: %s",
                    mapping.request_id,
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


def offboard_user(request):
    if not (
        request.user.user.has_permission("VIEW_USER_LIST")
        and request.user.user.has_permission("ALLOW_USER_OFFBOARD")
    ):
        raise Exception("Requested User is unauthorised to offboard user.")
    try:
        offboard_user_email = request.POST.get("offboard_email")
        if not offboard_user_email:
            raise Exception("Invalid request, attribute not found")
    except Exception as e:
        logger.debug("Error in request, not found or Invalid request type")
        logger.exception(str(e))
        return {"error": ERROR_MESSAGE}

    user = User.get_user_by_email(email=offboard_user_email)
    if not user:
        raise Exception("User not found")

    user.offboard(request.user.user)

    module_identities = user.get_all_active_identity()

    with transaction.atomic():
        for module_identity in module_identities:
            module_identity.decline_all_non_approved_access_mappings()
            access_mappings = module_identity.get_all_granted_access_mappings()

            for access_mapping in access_mappings:
                revoke_request(
                    user_access_mapping=access_mapping, revoker=request.user.user
                )

            module_identity.deactivate()

        user.revoke_all_memberships()
    return OFFBOARDING_SUCCESS_MESSAGE

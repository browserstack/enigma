from Access.models import GroupAccessMapping, User, GroupV2, MembershipV2, AccessV2
from Access import helpers, views_helper, notifications, accessrequest_helper
from django.db import transaction
import datetime
import logging
from Access.views_helper import execute_group_access
from enigma_automation.settings import MAIL_APPROVER_GROUPS, PERMISSION_CONSTANTS
from . import helpers as helper
from Access.background_task_manager import revoke_request
import json

from .helpers import get_available_access_type

logger = logging.getLogger(__name__)

NEW_GROUP_CREATE_SUCCESS_MESSAGE = {
    "title": "New Group Request submitted",
    "msg": """A request for New Group with name {group_name} has been submitted for approval.
    You will be notified for any changes in request status.""",
}

ERROR_MESSAGE = "Error in request not found OR Invalid request type"

INTERNAL_ERROR_MESSAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while loading the page. Please contact admin",
}

USER_UNAUTHORIZED_MESSAGE = "User unauthorised to perform the action."
GROUP_ACCESS_MAPPING_NOT_FOUND = "Group Access Mapping not found in the database."

NEW_GROUP_CREATE_ERROR_GROUP_EXISTS = {
    "error_msg": "Invalid Group Name",
    "msg": "This group name already exists. Please choose a new name.",
}

REQUEST_NOT_FOUND_ERROR = "Error request not found OR Invalid request type"
SELF_APPROVAL_ERROR = (
    "You cannot approve your own request. Please ask other admins to do that"
)
GROUP_APPROVAL_ERROR = (
    "Error Occured while Approving group creation. Please contact admin - "
)
APPROVAL_ERROR = "Error Occured while Approving the request. Please contact admin - "
REQUEST_PROCESSING = "The Request {requestId} is now being processed"
REQUEST_PROCESSED_BY = "The Request {requestId} is already Processed By : {user}"

LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR = {
    "error_msg": "Invalid Group Name",
    "msg": "A group with name {group_name} doesn't exist.",
}

NON_OWNER_PERMISSION_DENIED_ERROR = {
    "error_msg": "Permission Denied",
    "msg": "Permission denied, requester is non owner",
}

UPDATE_OWNERS_REQUEST_ERROR = {
    "error_msg": "Bad request",
    "msg": "The requested URL is of POST method but was called with other.",
}

ALL_USERS_NOT_ADDED = {
    "title": "Some users could not be added.",
    "msg": "Users not added to group - {users_not_added} .Users added - {users_added}",
}


class GroupAccessExistsException(Exception):
    def __init__(self):
        self.message = "Group Access Exists"
        super().__init__(self.message)


ERROR_LOADING_PAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while loading the page. Please contact admin.",
}

ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE = {
    "title": "Request Submitted",
    "msg": "Once Approved the newly added members will be granted the same \
    permissions as the group",
}

GROUP_REQUEST_ERR_MSG = {
    "error_msg": "Invalid Request",
    "msg": "Please Contact Admin",
}

GROUP_REQUEST_EMPTY_FORM_ERR_MSG = {
    "error_msg": "The submitted form is empty. Tried direct access to group reqeust access page",
    "msg": "Error Occured while submitting your Request. Please contact the Admin",
}

GROUP_REQUEST_NO_GROUP_ERR_MSG = {
    "error_msg": "This Group is not yet approved",
    "msg": "This Group is not yet approved. Please contact admin for any queries ",
}

GROUP_REQUEST_SUCCESS_MSG = {
    "title": "Request Submitted {access_tag}",
    "msg": "Once approved you will receive the update",
}

DUPLICATE_GROUP_MEMBER_ADD_REQUEST = "User or User's, {user_emails} is already added to \
group/or pending approval for group addition"
NO_GROUP_ERROR = "There is no group named {group_name}. Please contact admin for \
    any queries."


def create_group(request):
    base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        data = request.POST
        auth_user = request.user
        group_members = []
        if data.get("selectAllUsers") == 'true':
            group_members = list(map(lambda user: user["email"], auth_user.user.get_active_users().values('email')))
        new_group_name = data.get("newGroupName").lower()
        reason = data.get("newGroupReason")
        needs_access_approve = (
            data.get("requiresAccessApprove")
            and data.get("requiresAccessApprove") == "true"
        )
        if not group_members and data.getlist("selectedUserList[]"):
            group_members = data.getlist("selectedUserList[]")
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Create New Group request.")
        context = {}
        context["error"] = {
            "error_msg": INTERNAL_ERROR_MESSAGE["error_msg"],
            "msg": INTERNAL_ERROR_MESSAGE["msg"],
        }
        return context

    if GroupV2.group_exists(new_group_name):
        # the group name is not unique.
        context = {}
        context["error"] = {
            "error_msg": NEW_GROUP_CREATE_ERROR_GROUP_EXISTS["error_msg"],
            "msg": NEW_GROUP_CREATE_ERROR_GROUP_EXISTS["msg"].format(
                group_name=new_group_name
            ),
        }
        return context

    new_group = GroupV2.create(
        name=new_group_name,
        requester=auth_user.user,
        description=reason,
        needs_access_approve=needs_access_approve,
        date_time=base_datetime_prefix,
    )

    new_group.add_member(
        user=auth_user.user,
        is_owner=True,
        requested_by=auth_user.user,
        reason="Group Owner. Added as initial group member by requester.",
        date_time=base_datetime_prefix,
    )

    if group_members:
        initial_members = list(map(str, group_members))
        new_group.add_members(
            users=User.objects.filter(email__in=initial_members),
            requested_by=auth_user.user,
        )
    else:
        initial_members = [auth_user.email]

    notifications.send_new_group_create_notification(
        auth_user, base_datetime_prefix, new_group, initial_members
    )

    context = {}
    context["status"] = {
        "title": NEW_GROUP_CREATE_SUCCESS_MESSAGE["title"],
        "msg": NEW_GROUP_CREATE_SUCCESS_MESSAGE["msg"].format(
            group_name=new_group.name
        ),
    }
    return context


def get_generic_access(group_mapping):
    access_details = {}
    access_module = helpers.get_available_access_module_from_tag(
        group_mapping.access.access_tag
    )
    if not access_module:
        return {}

    access_details = group_mapping.get_access_request_details(access_module)
    logger.debug("Generic access generated: " + str(access_details))
    return access_details


def get_group_access_list(auth_user, group_name):
    context = {}

    group = GroupV2.get_active_group_by_name(group_name)
    if not group:
        logger.debug(f"Group does not exist with group name {group_name}")
        context = {
            "error": {
                "error_msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["error_msg"],
                "msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["msg"].format(
                    group_name=group_name
                ),
            }
        }
        return context

    auth_user = auth_user
    if not auth_user.user.is_allowed_admin_actions_on_group(group):
        logger.debug("Permission denied, requester is non owner")
        context = {
            "error": {
                "error_msg": NON_OWNER_PERMISSION_DENIED_ERROR["error_msg"],
                "msg": NON_OWNER_PERMISSION_DENIED_ERROR["msg"],
            }
        }
        return context

    group_members = group.get_all_members().filter(status="Approved")
    group_members = [
        {
            "name": member.user.name,
            "email": member.user.email,
            "is_owner": member.is_owner,
            "current_state": member.user.current_state().capitalize(),
            "membership_id": member.membership_id,
        }
        for member in group_members
    ]
    context["userList"] = group_members
    context["groupName"] = group_name

    allow_revoke = False
    if auth_user.user.is_allowed_to_offboard_user_from_group(group):
        allow_revoke = True
    context["allowRevoke"] = allow_revoke

    group_mappings = group.get_active_accesses()
    context["genericAccesses"] = [
        get_generic_access(group_mapping) for group_mapping in group_mappings
    ]
    context["is_current_user_owner"] = group.member_is_owner(auth_user.user)
    if context["genericAccesses"] == [{}]:
        context["genericAccesses"] = []

    return context


def get_role_based_on_membership(group_detail):
    for user in group_detail["userList"]:
        if user["is_owner"]:
            user["role"] = "Owner"
        else:
            user["role"] = "Member"
    return group_detail


def update_owners(request, group_name):
    context = {}
    group = GroupV2.get_active_group_by_name(group_name)
    if not group:
        context = {
            "error": {
                "error_msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["error_msg"],
                "msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["msg"].format(
                    group_name=group_name
                ),
            }
        }
        return context

    logger.debug(
        "updating owners for group "
        + group.name
        + " requested by "
        + request.user.username
    )
    if not request.POST:
        logger.debug("Update Owners POST request not found.")
        return {"error": UPDATE_OWNERS_REQUEST_ERROR}

    data = request.POST
    data = dict(data.lists())
    if "owners" not in data:
        data["owners"] = []

    auth_user = request.user
    destination = [auth_user.user.email]

    group_members = group.get_all_approved_members().exclude(user=auth_user.user)

    # we will only get data["owners"] as owners who are checked in UI
    # (exluding disabled checkbox owner who requested the change)
    with transaction.atomic():
        for membership in group_members:
            if membership.user.email in data["owners"]:
                membership.is_owner = True
                destination.append(membership.user.email)
            else:
                membership.is_owner = False
            membership.save()

    logger.debug("Owners changed to " + ", ".join(destination))
    destination.extend(MAIL_APPROVER_GROUPS)
    notifications.send_group_owners_update_mail(
        destination, group_name, auth_user.user.email
    )
    context["notification"] = "Owner's updated"

    return context


def getGroupMembers(groupMembers):
    return [
        {
            "name": member.user.name,
            "email": member.user.email,
            "is_owner": member.is_owner,
            "current_state": member.user.current_state(),
            "membership_id": member.membership_id,
        }
        for member in groupMembers
    ]


def approve_new_group_request(auth_user, group_id):
    try:
        group = GroupV2.get_pending_group(group_id=group_id)
    except Exception as e:
        logger.error("Error in approveNewGroup request, Unable to fetch group" + str(e))
        context = {}
        context["error"] = INTERNAL_ERROR_MESSAGE["msg"]
        return context
    if not group:
        logger.error("No pending group found, Unable to fetch group" + str(e))
        context = {}
        context["error"] = REQUEST_NOT_FOUND_ERROR
        return context

    try:
        if group.is_self_approval(approver=auth_user.user):
            context = {}
            context["error"] = SELF_APPROVAL_ERROR
            return context
        else:
            context = {}
            context["msg"] = REQUEST_PROCESSING.format(requestId=group_id)

            with transaction.atomic():
                group.approve(approved_by=auth_user.user)
                group.approve_all_pending_users(approved_by=auth_user.user)
            initial_members = group.get_all_members()
            initial_member_names = [user.user.name for user in initial_members]
            try:
                notifications.send_new_group_approved_notification(
                    group=group,
                    group_id=group_id,
                    initial_member_names=initial_member_names,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(
                    "Group approved, but Error in sending group approval notification"
                )
            logger.debug(
                "Approved group creation for - "
                + group_id
                + " - Approver="
                + auth_user.username
            )
            if initial_members:
                logger.debug(
                    "Members added to group - "
                    + group_id
                    + " ="
                    + ", ".join(initial_member_names)
                )
            return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Approving New Group request.")
        context = {}
        context["error"] = GROUP_APPROVAL_ERROR + str(e)
        return context


def get_user_group(request, group_name):
    try:
        context = {}
        group = GroupV2.get_approved_group_by_name(group_name=group_name)
        if not group:
            logger.debug(
                "addUserToGroup-- url received a bad group name requester-"
                + request.user.username
            )
            context = {}
            context["error"] = {
                "title": "Invalid Group",
                "msg": NO_GROUP_ERROR.format(group_name=group_name),
            }
            return context

        group_members = group.get_all_approved_members().only("user")
        auth_user = request.user

        if not auth_user.user.is_allowed_admin_actions_on_group(group):
            raise Exception("Permission denied, you're not owner of this group")

        group_members = get_users_from_groupmembers(group_members)
        context["groupMembers"] = group_members
        context["groupName"] = group_name
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context["error"] = {
            "error_msg": ERROR_LOADING_PAGE["error_msg"],
            "msg": ERROR_LOADING_PAGE["msg"].format(exception=str(e)),
        }
        return context


def get_users_from_groupmembers(group_members):
    return [member.user for member in group_members]


def add_user_to_group(request):
    try:
        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        data = request.POST
        group = GroupV2.get_approved_group_by_name(data.get("groupName"))
        if not group:
            context = {}
            context["error"] = {"error_msg": "Request failed", "msg": "Group not found"}
            return context

        if not request.user.user.is_allowed_admin_actions_on_group(group):
            context = {}
            context["error"] = {
                "error_msg": NON_OWNER_PERMISSION_DENIED_ERROR["error_msg"],
                "msg": NON_OWNER_PERMISSION_DENIED_ERROR["msg"],
            }
            return context

        selected_users_list = json.loads(data.get("selectedUserList"))

        duplicate_request_emails = _check_if_members_in_group(
            group=group, selected_members=selected_users_list
        )

        if duplicate_request_emails:
            context = {}
            msg = DUPLICATE_GROUP_MEMBER_ADD_REQUEST.format(
                user_emails=duplicate_request_emails
            )
            context["error"] = {"error_msg": "Duplicate Request", "msg": msg}
            return context

        selected_users = get_selected_users_by_email(selected_users_list)

        users_added = {}
        user_not_added = []
        for user in selected_users:
            try:
                with transaction.atomic():
                    membership = group.add_member(
                        user=user,
                        requested_by=request.user.user,
                        reason=data.get("memberReason"),
                        date_time=base_datetime_prefix,
                    )
                    membership_id = membership.membership_id
                    if not group.needsAccessApprove:
                        context = {}
                        context["accessStatus"] = {
                            "msg": REQUEST_PROCESSING.format(requestId=membership_id),
                            "desc": (
                                "A email will be sent after the requested access are granted"
                            ),
                        }
                        user_mappings_list = views_helper.generate_user_mappings(
                            membership.user, group, membership
                        )
                        membership.approve(approver=request.user.user)
                        views_helper.execute_group_access(
                            user_mappings_list=user_mappings_list
                        )
                        logger.debug(
                            "Process has been started for the Approval of request - "
                            + membership_id
                            + " - Approver="
                            + request.user.username
                        )
                    users_added[user.email] = membership_id
            except Exception as e:
                logger.debug(
                    "Error adding User: %s could not be added to the group, Exception: %s ",
                    user.email,
                    str(e),
                )
                user_not_added.append(user.email)
        if group.needsAccessApprove:
            notifications.send_mail_for_member_approval(
                ",".join(user_not_added),
                str(request.user),
                data.get("groupName"),
                data.get("memberReason"),
            )
            context = {}
            context["status"] = {
                "title": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["title"],
                "msg": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["msg"],
            }

        else:
            membership = MembershipV2.get_membership(membership_id=membership_id)
            notifications.send_mulitple_membership_accepted_notification(
                users_added,
                data.get("groupName"),
                membership,
            )
            if len(selected_users) - len(users_added) == 0:
                context = {}
                context["status"] = {
                    "title": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["title"],
                    "msg": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["msg"],
                }
            else:
                context = {}
                context["status"] = {
                    "title": ALL_USERS_NOT_ADDED["title"],
                    "msg": ALL_USERS_NOT_ADDED["msg"].format(
                        user_not_added=",".join(user_not_added),
                        users_added=",".join(users_added),
                    ),
                }

        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context["error"] = {
            "error_msg": ERROR_LOADING_PAGE["error_msg"],
            "msg": ERROR_LOADING_PAGE["msg"],
        }
        return context


def _check_if_members_in_group(group, selected_members):
    group_members_email = group.get_approved_and_pending_member_emails()
    duplicate_request_emails = set(selected_members).intersection(
        set(group_members_email)
    )
    return duplicate_request_emails


def _check_if_members_in_group(group, selected_members):
    group_members_email = group.get_approved_and_pending_member_emails()
    duplicate_request_emails = set(selected_members).intersection(
        set(group_members_email)
    )
    return duplicate_request_emails


def is_user_in_group(user_email, group_members_email):
    return user_email in group_members_email


def accept_member(auth_user, requestId, shouldRender=True):
    try:
        membership = MembershipV2.get_membership(membership_id=requestId)
        if not membership:
            logger.error("Error request not found OR Invalid request type")
            context = {}
            context["error"] = REQUEST_NOT_FOUND_ERROR + str(e)
            return context
    except Exception as e:
        context["error"] = {
            "error_msg": INTERNAL_ERROR_MESSAGE["error_msg"],
            "msg": INTERNAL_ERROR_MESSAGE["msg"],
        }

    try:
        if not membership.is_pending():
            logger.warning(
                "An Already Approved/Declined/Processing Request was accessed by - "
                + auth_user.username
            )
            context = {}
            context["error"] = REQUEST_PROCESSED_BY.format(
                requestId=requestId, user=membership.approver.user.username
            )
            return context
        elif membership.is_self_approval(approver=auth_user.user):
            context = {}
            context["error"] = SELF_APPROVAL_ERROR
            return context
        else:
            context = {}
            context["msg"] = REQUEST_PROCESSING.format(requestId=requestId)
            with transaction.atomic():
                membership.approve(auth_user.user)
                group = membership.group
                user = membership.user
                user_mappings_list = views_helper.generate_user_mappings(
                    user, group, membership
                )

            execute_group_access(user_mappings_list)

            notifications.send_membership_accepted_notification(
                user=user, group=group, membership=membership
            )
            logger.debug(
                "Process has been started for the Approval of request - "
                + requestId
                + " - Approver="
                + auth_user.username
            )
            return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Accept of New Member in Group request.")
        context = {}
        context["error"] = APPROVAL_ERROR + str(e)
        return context


def get_group_access(form_data, auth_user):
    data = dict(form_data.lists())
    group_name = data["groupName"][0]
    context = {}
    context["accesses"] = []

    group = GroupV2.get_active_group_by_name(group_name=group_name)
    validation_error = validate_group_access_create_request(
        group=group, auth_user=auth_user
    )
    if validation_error:
        context["status"] = validation_error
        return context

    access_module_list = data["accessList"]
    for module_value in access_module_list:
        module = helper.get_available_access_modules()[module_value]
        try:
            extra_fields = module.get_extra_fields()
        except Exception:
            extra_fields = []

        context["genericForm"] = True
        context["accesses"].append(
            {
                "formDesc": module.access_desc(),
                "accessTag": module.tag(),
                "accessTypes": module.access_types(),
                "accessRequestData": module.access_request_data(
                    form_data, is_group=True
                ),
                "extraFields": extra_fields,
                "accessRequestPath": module.fetch_access_request_form_path(),
            }
        )
    context["groupName"] = group_name
    return context


def save_group_access_request(form_data, auth_user):
    json_response = _validate_group_access_request(form_data, auth_user)
    if json_response:
        return json_response

    access_request = dict(form_data.lists())
    group_name = form_data.get("groupName")
    access_tag = form_data.get("access_tag")

    group = GroupV2.get_active_group_by_name(group_name=group_name)

    validation_error = validate_group_access_create_request(
        group=group, auth_user=auth_user
    )
    if validation_error:
        return validation_error

    access_module = helper.get_available_access_modules()[access_tag]

    module_access_labels = access_module.validate_request(form_data, auth_user.user)

    extra_fields = accessrequest_helper.get_extra_fields(access_request)
    extra_field_labels = accessrequest_helper.get_extra_field_labels(access_module)

    if extra_fields and extra_field_labels:
        for field in extra_field_labels:
            module_access_labels[0][field] = extra_fields[0]
            extra_fields = extra_fields[1:]

    request_id = (
        group.name
        + "-"
        + access_tag
        + "-"
        + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    )
    with transaction.atomic():
        for labelIndex, access_label in enumerate(module_access_labels):
            request_id = request_id + "_" + str(labelIndex)
            try:
                group_access_create_error = _create_group_access_mapping(
                    group=group,
                    user=auth_user.user,
                    request_id=request_id,
                    access_tag=access_tag,
                    access_label=access_label,
                    access_reason=access_request["accessReason"],
                )
            except GroupAccessExistsException:
                error_msg = "Duplicate request found" + json.dumps(access_label)
                logger.info(f"{error_msg}")
        json_response["status"] = {
            "title": GROUP_REQUEST_SUCCESS_MSG["title"].format(
                access_tag=access_tag
            ),
            "msg": GROUP_REQUEST_SUCCESS_MSG["msg"]
        }
        # email_destination = access_module.get_approvers()
        # member_list = group.get_all_approved_members()
        # notifications.send_group_access_add_email(
        #     destination=email_destination,
        #     group_name=group_name,
        #     requester=auth_user.user.email,
        #     request_id=request_id,
        #     member_list=member_list,
        # )
    return json_response


def _create_group_access_mapping(
    group, user, request_id, access_tag, access_label, access_reason
):
    access = AccessV2.get(access_tag=access_tag, access_label=access_label)
    if not access:
        access = AccessV2.create(access_tag=access_tag, access_label=access_label)
    else:
        if group.access_mapping_exists(access):
            raise GroupAccessExistsException()
    group.add_access(
        request_id=request_id,
        requested_by=user,
        request_reason=access_reason,
        access=access,
    )


def _validate_group_access_request(form_data, auth_user):
    json_response = {}
    if not form_data:
        json_response["error"] = {
            "error_msg": GROUP_REQUEST_ERR_MSG["error_msg"],
            "msg": GROUP_REQUEST_ERR_MSG["msg"]
        }
        logger.debug("Tried a direct Access to groupAccessRequest by-" + auth_user.username)
        return json_response

    if not form_data.get("groupName") or not form_data.get("access_tag") or not form_data.get("accessReason"):
        json_response["error"] = {
            "error_msg": GROUP_REQUEST_EMPTY_FORM_ERR_MSG["error_msg"],
            "msg": GROUP_REQUEST_EMPTY_FORM_ERR_MSG["msg"]
        }
    return json_response


def validate_group_access_create_request(group, auth_user):
    json_response = {}
    if not group:
        json_response["error"] = {
            "error_msg": GROUP_REQUEST_NO_GROUP_ERR_MSG["error_msg"],
            "msg": GROUP_REQUEST_NO_GROUP_ERR_MSG["msg"]
        }
        return json_response

    if not auth_user.user.is_allowed_admin_actions_on_group(group):
        json_response["error"] = {
            "error_msg": NON_OWNER_PERMISSION_DENIED_ERROR["error_msg"],
            "msg": NON_OWNER_PERMISSION_DENIED_ERROR["msg"]
        }
    return json_response


def revoke_user_access(user, access, revoker, decline_message):
    user_identity = user.get_active_identity(access.access_tag)
    user_identity.decline_non_approved_access_mapping(access, decline_message)
    access_mapping = user_identity.get_granted_access_mapping(access).first()
    if not access_mapping:
        return False
    revoke_request(access_mapping, revoker)

def remove_member(request, auth_user):
    try:
        membership_id = request.POST.get("membershipId")
        if not membership_id:
            raise Exception("Membership Id is not loaded.")
        membership = MembershipV2.get_membership(membership_id)

        if not auth_user.user.is_allowed_admin_actions_on_group(membership.group):
            logger.exception("Permission denied, you're not owner of this group")
            raise Exception("Permision Denied. You're not owner of this group")

        if membership.user == auth_user.user:
            raise Exception("User cannot remove itself")

    except Exception as exc:
        logger.error("Membership id not found in request")
        logger.exception(str(exc))
        return {"error": ERROR_MESSAGE}

    user = membership.user

    group_accesses = [
        mapping.access for mapping in membership.group.get_approved_accesses()
    ]

    other_memberships_groups = (
        user.get_all_approved_memberships()
        .exclude(group=membership.group)
        .values_list("group", flat=True)
    )
    other_group_accesses = []

    for group in other_memberships_groups:
        mapping = group.get_approved_accesses()
        other_group_accesses.append(mapping.access)

    accesses = list(set(group_accesses) - set(other_group_accesses))

    with transaction.atomic():
        for access in accesses:
            revoke_user_access(user, access, request.user.user, "User removed from the group")

    membership.revoke_membership()

    return {"message": "Successfully removed user from group"}


def access_exist_in_other_groups_of_user(membership, group, access):
    other_memberships = (
        membership.user.get_all_approved_memberships()
        .exclude(group=membership.group)
    )
    for membership in other_memberships:
        if membership.group.check_access_exist(access):
            return True

    return False


def revoke_access_from_group(request):
    try:
        request_id = request.POST.get("request_id")
        if not request_id:
            logger.debug("Cannot find request_id in the http request.")
            return {"error": ERROR_MESSAGE}

        mapping = GroupAccessMapping.get_by_id(request_id)
        if not mapping:
            logger.debug("Group Access Mapping not found in the database")
            return {"error": GROUP_ACCESS_MAPPING_NOT_FOUND}
    except Exception as e:
        logger.exception(str(e))
        return {"error": ERROR_MESSAGE}

    group = mapping.group
    auth_user = request.user
    if not (auth_user.user.has_permission("ALLOW_USER_OFFBOARD") or group.member_is_owner(auth_user.user)):
        return {"error": USER_UNAUTHORIZED_MESSAGE}

    revoke_access_memberships = []
    for membership in group.get_all_approved_members():
        if access_exist_in_other_groups_of_user(membership, group, mapping.access):
            continue
        revoke_access_memberships.append(membership)

    with transaction.atomic():
        for membership in revoke_access_memberships:
            revoke_user_access(membership.user, mapping.access, auth_user.user, "Access revoked for the group")

    mapping.mark_revoked(auth_user.user)

    return {"message": "Successfully initiated the revoke"}


def get_selected_users_by_email(user_emails):
    selected_users = User.get_users_by_emails(emails=user_emails)
    selected_users_email = {user.email: user for user in selected_users}
    not_found_emails = [
        email for email in user_emails if email not in selected_users_email
    ]

    if len(not_found_emails) == 1:
        raise User.DoesNotExist(
            "User with email {} does not exist".format(not_found_emails)
        )
    elif len(not_found_emails) > 1:
        raise User.DoesNotExist(
            "Users with email {} are not found".format(not_found_emails)
        )
    return selected_users


def get_group_status_list(selected_list):
    status_list = []
    for status in MembershipV2.STATUS:
        if status[0] not in selected_list:
            status_list.append(status[0])

    return status_list


def get_group_member_access_type(selected_list):
    access_type = []
    all_types = get_available_access_type()
    for type in all_types:
        if type not in selected_list:
            access_type.append(type)

    return access_type


def get_user_states(selected_list):
    user_state = []
    for state in User.USER_STATUS_CHOICES:
        current_state = state[1].capitalize()
        if current_state not in selected_list:
            user_state.append(current_state)

    return user_state


def get_access_types(group_mappings):
    status_list = []

    for group_mapping in group_mappings:
        access_module = helpers.get_available_access_module_from_tag(
            group_mapping.access.access_tag
        )
        if not access_module:
            break
        status_list.append(access_module.access_desc())

    return set(status_list)


def get_group_member_role_list(selected_list):
    roles = ["Member", "Owner"]
    role_list = []
    for role in roles:
        if role not in selected_list:
            role_list.append(role)

    return role_list

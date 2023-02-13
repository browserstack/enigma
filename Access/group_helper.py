from Access.models import User, GroupV2, MembershipV2, AccessV2
from Access import helpers, views_helper, notifications, accessrequest_helper
from django.db import transaction
import datetime
import logging
from Access.views_helper import execute_group_access
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS, PERMISSION_CONSTANTS
from . import helpers as helper
from Access.background_task_manager import background_task
import json

logger = logging.getLogger(__name__)

NEW_GROUP_CREATE_SUCCESS_MESSAGE = {
    "title": "New Group Request submitted",
    "msg": """A request for New Group with name {group_name} has been submitted for approval.
    You will be notified for any changes in request status.""",
}

ERROR_MESSAGE = "Error in request not found OR Invalid request type"

NEW_GROUP_CREATE_ERROR_MESSAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while loading the page. Please contact admin",
}

NEW_GROUP_CREATE_ERROR_GROUP_EXISTS = {
    "error_msg": "Invalid Group Name",
    "msg": "A group with name {group_name} already exists. Please choose a new name.",
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
    "msg": "A group with {group_name} doesn't exist.",
}

LIST_GROUP_ACCESSES_PERMISSION_DENIED = {
    "error_msg": "Permission Denied",
    "msg": "Permission denied, requester is non owner",
}

UPDATE_OWNERS_REQUEST_ERROR = {
    "error_msg": "Bad request",
    "msg": "The requested URL is of POST method but was called with other.",
}

class GroupAccessExistsException(Exception):
    def __init__(self):
            self.message = "Group Access Exists"
            super().__init__(self.message)    

ERROR_LOADING_PAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while loading the page. Please contact admin, {exception}"
}

ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE = {
    "title": "Request Submitted",
    "msg": "Once Approved the newly added members will be granted the same \
    permissions as the group",
}

DUPLICATE_GROUP_MEMBER_ADD_REQUEST = "User {user_email} is already added to \
group/or pending approval for group addition"
DUPLICATE_GROUP_MEMBERS_ADD_REQUEST = "Users {user_emails} are already added to \
    group/or pending approval for group addition"
NO_GROUP_ERROR = "There is no group named {group_name}. Please contact admin for \
    any queries."


class GroupAccessExistsException(Exception):
    def __init__(self):
        self.message = "Group Access Exists"
        super().__init__(self.message)


def create_group(request):
    base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        data = request.POST
        data = dict(data.lists())
        new_group_name = (data["newGroupName"][0]).lower()
        reason = data["newGroupReason"][0]
        needs_access_approve = (
            "requiresAccessApprove" in data
            and data["requiresAccessApprove"][0] == "true"
        )
        if "selectedUserList" in data:
            selected_users = data["selectedUserList"]
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Create New Group request.")
        context = {}
        context["error"] = {
            "error_msg": NEW_GROUP_CREATE_ERROR_MESSAGE["error_msg"],
            "msg": NEW_GROUP_CREATE_ERROR_MESSAGE["msg"],
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
        requester=request.user.user,
        description=reason,
        needsAccessApprove=needs_access_approve,
    )

    new_group.add_member(
        user=request.user.user,
        is_owner=True,
        requested_by=request.user.user,
        reason="Group Owner. Added as initial group member by requester.",
        date_time=base_datetime_prefix,
    )

    if "selectedUserList" in data:
        initial_members = list(map(str, selected_users))
        new_group.add_members(
            users=User.objects.filter(email__in=initial_members),
            requested_by=request.user.user,
        )
    else:
        initial_members = [request.user.email]

    notifications.send_new_group_create_notification(
        request.user, base_datetime_prefix, new_group, initial_members
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

    access_details = group_mapping.getAccessRequestDetails(access_module)
    logger.debug("Generic access generated: " + str(access_details))
    return access_details


def get_group_access_list(request, group_name):
    context = {}
    group = GroupV2.get_active_group_by_name(group_name)
    if not group:
        logger.debug(f"Group does not exist with group name {group_name}")
        context = {
            "error": {
                "error_msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["error_msg"],
                "msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["msg"],
            }
        }
        return context

    group_members = group.get_all_members().filter(status="Approved")
    auth_user = request.user

    if not auth_user.user.is_allowed_admin_actions_on_group(group):
        logger.debug("Permission denied, requester is non owner")
        context = {
            "error": {
                "error_msg": LIST_GROUP_ACCESSES_PERMISSION_DENIED["error_msg"],
                "msg": LIST_GROUP_ACCESSES_PERMISSION_DENIED["msg"],
            }
        }
        return context

    group_members = [
        {
            "name": member.user.name,
            "email": member.user.email,
            "is_owner": member.is_owner,
            "current_state": member.user.current_state(),
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
    if context["genericAccesses"] == [{}]:
        context["genericAccesses"] = []

    return context


def update_owners(request, group_name):
    context = {}
    group = GroupV2.get_active_group_by_name(group_name)
    if not group:
        context = {
            "error": {
                "error_msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["error_msg"],
                "msg": LIST_GROUP_ACCESSES_GROUP_DONT_EXIST_ERROR["msg"],
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

    group_members = (
        group.get_all_members().filter(status="Approved").exclude(user=auth_user.user)
    )

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


def check_user_is_group_owner(user_name, group):
    user = User.objects.get(user__username=user_name)
    try:
        return MembershipV2.objects.get(
            user=user, status="Approved", group__name=group.name
        ).is_owner
    except Exception:
        return False


def approve_new_group_request(request, group_id):

    try:
        group = GroupV2.get_pending_group(group_id=group_id)
    except Exception as e:
        logger.error(
            "Error in approveNewGroup request, Not found OR Invalid request type"
            + str(e)
        )
        context = {}
        context["error"] = REQUEST_NOT_FOUND_ERROR
        return context
    try:
        if group.is_self_approval(approver=request.user.user):
            context = {}
            context["error"] = SELF_APPROVAL_ERROR
            return context
        else:
            context = {}
            context["msg"] = REQUEST_PROCESSING.format(requestId=group_id)

            with transaction.atomic():
                group.approve(approved_by=request.user.user)
                group.approve_all_pending_users(approved_by=request.user.user)
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
                + request.user.username
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
            context["status"] = {
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
            "msg": ERROR_LOADING_PAGE["msg"].format(exception=str(e))
        }
        return context


def get_users_from_groupmembers(group_members):
    return [member.user for member in group_members]


def add_user_to_group(request):
    try:
        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        data = request.POST
        data = dict(data.lists())
        group = GroupV2.get_approved_group_by_name(data["groupName"][0])
        if not group:
            context = {}
            context["error"] = {
                "error_msg": "Request failed",
                "msg": "Group not found"
            }
            return context

        group_members_email = group.get_approved_and_pending_member_emails()
        auth_user = request.user

        if not auth_user.user.is_allowed_admin_actions_on_group(group):
            raise Exception("Permission denied, requester is non owner")

        duplicate_request_emails = set(
            data["selectedUserList"]).intersection(set(group_members_email))

        if duplicate_request_emails:
            context = {}
            if len(duplicate_request_emails) == 1:
                msg = DUPLICATE_GROUP_MEMBER_ADD_REQUEST.format(
                    user_email=duplicate_request_emails)
            else:
                msg = DUPLICATE_GROUP_MEMBERS_ADD_REQUEST.format(
                    user_emails=duplicate_request_emails)

            context["error"] = {
                "error_msg": "Duplicate Request",
                "msg": msg
            }
            return context

        selected_users = get_selected_users_by_email(data["selectedUserList"])
        new_memberships = []

        with transaction.atomic():
            for user in selected_users:
                member = group.add_member(user=user, requested_by=request.user.user,
                                        reason=data["memberReason"][0],
                                        date_time=base_datetime_prefix)
                new_memberships.append(member)

        for membership in new_memberships:
            membership_id = membership.membership_id
            if not group.needsAccessApprove:
                context = {}
                context["accessStatus"] = {
                    "msg": REQUEST_PROCESSING.format(requestId=membership_id),
                    "desc": (
                        "A email will be sent after the requested access are granted"
                    ),
                }
                membership.approve(approver=request.user.user)
                user_mappings_list = views_helper.generate_user_mappings(
                    membership.user, group, membership
                )

                views_helper.execute_group_access(user_mappings_list=user_mappings_list)
                logger.debug(
                    "Process has been started for the Approval of request - "
                    + membership_id
                    + " - Approver="
                    + request.user.username
                )

        notifications.send_mail_for_member_approval(
            user.email,
            str(request.user),
            data["groupName"][0],
            data["memberReason"][0],
        )

        context = {}
        context["status"] = {
            "title": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["title"],
            "msg": ADD_MEMBER_REQUEST_SUBMITTED_MESSAGE["msg"]
        }
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context["error"] = {
            "error_msg": ERROR_LOADING_PAGE["error_msg"],
            "msg": ERROR_LOADING_PAGE["msg"].format(exception=str(e))
        }
        return context


def is_user_in_group(user_email, group_members_email):
    return user_email in group_members_email


def accept_member(request, requestId, shouldRender=True):
    try:
        membership = MembershipV2.get_membership(membership_id=requestId)
    except Exception as e:
        logger.error("Error request not found OR Invalid request type")
        context = {}
        context["error"] = REQUEST_NOT_FOUND_ERROR + str(e)
        return context
    try:
        if membership.is_already_processed():
            logger.warning(
                "An Already Approved/Declined/Processing Request was accessed by - "
                + request.user.username
            )
            context = {}
            context["error"] = REQUEST_PROCESSED_BY.format(
                requestId=requestId, user=membership.approver.user.username
            )
            return context
        elif membership.is_self_approval(approver=request.user.user):
            context = {}
            context["error"] = SELF_APPROVAL_ERROR
            return context
        else:
            context = {}
            context["msg"] = REQUEST_PROCESSING.format(requestId=requestId)
            with transaction.atomic():
                membership.approve(request.user.user)
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
                + request.user.username
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
    access_request = dict(form_data.lists())
    group_name = access_request["groupName"][0]
    group = GroupV2.get_active_group_by_name(group_name=group_name)

    context = {"status_list": []}
    validation_error = validate_group_access_create_request(
        group=group, auth_user=auth_user
    )
    if validation_error:
        context["status"] = validation_error

    for accessIndex, access_type in enumerate(access_request["accessType"]):
        access_module = helper.get_available_access_modules()[access_type]
        access_labels = accessrequest_helper.validate_access_labels(
            access_labels_json=access_request["accessLabel"][accessIndex],
            access_type=access_type,
        )
        extra_fields = accessrequest_helper.get_extra_fields(access_request)
        extra_field_labels = accessrequest_helper.get_extra_field_labels(access_module)

        module_access_labels = access_module.validate_request(
            access_labels, auth_user, is_group=False
        )
        if extra_fields and extra_field_labels:
            for field in extra_field_labels:
                module_access_labels[0][field] = extra_fields[0]
                extra_fields = extra_fields[1:]

        request_id = (
            auth_user.username
            + "-"
            + access_type
            + "-"
            + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        )
        with transaction.atomic():
            for labelIndex, access_label in enumerate(module_access_labels):
                request_id = request_id + "_" + str(labelIndex)
                try:
                    _create_group_access_mapping(
                        group=group,
                        user=auth_user.user,
                        request_id=request_id,
                        access_type=access_type,
                        access_label=access_label,
                        access_reason=access_request["accessReason"],
                    )
                    context["status_list"].append(
                        {
                            "title": request_id + " Request Submitted",
                            "msg": "Once approved you will receive the update "
                            + json.dumps(access_label),
                        }
                    )
                except GroupAccessExistsException:
                    context["status_list"].append(
                        {
                            "title": request_id + " Request Submitted",
                            "msg": "Once approved you will receive the update "
                            + json.dumps(access_label),
                        }
                    )
        email_destination = access_module.get_approvers()
        member_list = group.get_all_approved_members()
        notifications.send_group_access_add_email(
            destination=email_destination,
            group_name=group_name,
            requester=auth_user.user.email,
            request_id=request_id,
            member_list=member_list,
        )

    return context


def _create_group_access_mapping(
    group, user, request_id, access_type, access_label, access_reason
):
    access = AccessV2.get(access_type=access_type, access_label=access_label)
    if not access:
        access = AccessV2.objects.create(
            access_tag=access_type, access_label=access_label
        )
    else:
        if group.check_access_exist(access):
            raise GroupAccessExistsException()
    group.add_access(
        request_id=request_id,
        requested_by=user,
        request_reason=access_reason,
        access=access,
    )


def validate_group_access_create_request(group, auth_user):
    if not group:
        logger.exception("This Group is not yet approved")
        return {"title": "Permisison Denied", "msg": "This Group is not yet approved"}

    if not (group.is_owner(auth_user.user) or auth_user.is_superuser):
        logger.exception("Permission denied, you're not owner of this group")
        return {"title": "Permision Denied", "msg": "You're not owner of this group"}
    return None


def remove_member(request):
    try:
        membership_id = request.POST.get("membershipId")
        if not membership_id:
            raise ("Membership Id is not loaded.")
        membership = MembershipV2.get_membership(membership_id)
    except Exception as e:
        logger.error("Membership id not found in request")
        logger.exception(str(e))
        return {"error": ERROR_MESSAGE}

    user = membership.user

    revoke_group_accesses = [
        mapping.access for mapping in membership.group.get_approved_accesses()
    ]

    other_memberships_groups = (
        user.get_all_memberships()
        .exclude(group=membership.group)
        .values_list("group", flat=True)
    )
    other_group_accesses = []

    for group in other_memberships_groups:
        mapping = group.get_approved_accesses()
        other_group_accesses.append(mapping.access)

    revoke_accesses = list(set(revoke_group_accesses) - set(other_group_accesses))

    for access in revoke_accesses:
        user_identity = user.get_active_identity(access.access_tag)
        user_identity.decline_non_approved_access_mapping(access)
        user_identity.offboarding_approved_access_mapping(access)
        background_task(
            "run_access_revoke",
            json.dumps(
                {
                    "request_id": user_identity.get_granted_access_mapping(access)
                    .first()
                    .request_id,
                    "revoker_email": request.user.user.email,
                }
            ),
        )

    membership.revoke_membership()

    return {"message": "Successfully removed user from group"}


def get_selected_users_by_email(user_emails):
    selected_users = User.get_users_by_email(emails=user_emails)
    selected_users_email = {user.email: user for user in selected_users}
    not_found_emails = [email for email in user_emails if email not in selected_users_email]

    if len(not_found_emails) == 1:
        raise User.DoesNotExist("User with email {} does not exist".format(not_found_emails))
    elif len(not_found_emails) > 1:
        raise User.DoesNotExist("Users with email {} are not found".format(not_found_emails))
    return selected_users


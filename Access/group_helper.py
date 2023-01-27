from Access.models import User, GroupV2, MembershipV2, Role
from Access import helpers, views_helper, notifications
import datetime
import logging
from bootprocess import general
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS, PERMISSION_CONSTANTS
import threading

logger = logging.getLogger(__name__)

NEW_GROUP_CREATE_SUCCESS_MESSAGE = {
    "title": "New Group Request submitted",
    "msg": """A request for New Group with name {group_name} has been submitted for approval.
    You will be notified for any changes in request status.""",
}

NEW_GROUP_CREATE_ERROR_MESSAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while loading the page. Please contact admin",
}

NEW_GROUP_CREATE_ERROR_GROUP_EXISTS = {
    "error_msg": "Invalid Group Name",
    "msg": "A group with name {group_name} already exists. Please choose a new name.",
}


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


def getAccessDetails(eachAccess):
    accessDetails = {}
    access_label = eachAccess.access_label
    logger.debug(accessDetails)
    for eachAccessModule in helpers.getAvailableAccessModules():
        if eachAccess.access_tag == eachAccessModule.tag():
            accessDetails["accessType"] = eachAccessModule.access_desc()
            accessDetails["accessCategory"] = eachAccessModule.get_label_desc(
                access_label
            )
            accessDetails["accessMeta"] = eachAccessModule.get_label_meta(access_label)

            if (
                eachAccess.access_tag == "other"
                and "grant_emails" in eachAccess.access_label
                and type(eachAccess.access_label["grant_emails"]) == list
            ):
                accessDetails["revokeOwner"] = ",".join(
                    eachAccess.access_label["grant_emails"]
                )
                accessDetails["grantOwner"] = accessDetails["revokeOwner"]
            else:
                accessDetails["revokeOwner"] = ",".join(eachAccessModule.revoke_owner())
                accessDetails["grantOwner"] = ",".join(eachAccessModule.grant_owner())
    logger.debug(accessDetails)
    return accessDetails


def getGroupAccessList(request, groupName):
    try:
        context = {}
        group = GroupV2.objects.get(name=groupName, status="Approved")
        groupMembers = group.get_group_members()
        ownerEmails = groupMembers.filter(is_owner=True).values_list(
            "user__user__email", flat=True
        )
        is_approver = User.is_approver(request.user.user.email)
        if request.user.user.email not in ownerEmails and not (
            request.user.is_superuser or request.user.user.is_ops or is_approver
        ):
            raise Exception("Permission denied, requester is non owner")

        groupMembers = [
            {
                "name": member.user.name,
                "email": member.user.email,
                "is_owner": member.is_owner,
                "current_state": member.user.current_state(),
                "membership_id": member.membership_id,
            }
            for member in groupMembers
        ]
        context["userList"] = groupMembers
        context["groupName"] = groupName

        groupMappings = group.get_all_accesses()
        accessV2s = [
            (groupMapping.access, groupMapping.request_id, groupMapping.status)
            for groupMapping in groupMappings
        ]

        allow_revoke = False
        if (
            request.user.user.email in ownerEmails
            or request.user.check_user_permissions("ALLOW_USER_OFFBOARD")
        ):
            allow_revoke = True
        context["allowRevoke"] = allow_revoke
        if accessV2s:
            split_details = []
            access_details = list(
                map(getAccessDetails, [access[0] for access in accessV2s])
            )
            for idx, each_access in enumerate(access_details):
                each_access["request_id"] = accessV2s[idx][1]
                each_access["status"] = accessV2s[idx][2]
                split_details.append(each_access)
            context["genericAccesses"] = split_details
    except Exception as e:
        logger.error(f"Error while getting the users and access of the group: {str(e)}")
        context = {
            "error": {
                "error_msg": "Internal Error",
                "msg": f"Error while getting the users and access of the group: {str(e)}",
            }
        }

    return context


def updateOwner(request, groupName):
    try:
        context = {}
        group = GroupV2.objects.get(name=groupName, status="Approved")
        logger.debug(
            "updating owners for group "
            + group.name
            + " requested by "
            + request.user.username
        )
        data = request.POST
        data = dict(data.lists())

        if "owners" not in data:
            data["owners"] = []
        destination = [request.user.user.email]

        groupMembers = group.get_group_members().exclude(user=request.user.user)

        # we will only get data["owners"] as owners who are checked in UI
        # (exluding disabled checkbox owner who requested the change)
        for membership_obj in groupMembers:
            if membership_obj.user.email is request.user.user.email:
                continue
            if membership_obj.user.email in data["owners"]:
                membership_obj.is_owner = True
                destination.append(membership_obj.user.email)
            else:
                membership_obj.is_owner = False
            membership_obj.save()

        logger.debug("Owners changed to " + ", ".join(destination))
        subject = "Enigma Group '" + group.name + "' owners changed"
        body = "\nGroup Name :- {} \nupdated owners :- {} \nupdated by :- {}".format(
            group.name, ", ".join(destination), request.user.user.email
        )
        destination.extend(MAIL_APPROVER_GROUPS)
        general.emailSES(destination, subject, body)
        context["notification"] = "Owner's updated"
    except Exception as e:
        logger.error(f"Error occured while updating the owners: {e}")
        context = {
            "error": {
                "error_msg": "Internal Error",
                "msg": f"Error occured while updating the owners: {e}",
            }
        }

    return context


def isAllowedGroupAdminFunctions(request, groupMembers):
    ownersEmail = [member.user.email for member in groupMembers.filter(is_owner=True)]
    is_approver = request.user.user.has_permission(
        PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]
    )

    if request.user.user.email not in ownersEmail and not (
        request.user.is_superuser or request.user.user.is_ops or is_approver
    ):
        return False
    return True


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


def approveNewGroupRequest(request, group_id):

    try:
        group = GroupV2.get_pending_group(group_id=group_id)
    except Exception as e:
        logger.error(
            "Error in approveNewGroup request, Not found OR Invalid request type"
            + str(e)
        )
        json_response = {}
        json_response["error"] = "Error request not found OR Invalid request type"
        return json_response
    try:
        if group.is_self_approval(approver=request.user.user):
            context = {}
            context["error"] = (
                "You cannot approve your own request. Please ask other admins to do"
                " that"
            )
            return context
        else:
            json_response = {}
            json_response["msg"] = (
                "The Request (" + group_id + ") is now being processed"
            )

            group.approve(approved_by=request.user.user)
            group.approve_all_pending_users(approved_by=request.user.user)
            initial_members = group.get_all_members()
            notifications.send_new_group_approved_notification(
                group=group, group_id=group_id
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
                    + ", ".join(initial_members)
                )
            return json_response
    except Exception as e:
        group = GroupV2.get_approved_group(group_id=group_id)
        if group:
            group.unapprove()
            group.unapprove_memberships()
        logger.exception(e)
        logger.error("Error in Approving New Group request.")
        context = {}
        context["error"] = (
            "Error Occured while Approving group creation. Please contact admin - "
            + str(e)
        )
        return context


def get_user_group(request, group_name):
    try:
        context = {}
        group = GroupV2.objects.filter(name=group_name).filter(status="Approved")
        # check if the groupName is valid.
        if len(group) == 0:
            # there does not exist no such group.
            logger.debug(
                "addUserToGroup-- url received a bad group name requester-"
                + request.user.username
            )
            context = {}
            context["status"] = {
                "title": "Invalid Group",
                "msg": "There is no group named "
                + group_name
                + ". Please contact admin for any queries.",
            }
            return context
        group = group[0]
        groupMembers = (
            MembershipV2.objects.filter(group=group)
            .filter(status="Approved")
            .only("user")
        )
        if not isAllowedGroupAdminFunctions(request, groupMembers):
            raise Exception("Permission denied, you're not owner of this group")

        groupMembers = get_users_from_groupmembers(groupMembers)
        context["groupMembers"] = groupMembers
        context["groupName"] = group_name
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context["error"] = {
            "error_msg": "Internal Error",
            "msg": "Error Occured while loading the page. Please contact admin, "
            + str(e),
        }
        return context


def get_users_from_groupmembers(group_members):
    return [member.user for member in group_members]


def add_user_to_group(request):
    try:

        data = request.POST
        data = dict(data.lists())
        group = GroupV2.objects.filter(name=data["groupName"][0]).filter(
            status="Approved"
        )[0]
        group_members = (
            MembershipV2.objects.filter(group=group)
            .filter(status__in=["Approved", "Pending"])
            .only("user")
        )

        if not isAllowedGroupAdminFunctions(request, group_members):
            raise Exception("Permission denied, requester is non owner")

        group_members_email = [member.user.email for member in group_members]
        for user_email in data["selectedUserList"]:
            if is_user_in_group(user_email, group_members_email):
                context = {}
                context["error"] = {
                    "error_msg": "Duplicate Request",
                    "msg": "User "
                    + user_email
                    + " is already added to group/or pending approval for group"
                    " addition",
                }
                return context

        for user_email in data["selectedUserList"]:
            user = User.objects.filter(email=user_email)[0]
            membership_id = (
                user.name
                + "-"
                + str(group)
                + "-membership-"
                + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            )
            member = MembershipV2.objects.create(
                group=group,
                user=user,
                reason=data["memberReason"][0],
                membership_id=membership_id,
                requested_by=request.user.user,
            )
            if not group.needsAccessApprove:
                json_response = {}
                json_response["accessStatus"] = {
                    "msg": "The Request (" + membership_id + ") is now being processed",
                    "desc": (
                        "A email will be sent after the requested access are granted"
                    ),
                }
                member.approver = request.user.user
                member.status = "Approved"
                userMappingsList = views_helper.generateUserMappings(
                    user, group, member
                )
                member.save()
                group_name = member.group.name
                accessAcceptThread = threading.Thread(
                    target=views_helper.executeGroupAccess,
                    args=(request, group_name, userMappingsList),
                )
                accessAcceptThread.start()
                logger.debug(
                    "Process has been started for the Approval of request - "
                    + membership_id
                    + " - Approver="
                    + request.user.username
                )
                return json_response

            sendMailForGroupApproval(
                membership_id,
                user_email,
                str(request.user),
                data["groupName"][0],
                request.META["HTTP_HOST"],
                data["memberReason"][0],
            )

        context = {}
        context["status"] = {
            "title": "Request Submitted",
            "msg": "Once Approved the newly added members will be granted"
            + " the same permissions as the group",
        }
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context["error"] = {
            "error_msg": "Internal Error",
            "msg": "Error Occured while loading the page. Please contact admin, "
            + str(e),
        }
        return context


def is_user_in_group(user_email, group_members_email):
    return user_email in group_members_email


def sendMailForGroupApproval(
    membership_id, userEmail, requester, group_name, http_host, reason
):
    primary_approver, otherApprover = helpers.getApprovers()
    subject = (
        "Request for addition of new members to group ("
        + group_name
        + ")"
        + "["
        + primary_approver
        + "]"
    )
    destination = MAIL_APPROVER_GROUPS[:]
    body = helpers.generateStringFromTemplate(
        filename="email.html",
        emailBody=generateUserAddToGroupEmailBody(
            membership_id,
            userEmail,
            primary_approver,
            otherApprover,
            requester,
            group_name,
            http_host,
            reason,
        ),
    )
    general.emailSES(destination, subject, body)


def generateUserAddToGroupEmailBody(
    user_email, primary_approver, other_approver, requester, group_name, reason
):
    return helpers.generateStringFromTemplate(
        filename="add_user_to_group_mail.html",
        user_email=user_email,
        primary_approver=primary_approver,
        other_approver=other_approver,
        requester=requester,
        group_name=group_name,
        reason=reason,
    )


def acceptMember(request, requestId, shouldRender=True):
    try:
        membership = MembershipV2.get_membership(membership_id=requestId)
    except Exception as e:
        logger.error("Error request not found OR Invalid request type")
        json_response = {}
        json_response[
            "error"
        ] = "Error request not found OR Invalid request type - " + str(e)
        return json_response
    try:
        if membership.is_already_processed():
            logger.warning(
                "An Already Approved/Declined/Processing Request was accessed by - "
                + request.user.username
            )
            json_response = {}
            json_response["error"] = (
                "The Request ("
                + requestId
                + ") is already Processed By : "
                + membership.approver.user.username
            )
            return json_response
        elif membership.is_self_approval(approver=request.user.user):
            context = {}
            context[
                "error"
            ] = "You cannot approve your own request. Please ask other admins to do that"
            return context
        else:
            json_response = {}
            json_response["msg"] = (
                "The Request (" + requestId + ") is now being processed"
            )
            membership.approve(request.user.user)
            group = membership.group
            user = membership.user
            userMappingsList = views_helper.generateUserMappings(
                user, group, membership
            )

            # TODO: Add celery task for executeGroupAccess
            # accessAcceptThread = threading.Thread(target=executeGroupAccess, args=(request, group.name, userMappingsList))
            # accessAcceptThread.start()

            notifications.send_membership_accepted_notification(
                user=user, group=group, membership=membership
            )
            logger.debug(
                "Process has been started for the Approval of request - "
                + requestId
                + " - Approver="
                + request.user.username
            )
            return json_response
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Accept of New Member in Group request.")
        membership.unapprove()
        context = {}
        context[
            "error"
        ] = "Error Occured while approving the request. Please contact admin - " + str(
            e
        )
        return context

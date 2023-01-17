from Access.models import User, GroupV2, MembershipV2, Role
from Access import helpers, views_helper, notifications
import datetime
import logging
from bootprocess import general
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS
import threading

logger = logging.getLogger(__name__)

NEW_GROUP_CREATE_SUCCESS_MESSAGE = {
    "title": "New Group Request submitted",
    "msg": """A request for New Group with name {group_name} has been submitted for approval.
    You will be notified for any changes in request status.""",
}

NEW_GROUP_CREATE_ERROR_MESSAGE = {
    "error_msg": "Internal Error",
    "msg": "Error Occured while load    ing the page. Please contact admin",
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
        description=data["newGroupReason"][0],
        needsAccessApprove=(
            "requiresAccessApprove" in data
            and data["requiresAccessApprove"][0] == "true"
        ),
    )

    new_group.add_member(
        user=request.user.user,
        is_owner=True,
        requested_by=request.user.user,
        reason="Group Owner. Added as initial group member by requester.",
        date_time=base_datetime_prefix,
    )

    if "selectedUserList" in data:
        initial_members = list(map(str, data["selectedUserList"]))
        new_group.add_members(users=User.objects.filter(email__in=initial_members))
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


def getGroupAccessList(request, groupName):
    return {}


def updateOwner(request, group, context):
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

    # we will only get data["owners"] as owners who are checked in UI
    # (exluding disabled checkbox owner who requested the change)
    for membership_obj in MembershipV2.objects.filter(
        group=group, status="Approved"
    ).exclude(user=request.user.user):
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


def isAllowedGroupAdminFunctions(request, groupMembers):
    ownersEmail = [member.user.email for member in groupMembers.filter(is_owner=True)]
    is_approver = (
        len(
            User.objects.filter(
                role=Role.objects.get(label="TEAMS:ACCESSAPPROVE"),
                state=1,
                email=request.user.user.email,
            )
        )
        > 0
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
        group_object = GroupV2.objects.get(group_id=group_id, status="Pending")
    except Exception as e:
        logger.error(
            "Error in approveNewGroup request, Not found OR Invalid request type" + str(e)
        )
        json_response = {}
        json_response["error"] = "Error request not found OR Invalid request type"
        return json_response
    try:
        if request.user.username == group_object.requester.user.username:
            # Approving self request
            context = {}
            context[
                "error"
            ] = "You cannot approve your own request. Please ask other admins to do that"
            return context
        else:
            json_response = {}
            json_response["msg"] = (
                "The Request (" + group_id + ") is now being processed"
            )

            group_object.approver = request.user.user
            group_object.status = "Approved"
            group_object.save()

            MembershipV2.objects.filter(group=group_object, status="Pending").update(
                status="Approved", approver=request.user.user
            )
            initial_members = list(
                MembershipV2.objects.filter(group=group_object).values_list(
                    "user__user__username", flat=True
                )
            )

            subject = "New Group Created (" + group_object.name + ")"
            body = (
                "New group with name "
                + group_object.name
                + " has been created with owner being "
                + group_object.requester.user.username
                + "<br>"
            )
            if initial_members:
                body += "The following members have been added to this team<br>"
                body += notifications.generateGroupMemberTable(initial_members)
            body = helpers.generateStringFromTemplate(
                filename="email.html", emailBody=body
            )
            destination = []
            destination += MAIL_APPROVER_GROUPS[:]
            destination.append(group_object.requester.email)
            # TODO send a mail to initial members
            logger.debug(group_id + " -- Approved email sent to - " + str(destination))
            general.emailSES(destination, subject, body)

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
        group_object = GroupV2.objects.filter(group_id=group_id, status="Approved")
        if len(group_object):
            group_object = group_object[0]
            group_object.status = "Pending"
            group_object.save()
            MembershipV2.objects.filter(group=group_object).update(
                status="Pending", approver=None
            )
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
                    + " is already added to group/or pending approval for group addition",
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
                    "desc": "A email will be sent after the requested access are granted",
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
            "msg": "Once Approved the newly added members will be granted" + 
            " the same permissions as the group",
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

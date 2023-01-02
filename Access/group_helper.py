from Access.models import User, GroupV2, MembershipV2
from Access import helpers
import datetime
import logging
from bootprocess import general
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS

logger = logging.getLogger(__name__)


def createGroup(request):
    try:
        data = request.POST
        data = dict(data.lists())
        newGroupName = (data["newGroupName"][0]).lower()
        # Group name has to be unique.
        existing_groups = GroupV2.objects.filter(name=newGroupName).filter(
            status__in=["Approved", "Pending"])
        if len(existing_groups):
            # the group name is not unique.
            context = {}
            context["error"] = {
                "error_msg": "Invalid Group Name",
                "msg": "A group with name "
                + newGroupName
                + " already exists. Please choose a new name.",
            }
            return context

        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        group_id = newGroupName + "-group-" + base_datetime_prefix

        needsAccessApprove = True
        if (
            not "requiresAccessApprove" in data
            or data["requiresAccessApprove"][0] != "true"
        ):
            needsAccessApprove = False

        group = GroupV2.objects.create(
            name=newGroupName,
            group_id=group_id,
            requester=request.user.user,
            description=data["newGroupReason"][0],
            needsAccessApprove=needsAccessApprove,
        )

        membership_id = (
            str(request.user.user.user.username)
            + "-"
            + newGroupName
            + "-membership-"
            + base_datetime_prefix
        )
        MembershipV2.objects.create(
            membership_id=membership_id,
            user=request.user.user,
            group=group,
            is_owner=True,
            requested_by=request.user.user,
            reason="Group Owner. Added as initial group member by requester.",
        )

        if "selectedUserList" in data:
            initialMembers = list(map(str, data["selectedUserList"]))
            for memberEmail in initialMembers:
                user = User.objects.filter(email=memberEmail)
                if len(user):
                    user = user[0]
                    membership_id = (
                        str(user.user.username)
                        + "-"
                        + newGroupName
                        + "-membership-"
                        + base_datetime_prefix
                    )
                    MembershipV2.objects.create(
                        membership_id=membership_id,
                        user=user,
                        group=group,
                        requested_by=request.user.user,
                        reason="Added as initial group member by requester.",
                    )
        else:
            initialMembers = [request.user.email]

        # Create a email for it.
        subject = (
            "Request for creation of new group from "
            + request.user.email
            + " -- "
            + base_datetime_prefix
        )
        body = helpers.generateStringFromTemplate(filename="email.html",emailBody=
            generateNewGroupCreationEmailBody(
                request,
                group_id,
                newGroupName,
                initialMembers,
                data["newGroupReason"][0],
                needsAccessApprove,
            )
        )

        # Send the email to the approvers.
        # TODO remove email references
        general.emailSES(MAIL_APPROVER_GROUPS, subject, body)
        logger.debug("Email sent for " + subject + " to " + str(MAIL_APPROVER_GROUPS))

        # Ack the user.
        context = {}
        context["status"] = {
            "title": "New Group Request submitted",
            "msg": "A request for New Group with name "
            + newGroupName
            + " has been submitted for approval. You will be notified for any changes in request status.",
        }
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Create New Group request.")
        context = {}
        context["error"] = {
            "error_msg": "Internal Error",
            "msg": "Error Occured while loading the page. Please contact admin",
        }
        return context


def generateNewGroupCreationEmailBody(request, requestId, groupName, memberList, reason, needsAccessApprove):
    return helpers.generateStringFromTemplate(filename="groupCreationEmailBody.html",
                            user = str(request.user.user),
                            first_name=request.user.first_name,
                            last_name = request.user.last_name,
                            email = request.user.email,
                            groupName = groupName,
                            memberList = generateGroupMemberTable(memberList),
                            reason = reason,
                            needsAccessApprove = needsAccessApprove)

def generateGroupMemberTable(memberList):
    if len(memberList) <= 0:
        return "No members are being added initially"
    return helpers.generateStringFromTemplate("listToTable.html", memberList=memberList)

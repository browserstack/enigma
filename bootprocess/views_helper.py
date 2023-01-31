import logging
from Access.models import (
    User as access_user,
    MembershipV2,
    GroupV2,
    UserAccessMapping,
)
from BrowserStackAutomation.settings import DEFAULT_ACCESS_GROUP
from Access.views_helper import executeGroupAccess, generateUserMappings
import threading
import json
import datetime

logger = logging.getLogger(__name__)


def getDashboardData(request):
    user = access_user.objects.get(user__username=request.user)

    # Add users to DEFAULT_ACCESS_GROUP if the user is not already on the group
    user_membership = str(
        MembershipV2.objects.filter(user=user).filter(status="Approved")
    )
    if DEFAULT_ACCESS_GROUP not in user_membership:
        group_objects = GroupV2.objects.filter(name=DEFAULT_ACCESS_GROUP).filter(
            status="Approved"
        )
        if len(group_objects) > 0:
            group = group_objects[0]
            group_members = (
                MembershipV2.objects.filter(group=group)
                .filter(status="Approved")
                .only("user")
            )
            group_owner = [member for member in group_members.filter(is_owner=True)]
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
                reason="New joiner added to Org defaut access group.",
                membership_id=membership_id,
                requested_by=group_owner[0].user,
            )
            member.approver = group_owner[0].user
            member.status = "Approved"

            user_mappings_list = generateUserMappings(user, group, member)
            member.save()
            group_name = member.group.name

            access_accept_thread = threading.Thread(
                target=executeGroupAccess,
                args=(request, group_name, user_mappings_list),
            )
            access_accept_thread.start()

            logger.debug(
                "Process has been started for the Approval of request - "
                + membership_id
                + " - Approver="
                + request.user.username
            )

    if not user.gitusername:
        logger.debug(
            "Redirecting User to Fill out git username and his public key for ssh"
            " access."
        )
        # return redirect('updateUserInfo')

    with open("instanceTypes.json") as data_file:
        data = json.load(data_file)
    ec2_regions = list(data.keys())

    context = {}

    gitCount = 0
    dashboardCount = 0
    sshMachineCount = 0
    groupCount = 0

    dashboardCount = len(
        UserAccessMapping.objects.filter(
            user=request.user.user, status="Approved", access__access_tag="other"
        )
    )
    sshMachineCount = len(
        UserAccessMapping.objects.filter(
            user=request.user.user, status="Approved", access__access_tag="ssh"
        )
    )
    gitCount = len(
        UserAccessMapping.objects.filter(
            user=request.user.user,
            status="Approved",
            access__access_tag="github_access",
        )
    )
    groupCount = len(
        MembershipV2.objects.filter(user=request.user.user, status="Approved")
    )

    context["regions"] = ec2_regions
    context["gitCount"] = gitCount
    context["dashboardCount"] = dashboardCount
    context["sshMachineCount"] = sshMachineCount
    context["groupCount"] = groupCount

    return context

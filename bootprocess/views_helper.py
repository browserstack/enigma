import logging
from Access.models import (
    User as access_user,
    MembershipV2,
    GroupV2,
    UserAccessMapping,
)
from EnigmaAutomation.settings import DEFAULT_ACCESS_GROUP
from Access.views_helper import generate_user_mappings, execute_group_access
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

            user_mappings_list = generate_user_mappings(user, group, member)
            member.save()

            execute_group_access(user_mappings_list)

            logger.debug(
                "Process has been started for the Approval of request - "
                + membership_id
                + " - Approver="
                + request.user.username
            )

    with open("instanceTypes.json") as data_file:
        data = json.load(data_file)
    ec2_regions = list(data.keys())

    context = {}

    groupCount = len(
        MembershipV2.objects.filter(user=request.user.user, status="Approved")
    )

    context["regions"] = ec2_regions
    context["groupCount"] = groupCount

    return context

""" helper for views of bootprocess """
import logging
import json
import datetime
from django.db import transaction
from Access.models import (
    User as access_user,
    MembershipV2,
    GroupV2,
)
from Access.views_helper import generate_user_mappings, execute_group_access
from EnigmaAutomation.settings import DEFAULT_ACCESS_GROUP

logger = logging.getLogger(__name__)


def get_dashboard_data(request):
    """ helper to get dashboard data """
    user = access_user.objects.get(user__username=request.user)

    # Add users to DEFAULT_ACCESS_GROUP if the user is not already on the group
    # The check and create run in one transaction holding a row lock on the
    # user, so concurrent dashboard loads cannot both add the membership.
    user_mappings_list = None
    with transaction.atomic():
        access_user.objects.select_for_update().get(pk=user.pk)
        already_member = (
            MembershipV2.objects.filter(user=user, status="Approved")
            .filter(group__name=DEFAULT_ACCESS_GROUP)
            .exists()
        )
        group_objects = GroupV2.objects.filter(name=DEFAULT_ACCESS_GROUP).filter(
            status="Approved"
        )
        if not already_member and len(group_objects) > 0:
            group = group_objects[0]
            group_members = (
                MembershipV2.objects.filter(group=group)
                .filter(status="Approved")
                .only("user")
            )
            group_owner = list(group_members.filter(is_owner=True))
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

    # Grant access outside the transaction so the row lock is not held while
    # the (slow, external) access modules run.
    if user_mappings_list is not None:
        execute_group_access(user_mappings_list)
        logger.debug(
            "Process has been started for the Approval of request - "
            + membership_id
            + " - Approver="
            + request.user.username
        )

    with open("instanceTypes.json", encoding="utf-8") as data_file:
        data = json.load(data_file)
    ec2_regions = list(data.keys())

    context = {}

    group_count = len(
        MembershipV2.objects.filter(user=request.user.user, status="Approved")
    )

    context["regions"] = ec2_regions
    context["groupCount"] = group_count

    return context

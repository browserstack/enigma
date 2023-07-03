""" helper module for views """
import datetime
import logging

import csv
from django.shortcuts import render
from django.http import HttpResponse
from Access.background_task_manager import accept_request
from . import helpers as helper
from .models import UserAccessMapping

logger = logging.getLogger(__name__)


def generate_user_mappings(user, group, membership):
    """ method to generate user mappings """
    group_mappings = group.get_approved_accesses()

    user_mappings_list = []
    for group_mapping in group_mappings:
        access = group_mapping.access
        approver_1 = group_mapping.approver_1
        approver_2 = group_mapping.approver_2
        membership_id = membership.membership_id
        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        reason = (
            "Added to group for request "
            + membership_id
            + " - "
            + membership.reason
            + " - "
            + group_mapping.request_reason
        )
        request_id = (
            user.user.username + "-" + access.access_tag + "-" + base_datetime_prefix
        )
        similar_id_mappings = list(
            UserAccessMapping.objects.filter(
                request_id__icontains=request_id
            ).values_list("request_id", flat=True)
        )

        request_id = get_next_index(
            request_id=request_id, similar_id_mappings=similar_id_mappings
        )

        user_identity = user.get_or_create_active_identity(access.access_tag)

        if user_identity and not user_identity.has_approved_access(access=access):
            user_mapping = user_identity.create_access_mapping(
                request_id=request_id,
                access=access,
                approver_1=approver_1,
                approver_2=approver_2,
                reason=reason,
                access_type="Group",
            )
            user_mappings_list.append(user_mapping)
    return user_mappings_list


def execute_group_access(user_mappings_list):
    """ method to execute group access """
    for mapping in user_mappings_list:
        user = mapping.user_identity.user
        if user.current_state() == "active":
            if "other" in mapping.request_id:
                decline_group_other_access(mapping)
            else:
                accept_request(mapping)
                logger.debug("Successful group access grant for %s", mapping.request_id)
        else:
            mapping.decline_access(decline_reason="User is not active")
            logger.debug(
                "Skipping group access grant for user %s as user is not active", user.user.username
            )


def decline_group_other_access(access_mapping):
    """ method to decline other access in the group """
    user = access_mapping.user
    access_mapping.decline_access(
        decline_reason="Auto decline for 'Other Access'. Please replace this with correct access."
    )
    logger.debug(
        "Skipping group access grant for user %s for request_id %s, as it is 'Other Access'",
        user.user.username, access_mapping.request_id
    )


def get_next_index(request_id, similar_id_mappings):
    """ method to get next index """
    idx = 0
    while True:
        new_request_id = request_id + "_" + str(idx)
        if new_request_id not in similar_id_mappings:
            return new_request_id
        idx += 1


def render_error_message(request, log_message, user_message, user_message_description):
    """ method to render error message """
    logger.error(log_message)
    return render(
        request,
        "EnigmaOps/accessStatus.html",
        {
            "error": {
                "error_msg": user_message,
                "msg": user_message_description,
            }
        },
    )


def get_filters_for_access_list(request):
    """ method to get filters for access list """
    filters = {}
    if "accessTag" in request.GET:
        filters["access__access_tag__icontains"] = request.GET.get("accessTag")
    if "accessTagExact" in request.GET:
        filters["access__access_tag"] = request.GET.get("accessTagExact")
    if "status" in request.GET:
        filters["status__icontains"] = request.GET.get("status")
    if "type" in request.GET:
        filters["access_type__icontains"] = request.GET.get("type")
    return filters


def prepare_datalist(paginator, record_date):
    """ method to prepare data-list """
    data_list = []
    for each_access_request in paginator:
        if (
            record_date is not None
            and record_date != str(each_access_request.updated_on)[:10]
        ):
            continue
        access_details = get_generic_user_access_mapping(each_access_request)
        data_list.append(access_details)
    return data_list


def gen_all_user_access_list_csv(data_list):
    """ method to get all user access list in csv """
    logger.debug("Processing CSV response")
    response = HttpResponse(content_type="text/csv")
    filename = (
        "AccessList-"
        + str(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
        + ".csv"
    )
    response["Content-Disposition"] = 'attachment; filename="' + filename + '"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "User",
            "AccessType",
            "Access",
            "AccessStatus",
            "RequestDate",
            "Approver",
            "Type",
        ]
    )
    for data in data_list:
        access_status = data["status"]
        if len(data["revoker"]) > 0:
            access_status += " by - " + data["revoker"]
        writer.writerow(
            [
                data["user"],
                data["access_desc"],
                (", ".join(data["access_label"])),
                access_status,
                data["requested_on"],
                data["approver_1"],
                data["access_type"],
            ]
        )
    return response


def get_generic_user_access_mapping(user_access_mapping):
    """ method to get generic user access mapping """
    access_module = helper.get_available_access_module_from_tag(
        user_access_mapping.access.access_tag
    )
    if access_module:
        access_details = user_access_mapping.get_access_request_details(access_module)
    logger.debug("Generic access generated: %s", str(access_details))
    return access_details

from Access import helpers
import logging
import time
from . import helpers as helper

from BrowserStackAutomation.settings import DECLINE_REASONS
from Access.models import UserAccessMapping, User, GroupV2, AccessV2
import datetime
import json
from django.db import transaction

logger = logging.getLogger(__name__)

REQUEST_SUCCESS_MSG = {
    "title": "{request_id}  Request Submitted",
    "msg": "Once approved you will receive the update. {access_label}",
}
REQUEST_DUPLICATE_ERR_MSG = {
    "title": "{access_tag}: Duplicate Request not submitted",
    "msg": "Access already granted or request in pending state. {access_label}",
}
REQUEST_ERR_MSG = {
    "error_msg": "Invalid Request",
    "msg": "Please Contact Admin",
}
REQUEST_EMPTY_FORM_ERR_MSG = {
    "error_msg": "The submitted form is empty. Tried direct access to reqeust access page",
    "msg": "Error Occured while submitting your Request. Please contact the Admin",
}

REQUEST_ACCESS_AUTO_APPROVED_MSG = {
    "title": "{request_id}  Request Approved",
    "msg": "Once granted you will receive the update",
}

REQUEST_DB_ERR_MSG = {
    "error_msg": "Error Saving Request",
    "msg": "Please Contact Admin",
}
REQUEST_IDENTITY_NOT_SETUP_ERR_MSG = {
    "error_msg": "Identity not setup",
    "msg": "User Identity for module {access_tag} not setup by the user",
}

REQUEST_SUCCESS_MSG = {
    "title": "{request_id}  Request Submitted",
    "msg": "Once approved you will receive the update. {access_label}",
}
REQUEST_DUPLICATE_ERR_MSG = {
    "title": "{access_tag}: Duplicate Request not submitted",
    "msg": "Access already granted or request in pending state. {access_label}",
}
REQUEST_ERR_MSG = {
    "error_msg": "Invalid Request",
    "msg": "Please Contact Admin",
}
REQUEST_EMPTY_FORM_ERR_MSG = {
    "error_msg": "The submitted form is empty. Tried direct access to reqeust access page",
    "msg": "Error Occured while submitting your Request. Please contact the Admin",
}

REQUEST_ACCESS_AUTO_APPROVED_MSG = {
    "title": "{request_id}  Request Approved",
    "msg": "Once granted you will receive the update",
}

REQUEST_DB_ERR_MSG = {
    "error_msg": "Error Saving Request",
    "msg": "Please Contact Admin",
}
REQUEST_IDENTITY_NOT_SETUP_ERR_MSG = {
    "error_msg": "Identity not setup",
    "msg": "User Identity for module {access_tag} not setup by the user",
}


def requestAccessGet(request):
    context = {}
    try:
        for each_tag, each_module in helpers.get_available_access_modules().items():
            if "access_" + each_tag in request.GET.getlist("accesses"):
                if "accesses" not in context:
                    context["accesses"] = []
                context["genericForm"] = True
                try:
                    extra_fields = each_module.get_extra_fields()
                except Exception:
                    extra_fields = []
                try:
                    notice = each_module.get_notice()

                except Exception:
                    notice = ""
                context["accesses"].append(
                    {
                        "formDesc": each_module.access_desc(),
                        "accessTag": each_tag,
                        "accessTypes": each_module.access_types(),
                        "accessRequestData": each_module.access_request_data(
                            request, is_group=False
                        ),
                        "extraFields": extra_fields,
                        "notice": notice,
                        "accessRequestPath": each_module.fetch_access_request_form_path(),
                    }
                )
    except Exception as e:
        logger.exception(e)
        context = {}
        context["status"] = {
            "title": "Error Occured",
            "msg": (
                "There was an error in getting the requested access resources. Please"
                " contact Admin"
            ),
        }
    return context


def getGrantFailedRequests(request):
    try:
        failures = UserAccessMapping.objects.filter(
            status__in=["GrantFailed"]
        ).order_by("-requested_on")
        if request.GET.get("username"):
            user = User.objects.get(user__username=request.GET.get("username"))
            failures = failures.filter(user=user).order_by("-requested_on")
        if request.GET.get("access_type"):
            access_tag = request.GET.get("access_type")
            failures = failures.filter(access__access_tag=access_tag).order_by(
                "-requested_on"
            )

        context = {"failures": failures, "heading": "Grant Failures"}
        return context
    except Exception as e:
        return process_error_response(request, e)


def get_pending_revoke_failures(request):
    if request.GET.get("username"):
        user = User.objects.get(user__username=request.GET.get("username"))
        failures = UserAccessMapping.objects.filter(
            status__in=["RevokeFailed"], user=user
        ).order_by("-requested_on")
    if request.GET.get("access_type"):
        access_tag = request.GET.get("access_type")
        failures = UserAccessMapping.objects.filter(
            status__in=["RevokeFailed"], access__access_tag=access_tag
        ).order_by("-requested_on")
    else:
        failures = UserAccessMapping.objects.filter(
            status__in=["RevokeFailed"]
        ).order_by("-requested_on")

    context = {"failures": failures, "heading": "Revoke Failures"}
    return context


def getPendingRequests(request):
    logger.info("Pending Request call initiated")

    try:
        context = {"declineReasons": DECLINE_REASONS, "otherAccessRecepients": []}
        start_time = time.time()

        context["membershipPending"] = GroupV2.getPendingMemberships()
        context["newGroupPending"] = GroupV2.getPendingCreation()

        user = request.user.user
        (
            context["genericRequests"],
            context["groupGenericRequests"],
        ) = get_pending_accesses_from_modules(user)

        duration = time.time() - start_time
        logger.info("Time to fetch all pending requests:" + str(duration))

        return context
    except Exception as e:
        return process_error_response(request, e)


def get_pending_accesses_from_modules(access_user):
    individual_requests = []
    group_requests = {}

    logger.info("Start looping all access modules")
    for (
        access_module_tag,
        access_module,
    ) in helpers.get_available_access_modules().items():
        access_module_start_time = time.time()

        try:
            pending_accesses = access_module.get_pending_accesses(access_user)
        except Exception as e:
            logger.exception(e)
            pending_accesses = {
                "individual_requests": [],
                "group_requests": [],
            }

        process_individual_requests(
            pending_accesses["individual_requests"],
            individual_requests,
            access_module_tag,
        )
        process_group_requests(pending_accesses["group_requests"], group_requests)

        logger.info(
            "Time to fetch pending requests of access module: "
            + access_module_tag
            + " - "
            + str(time.time() - access_module_start_time)
        )

    return individual_requests, list(group_requests.values())


def process_individual_requests(
    individual_pending_requests, individual_requests, access_tag
):
    if len(individual_pending_requests):
        clubbed_requests = {}
        for accessrequest in individual_pending_requests:
            club_id = accessrequest["requestId"].rsplit("_", 1)[0]
            if club_id not in clubbed_requests:
                clubbed_requests[club_id] = {
                    "club_id": club_id,
                    "userEmail": accessrequest["userEmail"],
                    "accessReason": accessrequest["accessReason"],
                    "accessType": accessrequest["accessType"],
                    "access_tag": accessrequest["access_tag"],
                    "requested_on": accessrequest["requested_on"],
                    "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                    "accessData": [],
                }
            accessData = {
                "accessCategory": accessrequest["accessCategory"],
                "accessMeta": accessrequest["accessMeta"],
                "requestId": accessrequest["requestId"],
            }
            clubbed_requests[club_id]["accessData"].append(accessData)
        individual_requests.append(
            {"module_tag": access_tag, "requests": list(clubbed_requests.values())}
        )


def process_group_requests(group_pending_requests, group_requests):
    if len(group_pending_requests):
        for accessrequest in group_pending_requests:
            club_id = (
                accessrequest["groupName"]
                + "-"
                + accessrequest["requestId"].rsplit("-", 1)[-1].rsplit("_", 1)[0]
            )
            needs_access_approve = GroupV2.objects.get(
                name=accessrequest["groupName"], status="Approved"
            ).needsAccessApprove
            if club_id not in group_requests:
                group_requests[club_id] = {
                    "group_club_id": club_id,
                    "userEmail": accessrequest["userEmail"],
                    "groupName": accessrequest["groupName"],
                    "needsAccessApprove": needs_access_approve,
                    "requested_on": accessrequest["requested_on"],
                    "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                    "hasOtherRequest": False,
                    "accessData": [],
                }
            if accessrequest["access_tag"] == "other":
                group_requests[club_id]["hasOtherRequest"] = True
            accessData = {
                "accessCategory": accessrequest["accessCategory"],
                "accessMeta": accessrequest["accessMeta"],
                "requestId": accessrequest["requestId"],
                "accessReason": accessrequest["accessReason"],
                "accessType": accessrequest["accessType"],
                "access_tag": accessrequest["access_tag"],
            }
            group_requests[club_id]["accessData"].append(accessData)


def process_error_response(request, e):
    logger.debug("Error in request not found OR Invalid request type")
    logger.exception(e)
    json_response = {}
    json_response["error"] = {
        "error_msg": str(e),
        "msg": "Error in request not found OR Invalid request type",
    }
    return json_response


def create_request(auth_user, access_request_form):
    json_response, access_request = _validate_access_request(
        access_request_form=access_request_form, user=auth_user
    )

    current_date_time = (
        datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + "  UTC"
    )
    json_response = {}
    json_response["status"] = []
    json_response["status_list"] = []
    extra_fields = get_extra_fields(access_request=access_request)

    for index1, access_type in enumerate(access_request["accessRequests"]):
        access_labels = validate_access_labels(
            access_labels_json=access_request["accessLabel"][index1],
            access_type=access_type,
        )
        access_reason = access_request["accessReason"][index1]

        request_id = (
            auth_user.username
            + "-"
            + access_type
            + "-"
            + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        )
        json_response[access_type] = {
            "requestId": request_id,
            "dateTime": current_date_time,
        }

        access_module = helper.get_available_access_modules()[access_type]
        module_access_labels = access_module.validate_request(
            access_labels, auth_user, is_group=False
        )

        extra_field_labels = get_extra_field_labels(access_module)

        if extra_fields and extra_field_labels:
            for field in extra_field_labels:
                module_access_labels[0][field] = extra_fields[0]
                extra_fields = extra_fields[1:]

        for index2, access_label in enumerate(module_access_labels):
            request_id = request_id + "_" + str(index2)
            access_create_error = _create_access(
                auth_user=auth_user,
                access_label=access_label,
                access_type=access_type,
                request_id=request_id,
                access_reason=access_reason,
            )
            if access_create_error:
                json_response["status_list"].append(access_create_error)
                continue

            if access_module.can_auto_approve():
                # start approval in celery
                json_response["status_list"].append(
                    {
                        "title": REQUEST_ACCESS_AUTO_APPROVED_MSG["title"].format(
                            request_id
                        ),
                        "msg": REQUEST_ACCESS_AUTO_APPROVED_MSG["msg"],
                    }
                )
                raise Exception("Implementation pending")
                continue

            json_response["status_list"].append(
                {
                    "title": REQUEST_SUCCESS_MSG["title"].format(request_id=request_id),
                    "msg": REQUEST_SUCCESS_MSG["msg"].format(
                        access_label=json.dumps(access_label)
                    ),
                }
            )

    return json_response


def _create_access(auth_user, access_label, access_type, request_id, access_reason):
    user_identity = auth_user.user.get_active_identity(access_tag=access_type)
    if not user_identity:
        return {
            "title": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["error_msg"],
            "msg": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["msg"].format(
                access_tag=access_type
            ),
        }

    access = AccessV2.get(access_type=access_type, access_label=access_label)
    if access:
        if user_identity.access_mapping_exists(access):
            return {
                "title": REQUEST_DUPLICATE_ERR_MSG["title"].format(
                    access_tag=access.access_tag
                ),
                "msg": REQUEST_DUPLICATE_ERR_MSG["msg"].format(
                    access_label=json.dumps(access.access_label)
                ),
            }

    try:

        access = _create_access_mapping(
            access=access,
            user_identity=user_identity,
            request_id=request_id,
            access_label=access_label,
            access_type=access_type,
            access_reason=access_reason,
        )
    except Exception:
        return {
            "error_msg": REQUEST_DB_ERR_MSG["error_msg"],
            "msg": REQUEST_DB_ERR_MSG["msg"],
        }


@transaction.atomic
def _create_access_mapping(
    user_identity, access, request_id, access_type, access_label, access_reason
):
    if not access:
        access = AccessV2.objects.create(
            access_tag=access_type, access_label=access_label
        )

    user_identity.user_access_mapping.create(
        request_id=request_id, request_reason=access_reason, access=access
    )
    return access


def get_extra_field_labels(access_module):
    try:
        return access_module.get_extra_fields()
    except Exception:
        return []


def get_extra_fields(access_request):
    if "extraFields" in access_request:
        return access_request["extraFields"]
    return []


def _validate_access_request(access_request_form, user):
    json_response = {}
    if not access_request_form:
        json_response["error"] = {
            "error_msg": REQUEST_ERR_MSG["error_msg"],
            "msg": REQUEST_ERR_MSG["msg"],
        }

        logger.debug("Tried a direct Access to accessRequest by-" + user.username)
        return json_response

    access_request = dict(access_request_form.lists())

    if "accessRequests" not in access_request:
        json_response["error"] = {
            "error_msg": REQUEST_EMPTY_FORM_ERR_MSG["error_msg"],
            "msg": REQUEST_EMPTY_FORM_ERR_MSG["msg"],
        }
        return json_response
    return {}, access_request


def validate_access_labels(access_labels_json, access_type):
    if access_labels_json is None or access_labels_json == "":
        raise Exception("No fields were selected in the request. Please try again.")
    access_labels = json.loads(access_labels_json)
    if len(access_labels) == 0:
        raise Exception(
            "No fields were selected in the request for {access_type}. Please try again.".format(
                access_type=access_type
            )
        )
    return access_labels

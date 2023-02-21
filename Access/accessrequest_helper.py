import logging
import time
from Access.views_helper import execute_group_access, accept_request

from BrowserStackAutomation.settings import DECLINE_REASONS, MAIL_APPROVER_GROUPS
import datetime
import json
from django.db import transaction
from Access import (
    helpers,
    notifications,
)
from Access.models import (
    UserAccessMapping,
    GroupAccessMapping,
    User,
    GroupV2,
    AccessV2,
    ApprovalType,
)
from Access.background_task_manager import background_task, accept_request
from . import helpers as helper

logger = logging.getLogger(__name__)

REQUEST_SUCCESS_MSG = {
    "title": "{request_id}  Request Submitted",
    "msg": "Once approved you will receive the update. {access_label}",
}
REQUEST_DUPLICATE_ERR_MSG = {
    "title": "{access_tag}: Duplicate Request not submitted",
    "msg": "Access already granted or request in pending state. {access_label}",
}
REQUEST_PROCESS_MSG = "The Request ({request_id}) is now being processed"
REQUEST_DECLINED_MSG = "The Request ({request_id}) is now declined"
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
USER_REQUEST_IN_PROCESS_ERR_MSG = "The Request ({request_id}) has already been processed. \
                                   Please check Access History for more information"
USER_REQUEST_PERMISSION_DENIED_ERR_MSG = "Permission Denied!"
USER_REQUEST_DECLINE_MSG = "Declined Request {request_id} - Reason: {decline_reason}"
USER_REQUEST_SECONDARY_PENDING_MSG = "The Request ({request_id}) is approved by {approved_by} \
                                      Pending on secondary approver"
INVALID_REQUEST_ERROR_MSG = "Error in request not found OR Invalid request type"
ALREADY_PROCESSED_REQUEST_MSG = "An Already Approved/Declined/Processing Request \
    ({request_id}) was accessed by {user}"
SELF_APPROVAL_ERROR_MSG = (
    "You cannot approve your own request. Please ask other admins to do that"
)
ERROR_APPROVING_REQUEST_LOG_MSG = "Error Occured in acceptGroupAccess : {error} \
    Error Occured while approving request {request_id}"
ERROR_APPROVING_REQUEST_DSP_MSG = (
    "Error Occured while accepting the request. Please contact the Admin - {error}"
)
SKIPPING_ACCESS_GRANT_MSG = (
    "Skipping group access grant for user {username} as user is not active"
)
APPROVAL_PROCESS_STARTED_MSG = "Process has been started for the Approval of request \
- {request_id} - Approver: {approver}"
ERROR_DECLINING_REQUEST_LOG_MSG = "Error in Decline of request {request_id}. \
 Error:{error} .Please contact admin."


def get_request_access(request):
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


def validate_approver_permissions(access_mapping, access_type, request):
    json_response = {}

    access_label = access_mapping.access.access_label
    try:
        permissions = _get_approver_permissions(access_type, access_label)
    except Exception as e:
        return process_error_response(e)

    approver_permissions = permissions["approver_permissions"]
    if "2" in approver_permissions and access_mapping.is_secondary_pending():
        if not request.user.user.has_permission(approver_permissions["2"]):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            json_response["error"] = USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            return json_response
    elif access_mapping.is_pending():
        if not request.user.user.has_permission(approver_permissions["1"]):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            json_response["error"] = USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            return json_response

    return json_response


def get_grant_failed_requests(request):
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
        return process_error_response(e)


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


def get_pending_requests(request):
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
        logger.info("Time to fetch all pending requests: %s " % str(duration))

        return context
    except Exception as e:
        return process_error_response(e)


def get_decline_access_request(request, access_type, request_id):
    logger.info("Decline Access Request call initiated")
    try:
        context = {"response": {}}
        reason = request.GET["reason"]
        request_ids = []
        return_ids = []
        if access_type.endswith("-club"):
            for value in [request_id]:
                return_ids.append(value)
                current_ids = list(
                    UserAccessMapping.get_pending_access_mapping(request_id=value)
                )
                request_ids.extend(current_ids)
            access_type = access_type.rsplit("-", 1)[0]
        elif access_type == "clubGroupAccess":
            for value in [request_id]:  # ready for bulk decline
                return_ids.append(value)
                group_name, date_suffix = value.rsplit("-", 1)
                current_ids = list(
                    GroupAccessMapping.get_pending_access_mapping(
                        request_id=group_name
                    ).filter(request_id__contains=date_suffix)
                )
                request_ids.extend(current_ids)
            access_type = "groupAccess"
        else:
            request_ids = [request_id]
        for current_request_id in request_ids:
            if access_type == "groupAccess":
                response = decline_group_access(request, current_request_id, reason)
            else:
                response = decline_individual_access(
                    request, access_type, current_request_id, reason
                )
            if "error" in response:
                response["success"] = False
            else:
                response["success"] = True
            context["response"][current_request_id] = response
        context["returnIds"] = return_ids
        return context
    except Exception as e:
        return process_error_response(e)


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
            "Time to fetch pending requests of access module: %s - %s "
            % access_module_tag,
            str(time.time() - access_module_start_time),
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
                    "accessType": accessrequest["access_desc"],
                    "access_tag": accessrequest["access_tag"],
                    "requested_on": accessrequest["requested_on"],
                    "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                    "accessData": [],
                }
            access_data = {
                "accessCategory": accessrequest["accessCategory"],
                "accessMeta": accessrequest["accessMeta"],
                "requestId": accessrequest["requestId"],
            }
            clubbed_requests[club_id]["accessData"].append(access_data)
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
            access_data = {
                "accessCategory": accessrequest["accessCategory"],
                "accessMeta": accessrequest["accessMeta"],
                "requestId": accessrequest["requestId"],
                "accessReason": accessrequest["accessReason"],
                "accessType": accessrequest["accessType"],
                "access_tag": accessrequest["access_tag"],
            }
            group_requests[club_id]["accessData"].append(access_data)


def process_error_response(e):
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
    if not access_request_form:
        json_response = {}
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


def validate_access_labels(access_labels_json, access_tag):
    if access_labels_json is None or access_labels_json == "":
        raise Exception("No fields were selected in the request. Please try again.")
    access_labels = json.loads(access_labels_json)
    if len(access_labels) == 0:
        raise Exception(
            "No fields were selected in the request for {access_tag}. Please try again.".format(
                access_tag=access_tag
            )
        )
    return access_labels


def _get_approver_permissions(access_tag, access_label=None):
    json_response = {}

    access_module = helper.get_available_access_module_from_tag(access_tag)
    approver_permissions = []
    approver_permissions = access_module.fetch_approver_permissions(access_label)

    json_response["approver_permissions"] = approver_permissions
    if len(json_response) == 0:
        raise Exception("Approver Permissions not found for module %s " % access_module)
    return json_response


def is_request_valid(request_id, access_mapping):
    if access_mapping.is_already_processed():
        logger.warning(
            USER_REQUEST_IN_PROCESS_ERR_MSG.format(
                request_id=request_id,
            )
        )
        return False

    return True


def accept_user_access_requests(auth_user, request_id):
    json_response = {}
    access_mapping = UserAccessMapping.get_access_request(request_id)
    if not is_request_valid(request_id, access_mapping):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id,
        )
        return json_response

    requester = access_mapping.user_identity.user.email
    if auth_user.username == requester:
        json_response["error"] = USER_REQUEST_PERMISSION_DENIED_ERR_MSG
        return json_response

    access_label = access_mapping.access.access_label

    try:
        permissions = _get_approver_permissions(access_mapping.access.access_tag, access_label)
        approver_permissions = permissions["approver_permissions"]
        if not helper.check_user_permissions(
            auth_user, list(approver_permissions.values())
        ):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            json_response["error"] = USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            return json_response

        is_primary_approver = (
            access_mapping.is_pending()
            and auth_user.user.has_permission(approver_permissions["1"])
        )
        is_secondary_approver = (
            access_mapping.is_secondary_pending()
            and auth_user.user.has_permission(approver_permissions["2"])
        )

        if not (is_primary_approver or is_secondary_approver):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            json_response["error"] = USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            return json_response
        if is_primary_approver and "2" in approver_permissions:
            access_mapping.approver_1 = auth_user.user
            access_mapping.update_access_status("SecondaryPending")
            json_response["msg"] = USER_REQUEST_SECONDARY_PENDING_MSG.format(
                request_id=request_id, approved_by=auth_user.username
            )
            logger.debug(
                USER_REQUEST_SECONDARY_PENDING_MSG.format(
                    request_id=request_id, approved_by=auth_user.username
                )
            )
        else:
            json_response = run_accept_request_task(
                is_primary_approver,
                access_mapping,
                auth_user=auth_user,
                request_id=request_id,
                access_label=access_label,
            )
    except Exception as e:
        return process_error_response(e)

    return json_response


def run_accept_request_task(
    is_primary_approver, access_mapping, auth_user, request_id, access_label
):
    json_response = {}
    json_response["status"] = []
    approval_type = ApprovalType.Primary if is_primary_approver else ApprovalType.Secondary
    json_response["msg"] = REQUEST_PROCESS_MSG.format(request_id=request_id)

    try:
        access_mapping.processing(approval_type = approval_type, approver=auth_user.user)
    except Exception as e:
        logger.exception(e)
        raise Exception(
            "Error in accepting the request - {request_id}. Please try again.".format(
                request_id=request_id
            )
        )
    accept_request(access_mapping)
    json_response["status"].append(
        {
            "title": REQUEST_SUCCESS_MSG["title"].format(request_id=request_id),
            "msg": REQUEST_SUCCESS_MSG["msg"].format(
                access_label=json.dumps(access_label)
            ),
        }
    )

    return json_response


def decline_individual_access(request, access_type, request_id, reason):
    json_response = {}
    access_mapping = UserAccessMapping.get_access_request(request_id)
    if not is_request_valid(request_id, access_mapping):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id,
        )
        return json_response

    json_response = validate_approver_permissions(access_mapping, access_type, request)
    if "error" in json_response:
        return json_response

    with transaction.atomic():
        access_mapping.decline_access(reason)
        if hasattr(access_mapping, "approver_1"):
            access_mapping.decline_reason = reason
            if access_mapping.approver_1 is not None:
                access_mapping.approver_2 = request.user.user
            else:
                access_mapping.approver_1 = request.user.user
        else:
            access_mapping.reason = reason
            access_mapping.approver = request.user.username

        access_mapping.save()

    access_module = helper.get_available_access_module_from_tag(access_type)
    access_labels = [access_mapping.access.access_label]
    description = access_module.combine_labels_desc(access_labels)
    notifications.send_mail_for_request_decline(
        request, description, request_id, reason, access_type
    )

    logger.debug(
        USER_REQUEST_DECLINE_MSG.format(
            request_id=request_id,
            decline_reason=reason,
        )
    )
    json_response = {}
    json_response["msg"] = USER_REQUEST_DECLINE_MSG.format(
        request_id=request_id,
        decline_reason=reason,
    )
    return json_response


def accept_group_access(auth_user, request_id):
    json_response = {}

    group_mapping = GroupAccessMapping.get_by_request_id(request_id=request_id)
    if not group_mapping:
        logger.debug(INVALID_REQUEST_ERROR_MSG)
        json_response["error"] = INVALID_REQUEST_ERROR_MSG
        return json_response

    try:
        access_type = group_mapping.access.access_tag
        access_label = group_mapping.access.access_label

        permissions = _get_approver_permissions(access_type, access_label)
        approver_permissions = permissions["approver_permissions"]

        if not helper.check_user_permissions(
            auth_user, list(approver_permissions.values())
        ):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            return create_error_response(
                error_msg=USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            )

        if not (group_mapping.is_pending() or group_mapping.is_secondary_pending()):
            logger.warning(
                ALREADY_PROCESSED_REQUEST_MSG.format(
                    request_id=request_id, user=auth_user.username
                )
            )
            return create_error_response(
                error_msg=USER_REQUEST_IN_PROCESS_ERR_MSG.format(request_id=request_id)
            )
        elif group_mapping.is_self_approval(approver=auth_user.user):
            return create_error_response(error_msg=SELF_APPROVAL_ERROR_MSG)
        else:
            is_primary_approver, is_secondary_approver = is_valid_approver(
                auth_user=auth_user,
                group_mapping=group_mapping,
                approver_permissions=approver_permissions,
            )
            if not (is_primary_approver or is_secondary_approver):
                logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
                return create_error_response(
                    error_msg=USER_REQUEST_PERMISSION_DENIED_ERR_MSG
                )
            if is_primary_approver and "2" in approver_permissions:
                group_mapping.set_primary_approver(auth_user.user)
                json_response["msg"] = USER_REQUEST_SECONDARY_PENDING_MSG.format(
                    request_id=request_id, approved_by=auth_user.username
                )
                group_mapping.update_access_status(current_status="SecondaryPending")
                logger.debug(
                    USER_REQUEST_SECONDARY_PENDING_MSG.format(
                        request_id=request_id, approved_by=auth_user.username
                    )
                )
            else:
                if is_primary_approver:
                    group_mapping.set_primary_approver(auth_user.user)
                else:
                    group_mapping.set_secondary_approver(auth_user.user)
                json_response["msg"] = REQUEST_ACCESS_AUTO_APPROVED_MSG["title"].format(
                    request_id=request_id
                )

                userMappingsList = create_members_user_access_mappings(
                    group_mapping=group_mapping, access_type=access_type
                )

                group_mapping.approve_access()
                execute_group_access(userMappingsList)
                logger.debug(
                    APPROVAL_PROCESS_STARTED_MSG.format(
                        request_id=request_id, approver=auth_user.username
                    )
                )
            return json_response
    except Exception as e:
        logger.exception(e)
        destination = [group_mapping.requested_by.email]
        notifications.send_accept_group_access_failed(
            destination=destination, request_id=request_id, error=str(e)
        )
        return create_error_response(
            error_msg=ERROR_APPROVING_REQUEST_DSP_MSG.format(error=str(e))
        )


def decline_group_access(request, request_id, reason):
    json_response = {}

    group_mapping = GroupAccessMapping.get_by_request_id(request_id=request_id)
    if not group_mapping:
        logger.error(INVALID_REQUEST_ERROR_MSG)
        json_response["error"] = INVALID_REQUEST_ERROR_MSG
        return json_response

    access_type = group_mapping.access.access_tag

    json_response = validate_approver_permissions(
        group_mapping, access_type, request, request_id
    )
    if "error" in json_response:
        return json_response

    if not is_request_valid(request_id=request_id, access_mapping=group_mapping):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id
        )
        logger.warning(
            ALREADY_PROCESSED_REQUEST_MSG.format(
                request_id=request_id, user=request.user.username
            )
        )
        return json_response

    try:
        with transaction.atomic():
            group_mapping.decline_access(decline_reason=reason)
            if group_mapping.get_primary_approver() is not None:
                group_mapping.set_secondary_approver(approver=request.user.user)
            else:
                group_mapping.set_primary_approver(request.user.user)

        destination = [group_mapping.requested_by.email]
        destination.extend(MAIL_APPROVER_GROUPS)

        notifications.send_group_access_declined(
            destination=destination,
            group_name=group_mapping.group.name,
            requester=group_mapping.requested_by.user.username,
            decliner=request.user.username,
            request_id=request_id,
            declined_access=group_mapping.access.access_tag,
            reason=reason,
        )
        logger.debug(
            USER_REQUEST_DECLINE_MSG.format(
                request_id=request_id, decline_reason=reason
            )
        )
        json_response = {}
        json_response["msg"] = REQUEST_DECLINED_MSG.format(request_id=request_id)
        return json_response
    except Exception as e:
        logger.exception(e)
        destination = [request.user.email]
        notifications.send_decline_group_access_failed(
            destination=destination, request_id=request_id, error=str(e)
        )
        return create_error_response(
            error_msg=ERROR_DECLINING_REQUEST_LOG_MSG.format(
                request_id=request_id, error=str(str(e))
            )
        )


def create_error_response(error_msg):
    json_response = {}
    json_response["error"] = error_msg
    return json_response


def is_valid_approver(auth_user, group_mapping, approver_permissions):
    is_primary_approver = (
        group_mapping.is_pending()
        and auth_user.user.has_permission(approver_permissions["1"])
    )
    is_secondary_approver = (
        group_mapping.is_secondary_pending()
        and auth_user.user.has_permission(approver_permissions["2"])
    )
    return is_primary_approver, is_secondary_approver


def create_members_user_access_mappings(group_mapping, access_type):
    user_mappings_list = []
    with transaction.atomic():
        for membership in group_mapping.group.get_all_approved_members():
            user = membership.user
            access = group_mapping.access
            approver_1 = group_mapping.get_primary_approver()
            approver_2 = group_mapping.get_secondary_approver()
            reason = (
                "Added for group request "
                + group_mapping.request_id
                + " - "
                + group_mapping.request_reason
            )
            request_id = (
                user.user.username
                + "-"
                + group_mapping.access.access_tag
                + "-"
                + group_mapping.request_id.rsplit("-", 1)[-1]
            )
            if not user.get_accesses_by_access_tag_and_status(
                access_tag=access.access_tag, status=["Approved"]
            ):
                existing_mapping = UserAccessMapping.get_access_request(
                    request_id=request_id
                )
                if not existing_mapping:
                    user_identity = user.get_or_create_active_identity(
                        access_tag=access_type
                    )
                    user_mapping = UserAccessMapping.create(
                        request_id=request_id,
                        user_identity=user_identity,
                        access=access,
                        approver_1=approver_1,
                        approver_2=approver_2,
                        request_reason=reason,
                        access_type="Group",
                        status="Processing",
                    )
                else:
                    logger.debug("Regranting " + request_id)
                    user_mapping = existing_mapping
                    existing_mapping.set_processing()

                user_mappings_list.append(user_mapping)
    return user_mappings_list

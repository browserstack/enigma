""" This file contains helper functions for access request """

import datetime
import json
import logging
import time
from django.db import transaction

from enigma_automation.settings import (
    DECLINE_REASONS,
    MAIL_APPROVER_GROUPS,
    PERMISSION_CONSTANTS,
)
from Access.views_helper import execute_group_access
from Access import helpers, notifications
from Access.models import (
    UserAccessMapping,
    GroupAccessMapping,
    User,
    GroupV2,
    AccessV2,
    MembershipV2,
    ApprovalType,
)
from Access.background_task_manager import accept_request

logger = logging.getLogger(__name__)

REQUEST_SUCCESS_MSG = {
    "title": "Request Submitted {access_tag}",
    "msg": "Once approved you will receive the update",
}
REQUEST_FAILED_MSG = {
    "error_msg": "Failed to create request",
    "msg": "Something when wrong while create the access request"
}
REQUEST_DUPLICATE_ERR_MSG = {
    "title": "{access_tag}: Duplicate Request not submitted",
    "msg": "Access already granted or request in pending state. {access_label}"
}
REQUEST_PROCESS_MSG = "The Request ({request_id}) is now being processed"
REQUEST_DECLINED_MSG = "The Request ({request_id}) is now declined"
REQUEST_ERR_MSG = {
    "error_msg": "Invalid Request",
    "msg": "Please Contact Admin",
}
REQUEST_EMPTY_FORM_ERR_MSG = {
    "error_msg": "The submitted form is empty."
    " Tried direct access to reqeust access page",
    "msg": "Error Occured while submitting your Request."
    " Please contact the Admin",
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
    "error_msg": "Identity not set.",
    "msg": "User Identity for module {access_tag} not setup by the user",
}
USER_REQUEST_IN_PROCESS_ERR_MSG = (
    "The Request ({request_id}) has already been processed. Please check"
    " Access History for more information"
)
USER_REQUEST_PERMISSION_DENIED_ERR_MSG = "Permission Denied!"
USER_REQUEST_DECLINE_MSG = (
    "Declined Request {request_id} - Reason: {decline_reason}"
)
USER_REQUEST_SECONDARY_PENDING_MSG = (
    "The Request ({request_id}) is approved by {approved_by} Pending on"
    "secondary approver"
)
INVALID_REQUEST_ERROR_MSG = (
    "Error in request not found OR Invalid request type"
)
ALREADY_PROCESSED_REQUEST_MSG = (
    "An Already Approved/Declined/Processing Request ({request_id})"
    " was accessed by {user}"
)
SELF_APPROVAL_ERROR_MSG = (
    "You cannot approve your own request. Please ask other admins to do that"
)
ERROR_APPROVING_REQUEST_DSP_MSG = (
    "Error Occured while accepting the request."
    " Please contact the Admin - {error}"
)
APPROVAL_PROCESS_STARTED_MSG = (
    "Process has been started for the Approval of request - "
    "{request_id} - Approver: {approver}"
)
ERROR_DECLINING_REQUEST_LOG_MSG = (
    "Error in Decline of request {request_id}. Error:{error}."
    "Please contact admin."
)
ERROR_MARKING_RESOLVE_FAIL_LOG_MSG = (
    "Error in resolving request {request_id}. Error:{error} ."
)


class ImplementationPendingException(Exception):
    """Implementation Pending Exception"""

    def __init__(self):
        self.message = "Implementation Pending"
        super().__init__(self.message)


def get_request_access(request):
    """ Get list of all accesses for requesting access to """
    context = {}
    try:
        for each_tag, each_module in \
                helpers.get_available_access_modules().items():
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
                context["accesses"].append({
                    "formDesc": each_module.access_desc(),
                    "accessTag": each_tag,
                    "accessTypes": each_module.access_types(),
                    "accessRequestData": each_module.access_request_data(
                        request, is_group=False
                    ),
                    "extraFields": extra_fields,
                    "notice": notice,
                    "accessRequestPath":
                        each_module.fetch_access_request_form_path(),
                })
    except Exception as exception:
        logger.exception(exception)
        context = {}
        context["status"] = {
            "title": "Error Occured",
            "msg": (
                "There was an error in getting the requested access"
                " resources. Please contact Admin"
            ),
        }
    return context


def validate_approver_permissions(access_mapping, access_type, request):
    """ Check if user has primary or secondary approver permissions """
    json_response = {}

    access_label = access_mapping.access.access_label
    try:
        permissions = _get_approver_permissions(access_type, access_label)
    except Exception as exception:
        return process_error_response(exception)

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
    """ Get all grant failed requests """
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
    except Exception as exception:
        return process_error_response(exception)


def get_pending_revoke_failures(request):
    """ Get revoke failed accesses """
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
    """ Get all pending requests """
    logger.info("Pending Request call initiated")

    try:
        context = {
            "declineReasons": DECLINE_REASONS,
            "otherAccessRecepients": []
        }
        start_time = time.time()
        user = request.user.user
        if user.has_permission(
                PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]):
            context["membershipPending"] = GroupV2.get_pending_memberships()
            context["newGroupPending"] = GroupV2.get_pending_creation()
        else:
            context["membershipPending"] = 0
            context["newGroupPending"] = 0

        (
            context["genericRequests"],
            context["groupGenericRequests"],
        ) = get_pending_accesses_from_modules(user)

        duration = time.time() - start_time
        logger.info("Time to fetch all pending requests: %s ", duration)

        return context
    except Exception as exception:
        return process_error_response(exception)


def get_decline_access_request(request, access_type, request_id):
    """ Function to decline accesses """
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
                    UserAccessMapping.get_pending_access_mapping(
                        request_id=value
                    )
                )
                request_ids.extend(current_ids)
            access_type = "moduleAccess"
        elif access_type == "clubGroupAccess":
            for value in [request_id]:  # ready for bulk decline
                return_ids.append(value)
                group_name, date_suffix = value.rsplit("-", 1)
                current_ids = list(
                    GroupAccessMapping.get_pending_access_mapping(
                        request_id=group_name
                    ).filter(request_id__icontains=date_suffix)
                )
                request_ids.extend(current_ids)
            access_type = "groupAccess"
        else:
            request_ids = [request_id]

        for current_request_id in request_ids:
            if access_type == "groupAccess":
                response = decline_group_access(
                    request,
                    current_request_id,
                    reason,
                )
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
    except Exception as exception:
        return process_error_response(exception)


def get_pending_accesses_from_modules(access_user):
    """ Get pending accesses from all access modules"""
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
        except Exception as exception:
            logger.exception(exception)
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
            "Time to fetch pending requests of access module: %s - %s",
            access_module_tag,
            str(time.time() - access_module_start_time)
        )

    return individual_requests, list(group_requests.values())


def process_individual_requests(
    individual_pending_requests, individual_requests, access_tag
):
    """ Add details for individual requests """
    if len(individual_pending_requests):
        clubbed_requests = {}
        for accessrequest in individual_pending_requests:
            club_id = accessrequest["requestId"].rsplit("_")[0]
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
    """ Add details for group requests """
    if len(group_pending_requests):
        for accessrequest in group_pending_requests:
            club_id = (
                accessrequest["groupName"]
                + "-"
                + accessrequest["requestId"].rsplit("-", 1)[-1].rsplit("_")[0]
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


def process_error_response(exception):
    """ Create error response """
    logger.debug("Error in request not found OR Invalid request type")
    logger.exception(exception)
    return {
        "error": {
            "error_msg": str(exception),
            "msg": "Error in request not found OR Invalid request type",
        }
    }


def create_request(auth_user, access_request_form):
    """ Log request to database """
    json_response = _validate_access_request(access_request_form, auth_user)
    if json_response:
        return json_response

    access_tag = access_request_form.get("access_tag")

    if not auth_user.user.get_active_identity(access_tag=access_tag):
        json_response["error"] = {
            "error_msg": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["error_msg"],
            "msg": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["msg"].format(
                access_tag=access_tag
            ),
        }
        return json_response

    access_reason = access_request_form.get("access_reason")
    access_module = helpers.get_available_access_module_from_tag(access_tag)
    module_access_labels = access_module.validate_request(access_request_form, auth_user.user)

    for _, access_label in enumerate(module_access_labels):
        request_id = (
            auth_user.username
            + "-"
            + access_tag
            + "-"
            + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        )

        access_create_error = _create_access(
            auth_user, access_label, access_tag,
            request_id, access_reason
        )
        if access_create_error:
            logger.info("Duplicate request found: %s", access_create_error)
            continue

        if access_module.can_auto_approve():
            raise ImplementationPendingException()

    json_response["status"] = {
        "title": REQUEST_SUCCESS_MSG["title"].format(
            access_tag=access_tag
        ),
        "msg": REQUEST_SUCCESS_MSG["msg"]
    }
    return json_response


def _create_access(
        auth_user, access_label, access_tag, request_id, access_reason):
    user_identity = auth_user.user.get_active_identity(access_tag=access_tag)
    if not user_identity:
        return {
            "title": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["error_msg"],
            "msg": REQUEST_IDENTITY_NOT_SETUP_ERR_MSG["msg"].format(
                access_tag=access_tag
            ),
        }

    access = AccessV2.get(access_tag=access_tag, access_label=access_label)
    if not access:
        try:
            _create_access_mapping(
                access_tag=access_tag,
                access_label=access_label,
                user_identity=user_identity,
                request_id=request_id,
                access_reason=access_reason,
            )
        except Exception:
            return {
                "title": REQUEST_DB_ERR_MSG["error_msg"],
                "msg": REQUEST_DB_ERR_MSG["msg"],
            }
        return {"title": "success", "msg": "success"}

    if user_identity.access_mapping_exists(access):
        return {
            "title": REQUEST_DUPLICATE_ERR_MSG["title"].format(
                access_tag=access.access_tag
            ),
            "msg": REQUEST_DUPLICATE_ERR_MSG["msg"].format(
                access_label=json.dumps(access.access_label)
            ),
        }

    user_identity.user_access_mapping.create(
        request_id=request_id,
        request_reason=access_reason,
        access=access,
    )
    return {"title": "success", "msg": "success"}


@transaction.atomic
def _create_access_mapping(
    user_identity, access_tag, access_label, request_id, access_reason
):
    """ Create AccessV2 and UserAccessMapping in db """
    access = AccessV2.objects.create(
        access_tag=access_tag, access_label=access_label
    )

    user_identity.user_access_mapping.create(
        request_id=request_id, request_reason=access_reason, access=access
    )
    return access


def get_extra_field_labels(access_module):
    """ Get labels from extra fields """
    try:
        return access_module.get_extra_fields()
    except Exception:
        return []


def get_extra_fields(access_request):
    """ Safe handling for extra fields """
    if "extraFields" in access_request:
        return access_request["extraFields"]
    return []


def _validate_access_request(access_request_form, user):
    """ Internal validation to ensure form fields"""
    json_response = {}
    if not access_request_form:
        json_response["error"] = {
            "error_msg": REQUEST_ERR_MSG["error_msg"],
            "msg": REQUEST_ERR_MSG["msg"],
        }

        logger.debug(
            "Tried a direct Access to accessRequest by %s", user.username)
        return json_response

    if not access_request_form.get("access_tag") or not access_request_form.get("access_reason"):
        json_response["error"] = {
            "error_msg": REQUEST_EMPTY_FORM_ERR_MSG["error_msg"],
            "msg": REQUEST_EMPTY_FORM_ERR_MSG["msg"]
        }

    return json_response


def validate_access_labels(access_labels_json, access_tag):
    """ Validate labels """
    if access_labels_json is None or access_labels_json == "":
        raise Exception("No fields were selected in the request."
                        " Please try again.")
    access_labels = json.loads(access_labels_json)
    if len(access_labels) == 0:
        raise Exception(
            f"No fields were selected in the request for {access_tag}."
            " Please try again."
        )
    return access_labels


def _get_approver_permissions(access_tag, access_label=None):
    json_response = {}
    access_module = helpers.get_available_access_module_from_tag(access_tag)
    approver_permissions = access_module.fetch_approver_permissions(
        access_label)

    json_response["approver_permissions"] = approver_permissions
    if len(json_response) == 0:
        raise Exception(
            f"Approver Permissions not found for module {access_module}")
    return json_response


def is_request_valid(request_id, access_mapping):
    """ Validate the request. Should not already be in-process"""
    if access_mapping.is_already_processed():
        logger.warning(
            USER_REQUEST_IN_PROCESS_ERR_MSG.format(
                request_id=request_id,
            )
        )
        return False

    return True


def accept_user_access_requests(auth_user, request_id):
    """ Grant for individual user access requests """
    json_response = {}
    access_mapping = UserAccessMapping.get_access_request(request_id)
    if not is_request_valid(request_id, access_mapping):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id,
        )
        return json_response

    requester = access_mapping.user_identity.user
    if auth_user.user == requester:
        json_response["error"] = SELF_APPROVAL_ERROR_MSG
        return json_response

    access_label = access_mapping.access.access_label

    try:
        permissions = _get_approver_permissions(
            access_mapping.access.access_tag, access_label
        )
        approver_permissions = permissions["approver_permissions"]
        if not helpers.check_user_permissions(
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
    except Exception as exception:
        return process_error_response(exception)

    return json_response


def run_accept_request_task(
    is_primary_approver, access_mapping, auth_user, request_id, access_label
):
    """ Grant access for indviduals """
    json_response = {}
    json_response["status"] = []
    approval_type = (
        ApprovalType.PRIMARY if is_primary_approver else ApprovalType.SECONDARY
    )
    json_response["msg"] = REQUEST_PROCESS_MSG.format(request_id=request_id)

    try:
        access_mapping.processing(
            approval_type=approval_type, approver=auth_user.user)
    except Exception as exception:
        logger.exception(exception)
        raise Exception(
            f"Error in accepting the request - {request_id}. Please try again."
        ) from exception
    accept_request(access_mapping)
    json_response["status"].append(
        {
            "title": REQUEST_SUCCESS_MSG["title"].format(
                request_id=request_id),
            "msg": REQUEST_SUCCESS_MSG["msg"].format(
                access_label=json.dumps(access_label)
            ),
        }
    )

    return json_response


def decline_group_membership(request, access_type, request_id, reason):
    """ Decline group membership """
    json_response = {}
    membership = MembershipV2.get_membership(request_id)

    if not membership:
        json_response["error"] = INVALID_REQUEST_ERROR_MSG
        return json_response

    if not is_request_valid(request_id, membership):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id,
        )
        return json_response

    membership.decline(reason, request.user.user)

    notifications.send_mail_for_request_decline(
        request, "Membership Creation", request_id, reason, access_type
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


def decline_individual_access(request, access_type, request_id, reason):
    """ Decline individual access """
    json_response = {}
    access_mapping = {}
    decline_new_group = False
    if access_type == "declineNewGroup":
        access_mapping = GroupV2.get_pending_group(request_id)
        decline_new_group = True
    elif access_type == "declineMember":
        return decline_group_membership(request, access_type, request_id, reason)
    else:
        access_mapping = UserAccessMapping.get_access_request(request_id)
        access_type = access_mapping.access.access_tag

    if not is_request_valid(request_id, access_mapping):
        json_response["error"] = USER_REQUEST_IN_PROCESS_ERR_MSG.format(
            request_id=request_id,
        )
        return json_response

    if not decline_new_group:
        json_response = validate_approver_permissions(
            access_mapping, access_type, request)
        if "error" in json_response:
            return json_response

    with transaction.atomic():
        access_mapping.decline_access(reason)
        if hasattr(access_mapping, "approver_1"):
            if access_mapping.approver_1 is not None:
                access_mapping.approver_2 = request.user.user
            else:
                access_mapping.approver_1 = request.user.user
        else:
            access_mapping.approver = request.user.user

        access_mapping.save()

    if not decline_new_group:
        access_module = helpers.get_available_access_module_from_tag(
            access_type)
        access_labels = [access_mapping.access.access_label]
        description = access_module.combine_labels_desc(access_labels)
        notifications.send_mail_for_request_decline(
            request, description, request_id, reason, access_type
        )
    else:
        MembershipV2.update_membership(access_mapping, reason)
        notifications.send_mail_for_request_decline(
            request, "Group Creation", request_id, reason, access_type
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
    """ Grant access for approved group request """
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

        if not helpers.check_user_permissions(
            auth_user, list(approver_permissions.values())
        ):
            logger.debug(USER_REQUEST_PERMISSION_DENIED_ERR_MSG)
            return create_error_response(
                error_msg=USER_REQUEST_PERMISSION_DENIED_ERR_MSG
            )

        if not (group_mapping.is_pending() or
                group_mapping.is_secondary_pending()):
            logger.warning(
                ALREADY_PROCESSED_REQUEST_MSG.format(
                    request_id=request_id, user=auth_user.username
                )
            )
            return create_error_response(
                error_msg=USER_REQUEST_IN_PROCESS_ERR_MSG.format(
                    request_id=request_id)
            )

        if group_mapping.is_self_approval(approver=auth_user.user):
            return create_error_response(error_msg=SELF_APPROVAL_ERROR_MSG)

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
            json_response["msg"] = \
                USER_REQUEST_SECONDARY_PENDING_MSG.format(
                    request_id=request_id, approved_by=auth_user.username)
            group_mapping.update_access_status(
                current_status="SecondaryPending")
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
            json_response["msg"] = \
                REQUEST_ACCESS_AUTO_APPROVED_MSG["title"].format(
                    request_id=request_id)

            user_mappings_list = create_members_user_access_mappings(
                group_mapping=group_mapping, access_type=access_type
            )

            group_mapping.approve_access()
            execute_group_access(user_mappings_list)
            logger.debug(
                APPROVAL_PROCESS_STARTED_MSG.format(
                    request_id=request_id, approver=auth_user.username
                )
            )
        return json_response
    except Exception as exception:
        logger.exception(exception)
        destination = [group_mapping.requested_by.email]
        notifications.send_accept_group_access_failed(
            destination=destination,
            request_id=request_id,
            error=str(exception),
        )
        return create_error_response(
            error_msg=ERROR_APPROVING_REQUEST_DSP_MSG.format(
                error=str(exception))
        )


def decline_group_access(request, request_id, reason):
    """ Decline access by access approver for group access """
    json_response = {}

    group_mapping = GroupAccessMapping.get_by_request_id(request_id=request_id)
    if not group_mapping:
        logger.error(INVALID_REQUEST_ERROR_MSG)
        json_response["error"] = INVALID_REQUEST_ERROR_MSG
        return json_response

    access_type = group_mapping.access.access_tag

    json_response = validate_approver_permissions(
        group_mapping, access_type, request
    )
    if "error" in json_response:
        return json_response

    if not is_request_valid(
            request_id=request_id, access_mapping=group_mapping):
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
                group_mapping.set_secondary_approver(
                    approver=request.user.user)
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
        return {
            "msg": REQUEST_DECLINED_MSG.format(request_id=request_id)
        }
    except Exception as exception:
        logger.exception(exception)
        destination = [request.user.email]
        notifications.send_decline_group_access_failed(
            destination=destination,
            request_id=request_id,
            error=str(exception),
        )
        return create_error_response(
            error_msg=ERROR_DECLINING_REQUEST_LOG_MSG.format(
                request_id=request_id, error=str(exception)
            )
        )


def run_ignore_failure_task(auth_user, access_mapping, request_id, selector):
    """
    Function to retrigger request in case we want to retry after failure
    """
    try:
        if selector == "decline":
            access_mapping.decline_access()
        elif selector == "approve":
            access_mapping.approve_access()
        notifications.send_mail_for_request_resolve(
            auth_user, selector, request_id)
        return None
    except Exception as exception:
        logger.exception(exception)
        return create_error_response(
            error_msg=ERROR_MARKING_RESOLVE_FAIL_LOG_MSG.format(
                request_id=request_id, error=str(str(exception))
            )
        )


def create_error_response(error_msg):
    """ Helper function to create error response"""
    return {
        "error": error_msg,
    }


def is_valid_approver(auth_user, group_mapping, approver_permissions):
    """ Validate user as approver """
    is_primary_approver = group_mapping.is_pending() and auth_user.user.has_permission(
        approver_permissions["1"]
    )
    is_secondary_approver = (
        group_mapping.is_secondary_pending()
        and auth_user.user.has_permission(approver_permissions["2"])
    )
    return is_primary_approver, is_secondary_approver


def create_members_user_access_mappings(group_mapping, access_type):
    """ Create UserAccessMappings for all members of the group """
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
                    logger.debug("Regranting %s", request_id)
                    user_mapping = existing_mapping
                    existing_mapping.set_processing()

                user_mappings_list.append(user_mapping)
    return user_mappings_list

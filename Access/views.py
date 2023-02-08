from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
import json
import logging

from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from Access import group_helper
from Access.accessrequest_helper import (
    requestAccessGet,
    getGrantFailedRequests,
    get_pending_revoke_failures,
    getPendingRequests,
    create_request,
)
from Access.models import User
from Access.userlist_helper import (
    getallUserList,
    get_identity_templates,
    create_identity,
    NEW_IDENTITY_CREATE_ERROR_MESSAGE,
)
from Access.views_helper import render_error_message
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS

INVALID_REQUEST_MESSAGE = "Error in request not found OR Invalid request type - "

logger = logging.getLogger(__name__)


@login_required
def showAccessHistory(request):
    if request.method == "POST":
        return render_error_message(
            request,
            "POST for showAccessHistory not supported",
            "Invalid Request",
            "Error request not found OR Invalid request type",
        )

    try:
        access_user = User.objects.get(email=request.user.email)
    except Exception as e:
        return render_error_message(
            request,
            "Access user with email %s not found. Error: %s"
            % (request.user.email, str(e)),
            "Invalid Request",
            "Please login again",
        )

    return render(
        request,
        "BSOps/showAccessHistory.html",
        {
            "dataList": access_user.get_access_history(
                helper.get_available_access_modules()
            )
        },
    )


@login_required
@user_admin_or_ops
def pendingFailure(request):
    try:
        response = getGrantFailedRequests(request)
        return render(request, "BSOps/failureAdminRequests.html", response)
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response["error"] = {"error_msg": str(e), "msg": INVALID_REQUEST_MESSAGE}
        return render(request, "BSOps/accessStatus.html", json_response)


@login_required
@user_admin_or_ops
def pending_revoke(request):
    try:
        response = get_pending_revoke_failures(request)
        return render(request, "BSOps/failureAdminRequests.html", response)
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response["error"] = {"error_msg": str(e), "msg": INVALID_REQUEST_MESSAGE}
        return render(request, "BSOps/accessStatus.html", json_response)


@login_required
def updateUserInfo(request):
    context = get_identity_templates()
    return render(request, "updateUser.html", context)


@api_view(["POST"])
@login_required
def saveIdentity(request):
    try:
        modname = request.POST.get("modname")
        if request.POST:
            context = create_identity(
                user_identity_form=request.POST, auth_user=request.user
            )
            return JsonResponse(json.dumps(context), safe=False, status=200)
    except Exception:
        context = {}
        context["error"] = {
            "title": NEW_IDENTITY_CREATE_ERROR_MESSAGE["title"],
            "msg": NEW_IDENTITY_CREATE_ERROR_MESSAGE["msg"].format(modulename=modname),
        }
        return JsonResponse(json.dumps(context), safe=False, status=400)


@login_required
def createNewGroup(request):
    if request.POST:
        context = group_helper.create_group(request)
        if "status" in context or "error" in context:
            return render(request, "BSOps/accessStatus.html", context)
        return render(request, "BSOps/createNewGroup.html", context)
    else:
        return render(request, "BSOps/createNewGroup.html", {})


@api_view(["GET"])
@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
@authentication_classes((TokenAuthentication, BasicAuthentication))
def allUserAccessList(request, load_ui=True):
    return False


@login_required
def allUsersList(request):
    context = getallUserList(request)
    return render(request, "BSOps/allUsersList.html", context)


@login_required
def requestAccess(request):
    if request.POST:
        context = create_request(
            auth_user=request.user, access_request_form=request.POST
        )
        return render(request, "BSOps/accessStatus.html", context)
    else:
        context = requestAccessGet(request)
        return render(request, "BSOps/accessRequestForm.html", context)


@login_required
def group_access(request):
    if request.GET:
        context = group_helper.get_group_access(request.GET, request.user)
        return render(request, "BSOps/groupAccessRequestForm.html", context)
    elif request.POST:
        context = group_helper.save_group_access_request(request.POST, request.user)
        return render(request, "BSOps/accessStatus.html", context)


@login_required
def group_access_list(request, groupName):
    try:
        context = group_helper.get_group_access_list(request, groupName)
        if "error" in context:
            return render(request, "BSOps/accessStatus.html", context)

        return render(request, "BSOps/groupAccessList.html", context)
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response["error"] = {"error_msg": str(e), "msg": INVALID_REQUEST_MESSAGE}
        return render(request, "BSOps/accessStatus.html", json_response)


@login_required
def update_group_owners(request, groupName):
    try:
        context = group_helper.update_owners(request, groupName)
        if "error" in context:
            return JsonResponse(context, status=400)

        return JsonResponse(context, status=200)
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response["error"] = INVALID_REQUEST_MESSAGE
        return JsonResponse(json_response, status=400)


@login_required
def groupDashboard(request):
    return render(request, "BSOps/createNewGroup.html")


def approveNewGroup(request, group_id):
    return group_helper.approve_new_group_request(request, group_id)


@login_required
def add_user_to_group(request, groupName):
    if request.POST:
        context = group_helper.add_user_to_group(request)
        return render(request, "BSOps/accessStatus.html", context)
    else:
        context = group_helper.get_user_group(request, groupName)
        return render(request, "BSOps/accessStatus.html", context)


@api_view(["GET"])
@login_required
@user_with_permission([PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]])
def pendingRequests(request):
    context = getPendingRequests(request)
    return render(request, "BSOps/pendingRequests.html", context)


@login_required
def accept_bulk(request, selector):
    try:
        context = {"response": {}}
        inputVals = request.GET.getlist("requestId")
        requestIds = []
        returnIds = []
        user = request.user.user
        is_access_approver = user.has_permission("ACCESS_APPROVE")
        requestIds = inputVals
        for value in requestIds:
            requestId = value
            if selector == "groupNew" and is_access_approver:
                json_response = group_helper.approve_new_group_request(
                    request, requestId
                )
            elif selector == "groupMember" and is_access_approver:
                json_response = group_helper.accept_member(request, requestId, False)
            else:
                raise ValidationError("Invalid request")
            if "error" in json_response:
                context["response"][requestId] = {
                    "error": json_response["error"],
                    "success": False,
                }
            else:
                context["response"][requestId] = {
                    "msg": json_response["msg"],
                    "success": True,
                }
        context["bulk_approve"] = True
        context["returnIds"] = returnIds
        return JsonResponse(context, status=200)
    except Exception as e:
        logger.debug(INVALID_REQUEST_MESSAGE + str(str(e)))
        json_response = {}
        json_response["error"] = INVALID_REQUEST_MESSAGE + str(str(e))
        json_response["success"] = False
        json_response["status_code"] = 401
        return JsonResponse(json_response, status=json_response["status_code"])

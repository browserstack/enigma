from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
import logging

from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from Access import group_helper
from Access.accessrequest_helper import (
    requestAccessGet,
    getGrantFailedRequests,
    get_pending_revoke_failures,
    getPendingRequests,
)
from Access.userlist_helper import getallUserList
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS

INVALID_REQUEST_MESSAGE = "Error in request not found OR Invalid request type - "

logger = logging.getLogger(__name__)

# Create your views here.
all_access_modules = helper.getAvailableAccessModules()


@login_required
def showAccessHistory(request):
    return False


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
        json_response['error'] = {'error_msg': str(e), 'msg': INVALID_REQUEST_MESSAGE}
        return render(request, 'BSOps/accessStatus.html', json_response)


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
        json_response['error'] = {'error_msg': str(e), 'msg': INVALID_REQUEST_MESSAGE}
        return render(request, 'BSOps/accessStatus.html', json_response)


@login_required
def updateUserInfo(request):
    return False


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
    context = requestAccessGet(request)
    return render(request, "BSOps/accessRequestForm.html", context)


@login_required
def groupRequestAccess(request):
    return False


@login_required
def groupAccessList(request, groupName):
    context = group_helper.getGroupAccessList(request, groupName)
    if "error" in context:
        return render(request, "BSOps/accessStatus.html", context)

    return render(request, "BSOps/groupAccessList.html", context)


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
        inputVals = request.GET.getlist('requestId')
        requestIds = []
        returnIds = []
        user = request.user.user
        is_access_approver = user.has_permission("ACCESS_APPROVE")
        requestIds = inputVals
        for value in requestIds:
            requestType, requestId = selector, value
            if selector == "groupNew" and is_access_approver:
                json_response = group_helper.approve_new_group_request(request, requestId)
            elif selector == "groupMember" and is_access_approver:
                json_response = group_helper.accept_member(request, requestId, False)
            else:
                raise ValidationError("Invalid request")
            if "error" in json_response:
                context['response'][requestId] = {"error": json_response["error"], "success": False}
            else:
                context['response'][requestId] = {"msg": json_response["msg"], "success": True}
        context['bulk_approve'] = True
        context["returnIds"] = returnIds
        return JsonResponse(context, status=200)
    except Exception as e:
        logger.debug(INVALID_REQUEST_MESSAGE + str(str(e)))
        json_response = {}
        json_response['error'] = INVALID_REQUEST_MESSAGE + str(str(e))
        json_response["success"] = False
        json_response["status_code"] = 401
        return JsonResponse(json_response, status=json_response["status_code"])

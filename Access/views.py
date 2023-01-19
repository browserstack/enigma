from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
import logging

from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from Access import group_helper
from Access.accessrequest_helper import requestAccessGet, getGrantFailedRequests, getPendingRevokeFailures, getPendingRequests
from Access.models import User, UserAccessMapping
from Access.userlist_helper import getallUserList
from Access.views_helper import render_error_message
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS

logger = logging.getLogger(__name__)

# Create your views here.
all_access_modules = helper.getAvailableAccessModules()


@login_required
def showAccessHistory(request):
    if request.method == 'POST':
        return render_error_message(
            request,
            "POST for showAccessHistory not supported",
            "Invalid Request",
            "Error request not found OR Invalid request type"
        )

    try:
        access_user = User.objects.get(email=request.user.email)
    except Exception as e:
        return render_error_message(
            request,
            "Access user with email %s not found. Error: %s" % (request.user.email, str(e)),
            "Invalid Request",
            "Please login again"
        )

    dataList = []
    genericAccessRequests = access_user.useraccessmapping_set.prefetch_related('access', 'approver_1', 'approver_2')
    for access_request_mapping in genericAccessRequests:
        access_details = access_request_mapping.getAccessRequestDetails(access_request_mapping)

        temp = {}
        temp['id'] = access_request_mapping.request_id
        temp['type'] = access_details["accessType"]
        temp['access'] = "%s details: %s" % (access_details["accessCategory"], json.dumps(access_details["accessMeta"]))
        temp['status'] = access_request_mapping.status
        temp['reason'] = access_request_mapping.request_reason
        temp['decline_reason'] = access_request_mapping.decline_reason
        temp['approver'] = ""
        if access_request_mapping.approver_1:
            temp["approver"] = access_request_mapping.approver_1.user.username
        if access_request_mapping.approver_2:
            temp["approver"] = "1: %s\n2: %s" % (access_request_mapping.approver_1.user.username, access_request_mapping.approver_2.user.username)

        dataList.append(temp)

    context = {}
    context['dataList'] = dataList
    return render(request, 'BSOps/showAccessHistory.html', context)


@login_required
@user_admin_or_ops
def pendingFailure(request):
    response = getGrantFailedRequests(request)
    if type(response) is dict:
        return render(request, 'BSOps/accessStatus.html', response)

    return render(request,'BSOps/failureAdminRequests.html',response)


@login_required
@user_admin_or_ops
def pendingRevoke(request):
    response = getPendingRevokeFailures(request)
    if type(response) is dict:
        return render(request, 'BSOps/accessStatus.html', response)
    return render(request,'BSOps/failureAdminRequests.html',response)

@login_required
def updateUserInfo(request):
    return False


@login_required
def createNewGroup(request):
    if request.POST:
        context = group_helper.createGroup(request)
        if "status" in context or "error" in context:
            return render(request, 'BSOps/accessStatus.html',context)
        return render(request,'BSOps/createNewGroup.html',context)
    else:
        return render(request,'BSOps/createNewGroup.html',{})

@api_view(["GET"])
@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
@authentication_classes((TokenAuthentication, BasicAuthentication))
def allUserAccessList(request, load_ui=True):
    return False


@login_required
def allUsersList(request):
    context = getallUserList(request)
    return render(request, 'BSOps/allUsersList.html', context)


@login_required
def requestAccess(request):
    context = requestAccessGet(request)
    return render(request, 'BSOps/accessRequestForm.html', context)


@login_required
def groupRequestAccess(request):
    return False

@login_required
def groupAccessList(request, groupName):
    context = group_helper.getGroupAccessList(request, groupName)
    if 'error' in context:
        return render(request,"BSOps/accessStatus.html", context)
        
    return render(request,"BSOps/groupAccessList.html", context)


@login_required
def groupDashboard(request):
    return render(request, 'BSOps/createNewGroup.html')


def approveNewGroup(request, group_id):
    return group_helper.approveNewGroupRequest(request, group_id)

@login_required
def add_user_to_group(request, groupName):
    if request.POST:
        context =  group_helper.add_user_to_group(request)
        return render(request, 'BSOps/accessStatus.html',context)
    else:
        context =  group_helper.get_user_group(request, groupName)
        return render(request, 'BSOps/accessStatus.html',context)

@api_view(["GET"])
@login_required
@user_with_permission([PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]])
def pendingRequests(request):
    context = getPendingRequests(request)
    return render(request, 'BSOps/pendingRequests.html', context)

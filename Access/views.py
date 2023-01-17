from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
import logging

from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from Access import group_helper
from Access.accessrequest_helper import requestAccessGet, getGrantFailedRequests, getPendingRevokeFailures, getPendingRequests
from Access.userlist_helper import getallUserList, getallUserList, get_identity_templates, create_identity
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Create your views here.
all_access_modules = helper.getAvailableAccessModules()


@login_required
def showAccessHistory(request):
    return False


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
    context = get_identity_templates()
    return render(request,'updateUser.html',context)


@api_view(['POST'])
@login_required
def saveIdentity(request):
    try:
        if request.POST:
            context = create_identity(request)
            return JsonResponse(json.dumps(context), safe=False, status=200)
    except:
        return JsonResponse("", safe=False, status=400)

@login_required
def createNewGroup(request):
    if request.POST:
        context = group_helper.create_group(request)
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

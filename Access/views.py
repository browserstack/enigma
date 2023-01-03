from django.contrib.auth.decorators import login_required
import logging
from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
from django.shortcuts import render
from Access.userlist_helper import getAllUserList
from Access.accessrequest_helper import requestAccessGet, getGrantFailedRequests, getPendingRequests
from Access import group_helper

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
    if response['error']:
        return render(request, 'BSOps/accessStatus.html', response)
    
    return render(request,'BSOps/failureAdminRequests.html',response)


@login_required
@user_admin_or_ops
def pendingRevoke(request):
    return False


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
    context = getAllUserList(request)
    return render(request, 'BSOps/allUsersList.html', context)


@login_required
def requestAccess(request):
    context = requestAccessGet(request)
    return render(request, 'BSOps/accessRequestForm.html', context)


@login_required
def groupRequestAccess(request):
    return False

@api_view(["GET"])
@login_required
@user_with_permission(["ACCESS_APPROVE"])
def pendingRequests(request):
    context = getPendingRequests(request)
    return render(request, 'BSOps/pendingRequests.html', context)

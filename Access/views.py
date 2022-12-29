from django.contrib.auth.decorators import login_required
import logging
from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
from django.shortcuts import render
from Access.userlist_helper import getallUserList
from Access.accessrequest_helper import requestAccessGet, getGrantFailedRequests, getPendingRevokeFailures
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
        if context["status"] or context['error']:
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
    return render(request, 'BSOps/accessStatus.html',context)


@login_required
def groupRequestAccess(request):
    return False

@login_required
def groupAccessList(request, groupName):
    context = group_helper.getGroupAccessList(request, groupName)
    if context['error']:
        return render(request,"BSOps/accessStatus.html",context)
    
    return render(request,"BSOps/accessStatus.html",context)

def approveNewGroup(request, group_id):
    return group_helper.approveNewGroupRequest(request, group_id)

@login_required
def addUserToGroup(request, groupName):
    context =  group_helper.addUserToGroup(request, groupName)
    return render(request, 'BSOps/accessStatus.html',context)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging
from . import helpers as helper
from bootprocess.general import emailSES
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission
from rest_framework.authentication import TokenAuthentication,BasicAuthentication
from rest_framework.decorators import api_view

logger = logging.getLogger(__name__)

# Create your views here.
all_access_modules = helper.getAvailableAccessModules()

@login_required
def showAccessHistory(request):
  return False

@login_required
@user_admin_or_ops
def pendingFailure(request):
   return False

@login_required
@user_admin_or_ops
def pendingRevoke(request):
   return False

@login_required
def updateUserInfo(request):
    return False

@login_required
def createNewGroup(request):
    return False

@api_view(['GET'])
@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
@authentication_classes((TokenAuthentication, BasicAuthentication))
def allUserAccessList(request,load_ui = True):
    return False

@login_required
def allUsersList(request):
    return False

@login_required
def requestAccess(request):
    return False

@login_required
def groupRequestAccess(request):
    return False


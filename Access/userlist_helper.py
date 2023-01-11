from Access import helpers, views_helper, accessrequest_helper
from Access.models import User, UserAccessMapping, SshPublicKey
from bootprocess import general
from django.forms.models import model_to_dict
from django.core import serializers
import json

import logging
import threading
import traceback

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PERMISSION_VIEW_USER_LIST = "VIEW_USER_LIST"
PERMISSION_ALLOW_USER_OFFBOARD = "ALLOW_USER_OFFBOARD"

EXCEPTION_USER_UNAUTHORIZED = "Unauthorized to list users"
ERROR_MESSAGE = "Error in request not found OR Invalid request type"

def getAllUserList(request):
    try:
        if not (helpers.check_user_permissions(request.user, PERMISSION_VIEW_USER_LIST)):
            raise Exception(EXCEPTION_USER_UNAUTHORIZED)
        
        allowOffboarding = request.user.user.has_permission(PERMISSION_ALLOW_USER_OFFBOARD)
        
        dataList = []
        for each_user in User.objects.all():
            dataList.append({
                'name': each_user.name,
                'first_name': each_user.user.first_name,
                'last_name': each_user.user.last_name,
                'email': each_user.email,
                'username': each_user.user.username,
                'git_username': each_user.gitusername,
                'is_active': each_user.user.is_active,
                'offbaord_date': each_user.offbaord_date,
                'state': each_user.current_state()
            })
        context = {}
        context['dataList'] = dataList
        context['viewDetails'] = {
            'numColumns': 8 if allowOffboarding else 7,
            'allowOffboarding': allowOffboarding
        }
        return context
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response['error'] = {'error_msg': str(e), 'msg': ERROR_MESSAGE}
        return json_response

def bulk_approve(request, access_tag):
    context = {}
    user=User.objects.get(user__username=request.user)
    accesses = UserAccessMapping.objects.filter(status__in=["Processing", "Approved", "GrantFailed"],access__access_tag__in=[access_tag], user=user)
    if accesses:
      for access in accesses:
          access.status = "Processing"
          access.save()
          requestid = access.request_id
          requestObject =  UserAccessMapping.objects.get(request_id=access.request_id,user=user)
          accessAcceptThread = threading.Thread(target=views_helper.run_access_grant, args=(requestid, requestObject, requestObject.access.access_tag, requestObject.user, requestObject.approver_1.user.username))
          accessAcceptThread.start() 

    if len(accesses) >= 1:
      list = []
      for tags in access_tag:
        if (len(tags.split('_')[0])>3): list.append(tags.split('_')[0].capitalize())
        else: list.append(tags.split('_')[0].upper())

      context['status'] = {'title':'Regranted all the previous requests for: ' + ','.join(list) , 'msg': 'Details updated.'} 
    else:
      context['status'] = {'title':'No granted accesses found. Please request access for required modules. ' , 'msg': 'Request access. No details found.'} 
       
    return context


def update_user(request):
    context = {}
    try:
        userInfo = []
        userInfo.append(('confluenceusername', request.POST.get("confluenceusername")))
        userInfo.append(('slackusername', request.POST.get("slackusername")))
        userInfo.append(('zoomusername', request.POST.get("zoomusername")))
        userInfo.append(('awsusername', request.POST.get("awsusername")))
        userInfo.append(('opsgenieusername', request.POST.get("opsgenieusername")))
        userInfo.append(('gcpusername', request.POST.get("gcpusername")))
        userInfo.append(('gitusername', request.POST.get("gitusername")))
        userInfo.append(('ssh_public_key', request.POST.get("ssh_pub_key")))
        
        user=User.objects.get(user__username=request.user)
        msg = ''
        for info in userInfo:
          key = info[0]
          value = info[1]
          msg = update(user, key, value, msg)

        context = {}
        context['status'] = {'title':'Details Updated', 'msg': msg}
        return context
    except Exception as e:
        logger.exception(e)
        context['error'] = {'error':'Error ocurred while updating details.'}
        return context 
        
def update(user, key, value, msg):
    if key=='ssh_public_key':
      if not user.has_module_credentials[key] or value != user.has_module_credentials[key]['key']:
        new_ssh_key = SshPublicKey.objects.create(key = value).__dict__
        if user.ssh_public_key:
            user.ssh_public_key.status = "Revoked"
            user.ssh_public_key.save()
        user.update_module_credentials(key, new_ssh_key['key'])
        msg += "SSH Key updated.\n"
    else:
      if value and value != user.has_module_credentials[key]:
          if user.has_module_credentials[key] != None:
              #mark old accesses as grantfailed
              accesses = UserAccessMapping.objects.filter(status__in=["Approved", "Processing"],access__access_tag="github_access", user=user)
              for access in accesses:
                  access.status = "GrantFailed"
                  access.save()
          user.update_module_credentials(key, value)
          if (len(key.split('username')[0])>3): key = key.split('username')[0].capitalize()
          else:  key = key.split('username')[0].upper()

          msg += key + " Username updated.\n"
    
    return msg

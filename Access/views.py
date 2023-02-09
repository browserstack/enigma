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
from Access.userlist_helper import getallUserList, get_identity_templates, create_identity, NEW_IDENTITY_CREATE_ERROR_MESSAGE, IDENTITY_UNCHANGED_ERROR_MESSAGE, IdentityNotChangedException
from Access.views_helper import render_error_message
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS
from Access.background_task_manager import background_task
from bootprocess import general


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
    context = get_identity_templates(request.user)
    return render(request,'updateUser.html',context)


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
    except IdentityNotChangedException:
        context = {}
        context["error"] = {
            "title": IDENTITY_UNCHANGED_ERROR_MESSAGE["title"],
            "msg": IDENTITY_UNCHANGED_ERROR_MESSAGE["msg"].format(modulename = modname),
        }
        return JsonResponse(json.dumps(context), safe=False, status=400)

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
        if selector.endswith("-club"):
            for value in inputVals:
                returnIds.append(value)
                current_ids = list(UserAccessMapping.objects.filter(request_id__contains=value, status__in=["Pending", "SecondaryPending"]).values_list('request_id', flat=True))
                requestIds.extend(current_ids)
        else:
            requestIds = inputVals
        for value in requestIds:
            requestId = value
            if selector == "groupNew" and is_access_approver:
                json_response = group_helper.approve_new_group_request(
                    request, requestId
                )
            elif selector == "groupMember" and is_access_approver:
                json_response = group_helper.accept_member(request, requestId, False)
            elif selector.endswith("-club"):
                requestType = selector.rsplit("-",1)[0]
                json_response = preAcceptProcessing(request, requestType, requestId)
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

def preAcceptProcessing(request, access_type, requestId):
    print("in pre processing")
    json_response = {}
    approver_permissions, json_response = _get_approver_permissions(requestId, access_type)
    print(approver_permissions)
    print(json_response)
    if "erorr" in json_response:
        return json_response

    if not helper.check_user_permissions(request.user, list(approver_permissions.values())):
        logger.debug("Permission Denied!")
        json_response['error'] = "Permission Denied!"
        return json_response

    requestObject = UserAccessMapping.get_access_request(requestId)
    requester = requestObject.user_identity.user.email

    if requestObject.status in ['Declined','Approved','Processing','Revoked']:
        logger.warning("An Already Approved/Declined/Processing Request was accessed by - "+request.user.username)
        json_response['error'] = 'The Request ('+requestId+') is already Processed By : '+str(requestObject.approver_1)
        return json_response
    elif request.user.username == requester:
        json_response["error"] = "You cannot ̀approve your own request. Please ask other admins to do that"
        return json_response
    else:
        primary_approver_bool = requestObject.status == "Pending" and helper.check_user_permissions(request.user, [approver_permissions['1']])
        secondary_approver_bool = requestObject.status == "SecondaryPending" and helper.check_user_permissions(request.user, [approver_permissions['2']])
        if not (primary_approver_bool or secondary_approver_bool):
            logger.debug("Permission Denied!")
            json_response['error'] = "Permission Denied!"
            return json_response
        if primary_approver_bool and "2" in approver_permissions:
            requestObject.approver_1 = request.user.user
            json_response['msg'] = 'The Request ('+requestId+') is approved. Pending on secondary approver'
            requestObject.status = 'SecondaryPending'
            requestObject.save()
            logger.debug("Marked as SecondaryPending - "+requestId+" - Approver="+request.user.username)
        else:
            if primary_approver_bool:
                requestObject.approver_1 = request.user.user
            else:
                requestObject.approver_2 = request.user.user
            json_response['msg'] = 'The Request ('+requestId+') is now being processed'
            requestObject.status = 'Processing'
            requestObject.save()

            background_task("run_accept_request", json.dumps({"request_id": requestId, "access_type": access_type}))

            print("Process has been started for the Approval of request - "+requestId+" - Approver="+request.user.username)
            logger.debug("Process has been started for the Approval of request - "+requestId+" - Approver="+request.user.username)
        return json_response


@login_required
def decline_access(request,accessType,requestId):
    try:
        if request.GET:
            context = {"response":{}}
            user = request.user.user
            is_access_approver = user.has_permission("ACCESS_APPROVE")
            reason = request.GET["reason"]
            requestIds = []
            returnIds = []
            if accessType.endswith("-club"):
                for value in [requestId]: #ready for bulk decline
                    returnIds.append(value)
                    current_ids = list(UserAccessMapping.objects.filter(request_id__contains=value, status__in=["Pending", "SecondaryPending"]).values_list('request_id', flat=True))
                    requestIds.extend(current_ids)
                accessType = accessType.rsplit("-",1)[0]
            else:
                requestIds = [requestId]
            print("----------started------------")
            print(requestIds)
            for requestId in requestIds:
                response = declineIndividualAccess(request, accessType, requestId, reason)
                print("response: ")
                print(response)
                if "error" in response:
                    response["success"] = False
                else:
                    response["success"] = True
                context["response"][requestId] = response
            context["returnIds"] = returnIds
            print("----------end------------")
            return JsonResponse(context, status = 200)
    except Exception as e:
        json_response = {}
        logger.error("Error in rejecting the request. Please contact admin - "+str(str(e)))
        json_response['error'] = "Error in rejecting the request. Please contact admin - "+str(str(e))
        json_response['status_code'] = 401
        return JsonResponse(json_response, status = json_response["status_code"])

def declineIndividualAccess(request, access_type, requestId, reason):
    json_response = {}
    approver_permissions, json_response = _get_approver_permissions(requestId, access_type)
    if "error" in json_response:
        return json_response

    requestObject = UserAccessMapping.get_access_request(requestId)

    if "2" in approver_permissions and requestObject.status == "SecondaryPending":
        if not helper.check_user_permissions(request.user, approver_permissions["2"]):
            logger.debug("Permission Denied!")
            json_response['error'] = "Permission Denied!"
            return json_response
    elif "2" in approver_permissions and requestObject.status == "Pending":
        if not helper.check_user_permissions(request.user, approver_permissions["1"]):
            logger.debug("Permission Denied!")
            json_response['error'] = "Permission Denied!"
            return json_response

    if requestObject.status in ['Declined','Approved','Processing','Revoked']:
        json_response = {}
        approver = None
        if requestObject.approver_2:
            approver = requestObject.approver_2.user.username
        else:
            approver = requestObject.approver_1.user.username
        json_response['error'] = 'The Request ('+requestId+') is already Processed By : '+approver
        logger.warning("Already processed request -"+requestId+" accessed in decline request by-"+request.user.username)
        return json_response

    user = requestObject.user_identity.user

    try:
        requestObject.status='Declined'
        if hasattr(requestObject, 'approver_1'):
            requestObject.decline_reason=reason
            if requestObject.approver_1 != None:
                requestObject.approver_2=request.user.user
            else:
                requestObject.approver_1=request.user.user
        else:
            requestObject.reason=reason
            requestObject.approver=request.user.username

        requestObject.save()
        body="Request by "+user.email+" for "+requestId+" is declined by "+request.user.username+ '.<br>Reason: '+reason
        destination=[user.email]
        access_module = helper.get_available_access_modules()[access_type]
        access_labels = [requestObject.access.access_label]
        description = access_module.combine_labels_desc(access_labels)
        subject = "[Enigma][Access Management] " + user.email + " - " + access_type + " - " + description + " Request Denied"
        # emailThread = threading.Thread(target=emailSES, args=(destination,subject,body))
        # emailThread.start()
        general.emailSES(destination,subject,body)
        logger.debug("Declined Request "+requestId+" By-"+request.user.username+ " Reason: "+reason)
        json_response = {}
        json_response['msg'] = 'The Request ('+requestId+') is now Declined'
        return json_response
    except Exception as e:
        logger.exception(e)
        requestObject.status='Pending'
        requestObject.save()

        helper.error_helper("Error in Decline of request "+requestId+" error:"+str(e),
        "Error in Decline of "+requestId+" Request",
        "Error msg : "+str(e), [user.email, request.user.email])

        json_response = {}
        json_response['error'] = "Error in rejecting the request. Please contact admin - "+str(e)
        return json_response

def _get_approver_permissions(request_id, access_type):
    err_message = {}
    try:
        approver_permissions = {
            "1": "ACCESS_APPROVE"
        }
        found_generic_type = False
        access_module = helper.get_available_access_modules()[access_type]
        try:
            access_label = None
            req_obj = UserAccessMapping.get_access_request(request_id)
            if req_obj is not None:
                try:
                    access_label = req_obj.access.access_label
                except:
                    pass
                    approver_permissions = access_module.fetch_approver_permissions(access_label) if access_label is not None else access_module.fetch_approver_permissions()
        except:
            pass
        found_generic_type = True
        if not found_generic_type:
            logger.debug("Invalid Params passed!")
            err_message['error'] = "Invalid Params passed!"
            return None, err_message
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type - "+str(e))
        err_message['error'] = "Error in request not found OR Invalid request type - "+str(e)
        return None, err_message

    return approver_permissions, err_message

def remove_group_member(request):
    try:
        response = group_helper.remove_member(request)
        if "error" in response:
            return JsonResponse(response, status=400)
        return JsonResponse({"message": "Success"})
    except Exception as e:
        logger.exception(str(e))
        return JsonResponse({"error": "Failed to remove the user"}, status=400)

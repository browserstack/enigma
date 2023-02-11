from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth.models import User as djangoUser
from .models import UserAccessMapping
from Access import views_helper
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
import json
import math
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

INVALID_REQUEST_MESSAGE = "Error in request not found OR Invalid request type"

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

    page = int(request.GET.get('page') or 1) - 1
    limit = 20

    start_index = page * limit
    max_pagination = math.ceil(access_user.get_total_access_count() / limit)

    return render(
        request,
        "BSOps/showAccessHistory.html",
        {
            "dataList": access_user.get_access_history(
                helper.get_available_access_modules(),
                start_index,
                limit,
            ),
            "maxPagination": max_pagination,
            "allPages": range(1, max_pagination + 1),
            "currentPagination": page + 1,
        },
    )

@login_required
def new_access_request(request):
    if request.method == "POST":
        return render_error_message(
            request,
            "POST for this endpoint is not supported",
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
        "BSOps/newAccessRequest.html",
        {
            "modulesList": helper.get_available_access_modules(),
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
        logger.debug(INVALID_REQUEST_MESSAGE + " - " + str(str(e)))
        json_response = {}
        json_response['error'] = INVALID_REQUEST_MESSAGE + " - " + str(str(e))
        json_response["success"] = False
        json_response["status_code"] = 401
        return JsonResponse(json_response, status=json_response["status_code"])


def remove_group_member(request):
    try:
        response = group_helper.remove_member(request)
        if "error" in response:
            return JsonResponse(response, status=400)
        return JsonResponse({"message": "Success"})
    except Exception as e:
        logger.exception(str(e))
        return JsonResponse({"error": "Failed to remove the user"}, status=400)


@api_view(['GET'])
@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
@authentication_classes((TokenAuthentication, BasicAuthentication))
def all_user_access_list(request, load_ui=True):
    user = None
    page = 1
    try:
        if request.GET.get('username'):
            username = request.GET.get('username')
            user = djangoUser.objects.get(username=username)
    except Exception as e:
        # show all
        logger.exception(e)

    try:
        data_list = []
        last_page = 1
        show_tabs = False
        username = ""
        generic_accesses = UserAccessMapping.get_accesses_not_declined()
        response_type = request.GET.get('responseType', "ui")
        load_ui = request.GET.get('load_ui', "true").lower() == "true"
        record_date = request.GET.get('recordDate', None)

        if user:
            generic_accesses = generic_accesses.filter(
                user_identity__user=user.user).order_by("-requested_on")
            show_tabs = True
            username = user.username
        elif "usersearch" in request.GET:
            generic_accesses = generic_accesses.filter(
                user_identity__user__user__username__icontains=request.GET.get('usersearch')) \
                .order_by("user_identity__user__user__username")
        else:
            generic_accesses = generic_accesses.order_by("user_identity__user__user__username")

        filters = views_helper.get_filters_for_access_list(request)
        generic_accesses = generic_accesses.filter(**filters)

        page = int(request.GET.get('page', 1))

        if load_ui and response_type != "csv":
            paginator_obj = Paginator(generic_accesses, 10)
            last_page = paginator_obj.num_pages
            page = min(page, last_page) if page > last_page else page
            paginator = paginator_obj.page(page)
        else:
            paginator = generic_accesses

        access_types = list(set(generic_accesses.values_list("access__access_tag", flat=True)))

        data_list = views_helper.prepare_datalist(paginator=paginator, record_date=record_date)

        context = {}
        logger.debug(data_list)

        data_dict = {
            'dataList': data_list,
            'last_page': last_page,
            'current_page': page,
            'access_types': sorted(access_types, key=str.casefold),
            'show_tabs': show_tabs,
            'username': username
        }

        context.update(data_dict)

        if response_type == "json":
            return JsonResponse(context, status=200)
        elif response_type == "csv":
            return views_helper.gen_all_user_access_list_csv(data_list=data_list)
        if load_ui:
            return render(request, 'BSOps/allUserAccessList.html', context)
        else:
            return JsonResponse(context)

    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response['error'] = {'error_msg': str(e), 'msg': INVALID_REQUEST_MESSAGE}
        return render(request, 'BSOps/accessStatus.html', json_response)


@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
def mark_revoked(request):
    json_response = {}
    status = 200
    request_id = None
    try:
        request_id = request.GET.get("requestId")
        if request_id.startswith("module-"):
            username = request.GET.get("username")
            if not username:
                json_response["error"] = "Username is invalid!"
                status = 403
                return JsonResponse(json_response, status=status)
            access_tag = request_id.split("-", 1)[1]
            user = User.get_user_from_username(username=username)
            if user:
                requests = user.get_accesses_by_access_tag_and_status(access_tag=access_tag, status=["Approved", "Offboarding"])
            else:
                raise User.DoesNotExist(f"User with username '{username}' does not exist")
        else:
            requests = UserAccessMapping.get_unrevoked_accesses_by_request_id(request_id=request_id)
        success_list = []
        for mapping_object in requests:
            logger.info("Marking access revoke - %s by user %s "
                        % (mapping_object.request_id, request.user.user))
            mapping_object.revoke(revoker=request.user.user)
            success_list.append(mapping_object.request_id)
        json_response["msg"] = "Success"
        json_response["request_ids"] = success_list
    except Exception as e:
        logger.exception(str(e))
        json_response["error"] = str(e)
        status = 403
    return JsonResponse(json_response, status=status)

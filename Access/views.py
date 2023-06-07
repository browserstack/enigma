"""Django views."""
import json
import logging
import traceback
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth.models import User as djangoUser
from django.http import JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse

from Access import views_helper
from Access import group_helper
from Access.accessrequest_helper import (
    get_request_access,
    get_grant_failed_requests,
    get_pending_revoke_failures,
    get_pending_requests,
    create_request,
    accept_user_access_requests,
    get_decline_access_request,
    accept_group_access,
    run_accept_request_task,
    run_ignore_failure_task,
    ImplementationPendingException,
    REQUEST_FAILED_MSG
)
from Access.models import User, UserAccessMapping, GroupAccessMapping

from Access.userlist_helper import (
    getallUserList,
    get_identity_templates,
    create_identity,
    offboard_user,
    NEW_IDENTITY_CREATE_ERROR_MESSAGE,
    IDENTITY_UNCHANGED_ERROR_MESSAGE,
    IdentityNotChangedException,
)
from Access.views_helper import render_error_message
from enigma_automation.settings import PERMISSION_CONSTANTS
from . import helpers as helper
from .decorators import user_admin_or_ops, authentication_classes, user_with_permission, user_any_approver

INVALID_REQUEST_MESSAGE = "Error in request not found OR Invalid request type"
IMPLEMENTATION_PENDING_ERROR_MESSAGE = {
    "error_msg": "Failed to process the request",
    "msg": "Implementation of the {feature_name} feature is pending."
}

logger = logging.getLogger(__name__)
logger.info("Server Started")


@login_required
@paginated_search
def show_access_history(request):
    """Show access request history for a User."""
    if request.method == "POST":
        return render_error_message(
            request,
            "POST for showAccessHistory not supported",
            "Invalid Request",
            "Error request not found OR Invalid request type",
        )

    try:
        access_user = User.objects.get(email=request.user.email)
    except Exception as ex:
        return render_error_message(
            request,
            f"Access user with email {request.user.email} not found. Error: {str(ex)}",
            "Invalid Request",
            "Please login again",
        )

    selected_status = request.GET.getlist("status")
    selected_access_modules = request.GET.getlist("access_desc")

    context = {
        "dataList": access_user.get_access_history(
            helper.get_available_access_modules()
        ),
        "search_data_key": "dataList",
        "search_rows": ["access_desc", "access_tag", "requestId"],
        "filter_rows": ["status", "access_desc"],
        "possibleStatuses": {
            "selected": selected_status,
            "notSelected": [status for status in UserAccessMapping.get_unique_statuses()
                            if status not in selected_status]
        },

        "possibleAccessModules": {
            "selected": selected_access_modules,
            "notSelected": [access_desc for access_desc in helper.get_available_access_module_desc()
                            if access_desc not in selected_access_modules]
        },

        "search_value": request.GET.get('search')
    }
    print(context["dataList"][0])

    return TemplateResponse(request, "EnigmaOps/showAccessHistory.html"), context


@login_required
def new_access_request(request):
    """ new access request """
    if request.method == "POST":
        return render_error_message(
            request,
            "POST for this endpoint is not supported",
            "Invalid Request",
            "Error request not found OR Invalid request type",
        )

    try:
        User.objects.get(email=request.user.email)
    except Exception as exc:
        return render_error_message(
            request,
            f"Access user with email {request.user.email} not found. Error: {str(exc)}",
            "Invalid Request",
            "Please login again",
        )

    return render(
        request,
        "EnigmaOps/newAccessRequest.html",
        {
            "modulesList": helper.get_available_access_modules(),
        },
    )


@login_required
@user_admin_or_ops
def pending_failure(request):
    """Access requests where grant failed."""
    try:
        response = get_grant_failed_requests(request)
        return render(request, "EnigmaOps/failureAdminRequests.html", response)
    except Exception as ex:
        logger.error(
            "Error in request not found OR Invalid request type, Error: %s", str(ex)
        )
        json_response = {}
        json_response["error"] = {"error_msg": str(ex), "msg": INVALID_REQUEST_MESSAGE}
        return render(request, "EnigmaOps/accessStatus.html", json_response)


@login_required
@user_admin_or_ops
def pending_revoke(request):
    """Access requests where the revoke failed."""
    try:
        response = get_pending_revoke_failures(request)
        return render(request, "EnigmaOps/failureAdminRequests.html", response)
    except Exception as ex:
        logger.debug(
            "Error in request not found OR Invalid request type, Error: %s", str(ex)
        )
        json_response = {}
        json_response["error"] = {"error_msg": str(ex), "msg": INVALID_REQUEST_MESSAGE}
        return render(request, "EnigmaOps/accessStatus.html", json_response)


@login_required
def update_user_info(request):
    """Templates to capture indentity information,
    with already saved Identity information for access modules"""
    context = get_identity_templates(request.user)
    return render(request, "updateUser.html", context)


@api_view(["POST"])
@login_required
def save_identity(request):
    """save the identity information for the user.

    Args:
        request (HTTPRequest): User Identity information for different access modules.

    Returns:
        JsonResponse: success message if the identity is saved or
        failure message in case of failure.
    """
    context = {}
    modname = ""
    try:
        modname = request.POST.get("modname")
        if request.POST:
            context = create_identity(
                user_identity_form=request.POST, auth_user=request.user
            )
            return JsonResponse(json.dumps(context), safe=False, status=200)
    except IdentityNotChangedException:
        context["error"] = {
            "title": IDENTITY_UNCHANGED_ERROR_MESSAGE["title"],
            "msg": IDENTITY_UNCHANGED_ERROR_MESSAGE["msg"].format(modulename=modname),
        }
        return JsonResponse(json.dumps(context), safe=False, status=200)

    except Exception:
        context["error"] = {
            "title": NEW_IDENTITY_CREATE_ERROR_MESSAGE["title"],
            "msg": NEW_IDENTITY_CREATE_ERROR_MESSAGE["msg"].format(modulename=modname),
        }
        return JsonResponse(json.dumps(context), safe=False, status=200)
    context["error"] = {
        "title": "Bad Request",
        "msg": "Invalid Request.",
    }
    return JsonResponse(json.dumps(context), safe=False, status=400)


@login_required
def create_new_group(request):
    """Template to capture new group info, or status of save request."""
    if request.POST:
        context = group_helper.create_group(request)
        if "status" in context or "error" in context:
            return render(request, "EnigmaOps/accessStatus.html", context)
        return render(request, "EnigmaOps/createNewGroup.html", context)
    return render(request, "EnigmaOps/createNewGroup.html", {})


@login_required
def all_users_list(request):
    """List of all users."""
    context = getallUserList(request)
    return render(request, "EnigmaOps/allUsersList.html", context)


@login_required
def user_offboarding(request):
    """offboard a user.

    Args:
        request (HTTPRequest):  Details of the user to be offboarded.

    Returns:
        JsonResponse: success message if the User offboarding succeeds or
        failure message in case it fails.
    """
    try:
        response = offboard_user(request)
        if "error" in response:
            return JsonResponse(response, status=400)

        return JsonResponse(response)
    except Exception as ex:
        logger.exception("Error offboarding user: Error: %s", str(ex))
        return JsonResponse({"error": "Failed to offboard User"}, status=400)


@login_required
def request_access(request):
    """Request access to a module.

    Args:
        request (HTTPRequest): Access module form details.

    Returns:
        HTTPResponse: Access request form template or the status of access save request.
    """
    if request.POST:
        print((request.POST))
        context = create_request(
            auth_user=request.user, access_request_form=request.POST
        )
        return render(request, "EnigmaOps/accessStatus.html", context)

    context = get_request_access(request)
    return render(request, "EnigmaOps/accessRequestForm.html", context)


@login_required
def new_group_access_request(request):
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

    context = {
        "modulesList": helper.get_available_access_modules(),
        "groupName": dict(request.GET.lists())["groupName"][0]
    }
    return render(request, "EnigmaOps/newAccessGroupRequest.html", context)


@login_required
def group_access(request):
    """Request access to a group.

    Args:
        request (HTTPRequest): Group access form details.

    Returns:
        HTTPResponse: access request form template or
        status of whether the group access save request.
    """
    if request.POST:
        status = 200
        try:
            context = group_helper.save_group_access_request(request.POST, request.user)
            if "error" in context :
                status = 400
        except Exception as exception:
            print(exception)
            status = 500
            context = {
                "error" : group_helper.GROUP_REQUEST_ERR_MSG
            }
        return JsonResponse(context, status=status)

    context = group_helper.get_group_access(request.GET, request.user)
    if "status" in context:
        return render(request, 'EnigmaOps/accessStatus.html',context)
    return render(request, "EnigmaOps/groupAccessRequestForm.html", context)


@login_required
@paginated_search
def group_access_list(request):
    """lists the accesses for a group."""
    try:
        group_name = request.GET.get('group_name')
        group_detail = group_helper.get_group_access_list(request.user, group_name)
        if "error" in group_detail:
            return TemplateResponse(request, "EnigmaOps/accessStatus.html"), group_detail

        group_detail = group_helper.get_role_based_on_membership(group_detail)
        context = {
            "search_value": request.GET.get("search"),
            "groupName": group_name,
            "allowRevoke": group_detail["allowRevoke"]
        }

        show_tab = request.GET.get("show_tab")
        if show_tab == "membersList":
            selected_role = request.GET.getlist("role")
            selected_current_state = request.GET.getlist("current_state")
            context["roleFilter"] = {
                "selected": selected_role,
                "notSelected": group_helper.get_group_member_role_list(selected_role)
            }
            context["currentStateFilter"] = {
                "selected": selected_current_state,
                "notSelected": group_helper.get_user_states(selected_current_state)
            }
            context["search_data_key"] = "userList"
            context["search_rows"] = ["name", "email"]
            context["filter_rows"] = ["role", "current_state"]
            context["userList"] = group_detail["userList"]
            context["isMembersList"] = True
        else:
            selected_access_type = request.GET.getlist("accessType")
            selected_status = request.GET.getlist("status")
            context["accessTypeFilter"] = {
                "selected": selected_access_type,
                "notSelected": group_helper.get_group_member_access_type(selected_access_type)
            }
            context["statusFilter"] = {
                "selected": selected_status,
                "notSelected": group_helper.get_group_status_list(selected_status),
            }
            context["search_data_key"] = "dataList"
            context["search_rows"] = ["module", "status", "accessType"]
            context["dataList"] = group_detail['genericAccesses']
            context["filter_rows"] = ["accessType", "status"]

        return TemplateResponse(
            request,
            "EnigmaOps/groupAccessList.html"), context
    except Exception as ex:
        logger.exception(
            "Error in Group Access List, Error: %s", str(ex)
        )
        json_response = {}
        json_response["error"] = {
            "error_msg": INVALID_REQUEST_MESSAGE,
            "msg": INVALID_REQUEST_MESSAGE,
        }
        return TemplateResponse(request, "EnigmaOps/accessStatus.html"), json_response


@login_required
def update_group_owners(request, group_name):
    """Update owner of a group.

    Args:
        request (HTTPRequest): forms data with User to be added as owner.
        group_name (str): Name of the group.

    Returns:
        JsonResponse: status message of the update request.
    """
    try:
        context = group_helper.update_owners(request, group_name)
        if "error" in context:
            return JsonResponse(context, status=400)

        return JsonResponse(context, status=200)
    except Exception as ex:
        logger.debug(
            "Error in request not found OR Invalid request type, Error: %s", str(ex)
        )
        json_response = {}
        json_response["error"] = INVALID_REQUEST_MESSAGE
        return JsonResponse(json_response, status=400)


@login_required
@paginated_search
def group_dashboard(request):
    """ view group dashboard """
    if request.method == "POST":
        return render_error_message(
            request,
            "POST for groupHistory not supported",
            "Invalid Request",
            "Error request not found OR Invalid request type",
        )

    try:
        access_user = request.user.user
    except Exception as exc:
        return render_error_message(
            request,
            f"Access user with email {request.user.email} not found. Error: {str(exc)}",
            "Invalid Request",
            "Please login again",
        )

    selected_role = request.GET.getlist("role")
    selected_status = request.GET.getlist("status")

    context = {
        "search_data_key": "dataList",
        "search_rows": ["name"],
        "dataList": access_user.get_groups_history(),
        "statusFilter": {
            "selected": selected_status,
            "notSelected": group_helper.get_group_status_list(selected_status),
        },
        "roleFilter": {
            "selected": selected_role,
            "notSelected": group_helper.get_group_member_role_list(selected_role)
        },
        "search_value": request.GET.get("search"),
        "filter_rows": ["role", "status"]
    }
    return TemplateResponse(
        request,
        "EnigmaOps/showGroupHistory.html"), context


def approve_new_group(request, group_id):
    """Approve a new group request.

    Args:
        request (HTTPRequest): Details of the request approver.
        group_id (str): ID of the group to be approved.

    Returns:
        HTTPResponse: Status of the request approval.
    """
    return group_helper.approve_new_group_request(request, group_id)


@login_required
def add_user_to_group(request, group_name):
    """Add one or more users to a group.

    Args:
        request (HTTPRequest): Details of user to be added to group.
        groupName (str): Name of the group.

    Returns:
        HTTPResponse: Status of the add request for each user.
    """
    if request.POST:
        context = group_helper.add_user_to_group(request)
        return render(request, "EnigmaOps/accessStatus.html", context)

    context = group_helper.get_user_group(request, group_name)
    all_users = User.objects.filter().exclude( user__username='system_user').only("user")
    context["users"] = []
    for user in all_users :
        if user not in context["groupMembers"] :
            context["users"].append(user)
    return render(request, "EnigmaOps/addUserToGroupForm.html", context)


@api_view(["GET"])
@login_required
@user_any_approver
def pending_requests(request):
    """pending access requests"""
    context = get_pending_requests(request)
    return render(request, "EnigmaOps/pendingRequests.html", context)


@login_required
def accept_bulk(request, selector):
    """approve one or more access request.

    Args:
        request (HTTPRequest): Details of access and access approver.
        selector (str): access type being approved.

    Raises:
        ValidationError: incorrect access type passed in selector

    Returns:
        JsonResponse: status of request accept.
    """
    try:
        context = {"response": {}}
        input_vals = request.GET.getlist("requestId")
        user = request.user.user
        is_access_approver = user.has_permission("ACCESS_APPROVE")
        request_ids, return_ids, selector = _get_request_ids_for_bulk_processing(
            input_vals, selector
        )
        for value in request_ids:
            request_id = value
            if selector == "groupNew" and is_access_approver:
                json_response = group_helper.approve_new_group_request(
                    request.user, request_id
                )
            elif selector == "groupMember" and is_access_approver:
                json_response = group_helper.accept_member(
                    request.user, request_id, False
                )
            elif selector == "groupAccess":
                json_response = accept_group_access(request.user, request_id)
            elif selector == "moduleAccess":
                json_response = accept_user_access_requests(request.user, request_id)
            else:
                raise ValidationError("Invalid request")
            if "error" in json_response:
                context["response"][request_id] = {
                    "error": json_response["error"],
                    "success": False,
                }
            else:
                context["response"][request_id] = {
                    "msg": json_response["msg"],
                    "success": True,
                }
        context["bulk_approve"] = True
        context["returnIds"] = return_ids
        return JsonResponse(context, status=200)
    except Exception:
        logger.error("Error processing bulk accept, Error: %s", traceback.format_exc())
        json_response = {}
        json_response["error"] = INVALID_REQUEST_MESSAGE
        json_response["success"] = False
        return JsonResponse(json_response, status=400)


def _get_request_ids_for_bulk_processing(posted_request_ids, selector):
    input_vals = posted_request_ids
    return_ids = []
    access_request_ids = []
    if selector.endswith("-club"):
        for value in input_vals:
            return_ids.append(value)
            current_ids = list(
                UserAccessMapping.get_pending_access_mapping(request_id=value)
            )
            access_request_ids.extend(current_ids)
        selector = "moduleAccess"
    elif selector == "clubGroupAccess":
        for value in input_vals:
            return_ids.append(value)
            group_name, date_suffix = value.rsplit("-", 1)
            current_ids = list(
                GroupAccessMapping.get_pending_access_mapping(
                    request_id=group_name
                ).filter(request_id__icontains=date_suffix)
            )
            access_request_ids.extend(current_ids)
        selector = "groupAccess"
    else:
        access_request_ids = input_vals
    logger.debug("Got the ids %s for bulk processing", (",".join(access_request_ids)))
    return access_request_ids, return_ids, selector


@login_required
@user_any_approver
def decline_access(request, access_type, request_id):
    """Decline an access request.

    Args:
        request (HTTPRequest): Details of the User declining access.
        access_type (str): Type of access
        request_id (str): Access Request ID.

    Returns:
        JsonResponse: Status of decline request.
    """
    if request.GET:
        try:
            context = get_decline_access_request(request, access_type, request_id)
            return JsonResponse(context, status=200)
        except Exception:
            logger.exception("Error declining access, Error: %s", traceback.format_exc())
            return JsonResponse(
                {"error": "Failed to decline the access request"}, status=400
            )
    return JsonResponse({"error": "Invalid request"}, status=400)


def remove_group_member(request):
    """Remove a user from a group.

    Args:
        request (HTTPRequest): Details of the User to be removed from group.

    Returns:
        JsonResponse: Status of the User remove.
    """
    try:
        response = group_helper.remove_member(request, request.user)
        if "error" in response:
            return JsonResponse(response, status=400)
        return JsonResponse({"message": "Success"})
    except Exception:
        logger.exception("Error removing memeber from group, Error: %s", traceback.format_exc())
        return JsonResponse({"error": "Failed to remove the user"}, status=400)


def get_generic_accesses(request, user, generic_accesses, show_tabs, username):
    """ method to get generic accesses """
    if user:
        generic_accesses = generic_accesses.filter(
            user_identity__user=user.user
        ).order_by("-requested_on")
        show_tabs = True
        username = user.username
    elif "usersearch" in request.GET:
        generic_accesses = generic_accesses.filter(
            user_identity__user__user__username__icontains=request.GET.get(
                "usersearch"
            )
        ).order_by("user_identity__user__user__username")
    else:
        generic_accesses = generic_accesses.order_by(
            "user_identity__user__user__username"
        )
    return generic_accesses, show_tabs, username


@api_view(["GET"])
@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
@authentication_classes((TokenAuthentication, BasicAuthentication))
def all_user_access_list(request, load_ui=True):
    """Lists all the user with the access of the users.

    Args:
        request (HTTPRequest): Filtering crtieria for the list of user data.
        load_ui (bool, optional): Data to be returned for UI or in a file.

    Returns:
        HTTPResponse: List of all users with access details.
    """
    user = None
    try:
        if request.GET.get("username"):
            username = request.GET.get("username")
            user = djangoUser.objects.get(username=username)
    except Exception:
        # show all
        logger.exception("Error raised in all_user_access_list: %s", (traceback.format_exc()))

    try:
        last_page = 1
        show_tabs = False
        username = ""
        generic_accesses = UserAccessMapping.get_accesses_not_declined()
        response_type = request.GET.get("responseType", "ui")
        load_ui = request.GET.get("load_ui", "true").lower() == "true"
        record_date = request.GET.get("recordDate", None)

        generic_accesses, show_tabs, username = \
            get_generic_accesses(request, user, generic_accesses, show_tabs, username)

        filters = views_helper.get_filters_for_access_list(request)
        generic_accesses = generic_accesses.filter(**filters)

        page = int(request.GET.get("page", 1))

        if load_ui and response_type != "csv":
            paginator_obj = Paginator(generic_accesses, 10)
            last_page = paginator_obj.num_pages
            page = min(page, last_page) if page > last_page else page
            paginator = paginator_obj.page(page)
        else:
            paginator = generic_accesses

        access_types = list(
            set(generic_accesses.values_list("access__access_tag", flat=True))
        )

        data_list = views_helper.prepare_datalist(
            paginator=paginator, record_date=record_date
        )

        context = {}
        logger.debug(data_list)

        data_dict = {
            "dataList": data_list,
            "last_page": last_page,
            "current_page": page,
            "access_types": sorted(access_types, key=str.casefold),
            "show_tabs": show_tabs,
            "username": username,
        }

        context.update(data_dict)

        if response_type == "json":
            return JsonResponse(context, status=200)
        if response_type == "csv":
            return views_helper.gen_all_user_access_list_csv(data_list=data_list)
        if load_ui:
            return render(request, "EnigmaOps/allUserAccessList.html", context)

        return JsonResponse(context)

    except Exception:
        logger.exception(
            """Error fetching all users access list,
                        request not found OR Invalid request type, Error: %s""",
            traceback.format_exc(),
        )
        json_response = {}
        json_response["error"] = {
            "error_msg": INVALID_REQUEST_MESSAGE,
            "msg": INVALID_REQUEST_MESSAGE,
        }
        return render(request, "EnigmaOps/accessStatus.html", json_response)


@login_required
@user_with_permission(["VIEW_USER_ACCESS_LIST"])
def mark_revoked(request):
    """Revoke an access

    Args:
        request (HTTPRequest): Details of the access to be revoked.

    Raises:
        User.DoesNotExist: User does not exists.

    Returns:
        HTTPResponse: Status of the Revoke request.
    """
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
                requests = user.get_accesses_by_access_tag_and_status(
                    access_tag=access_tag, status=["Approved", "Offboarding"]
                )
            else:
                raise Exception(f"User with username '{username}' does not exist")
        else:
            requests = UserAccessMapping.get_unrevoked_accesses_by_request_id(
                request_id=request_id
            )
        success_list = []
        for mapping_object in requests:
            logger.info(
                "Marking access revoke - %s by user %s",
                mapping_object.request_id,
                request.user.user,
            )
            mapping_object.revoke(revoker=request.user.user)
            success_list.append(mapping_object.request_id)
        json_response["msg"] = "Success"
        json_response["request_ids"] = success_list
    except Exception:
        logger.exception("Error Revoking User Access, Error: %s", traceback.format_exc())
        json_response["error"] = "Error Revoking User Access"
    return JsonResponse(json_response, status=403)


def individual_resolve(request):
    """ method to resolve individually """
    json_response = {"status_list": []}
    try:
        request_ids = request.GET.getlist("requestId")
        if not request_ids:
            raise Exception("Request id not found in the request")

        for request_id in request_ids:
            user_access_mapping = UserAccessMapping.get_access_request(request_id)
            if user_access_mapping.status.lower() in ["grantfailed", "approved"]:
                response = run_accept_request_task(
                    False,
                    user_access_mapping,
                    request.user,
                    user_access_mapping.request_id,
                    user_access_mapping.access.access_label,
                )
                json_response["status_list"] += response["status"]
            else:
                json_response["status_list"].\
                    append({'title': 'The Request (' + request_id + ') is already resolved.',
                            'msg': 'The request is already in final state.'})
        return render(request, 'EnigmaOps/accessStatus.html', json_response)
    except Exception:
        logger.exception("Error raised during individual_resolve %s", (traceback.format_exc()))
        json_response["error"] = {
            "error_msg": "Bad request",
            "msg": "Error in request not found OR Invalid request type",
        }
        return render(request, "EnigmaOps/accessStatus.html", json_response)


@login_required
@user_with_permission([PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]])
def ignore_failure(request, selector):
    """ method to ignore failure of the request """
    try:
        json_response = {"status_list": []}
        request_ids = request.GET.getlist("requestId")
        for request_id in request_ids:
            user_access_mapping = UserAccessMapping.get_access_request(request_id)
            if user_access_mapping.status.lower() in ["grantfailed", "revokefailed"]:
                run_ignore_failure_task(
                    request.user,
                    user_access_mapping,
                    user_access_mapping.request_id,
                    selector,
                )
                json_response["status_list"].append(
                    {
                        "title": "The Request ("
                        + request_id
                        + ") is now being ignored. Mark - "
                        + selector,
                        "msg": "A email will be sent after the requested access is ignored",
                    }
                )
            else:
                logger.debug("Cannot ignore %s", request_id)
                json_response["status_list"].append(
                    {
                        "title": "The Request ("
                        + request_id
                        + ") is already resolved.",
                        "msg": "The request is already in final state.",
                    }
                )
        return render(request, "EnigmaOps/accessStatus.html", json_response)
    except Exception as exc:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception("Error while executing ignore_failure: %s", (traceback.format_exc()))
        json_response = {}
        json_response["error"] = {
            "error_msg": str(exc),
            "msg": "Error in request not found OR Invalid request type",
        }
        return render(request, "EnigmaOps/accessStatus.html", json_response)


@login_required
@user_with_permission([PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]])
def resolve_bulk(request):
    """ method to resolve requests in bulk """
    try:
        json_response = {"status_list": []}
        request_ids = request.GET.getlist("requestId")
        for request_id in request_ids:
            user_access_mapping = UserAccessMapping.get_access_request(request_id)
            if user_access_mapping.status.lower() in ["grantfailed"]:
                response = run_accept_request_task(
                    False,
                    user_access_mapping,
                    request.user,
                    user_access_mapping.request_id,
                    user_access_mapping.access.access_label,
                )
                json_response["status_list"] += response["status"]
            else:
                json_response["status_list"].append(
                    {
                        "title": "The Request ("
                        + request_id
                        + ") is already resolved.",
                        "msg": "The request is already in final state.",
                    }
                )
        return render(request, "EnigmaOps/accessStatus.html", json_response)
    except Exception:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception("Raised error during resolve_bulk: %s", (traceback.format_exc()))
        json_response = {}
        json_response['error'] = {'error_msg': "Bad request",
                                  'msg': "Error in request not found OR Invalid request type"}
        return render(request, 'EnigmaOps/accessStatus.html', json_response)


def revoke_group_access(request):
    """ method to revoke group access """
    try:
        response = group_helper.revoke_access_from_group(request)
        if "error" in response:
            return JsonResponse(response, status=400)

        return JsonResponse(response)
    except Exception:
        logger.exception("Error while revoking group access %s", (traceback.format_exc()))
        logger.debug("Something went wrong while revoking group access")
        return JsonResponse({"message": "Failed to revoke group Access"}, status=400)


def error_404(request, _exception, template_name='404.html'):
    """ render template for 404 error code """
    data = {}
    return render(request, template_name, data)


def error_500(request, template_name='500.html'):
    """ render template for 500 error code """
    data = {}
    return render(request, template_name, data)

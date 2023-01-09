from Access import helpers
import logging
import time

from BrowserStackAutomation.settings import DECLINE_REASONS
from Access.models import UserAccessMapping, User, GroupV2, MembershipV2

logger = logging.getLogger(__name__)

def requestAccessGet(request):
    context = {}
    try:
        for each_access in helpers.getAvailableAccessModules():
            if "access_" + each_access.tag() in request.GET.getlist('accesses'):
                if 'accesses' not in context:
                    context['accesses'] = []
                    context['genericForm'] = True
                    try:
                        extra_fields = each_access.get_extra_fields()
                    except:
                        extra_fields = []
                    try:
                        notice = each_access.get_notice()

                    except Exception:
                        notice = ""
                    context['accesses'].append({
                            'formDesc': each_access.access_desc(),
                            'accessTag': each_access.tag(),
                            'accessTypes': each_access.access_types(),
                            'accessRequestData': each_access.access_request_data(request, is_group=False),
                            'extraFields': extra_fields,
                            'notice': notice,
                            'accessRequestPath': each_access.fetch_access_request_form_path()
                        })
    except Exception as e:
        logger.exception(e)
        context = {}
        context['status'] = {'title':'Error Occured', 'msg': 'There was an error in getting the requested access resources. Please contact Admin'}
    return context


def getGrantFailedRequests(request):
    try:
        failures = UserAccessMapping.objects.filter(status__in=['grantfailed']).order_by('-requested_on')
        if request.GET.get('username'):
            user = User.objects.get(user__username=request.GET.get('username'))
            failures = failures.filter(user=user).order_by('-requested_on')
        if request.GET.get('access_type'):
            access_tag = request.GET.get('access_type')
            failures = failures.filter(access__access_tag=access_tag).order_by('-requested_on')

        context = {
            'failures': failures,
            'heading': "Grant Failures"
        }
        return context
    except Exception as e:
        return process_error_response(request, e)

    

def getPendingRevokeFailures(request):
    if request.GET.get('username'):
        user = User.objects.get(user__username=request.GET.get('username'))
        failures = UserAccessMapping.objects.filter(status__in=['revokefailed'], user=user).order_by('-requested_on')
    if request.GET.get('access_type'):
        access_tag = request.GET.get('access_type')
        failures = UserAccessMapping.objects.filter(status__in=['revokefailed'], access__access_tag=access_tag).order_by('-requested_on')
    else:
        failures = UserAccessMapping.objects.filter(status__in=['revokefailed']).order_by('-requested_on')

    context = {
        'failures': failures,
        'heading': "Revoke Failures"
    }
    return context

def getPendingRequests(request):
    logger.info("Pending Request call initiated")

    try:
        context = {
            "declineReasons": DECLINE_REASONS,
            "otherAccessRecepients": []
        }
        start_time = time.time()

        context["membershipPending"] = get_pending_membership()
        context["newGroupPending"] = get_pending_group_creation()

        context["genericRequests"], context["groupGenericRequests"] = get_pending_accesses_from_modules(request)

        duration = time.time() - start_time
        logger.info("Time to fetch all pending requests:" + str(duration))

        return context
    except Exception as e:
        return process_error_response(request, e)

def get_pending_membership():
    return MembershipV2.objects.filter(status="Pending", group__status="Approved")

def get_pending_group_creation():
    new_group_pending = GroupV2.objects.filter(status="Pending")
    new_group_pending_data = []
    for new_group in new_group_pending:
        initial_members = ", ".join(list(MembershipV2.objects.filter(group=new_group).values_list("user__user__username", flat=True)))
        new_group_pending_data.append({
            "groupRequest": new_group,
            "initialMembers": initial_members
        })

    return new_group_pending_data

def get_pending_accesses_from_modules(request):
    user_permissions = [permission.label for permission in request.user.user.permissions]

    individual_requests = []
    group_requests = {}

    logger.info("Start looping all access modules")
    for access_module in helpers.getAvailableAccessModules():
        access_module_start_time = time.time()

        try:
            pending_accesses = access_module.get_pending_accesses(request, user_permissions)
        except Exception as e:
            logger.exception(e)
            pending_accesses = {
               "individual_requests": [],
                "group_requests": [],
            }

        process_individual_requests(pending_accesses["individual_requests"], individual_requests, access_module.tag())
        process_group_requests(pending_accesses["group_requests"], group_requests)

        logger.info("Time to fetch pending requests of access module: " + access_module.tag() + " - " + str(time.time() - access_module_start_time))

    return individual_requests, list(group_requests.values())

def process_individual_requests(individual_pending_requests, individual_requests, access_tag):
    if len(individual_pending_requests):
        clubbed_requests = {}
        for accessrequest in individual_pending_requests:
            club_id = accessrequest["requestId"].rsplit("_",1)[0]
            if club_id not in clubbed_requests:
                clubbed_requests[club_id] = {
                                "club_id": club_id,
                                "userEmail": accessrequest["userEmail"],
                                "accessReason": accessrequest["accessReason"],
                                "accessType": accessrequest["accessType"],
                                "access_tag": accessrequest["access_tag"],
                                "requested_on": accessrequest["requested_on"],
                                "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                                "accessData":[]
                            }
            accessData = {
                    "accessCategory":accessrequest["accessCategory"],
                    "accessMeta": accessrequest["accessMeta"],
                    "requestId": accessrequest["requestId"]
                }
            clubbed_requests[club_id]["accessData"].append(accessData)
        individual_requests.append({"module_tag": access_tag, "requests": list(clubbed_requests.values())})

def process_group_requests(group_pending_requests, group_requests):
    if len(group_pending_requests):
        for accessrequest in group_pending_requests:
            club_id = accessrequest["groupName"]+"-"+accessrequest["requestId"].rsplit("-",1)[-1].rsplit("_",1)[0]
            needs_access_approve = GroupV2.objects.get(name=accessrequest["groupName"], status="Approved").needsAccessApprove
            if club_id not in group_requests:
                group_requests[club_id] = {
                                "group_club_id": club_id,
                                "userEmail": accessrequest["userEmail"],
                                "groupName": accessrequest["groupName"],
                                "needsAccessApprove": needs_access_approve,
                                "requested_on": accessrequest["requested_on"],
                                "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                                "hasOtherRequest": False,
                                "accessData":[]
                            }
            if accessrequest["access_tag"] == "other":
                group_requests[club_id]["hasOtherRequest"] = True
            accessData = {
                    "accessCategory":accessrequest["accessCategory"],
                    "accessMeta": accessrequest["accessMeta"],
                    "requestId": accessrequest["requestId"],
                    "accessReason": accessrequest["accessReason"],
                    "accessType": accessrequest["accessType"],
                    "access_tag": accessrequest["access_tag"],
                }
            group_requests[club_id]["accessData"].append(accessData)

def process_error_response(request, e):
    logger.debug("Error in request not found OR Invalid request type")
    logger.exception(e)
    json_response = {}
    json_response["error"] = {"error_msg": str(e), "msg": "Error in request not found OR Invalid request type"}
    return json_response

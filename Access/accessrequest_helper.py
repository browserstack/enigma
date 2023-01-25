from Access import helpers
import logging
import time
from . import helpers as helper

from BrowserStackAutomation.settings import DECLINE_REASONS
from Access.models import UserAccessMapping, User, GroupV2, AccessV2
import datetime
import json

logger = logging.getLogger(__name__)
all_access_modules = helper.get_available_access_modules()


def requestAccessGet(request):
    context = {}
    try:
        for each_access in helpers.getAvailableAccessModules():
            if "access_" + each_access.tag() in request.GET.getlist("accesses"):
                if "accesses" not in context:
                    context["accesses"] = []
                context["genericForm"] = True
                try:
                    extra_fields = each_access.get_extra_fields()
                except:
                    extra_fields = []
                try:
                    notice = each_access.get_notice()

                except Exception:
                    notice = ""
                context["accesses"].append(
                    {
                        "formDesc": each_access.access_desc(),
                        "accessTag": each_access.tag(),
                        "accessTypes": each_access.access_types(),
                        "accessRequestData": each_access.access_request_data(
                            request, is_group=False
                        ),
                        "extraFields": extra_fields,
                        "notice": notice,
                        "accessRequestPath": each_access.fetch_access_request_form_path(),
                    }                    
                )
    except Exception as e:
        logger.exception(e)
        context = {}
        context["status"] = {
            "title": "Error Occured",
            "msg": (
                "There was an error in getting the requested access resources. Please"
                " contact Admin"
            ),
        }
    return context


def getGrantFailedRequests(request):
    try:
        failures = UserAccessMapping.objects.filter(
            status__in=["grantfailed"]
        ).order_by("-requested_on")
        if request.GET.get("username"):
            user = User.objects.get(user__username=request.GET.get("username"))
            failures = failures.filter(user=user).order_by("-requested_on")
        if request.GET.get("access_type"):
            access_tag = request.GET.get("access_type")
            failures = failures.filter(access__access_tag=access_tag).order_by(
                "-requested_on"
            )

        context = {"failures": failures, "heading": "Grant Failures"}
        return context
    except Exception as e:
        return process_error_response(request, e)


def getPendingRevokeFailures(request):
    if request.GET.get("username"):
        user = User.objects.get(user__username=request.GET.get("username"))
        failures = UserAccessMapping.objects.filter(
            status__in=["revokefailed"], user=user
        ).order_by("-requested_on")
    if request.GET.get("access_type"):
        access_tag = request.GET.get("access_type")
        failures = UserAccessMapping.objects.filter(
            status__in=["revokefailed"], access__access_tag=access_tag
        ).order_by("-requested_on")
    else:
        failures = UserAccessMapping.objects.filter(
            status__in=["revokefailed"]
        ).order_by("-requested_on")

    context = {"failures": failures, "heading": "Revoke Failures"}
    return context


def getPendingRequests(request):
    logger.info("Pending Request call initiated")

    try:
        context = {"declineReasons": DECLINE_REASONS, "otherAccessRecepients": []}
        start_time = time.time()

        context["membershipPending"] = GroupV2.getPendingMemberships()
        context["newGroupPending"] = GroupV2.getPendingCreation()

        (
            context["genericRequests"],
            context["groupGenericRequests"],
        ) = get_pending_accesses_from_modules(request)

        duration = time.time() - start_time
        logger.info("Time to fetch all pending requests:" + str(duration))

        return context
    except Exception as e:
        return process_error_response(request, e)


def get_pending_accesses_from_modules(accessUser):
    individual_requests = []
    group_requests = {}

    logger.info("Start looping all access modules")
    for access_module in helpers.getAvailableAccessModules():
        access_module_start_time = time.time()

        try:
            pending_accesses = access_module.get_pending_accesses(accessUser)
        except Exception as e:
            logger.exception(e)
            pending_accesses = {
                "individual_requests": [],
                "group_requests": [],
            }

        process_individual_requests(
            pending_accesses["individual_requests"],
            individual_requests,
            access_module.tag(),
        )
        process_group_requests(pending_accesses["group_requests"], group_requests)

        logger.info(
            "Time to fetch pending requests of access module: "
            + access_module.tag()
            + " - "
            + str(time.time() - access_module_start_time)
        )

    return individual_requests, list(group_requests.values())


def process_individual_requests(
    individual_pending_requests, individual_requests, access_tag
):
    if len(individual_pending_requests):
        clubbed_requests = {}
        for accessrequest in individual_pending_requests:
            club_id = accessrequest["requestId"].rsplit("_", 1)[0]
            if club_id not in clubbed_requests:
                clubbed_requests[club_id] = {
                    "club_id": club_id,
                    "userEmail": accessrequest["userEmail"],
                    "accessReason": accessrequest["accessReason"],
                    "accessType": accessrequest["accessType"],
                    "access_tag": accessrequest["access_tag"],
                    "requested_on": accessrequest["requested_on"],
                    "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                    "accessData": [],
                }
            accessData = {
                "accessCategory": accessrequest["accessCategory"],
                "accessMeta": accessrequest["accessMeta"],
                "requestId": accessrequest["requestId"],
            }
            clubbed_requests[club_id]["accessData"].append(accessData)
        individual_requests.append(
            {"module_tag": access_tag, "requests": list(clubbed_requests.values())}
        )


def process_group_requests(group_pending_requests, group_requests):
    if len(group_pending_requests):
        for accessrequest in group_pending_requests:
            club_id = (
                accessrequest["groupName"]
                + "-"
                + accessrequest["requestId"].rsplit("-", 1)[-1].rsplit("_", 1)[0]
            )
            needs_access_approve = GroupV2.objects.get(
                name=accessrequest["groupName"], status="Approved"
            ).needsAccessApprove
            if club_id not in group_requests:
                group_requests[club_id] = {
                    "group_club_id": club_id,
                    "userEmail": accessrequest["userEmail"],
                    "groupName": accessrequest["groupName"],
                    "needsAccessApprove": needs_access_approve,
                    "requested_on": accessrequest["requested_on"],
                    "sla_breached": helpers.sla_breached(accessrequest["requested_on"]),
                    "hasOtherRequest": False,
                    "accessData": [],
                }
            if accessrequest["access_tag"] == "other":
                group_requests[club_id]["hasOtherRequest"] = True
            accessData = {
                "accessCategory": accessrequest["accessCategory"],
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
    json_response["error"] = {
        "error_msg": str(e),
        "msg": "Error in request not found OR Invalid request type",
    }
    return json_response

def create_request(user, access_request_form):
    def _validate_access_request(access_request_form, user):
        if not access_request_form:
            json_response = {}
            json_response['error'] = {'error_msg': 'Invalid Request', 'msg': 'Please Contact Admin'}
            logger.debug("Tried a direct Access to accessRequest by-"+user.username)
            return json_response
        
        access_request=dict(access_request_form.lists())
        
        if 'accessRequests' not in access_request:
            json_response['error'] = {
                'error_msg': 'The submitted form is empty. Tried direct access to requstAccess page',
                'msg': 'Error Occured while submitting your Request. Please contact the Admin'
            }
            return json_response
        return {}, access_request
    
    json_response, access_request = _validate_access_request(access_request_form=access_request_form, user=user)
    
    current_date_time=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")+'  UTC'
    json_response = {}
    json_response['status'] = []
    json_response['status_list'] = []
    extra_fields = []
    if "extraFields" in access_request:
        extra_fields = access_request["extraFields"]
    
    for index, access_type in enumerate(access_request['accessRequests']):        
        access_labels = _validate_access_labels(access_labels_json=access_request['accessLabel'][index], access_type=access_type)
        
        request_id = user.username + '-' + access_type + '-' + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        json_response[access_type] = {'requestId':request_id,'dateTime':current_date_time}
        
        access_module = all_access_modules[access_type]
        
        generic_request_data = _create_generic_request(access_module = access_module, 
                                                     access_reason = access_request['accessReason'][index],
                                                     access_labels = access_labels,
                                                     user = user)
        
        try:
            extra_field_labels = access_module.get_extra_fields()
        except:
            extra_field_labels = []
        
        if extra_fields and extra_field_labels:
            for field in extra_field_labels:
                generic_request_data['accessLabel'][0][field] = extra_fields[0]
                extra_fields =  extra_fields[1:]

        for index, access_label in enumerate(generic_request_data['accessLabel']):
            access = AccessV2.get(access_tag=access_type, access_label=access_label)
            if not access:
                access = AccessV2.objects.create(access_tag=access_type, access_label=access_label)
            else:    
                existing_individual_access = UserAccessMapping.objects.filter(
                        user=User.objects.get(user__username=user),
                        access=access,
                        status__in=["Approved", "Pending"]
                )
                
                if existing_individual_access:
                    json_response['status_list'].append({'title': access.access_tag+' - Duplicate Request not submitted', 'msg': 'Access already granted or request in pending state. '+json.dumps(access.access_label)})
                    continue 
            request_id = request_id + "_" + str(index)
            UserAccessMapping.objects.create(request_id=request_id,
                                user=User.objects.get(user__username=user.user),
                                request_reason=generic_request_data['accessReason'],
                                access=access)
            if access_module.can_auto_approve():
                #start approval in celery
                raise Exception("Implementation pending")
            else:
                json_response['status_list'].append({'title': request_id +' Request Submitted', 'msg': 'Once approved you will receive the update ' +json.dumps(access.access_label)})
            
    return json_response
    
def _validate_access_labels(access_labels_json, access_type):
    if access_labels_json is None or access_labels_json == "":
        raise Exception('No fields were selected in the request. Please try again.')
    access_labels = json.loads(access_labels_json)
    if len(access_labels) == 0:
        raise Exception("No fields were selected in the request for {}. Please try again.".format(access_type))
    return access_labels    

def _create_generic_request(access_module, access_reason, access_labels, user):
    generic_request_data = {}        
    generic_request_data['accessLabel'] = access_module.validate_request(access_labels,user,is_group=False)
    generic_request_data['accessCategory'] = access_module.combine_labels_desc(generic_request_data['accessLabel'])
    generic_request_data['accessMeta'] = access_module.combine_labels_meta(generic_request_data['accessLabel'])
    generic_request_data['accessDesc'] = access_module.access_desc()
    generic_request_data['accessReason'] = access_reason
    return generic_request_data

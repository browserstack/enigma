from .models import UserAccessMapping, GroupAccessMapping
from django.http import HttpResponse
import datetime
import traceback
import logging
import csv
from . import helpers as helper
from bootprocess import general

logger = logging.getLogger(__name__)
all_access_modules = helper.getAvailableAccessModules()


def generateUserMappings(user, group, membershipObj):
    groupMappings = GroupAccessMapping.objects.filter(group=group, status="Approved")

    userMappingsList = []
    for groupMapping in groupMappings:
        access = groupMapping.access
        approver_1 = groupMapping.approver_1
        approver_2 = groupMapping.approver_2
        membership_id = membershipObj.membership_id
        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        reason = (
            "Added to group for request "
            + membership_id
            + " - "
            + membershipObj.reason
            + " - "
            + groupMapping.request_reason
        )
        request_id = (
            user.user.username + "-" + access.access_tag + "-" + base_datetime_prefix
        )
        similar_id_mappings = list(
            UserAccessMapping.objects.filter(
                request_id__icontains=request_id
            ).values_list("request_id", flat=True)
        )
        idx = 0
        while request_id + "_" + str(idx) in similar_id_mappings:
            idx += 1
        request_id = request_id + "_" + str(idx)
        if not len(
            UserAccessMapping.objects.filter(
                user=user, access=access, status="Approved"
            )
        ):
            userMappingObj = UserAccessMapping.objects.create(
                request_id=request_id,
                user=user,
                access=access,
                approver_1=approver_1,
                approver_2=approver_2,
                request_reason=reason,
                access_type="Group",
                status="Processing",
            )
            userMappingsList.append(userMappingObj)
    return userMappingsList


def executeGroupAccess(userMappingsList):
    for mappingObj in userMappingsList:

        accessType = mappingObj.access.access_tag
        user = mappingObj.user
        approver = mappingObj.approver_1.user.username
        if user.current_state() == "active":
            if "other" in mappingObj.request_id:
                decline_group_other_access(mappingObj)
            else:
                run_access_grant(
                    mappingObj.request_id, mappingObj, accessType, user, approver
                )
                logger.debug(
                    "Successful group access grant for " + mappingObj.request_id
                )
        else:
            mappingObj.status = "Declined"
            mappingObj.decline_reason = "User is not active"
            mappingObj.save()
            logger.debug(
                "Skipping group access grant for user "
                + user.user.username
                + " as user is not active"
            )


def decline_group_other_access(access_mapping):
    user = access_mapping.user
    access_mapping.status = "Declined"
    access_mapping.decline_reason = (
        "Auto decline for 'Other Access'. Please replace this with correct access."
    )
    access_mapping.save()
    logger.debug(
        "Skipping group access grant for user "
        + user.user.username
        + " for request_id "
        + access_mapping.request_id
        + " as it is 'Other Access'"
    )


def run_access_grant(requestId, requestObject, accessType, user, approver):
    message = ""
    if not requestObject.user.state == "1":
        requestObject.status = "Declined"
        requestObject.save()
        logger.debug(
            {
                "requestId": requestId,
                "status": "Declined",
                "by": approver,
                "response": message,
            }
        )
        return False
    for each_access_module in all_access_modules:
        if accessType == each_access_module.tag():
            try:
                response = each_access_module.approve(
                    user,
                    [requestObject.access.access_label],
                    approver,
                    requestId,
                    is_group=False,
                )
                if type(response) is bool:
                    approve_success = response
                else:
                    approve_success = response[0]
                    message = str(response[1])
            except Exception:
                logger.exception(
                    "Error while running approval module: "
                    + str(traceback.format_exc())
                )
                approve_success = False
                message = str(traceback.format_exc())
            if approve_success:
                requestObject.status = "Approved"
                requestObject.save()
                logger.debug(
                    {
                        "requestId": requestId,
                        "status": "Approved",
                        "by": approver,
                        "response": message,
                    }
                )
            else:
                requestObject.status = "GrantFailed"
                requestObject.save()
                logger.debug(
                    {
                        "requestId": requestId,
                        "status": "GrantFailed",
                        "by": approver,
                        "response": message,
                    }
                )
                try:
                    destination = [
                        each_access_module.access_mark_revoke_permission(accessType)
                    ]
                    subject = str("Access Grant Failed - ") + accessType.upper()
                    body = (
                        "Request by "
                        + user.email
                        + " having Request ID = "
                        + requestId
                        + " is GrantFailed. Please debug and rerun the grant.<BR/>"
                    )
                    body = body + "Failure Reason - " + message
                    body = (
                        body
                        + "<BR/><BR/> <a target='_blank'"
                        + "href "
                        + "='https://enigma.browserstack.com/resolve/pendingFailure?access_type="
                        + accessType
                        + "'>View all failed grants</a>"
                    )
                    logger.debug(
                        "Sending Grant Failed email - "
                        + str(destination)
                        + " - "
                        + subject
                        + " - "
                        + body
                    )
                    general.emailSES(destination, subject, body)
                except Exception:
                    logger.debug(
                        "Grant Failed - Error while sending email - "
                        + requestId
                        + "-"
                        + str(str(traceback.format_exc()))
                    )

            # For generic modules, approve method will send an email on "Access granted",
            # additional email of "Access approved" is not needed
            return True
    return False


def get_filters(request):
    filters = {}
    if "accessTag" in request.GET:
        filters['access__access_tag__icontains'] = request.GET.get('accessTag')
    if "accessTagExact" in request.GET:
        filters['access__access_tag'] = request.GET.get('accessTagExact')
    if "status" in request.GET:
        filters['status__icontains'] = request.GET.get('status')
    if "type" in request.GET:
        filters['access_type__icontains'] = request.GET.get('type')
    return filters


def prepare_datalist(paginator, record_date):
    data_list = []
    for each_access_request in paginator:
        if record_date is not None and record_date != str(each_access_request.updated_on)[:10]:
            continue
        access_details = helper.get_access_details(each_access_request.access)
        for each_access_split in helper.split_access_details(access_details):
            data_list.append({
                'request_id': each_access_request.request_id,
                'user': str(each_access_request.user),
                'name': [key + " - " + str(value).strip("[]")
                         for key, value in list(each_access_request.access.access_label.items())
                         if key != "keySecret"],
                'details': each_access_split['accessType'] + " => "
                + each_access_split['accessCategory'],
                'accessStatus': each_access_request.status,
                'grantOwner': access_details['grantOwner'],
                'revokeOwner': access_details['revokeOwner'],
                'approver': each_access_request.approver_1.user.username
                if each_access_request.approver_1 else "",
                'accessType': each_access_request.access.access_tag,
                'type': each_access_request.access_type,
                'dateRequested': str(each_access_request.requested_on)[:19] + "UTC",
                'offboardingDate': str(each_access_request.user.offbaord_date)[:19] + "UTC"
                if each_access_request.user.offbaord_date else "",
                'lastUpdated': str(each_access_request.updated_on)[:19] + "UTC",
                'revoker': each_access_request.revoker.user.username
                if each_access_request.revoker else "",
                'approvedOn': str(each_access_request.approved_on)[:19] + "UTC"
                if each_access_request.approved_on else ""
            })
    return data_list


def gen_all_user_access_list_csv(data_list):
    logger.debug("Processing CSV response")
    response = HttpResponse(content_type='text/csv')
    filename = "AccessList-" + str(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')) + ".csv"
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

    writer = csv.writer(response)
    writer.writerow(['User', 'AccessType', 'Access', 'AccessStatus',
                     'RequestDate', 'Approver', 'GrantOwner',
                     'RevokeOwner', 'Type'])
    for data in data_list:
        access_status = data["accessStatus"]
        if len(data["revoker"]) > 0:
            access_status += " by - " + data["revoker"]
        writer.writerow([data['user'], data['accessType'],
                         (", ".join(data["name"])),
                         access_status, data["dateRequested"],
                         data["approver"], data["grantOwner"],
                         data["revokeOwner"], data["type"]])
    return response

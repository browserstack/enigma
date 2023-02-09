import logging
from . import helpers as helper
import traceback
from bootprocess.general import emailSES

logger = logging.getLogger(__name__)
all_access_modules = helper.getAvailableAccessModules()

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
                    "Error while running approval module: " + str(traceback.format_exc())
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
                    emailSES(destination, subject, body)
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

import json
import threading
import traceback
import logging

from celery import shared_task
from celery.signals import task_success, task_failure

from Access import helpers
from bootprocess import general
from BrowserStackAutomation.settings import AUTOMATED_EXEC_IDENTIFIER

logger = logging.getLogger(__name__)

with open("config.json") as data_file:
    background_task_manager_type = json.load(data_file)["background_task_manager"]["type"]


def background_task(func, *args):
    if background_task_manager_type == "celery":
        if func == "run_access_grant":
            run_access_grant.delay(*args)

        if func == "test_grant":
            test_grant.delay(*args)

    else:
        if func == "run_access_grant":
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=args,
            )
            accessAcceptThread.start()
        
        if func == "run_access_revoke":
            access_revoke_thread = threading.Thread(
                target=run_access_revoke,
                args=args
            )

            access_revoke_thread.start()

@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
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
    for each_access_module in helpers.getAvailableAccessModules():
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

@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_access_revoke(access, user_identity, request, revoker):
    for access_module in helpers.getAccessModules():
        if access_module.tag() == access.access_tag:
            response = access_module.revoke(user_identity, access.access_label, request)
            logger.debug("Response from the revoke function: ", str(response))
            if type(response) is bool:
                    revoke_success = response
                    message = None
            else:
                revoke_success = response[0]
                message = str(response[1])

            if revoke_success:
                if AUTOMATED_EXEC_IDENTIFIER in access_module.revoke_owner():
                    user_identity.update_mapping_status_revoked()
                    request.update(status="Revoked", revoker=revoker)
            else:
                logger.debug("Failed to revoke the request: {} due to exception: {}".format(request.request_id, message))
                raise Exception("Failed to revoke the access due to: "+ str(message))
                
            return True
    
    return False



@task_success.connect(sender=run_access_grant)
def task_success(sender=None, **kwargs):
    success_func()
    logger.info("you are in task success middleman")
    return

@task_failure.connect(sender=run_access_grant)
def task_failure(sender=None, **kwargs):
    fail_func()
    logger.info("you are in task fail middleman")
    return

def success_func():
    logger.info("task successful")

def fail_func():
    logger.info("task failed")

@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def test_grant():
    for each_access_module in helpers.getAvailableAccessModules():
        logger.info(each_access_module.tag())
        if each_access_module.tag() == 'confluence_module':
            # call access_desc method of confluence module here
            # and return the result to the caller of this function
            return each_access_module.access_desc()

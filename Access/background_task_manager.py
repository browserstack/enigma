import json
import threading
import traceback
import logging

from celery import shared_task
from celery.signals import task_success, task_failure

from Access import helpers
from bootprocess import general
from Access.models import UserAccessMapping
from Access import notifications


logger = logging.getLogger(__name__)

with open("config.json") as data_file:
    background_task_manager_type = json.load(data_file)["background_task_manager"]["type"]


def background_task(func, *args):
    if background_task_manager_type == "celery":
        if func == "run_access_grant":
            run_access_grant.delay(*args)

        if func == "test_grant":
            test_grant.delay(*args)

        if func == "run_accept_request":
            run_accept_request.delay(*args)

    else:
        if func == "run_access_grant":
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=args,
            )
            accessAcceptThread.start()

        if func == "run_accept_request":
            accessAcceptThread = threading.Thread(
                target=run_accept_request,
                args=args,
            )
            accessAcceptThread.start()


@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_access_grant(request_id):
    user_access_mapping = UserAccessMapping.get_access_request(request_id=request_id)
    access_type = user_access_mapping.access.access_tag
    user = user_access_mapping.user_identity.user
    approver = user_access_mapping.approver_1.user.username
    message = ""
    if not user_access_mapping.user_identity.user.state == "1":
        user_access_mapping.decline_access(decline_reason="User is not active")
        logger.debug(
            {
                "requestId": request_id,
                "status": "Declined",
                "by": approver,
                "response": message,
            }
        )
        return False
    elif user_access_mapping.user_identity.identity == {}:
        user_access_mapping.grant_fail_access()
        logger.debug(
            {
                "requestId": request_id,
                "status": "GrantFailed",
                "by": approver,
                "response": message,
            }
        )
        return False

    access_module = helpers.get_available_access_module_from_tag(access_type)
    if not access_module:
        return False

    try:
        response = access_module.approve(user_identity=user_access_mapping.user_identity,
                                         labels=[user_access_mapping.access.access_label],
                                         approver=approver,
                                         request_id=request_id,
                                         is_group=False,)
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

    logger.debug("response >>>>>>>> ")
    logger.debug(approve_success)

    if approve_success:
        user_access_mapping.approve_access()
        logger.debug(
            {
                "requestId": request_id,
                "status": "Approved",
                "by": approver,
                "response": message,
            }
        )
    else:
        user_access_mapping.grant_fail_access()
        logger.debug(
            {
                "requestId": request_id,
                "status": "GrantFailed",
                "by": approver,
                "response": message,
            }
        )
        try:
            destination = access_module.access_mark_revoke_permission(access_type)
            notifications.send_mail_for_access_grant_failed(destination,
                                                            access_type.upper(),
                                                            user.email,
                                                            request_id=request_id,
                                                            message=message)
            logger.debug(
                "Sending Grant Failed email - "
                + str(destination)
            )
        except Exception:
            logger.debug(
                "Grant Failed - Error while sending email - "
                + request_id
                + "-"
                + str(str(traceback.format_exc()))
            )

    # For generic modules, approve method will send an email on "Access granted",
    # additional email of "Access approved" is not needed
    return True


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
    access_module = helpers.get_available_access_module_from_tag('confluence_module')

    # call access_desc method of confluence module here
    # and return the result to the caller of this function
    return access_module.access_desc()

@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 1, "countdown": 5}
)
def run_accept_request(data):
    logger.debug("---------------process accept--------------------")
    subject = ""
    data = json.loads(data)
    request_id = data["request_id"]
    request = UserAccessMapping.get_access_request(data["request_id"])
    approver = request.approver_1.user
    user = request.user_identity.user
    access_type = data["access_type"]
    response = ""

    try:
        if access_type == "other":
            emails = request.GET["checkedEmails"].split(",")
            accessObj = request.access
            accessObj.access_label["grant_emails"] = emails
            accessObj.save()

        result = background_task("run_access_grant", request_id)
        if result:
            return True

        request.status='Approved'
        request.save()

        destination=[user.email]
        destination.extend(approver.email) #Send the confirmation email to all the approvers.
        subject = "[Enigma][Access Management] %s - %s Request Approved - %s" % (
            str(user.email), access_type.upper(), request_id)
        body="Request by %s having Request ID %s is Approved by %s" % (
            str(user.email),
            request_id,
            str(approver)
        )
        general.emailSES(destination,subject,body)
        logger.debug({'requestId':request_id,'status':'Approved','By':approver, 'response':str(response)})
    except Exception as e:
        logger.exception(e)
        request.status = 'Pending'
        request.approver = ''
        request.save()
        destination = [user.email, approver.email]

        logger.debug(
            "Error in accept of request "+request_id
            +" error: "
            + str(e),"Error while Approving "
            + request_id
            +" Request","Error msg : "+str(e)
        )

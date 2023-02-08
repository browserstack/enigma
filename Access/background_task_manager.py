import json
import threading
import traceback
import logging

from celery import shared_task
from celery.signals import task_success, task_failure

from Access import helpers
from Access.models import UserAccessMapping
from Access import notifications

logger = logging.getLogger(__name__)

with open("config.json") as data_file:
    background_task_manager_type = json.load(data_file)["background_task_manager"]["type"]


def background_task(func, *args):
    if background_task_manager_type == "celery":
        if func == "run_access_grant":
            request_id = args[0]
            run_access_grant.delay(request_id)
        elif func == "test_grant":
            test_grant.delay(*args)

    else:
        if func == "run_access_grant":
            request_id = args[0]
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=(request_id,),
            )
            accessAcceptThread.start()


@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_access_grant(request_id):
    mapping_obj = UserAccessMapping.get_from_request_id(request_id=request_id)
    access_type = mapping_obj.access.access_tag
    user = mapping_obj.user_identity.user
    approver = mapping_obj.approver_1.user.username
    message = ""
    if not mapping_obj.user_identity.user.state == "1":
        mapping_obj.set_status_declined()
        logger.debug(
            {
                "requestId": request_id,
                "status": "Declined",
                "by": approver,
                "response": message,
            }
        )
        return False
    elif mapping_obj.user_identity.identity == {}:
        mapping_obj.set_status_grant_failed()
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
        response = access_module.approve(user_identity=mapping_obj.user_identity,
                                         labels=[mapping_obj.access.access_label],
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

    if approve_success:
        mapping_obj.set_status_approved()
        logger.debug(
            {
                "requestId": request_id,
                "status": "Approved",
                "by": approver,
                "response": message,
            }
        )
    else:
        mapping_obj.set_status_grant_failed()
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

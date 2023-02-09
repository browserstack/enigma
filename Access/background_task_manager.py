import json
import threading
import traceback
import logging

from celery import shared_task
from celery.signals import task_success, task_failure

from Access import helpers
from bootprocess import general
from BrowserStackAutomation.settings import AUTOMATED_EXEC_IDENTIFIER
from Access.models import UserAccessMapping, User
from Access import notifications

logger = logging.getLogger(__name__)

with open("config.json") as data_file:
    background_task_manager_type = json.load(data_file)["background_task_manager"][
        "type"
    ]


def background_task(func, *args):
    if background_task_manager_type == "celery":
        if func == "run_access_grant":
            request_id = args[0]
            run_access_grant.delay(request_id)
        elif func == "test_grant":
            test_grant.delay(*args)
        elif func == "run_access_revoke":
            run_access_revoke.delay(*args)

    else:
        if func == "run_access_grant":
            request_id = args[0]
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=(request_id,),
            )
            accessAcceptThread.start()
        elif func == "run_access_revoke":
            access_revoke_thread = threading.Thread(target=run_access_revoke, args=args)

            access_revoke_thread.start()


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
        user_access_mapping.grant_fail_access(fail_reason="Failed since identity is blank for user identity")
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
                                         request=user_access_mapping,
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
        user_access_mapping.grant_fail_access(fail_reason="Error while running approve in module")
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


@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_access_revoke(data):
    data = json.loads(data)
    access_mapping = UserAccessMapping.get_access_request(data["request_id"])
    if not access_mapping:
        # TODO: Have to add the email targets for failure
        targets = []
        message = "Request not found"
        notifications.send_revoke_failure_mail(
            targets, data["request_id"], data["revoker_email"], 0, message
        )
        return {"status": False}
    elif access_mapping.status == "Revoked":
        return {"status": True}
    access = access_mapping.access
    user_identity = access_mapping.user_identity

    revoker = User.get_user_by_email(data["revoker_email"])
    if not revoker:
        # TODO: Have to add the email targets for failure
        targets = []
        message = "Revoker not found"
        notifications.send_revoke_failure_mail(
            targets,
            data["request_id"],
            data["revoker_email"],
            0,
            message,
            access.access_tag,
        )
        user_identity.mark_revoke_failed_for_approved_access_mapping(access)
        return {"status": False}

    access_modules = helpers.get_available_access_modules()

    access_module = access_modules[access.access_tag]

    response = access_module.revoke(
        user_identity.user, user_identity, access.access_label, access_mapping
    )
    logger.debug("Response from the revoke function: " + str(response))
    if type(response) is bool:
        revoke_success = response
        message = None
    else:
        revoke_success = response[0]
        message = str(response[1])

    if revoke_success:
        if AUTOMATED_EXEC_IDENTIFIER in access_module.revoke_owner():
            user_identity.revoke_approved_access_mapping(access)
    else:
        logger.debug(
            "Failed to revoke the request: {} due to exception: {}".format(
                access_mapping.request_id, message
            )
        )
        logger.debug("Retry count: {}".format(run_access_revoke.request.retries))
        if run_access_revoke.request.retries == 3:
            logger.info("Sending the notification for failure")
            notifications.send_revoke_failure_mail(
                access_module.access_mark_revoke_permission(access_mapping.access_type),
                access_mapping.request_id,
                revoker.email,
                run_access_revoke.request.retries,
                message,
                access.access_tag,
            )
            user_identity.mark_revoke_failed_for_approved_access_mapping(access)
        raise Exception("Failed to revoke the access due to: " + str(message))

    return {"status": True}


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

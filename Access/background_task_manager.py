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
        elif func == "run_accept_request":
            run_accept_request.delay(*args)
        elif func == "run_access_revoke":
            request_id = args[0]
            run_access_revoke.delay(request_id)
    else:
        if func == "run_access_grant":
            request_id = args[0]
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=(request_id,),
            )
            accessAcceptThread.start()
        elif func == "run_accept_request":
            accessAcceptThread = threading.Thread(
                target=run_accept_request,
                args=args,
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
    access_tag = user_access_mapping.access.access_tag
    user = user_access_mapping.user_identity.user
    approver = user_access_mapping.approver_1.user
    message = ""
    access_module = helpers.get_available_access_module_from_tag(access_tag)
    if not user_access_mapping.user_identity.user.is_active():
        user_access_mapping.decline_access(decline_reason="User is not active")
        logger.debug(
            {
                "requestId": request_id,
                "status": "Declined",
                "by": approver.username,
                "response": message,
            }
        )
        return False
    elif user_access_mapping.user_identity.identity == {} and access_module.get_identity_template() != "":
        user_access_mapping.grant_fail_access(
            fail_reason="Failed since identity is blank for user identity"
        )
        notifications.send_mail_for_request_granted_failure(
            user, approver, access_tag, request_id
        )

        logger.debug(
            {
                "requestId": request_id,
                "status": "GrantFailed",
                "by": approver,
                "response": message,
            }
        )
        return False

    if not access_module:
        return False

    try:
        response = access_module.approve(
            user_identity=user_access_mapping.user_identity,
            labels=[user_access_mapping.access.access_label],
            approver=approver,
            request=user_access_mapping,
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
        user_access_mapping.grant_fail_access(
            fail_reason="Error while running approve in module"
        )
        logger.debug(
            {
                "requestId": request_id,
                "status": "GrantFailed",
                "by": approver,
                "response": message,
            }
        )
        try:
            destination = access_module.access_mark_revoke_permission(access_tag)
            notifications.send_mail_for_access_grant_failed(
                destination,
                access_tag.upper(),
                user.email,
                request_id=request_id,
                message=message,
            )
            logger.debug("Sending Grant Failed email - " + str(destination))
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
def run_access_revoke(request_id):
    access_mapping = UserAccessMapping.get_access_request(request_id=request_id)
    if not access_mapping:
        logger.debug(f"Cannot find access mapping with id: {request_id}")
        return False
    elif access_mapping.status == "Revoked":
        logger.debug(f"The request with id {request_id} is already revoked.")
        return True
    access = access_mapping.access
    user_identity = access_mapping.user_identity

    revoker = access_mapping.revoker
    access_modules = helpers.get_available_access_modules()
    access_module = access_modules[access.access_tag]
    if not revoker:
        logger.debug(f"The revoker is not set for the request with id {request_id}")
        access_mapping.revoke_failed("Revoker was not set.")
        return False

    try:
        response = access_module.revoke(
            user_identity.user, user_identity, access.access_label, access_mapping
        )
        if type(response) is bool:
            revoke_success = response
            message = None
        else:
            revoke_success = response[0]
            message = str(response[1])
    except Exception as e:
        logger.exception(
            "Error while running revoke function: " + str(traceback.format_exc())
        )
        revoke_success = False
        message = str(traceback.format_exc())


    if revoke_success:
        access_mapping.revoke()
        logger.debug(
            {
                "requestId": request_id,
                "status": "revoked",
                "by": revoker,
                "response": message,
            }
        )
    else:
        access_mapping.revoke_failed(
            fail_reason="Error while running revoke in module"
        )
        logger.debug(
            {
                "requestId": request_id,
                "status": "RevokeFailed",
                "by": revoker,
                "response": message,
                "retry_count": run_access_revoke.request.retries
            }
        )
        if run_access_revoke.request.retries == 3:
            logger.info("Sending the notification for failure")
            try:
                notifications.send_revoke_failure_mail(
                    access_module.access_mark_revoke_permission(access_mapping.access_type),
                    access_mapping.request_id,
                    revoker.email,
                    run_access_revoke.request.retries,
                    message,
                    access.access_tag,
                )
            except Exception as e:
                logger.debug(f"Failed to send Revoke failed mail due to exception: {str(e)}")
        raise Exception("Failed to revoke the access due to: " + str(message))

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
    access_module = helpers.get_available_access_module_from_tag("confluence_module")

    # call access_desc method of confluence module here
    # and return the result to the caller of this function
    return access_module.access_desc()


@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_accept_request(data):
    data = json.loads(data)
    request_id = data["request_id"]
    user_access_mapping = UserAccessMapping.get_access_request(data["request_id"])
    approver = user_access_mapping.approver_1.user
    user = user_access_mapping.user_identity.user
    access_type = data["access_type"]
    response = ""

    result = background_task("run_access_grant", request_id)
    if result:
        return {"status": True}

    notifications.send_mail_for_request_granted_failure(
        user, approver, access_type, request_id
    )
    logger.debug(
        {
            "requestId": request_id,
            "status": "GrantFailed",
            "By": approver,
            "response": str(response),
        }
    )

    return {"status": False}


def accept_request(user_access_mapping):
    result = None
    try:
        result = run_access_grant.delay(user_access_mapping.request_id)
    except Exception:
        user_access_mapping.grant_fail_access(fail_reason="Task could not be queued")

    if result:
        return True
    return False


def revoke_request(user_access_mapping, revoker=None):
    result = None
    # change the status to revoke processing
    user_access_mapping.revoking(revoker)
    try:
        result = run_access_revoke.delay(user_access_mapping.request_id)
    except Exception:
        user_access_mapping.RevokeFailed(fail_reason="Task could not be queued")

    if result:
        return True
    return False

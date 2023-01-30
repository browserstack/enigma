import json
import threading

from celery import shared_task
from celery.signals import task_success, task_failure

from Access.views_helper import run_access_grant

with open("config.json") as data_file:
    data = json.load(data_file)

background_task_manager = data["background_task_manager"]["type"]


def background_task(func, args):
    if background_task_manager == "celery":
        if func == "run_access_grant":
            run_access_grant_celery_task.delay(args)

    else:
        if func == "run_access_grant":
            accessAcceptThread = threading.Thread(
                target=run_access_grant,
                args=args,
            )
            accessAcceptThread.start()

@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def run_access_grant_celery_task(args):
    print("run_access_grant running")
    run_access_grant(args)
    return

@task_success.connect(sender=run_access_grant_celery_task)
def task_success(sender=None, **kwargs):
    success_func()
    print("you are in task success middleman")
    return


@task_failure.connect(sender=run_access_grant_celery_task)
def task_failure(sender=None, **kwargs):
    fail_func()
    print("you are in task fail middleman")
    return

def success_func():
    print("task successful")

def fail_func():
    print("task failed")

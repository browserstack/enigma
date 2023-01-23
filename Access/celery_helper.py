from celery import shared_task
from celery.signals import task_prerun, task_postrun, task_success, task_failure
from time import sleep
from Access.sample_code.zoom import Zoom
from celery.result import AsyncResult


class coordinator:
    def __init__(self, module_name):
        self.module = {}
        print("Welcome to coordinator")

    def exec_func(self, module_name, func_name, args):
        print("you are in coordinator exec_func")
        obj = globals()[module_name]
        instance = obj()
        self.module = instance.module_functions
        if func_name in self.module[module_name]:
            method = getattr(obj, self.module[module_name][func_name]["exec"])
            method(obj, *args)
        else:
            print(func_name, " doesn't exists in ", module_name)

    def success_func(self, module_name, func_name):
        print("you are in coordinator success_func")
        obj = globals()[module_name]
        instance = obj()
        self.module = instance.module_functions
        if func_name in self.module[module_name]:
            method = getattr(obj, self.module[module_name][func_name]["success"])
            method(obj)
        else:
            print(func_name, " doesn't exists in ", module_name)

    def fail_func(self, module_name, func_name):
        print("you are in coordinator fail_func")
        obj = globals()[module_name]
        instance = obj()
        self.module = instance.module_functions
        if func_name in self.module[module_name]:
            method = getattr(obj, self.module[module_name][func_name]["fail"])
            method(obj)
        else:
            print(func_name, " doesn't exists in ", module_name)


@shared_task(
    autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}
)
def celery_task(module, command, args):
    c = coordinator(module)
    c.exec_func(module, command, args)
    print("you are in middleman")
    return


@task_success.connect(sender=celery_task)
def task_success(sender=None, **kwargs):
    task = AsyncResult(sender.request.id)
    task_data = task.args
    module = task_data[0]
    command = task_data[1]
    c = coordinator(module)
    c.success_func(module, command)
    print("you are in task success middleman")
    return


@task_failure.connect(sender=celery_task)
def task_failure(sender=None, **kwargs):
    task = AsyncResult(sender.request.id)
    task_data = task.args
    module = task_data[0]
    command = task_data[1]
    c = coordinator(module)
    c.fail_func(module, command)
    print("you are in task fail middleman")
    return

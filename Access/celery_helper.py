from celery import shared_task
from celery.signals import task_prerun, task_postrun, task_success, task_failure
from time import sleep
from Access.zoom import Zoom
from celery.result import AsyncResult
import json
from json.decoder import JSONDecodeError

class module_initialisation:
  def __init__(self):
    self.modules = {
        "Zoom": {
        "module": Zoom(),
        "grant": {
              "exec": "grant",
              "success": "on_success_grant",
              "fail": "on_fail_grant"
          },
          "revoke": {
              "exec": "revoke",
              "success": "on_success_revoke",
              "fail": "on_fail_revoke"
          }
      }
    }

  def func(self, module_name):
    if module_name in self.modules:
      return self.modules[module_name]
    else:
      print("Module is not present")
      return {}


class coordinator:
  def __init__(self, module_name):
    self.modules = module_initialisation()

  def exec_func(self, module_name, func_name, args):
    print("you are in coordinator exec_func")
    target_module = self.modules.func(module_name)
    if func_name in target_module:
      obj = target_module["module"]
      method = getattr(obj, target_module[func_name]["exec"])
      method(*args)
    else:
      print(func_name, " doesn't exists in ", module_name)

  def success_func(self, module_name, func_name):
    print("you are in coordinator success_func")
    target_module = self.modules.func(module_name)
    if func_name in target_module:
      obj = target_module["module"]
      method = getattr(obj, target_module[func_name]["success"])
      method()
    else:
      print(func_name, " doesn't exists in ", module_name)
  
  def fail_func(self, module_name, func_name):
    print("you are in coordinator fail_func")
    target_module = self.modules.func(module_name)
    if func_name in target_module:
      obj = target_module["module"]
      method = getattr(obj, target_module[func_name]["fail"])
      method()
    else:
      print(func_name, " doesn't exists in ", module_name)


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def celery_task(module,command,args):
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

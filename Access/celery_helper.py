from celery import shared_task
from celery.signals import task_prerun, task_postrun, task_success, task_failure
from time import sleep
from Access.zoom import Zoom
from celery.result import AsyncResult
import json
from json.decoder import JSONDecodeError

class register_module:
  def __init__(self):
    try:
      with open("modules.json", "r") as f:
      # Load the contents of the file as a JSON object
        self.modules = json.load(f)
      f.close()
    except JSONDecodeError:
      self.modules = {}
  
  def register(self, module_name, functions, on_success_functions, on_fail_functions):
    if module_name not in self.modules:
      new_module = {}
      new_module[module_name] = {}
      for i in range(len(functions)):
        new_module[module_name][functions[i]] = {}
        new_module[module_name][functions[i]]["exec"] = functions[i]
        new_module[module_name][functions[i]]["success"] = on_success_functions[i]
        new_module[module_name][functions[i]]["fail"] = on_fail_functions[i]
      
      self.modules.update(new_module)
      json_str = json.dumps(self.modules)
      with open("modules.json", "w") as f:
        # Write the JSON string to the file
        f.write(json_str)
      f.close()
    else:
      print("Module is already registered.")
    return
  
  def add_func(self, module_name, functions, on_success_functions, on_fail_functions):
    if module_name in self.modules:
      for i in range(len(functions)):
        if functions[i] not in self.modules[module_name]:
          self.modules[module_name][functions[i]] = {}
          self.modules[module_name][functions[i]]["exec"] = functions[i]
          self.modules[module_name][functions[i]]["success"] = on_success_functions[i]
          self.modules[module_name][functions[i]]["fail"] = on_fail_functions[i]
        else:
          print(functions[i], " is already present in the module")
      json_str = json.dumps(self.modules)
      with open("modules.json", "w") as f:
        # Write the JSON string to the file
        f.write(json_str)
    else:
      print("Please enter correct module name")
    return

class coordinator:
  def __init__(self):
    try:
      with open("modules.json", "r") as f:
      # Load the contents of the file as a JSON object
        self.modules = json.load(f)
      f.close()
    except JSONDecodeError:
      self.modules = {}

  def exec_func(self, module_name, func_name, args):
    print("you are in coordinator exec_func")
    if module_name in self.modules:
      if func_name in self.modules[module_name]:
        obj = globals()[module_name]
        method = getattr(obj, self.modules[module_name][func_name]["exec"])
        method(obj,*args)
      else:
        print(func_name, " doesn't exists in ", module_name)
    else:
      print("module doesn't exists")

  def success_func(self, module_name, func_name):
    print("you are in coordinator success_func")
    if module_name in self.modules:
      if func_name in self.modules[module_name]:
        obj = globals()[module_name]
        method = getattr(obj, self.modules[module_name][func_name]["success"])
        method(obj)
      else:
        print(func_name, " doesn't exists in ", module_name)
    else:
      print("module doesn't exists")
  
  def fail_func(self, module_name, func_name):
    print("you are in coordinator fail_func")
    if module_name in self.modules:
      if func_name in self.modules[module_name]:
        obj = globals()[module_name]
        method = getattr(obj, self.modules[module_name][func_name]["fail"])
        method(obj)
      else:
        print(func_name, " doesn't exists in ", module_name)
    else:
      print("module doesn't exists")


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def celery_task(module,command,args):
  c = coordinator()
  c.exec_func(module, command, args)
  print("you are in middleman")
  return

@task_success.connect(sender=celery_task)
def task_success(sender=None, **kwargs):
  task = AsyncResult(sender.request.id)
  task_data = task.args
  module = task_data[0]
  command = task_data[1]
  c = coordinator()
  c.success_func(module, command)
  print("you are in task success middleman")
  return

@task_failure.connect(sender=celery_task)
def task_failure(sender=None, **kwargs):
  task = AsyncResult(sender.request.id)
  task_data = task.args
  module = task_data[0]
  command = task_data[1]
  c = coordinator()
  c.fail_func(module, command)
  print("you are in task fail middleman")
  return

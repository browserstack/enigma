from celery import shared_task
from time import sleep

@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def generate_celery_task(func_name,args):
  print("You are in generate_celery_task function, it will perform the task asynchronously with celery")
  globals()[func_name](*args)
  return

def dummy_func(arg1, arg2):
  print("Given arguments are:", arg1, arg2)
  sleep(5)
  return

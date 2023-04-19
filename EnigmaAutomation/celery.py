from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EnigmaAutomation.settings")
app = Celery("EnigmaAutomation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "default_queue"
app.conf.update(task_track_started=True)
app.conf.update(result_extended=True)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name="background_task_manager")

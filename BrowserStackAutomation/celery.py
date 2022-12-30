from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.apps import apps

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BrowserStackAutomation.settings")
app = Celery("BrowserStackAutomation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = 'default_queue'
app.conf.update(task_track_started=True)
app.conf.update(result_extended=True)
app.autodiscover_tasks(['Access'])
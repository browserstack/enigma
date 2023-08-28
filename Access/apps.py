""" This file contains registered application """

from django.apps import AppConfig


class AccessConfig(AppConfig):
    """ class ro register the application"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "Access"

""" views for bootprocess """
import logging
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .views_helper import get_dashboard_data

logger = logging.getLogger(__name__)


@login_required
def logout_view(request):
    """Logout View runs when logout url call"""
    logout(request)
    logger.debug("User: %s is logging out", request.user.username)
    return render(request, "registration/login.html")


@login_required
def dashboard(request):
    """Loaded dashboard"""
    context = get_dashboard_data(request)
    logger.info("Dashboard load for user %s", request.user.username)
    return render(request, "EnigmaOps/dashboard.html", context)

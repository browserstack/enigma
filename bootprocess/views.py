from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import logging
from .views_helper import getDashboardData

logger = logging.getLogger(__name__)
# Create your views here.


@login_required
def logout_view(request):
    """Logout View runs when logout url call"""
    logout(request)
    logger.debug("User: {0} is logging out".format(request.user.username))
    return render(request, "registration/login.html")


@login_required
def dashboard(request):
    """Loaded dashboard"""
    context = getDashboardData(request)
    return render(request, "BSOps/dashboard.html", context)

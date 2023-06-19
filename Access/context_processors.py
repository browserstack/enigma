""" This file contains context processor methods"""

from Access.models import User
from Access.helpers import get_available_access_modules


def add_variables_to_context(request):
    """
    Function adds variables to the context of a web request.
     """
    # Skip adding context variables in case of API request
    if request.headers["Content-Type"] == "application/json":
        return {}

    try:
        current_user = User.objects.get(user__username=request.user)
    except User.DoesNotExist:
        return {}

    all_access_modules = get_available_access_modules()

    context = {}
    context["currentUser"] = current_user

    context["totalAccessCount"] = current_user.get_total_access_count()
    context["groupsMemberFor"] = len(current_user.get_active_groups())
    context["pendingActionsCount"] = current_user.get_pending_approvals_count(all_access_modules)

    return context

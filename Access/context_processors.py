from Access.models import User
from Access.helpers import get_available_access_modules, getPossibleApproverPermissions


def add_variables_to_context(request):
    # Skip adding context variables in case of API request
    if request.headers["Content-Type"] == "application/json":
        return {}

    try:
        currentUser = User.objects.get(user__username=request.user)
    except User.DoesNotExist:
        return {}

    all_access_modules = get_available_access_modules()

    context = {}
    context["currentUser"] = currentUser

    context["totalAccessCount"] = currentUser.get_total_access_count()
    context["groupsMemberFor"] = len(currentUser.get_active_groups())
    context["users"] = User.objects.filter().exclude(
        user__username='system_user').only("user")
    return context

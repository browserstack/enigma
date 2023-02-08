from Access.models import User
from Access.helpers import getAvailableAccessModules, getPossibleApproverPermissions


def add_variables_to_context(request):
    # Skip adding context variables in case of API request
    if request.headers["Content-Type"] == "application/json":
        return {}

    try:
        currentUser = User.objects.get(user__username=request.user)
    except User.DoesNotExist:
        return {}

    all_access_modules = getAvailableAccessModules()

    context = {}
    context["currentUser"] = currentUser

    context["groupsMemberFor"] = len(currentUser.get_active_groups())

    return context

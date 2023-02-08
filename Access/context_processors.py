import datetime

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
    context["currentYear"] = datetime.datetime.now().year
    context["users"] = User.objects.filter().only("user")
    context["anyApprover"] = currentUser.isAnApprover(getPossibleApproverPermissions())
    context["is_ops"] = currentUser.is_ops
    context["access_list"] = [
        {"tag": each_tag, "desc": each_module.access_desc()}
        for each_tag, each_module in all_access_modules.items()
    ]

    context["pendingCount"] = currentUser.getPendingApprovalsCount(all_access_modules)
    context["grantFailureCount"] = currentUser.getFailedGrantsCount()
    context["revokeFailureCount"] = currentUser.getFailedRevokesCount()

    context["groups"] = sorted([group.name for group in currentUser.getOwnedGroups()])

    return context

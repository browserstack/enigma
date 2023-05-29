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
    context["anyApprover"] = currentUser.is_an_approver(getPossibleApproverPermissions())
    context["is_ops"] = currentUser.is_ops
    context["access_list"] = [
        {"tag": each_tag, "desc": each_module.access_desc()}
        for each_tag, each_module in all_access_modules.items()
    ]

    context["pendingCount"] = currentUser.get_pending_approvals_count(all_access_modules)
    context["grantFailureCount"] = currentUser.get_failed_grants_count()
    context["revokeFailureCount"] = currentUser.get_failed_revokes_count()

    context["groups"] = sorted([group.name for group in currentUser.get_owned_groups()])

    return context

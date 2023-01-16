import datetime

from Access.models import User
from Access.helpers import getAvailableAccessModules, getPossibleApproverPermissions


def add_variables_to_context(request):
    if request.headers['Content-Type'] == "application/json":
        return {}

    try:
        currentUser = User.objects.get(user__username=request.user)
    except User.DoesNotExist:
        return {}

    all_access_modules = getAvailableAccessModules()

    context = {}
    context["currentYear"] = datetime.datetime.now().year
    context["users"] = User.objects.filter().only('user')
    context["anyApprover"] = currentUser.isAnApprover(getPossibleApproverPermissions())
    context["is_ops"] = currentUser.is_ops
    context["access_list"] = [{
        'tag': each_module.tag(),
        'desc': each_module.access_desc()
    } for each_module in all_access_modules]

    context['pendingCount'] = currentUser.getPendingApprovalsCount(all_access_modules)
    context['grantFailureCount'] = currentUser.getFailedGrantsCount()
    context['revokeFailureCount'] = currentUser.getFailedRevokesCount()

    context["groups"] = sorted([group.name for group in currentUser.getOwnedGroups()])

    return context

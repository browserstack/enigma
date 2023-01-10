import datetime, json

from Access.models import (User, GroupAccessMapping, UserAccessMapping, GroupV2, MembershipV2)
from Access.helpers import check_user_permissions, getAvailableAccessModules, getPossibleApproverPermissions
from BrowserStackAutomation.settings import PERMISSION_CONSTANTS

def add_variables_to_context(request):
    pendingCount = 0
    now = datetime.datetime.now()
    try:
        currentUser = User.objects.get(user__username=request.user)
    except User.DoesNotExist:
        return {}

    context = {}
    context['currentYear'] = now.year
    context["users"] = User.objects.filter().only('user')

    if check_user_permissions(request.user, PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]):
        pendingCount += MembershipV2.objects.filter(status='pending', group__status="Approved").count()
        pendingCount += GroupAccessMapping.objects.filter(status='pending').count()
        pendingCount += GroupV2.objects.filter(status='pending').count()

    all_access_modules = getAvailableAccessModules()

    ### Get count of pending requests on user.
    for each_access_module in all_access_modules:
        try:
            module_permissions = each_access_module.fetch_approver_permissions()
        except:
            module_permissions = {
                "1": PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]
            }
        access_tag = each_access_module.tag()
        requests = []

        if check_user_permissions(request.user, module_permissions["1"]):
            pendingCount += UserAccessMapping.objects.filter(status='pending', access__access_tag=access_tag).count()
        elif "2" in module_permissions and check_user_permissions(request.user, module_permissions["2"]):
            pendingCount += UserAccessMapping.objects.filter(status='secondarypending', access__access_tag=access_tag).count()

    context['anyApprover'] = request.user.user.isAnApprover(getPossibleApproverPermissions())
    context['pendingCount'] = pendingCount
    context['is_ops'] = currentUser.is_ops

    failureCount = 0
    if currentUser.user.is_superuser or currentUser.is_ops:
        failureCount += UserAccessMapping.objects.filter(status__in=["grantfailed"]).count()
    context['failureCount'] = failureCount

    revokefailureCount = 0
    if currentUser.user.is_superuser or currentUser.is_ops:
        revokefailureCount += UserAccessMapping.objects.filter(status__in=["revokefailed"]).count()
    context['revokefailureCount'] = revokefailureCount

    if currentUser.user.is_superuser or currentUser.is_ops:
        context["groups"] = sorted([str(group.name) for group in GroupV2.objects.all().filter(status='Approved')])
    else:
        context["groups"] = sorted([str(membership_obj.group.name) for membership_obj in MembershipV2.objects.filter(is_owner=True,user=request.user.user)])

    context["access_list"] = [{ 'tag': each_module.tag(), 'desc': each_module.access_desc()} for each_module in all_access_modules ]

    return context

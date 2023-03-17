"""BrowserStackAutomation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from bootprocess.views import dashboard, logout_view
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import re_path, include
from Access.views import (
    revoke_group_access,
    user_offboarding,
    show_access_history,
    pending_requests,
    pending_failure,
    pending_revoke,
    update_user_info,
    save_identity,
    create_new_group,
    all_user_access_list,
    mark_revoked,
    all_users_list,
    request_access,
    group_access,
    group_access_list,
    approve_new_group,
    add_user_to_group,
    group_dashboard,
    accept_bulk,
    decline_access,
    update_group_owners,
    remove_group_member,
    individual_resolve
)
from Access.helpers import get_available_access_modules

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^$", dashboard, name="dashboard"),
    re_path(r"^login/$", auth_views.LoginView.as_view(), name="login"),
    re_path(r"^logout/$", logout_view, name="logout"),
    re_path(r"^access/markRevoked", mark_revoked, name="markRevoked"),
    re_path(r"^oauth/", include("social_django.urls", namespace="social")),
    re_path(r"^access/showAccessHistory$", show_access_history, name="showAccessHistory"),
    re_path(r"^access/pendingRequests$", pending_requests, name="pendingRequests"),
    re_path(r"^resolve/pendingFailure", pending_failure, name="pendingFailure"),
    re_path(r"^resolve/pendingRevoke", pending_revoke, name="pendingRevoke"),
    re_path(r"^user/updateUserInfo/", update_user_info, name="updateUserInfo"),
    re_path(r"^user/saveIdentity/", save_identity, name="saveIdentity"),
    re_path(r"^group/create$", create_new_group, name="createNewGroup"),
    re_path(r"^group/dashboard/$", group_dashboard, name="groupDashboard"),
    re_path(r"^access/userAccesses$", all_user_access_list, name="allUserAccessList"),
    re_path(r"^access/usersList$", all_users_list, name="allUsersList"),
    re_path(r"^user/offboardUser$", user_offboarding, name="offboarding_user"),
    re_path(r"^access/requestAccess$", request_access, name="requestAccess"),
    re_path(r"^group/requestAccess$", group_access, name="groupRequestAccess"),
    re_path(
        r"^group/access/list/(?P<group_name>[\w -]+)$",
        group_access_list,
        name="groupAccessList",
    ),
    re_path(
        r"^group/new/accept/(?P<requestId>.*)$", approve_new_group, name="approveNewGroup"
    ),
    re_path(
        r"^group/adduser/(?P<groupName>[\w -]+)$",
        add_user_to_group,
        name="addUserToGroup",
    ),
    re_path(
        r"^group/updateOwners/(?P<groupName>[\w -]+)$",
        update_group_owners,
        name="updateGroupOwners",
    ),
    re_path(r"^access/pendingRequests$", pending_requests, name="pendingRequests"),
    re_path(r"^accept_bulk/(?P<selector>[\w-]+)", accept_bulk, name="accept_bulk"),
    re_path(
        r"^decline/(?P<accessType>[\w-]+)/(?P<requestId>.*)$",
        decline_access,
        name="decline",
    ),
    re_path(
        r"^group/removeGroupMember$", remove_group_member, name="remove_group_member"
    ),
    re_path(r"^group/revokeAccess", revoke_group_access, name="revoke_group_access"),
    re_path(r"^individual_resolve$", individual_resolve, name="individual_resolve")
]

for tag, each_module in get_available_access_modules().items():
    urlpatterns.extend(each_module.urlpatterns)

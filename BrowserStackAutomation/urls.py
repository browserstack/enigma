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
    showAccessHistory,
    pendingRequests,
    pendingFailure,
    pending_revoke,
    updateUserInfo,
    saveIdentity,
    createNewGroup,
    allUserAccessList,
    allUsersList,
    requestAccess,
    group_access,
    group_access_list,
    approveNewGroup,
    add_user_to_group,
    groupDashboard,
    accept_bulk,
    update_group_owners,
    remove_group_member,
)

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^$", dashboard, name="dashboard"),
    re_path(r"^login/$", auth_views.LoginView.as_view(), name="login"),
    re_path(r"^logout/$", logout_view, name="logout"),
    re_path(r"^oauth/", include("social_django.urls", namespace="social")),
    re_path(r"^access/showAccessHistory$", showAccessHistory, name="showAccessHistory"),
    re_path(r"^access/pendingRequests$", pendingRequests, name="pendingRequests"),
    re_path(r"^resolve/pendingFailure", pendingFailure, name="pendingFailure"),
    re_path(r"^resolve/pendingRevoke", pending_revoke, name="pendingRevoke"),
    re_path(r"^user/updateUserInfo/", updateUserInfo, name="updateUserInfo"),
    re_path(r"^user/saveIdentity/", saveIdentity, name="saveIdentity"),
    re_path(r"^group/create$", createNewGroup, name="createNewGroup"),
    re_path(r"^group/dashboard/$", groupDashboard, name="groupDashboard"),
    re_path(r"^access/userAccesses$", allUserAccessList, name="allUserAccessList"),
    re_path(r"^access/usersList$", allUsersList, name="allUsersList"),
    re_path(r"^access/requestAccess$", requestAccess, name="requestAccess"),
    re_path(r"^group/requestAccess$", group_access, name="groupRequestAccess"),
    re_path(
        r"^group/access/list/(?P<groupName>[\w -]+)$",
        group_access_list,
        name="groupAccessList",
    ),
    re_path(
        r"^group/new/accept/(?P<requestId>.*)$", approveNewGroup, name="approveNewGroup"
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
    re_path(r"^accept_bulk/(?P<selector>[\w-]+)", accept_bulk, name="accept_bulk"),
    re_path(
        r"^group/removeGroupMember$", remove_group_member, name="remove_group_member"
    ),
]

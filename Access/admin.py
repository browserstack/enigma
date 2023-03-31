'''
Models to configure diplay, search and filtering for models on admin panel
'''

from django.contrib import admin

from Access.models import (
    User,
    Permission,
    UserAccessMapping,
    Role,
    AccessV2,
    GroupV2,
    MembershipV2,
    GroupAccessMapping,
    UserIdentity,
)


class UserAdmin(admin.ModelAdmin):
    '''Class to describe how to display User model on admin panel'''
    ordering = ("name", "email")
    search_fields = ("name", "email")
    list_display = ("name", "email")


class MembershipV2AdminPanel(admin.ModelAdmin):
    '''Class to describe how to display MembershipV2 on admin panel'''
    ordering = ("membership_id", "user", "group")
    search_fields = ("membership_id", "user", "group")
    list_display = ("membership_id", "user", "group")


class AccessV2AdminPanel(admin.ModelAdmin):
    '''Class to describe how to display AccessV2 model on admin panel'''
    search_fields = ("access_tag", "access_label")
    list_display = ("access_tag", "access_label")


class UserIdentityAdminPanel(admin.ModelAdmin):
    '''Class to describe how to display User Identity on admin panel'''
    search_fields = ("access_tag", "user", "identity", "status")
    list_display = ("access_tag", "user", "identity", "status")


admin.site.register(User, UserAdmin)
admin.site.register(Permission)
admin.site.register(UserAccessMapping)
admin.site.register(Role)
admin.site.register(AccessV2, AccessV2AdminPanel)
admin.site.register(GroupV2)
admin.site.register(MembershipV2, MembershipV2AdminPanel)
admin.site.register(GroupAccessMapping)
admin.site.register(UserIdentity, UserIdentityAdminPanel)

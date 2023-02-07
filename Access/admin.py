from django.contrib import admin

from Access.models import (
    User,
    Permission,
    UserAccessMapping,
    Role,
    AccessV2,
    GroupV2,
    MembershipV2,
    GroupAccessMapping
)


class UserAdmin(admin.ModelAdmin):
    ordering = ("name", "email")
    search_fields = ("name", "email")
    list_display = ("name", "email")


admin.site.register(User, UserAdmin)

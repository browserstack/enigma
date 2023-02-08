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
    UserIdentity
)

admin.site.register(AccessV2)
admin.site.register(GroupV2)
admin.site.register(MembershipV2)
admin.site.register(GroupAccessMapping)
admin.site.register(UserIdentity)

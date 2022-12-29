from django.contrib import admin

from Access.models import User, Permission, UserAccessMapping, Role

admin.site.register(Permission)
admin.site.register(UserAccessMapping)
admin.site.register(Role)
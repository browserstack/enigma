from django.contrib import admin
from Access.models import User


class UserAdmin(admin.ModelAdmin):
    ordering = ("name", "email")
    search_fields = ("name", "email")
    list_display = ("name", "email")

admin.site.register(User, UserAdmin)

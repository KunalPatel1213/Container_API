from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model

from .models import Register

User = get_user_model()

try:
    admin.site.unregister(User)
except NotRegistered:
    pass


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ("id", "fullname", "company", "email", "auth_user", "created_at")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("fullname", "company", "email", "user__username")
    list_filter = ("company", "created_at")

    @admin.display(description="Auth User")
    def auth_user(self, obj):
        return obj.user.username

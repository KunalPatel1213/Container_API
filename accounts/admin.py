from django.contrib import admin

from .models import Register


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ("id", "fullname", "company", "email", "user", "created_at")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("fullname", "company", "email", "user__username")

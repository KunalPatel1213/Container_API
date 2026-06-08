from django.contrib import admin

from .models import ServiceProvider


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "mobile_number",
        "email",
        "account_type",
        "payment_setup",
        "otp_verified",
        "is_active",
        "created_at",
    ]
    list_filter = ["account_type", "payment_setup", "otp_verified", "is_active", "created_at"]
    list_select_related = ["user"]
    search_fields = ["name", "mobile_number", "email", "user__username"]
    readonly_fields = ["created_at", "updated_at"]

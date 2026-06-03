from django.contrib import admin

from .models import ServiceProvider


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ["name", "mobile_number", "email", "payment_setup", "otp_verified", "is_active"]
    list_filter = ["payment_setup", "otp_verified", "is_active"]
    search_fields = ["name", "mobile_number", "email"]
    readonly_fields = ["created_at", "updated_at"]

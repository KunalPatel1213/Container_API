from django.contrib import admin

from .models import ServiceProviderAvailability


@admin.register(ServiceProviderAvailability)
class ServiceProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        "current_location",
        "vehicle_type",
        "weight_capacity_kg",
        "price_per_km",
        "available_until",
        "is_published",
    ]
    list_filter = ["vehicle_type", "is_published", "available_until"]
    search_fields = ["current_location", "can_travel_upto", "notes", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

from django.contrib import admin
from .models import BookingValidation

@admin.register(BookingValidation)
class BookingValidationAdmin(admin.ModelAdmin):
    list_display = (
        'container_id',
        'container_type',
        'total_capacity',
        'available_capacity',
        'capacity_unit',
        'origin_location',
        'destination_location',
        'departure_date',
        'arrival_date',
        'status',
        'last_updated',
        'provider_id',
    )
    search_fields = ('container_id', 'container_type', 'origin_location', 'destination_location')
    list_filter = ('status', 'container_type', 'origin_location', 'destination_location')
    ordering = ('departure_date',)

    # Optional: read-only fields
    readonly_fields = ('last_updated',)

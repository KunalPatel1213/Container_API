from django.utils import timezone
from rest_framework import serializers

from serviceprovider.models import ServiceProvider

from .models import ServiceProviderAvailability


class ServiceProviderAvailabilitySerializer(serializers.ModelSerializer):
    service_provider = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        required=False,
        allow_null=True,
    )
    service_provider_name = serializers.CharField(source="service_provider.name", read_only=True)

    class Meta:
        model = ServiceProviderAvailability
        fields = [
            "id",
            "service_provider",
            "service_provider_name",
            "current_location",
            "vehicle_type",
            "weight_capacity_kg",
            "empty_space",
            "can_travel_upto",
            "price_per_km",
            "available_until",
            "notes",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "service_provider_name", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields["service_provider"].queryset = ServiceProvider.objects.filter(user=request.user)

    def validate_available_until(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Available until must be a future date and time.")
        return value

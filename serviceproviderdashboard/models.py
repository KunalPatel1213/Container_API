from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ServiceProviderAvailability(models.Model):
    VEHICLE_TRUCK = "truck"
    VEHICLE_PICKUP = "pickup"
    VEHICLE_TEMPO = "tempo"
    VEHICLE_VAN = "van"
    VEHICLE_BIKE = "bike"
    VEHICLE_OTHER = "other"

    VEHICLE_CHOICES = [
        (VEHICLE_TRUCK, "Truck"),
        (VEHICLE_PICKUP, "Pickup"),
        (VEHICLE_TEMPO, "Tempo"),
        (VEHICLE_VAN, "Van"),
        (VEHICLE_BIKE, "Bike"),
        (VEHICLE_OTHER, "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_provider_availabilities",
    )
    service_provider = models.ForeignKey(
        "serviceprovider.ServiceProvider",
        on_delete=models.CASCADE,
        related_name="availabilities",
        blank=True,
        null=True,
    )
    current_location = models.CharField(max_length=255)
    vehicle_type = models.CharField(max_length=30, choices=VEHICLE_CHOICES, default=VEHICLE_TRUCK)
    weight_capacity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    empty_space = models.CharField(max_length=150)
    can_travel_upto = models.CharField(max_length=255)
    price_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    available_until = models.DateTimeField()
    notes = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Service Provider Availability"
        verbose_name_plural = "Service Provider Availabilities"

    def __str__(self):
        return f"{self.get_vehicle_type_display()} at {self.current_location}"

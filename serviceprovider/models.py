from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


class ServiceProvider(models.Model):
    PAYMENT_CASH = "cash"
    PAYMENT_UPI = "upi"
    PAYMENT_CARD = "card"
    PAYMENT_BANK = "bank_transfer"

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_UPI, "UPI"),
        (PAYMENT_CARD, "Card"),
        (PAYMENT_BANK, "Bank Transfer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_provider_profile",
    )
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[1-9]\d{9,14}$",
                message="Enter a valid mobile number with country code optional.",
            )
        ],
    )
    otp_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    payment_setup = models.CharField(max_length=30, choices=PAYMENT_CHOICES)
    profile_photo = models.FileField(
        upload_to="serviceproviders/profile_photos/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    payment_setup_image = models.FileField(
        upload_to="serviceproviders/payment_setup/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    allow_location_access = models.BooleanField(default=False)
    enable_gps_tracking = models.BooleanField(default=False)
    allow_contacts_access = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.mobile_number})"

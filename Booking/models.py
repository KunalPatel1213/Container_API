from django.db import models
from django.utils import timezone

class Booking(models.Model):
    booking_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    provider_id = models.CharField(max_length=50, null=True, blank=True)
    provider_email = models.EmailField(max_length=254, null=True, blank=True)
    provider_name = models.CharField(max_length=100, null=True, blank=True)

    user_name = models.CharField(max_length=100, null=True, blank=True)
    user_email = models.EmailField(max_length=254, null=True, blank=True)
    user_mobile = models.CharField(max_length=20, null=True, blank=True)
    user_location = models.CharField(max_length=255, null=True, blank=True)
    drop_location = models.CharField(max_length=255, blank=True, default='')
    cargo_weight_kg = models.CharField(max_length=50, blank=True, default='')
    cargo_space = models.CharField(max_length=50, blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)

    user_id = models.CharField(max_length=20, blank=True, null=True)
    item_id = models.IntegerField(blank=True, null=True)
    booking_date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    STATUS_CHOICES = [
        ('new', 'New'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='INR')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Booking {self.id}"

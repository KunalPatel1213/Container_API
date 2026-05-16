from django.db import models

class BookingValidation(models.Model):
    # Container details
    container_id = models.IntegerField()
    container_type = models.CharField(max_length=50)   # e.g. 20ft, 40ft, refrigerated
    total_capacity = models.FloatField()               # e.g. 20.0 CBM
    available_capacity = models.FloatField()           # remaining space
    capacity_unit = models.CharField(max_length=20)    # CBM, Tons, Pallets

    # Location & Route
    origin_location = models.CharField(max_length=100)
    destination_location = models.CharField(max_length=100)
    departure_date = models.DateTimeField()
    arrival_date = models.DateTimeField()

    # Status & Metadata
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('FULL', 'Full'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    last_updated = models.DateTimeField(auto_now=True)   # auto update on save
    provider_id = models.IntegerField()

    def __str__(self):
        return f"Container {self.container_id} - {self.status}"

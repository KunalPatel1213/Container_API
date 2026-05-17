from django.db import models

class Container(models.Model):
    container_id = models.CharField(max_length=100, unique=True)  
    transport_mode = models.CharField(max_length=50, choices=[
        ('Ship', 'Ship'),
        ('Train', 'Train'),
        ('Truck', 'Truck'),
        ('Bus', 'Bus'),
    ])
    container_type = models.CharField(max_length=50)  # e.g. 20ft, 40ft, refrigerated
    capacity_volume = models.FloatField()  # in cubic meters
    capacity_weight = models.FloatField()  # in kilograms
    available_volume = models.FloatField()
    available_weight = models.FloatField()
    location = models.CharField(max_length=100)  # current city/port
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)  # per kg/CBM
    provider_name = models.CharField(max_length=100)

    status = models.CharField(max_length=50, choices=[
        ('Available', 'Available'),
        ('Limited', 'Limited'),
        ('Full', 'Full'),
        ('In Transit', 'In Transit'),
    ], default='Available')
    verification_status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
    ], default='Pending')
    special_handling = models.CharField(max_length=200, blank=True, null=True)  # fragile, hazardous, etc.
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.container_id} - {self.transport_mode} ({self.status})"

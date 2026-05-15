from django.db import models

class Booking(models.Model):
    user_id = models.CharField(max_length=20)
    item_id = models.IntegerField()   
    booking_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Booking {self.id}"

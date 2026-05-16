from rest_framework import serializers
from .models import BookingValidation

class BookingValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingValidation
        fields = '__all__'

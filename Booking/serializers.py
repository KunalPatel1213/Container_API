from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(required=True, allow_blank=False)
    provider_id = serializers.CharField(required=True, allow_blank=False)
    provider_email = serializers.EmailField(required=True)
    provider_name = serializers.CharField(required=True, allow_blank=False)

    user_name = serializers.CharField(required=True, allow_blank=False)
    user_email = serializers.EmailField(required=True)
    user_mobile = serializers.CharField(required=True, allow_blank=False)
    user_location = serializers.CharField(required=True, allow_blank=False)

    drop_location = serializers.CharField(required=False, allow_blank=True, default='')
    cargo_weight_kg = serializers.CharField(required=False, allow_blank=True, default='')
    cargo_space = serializers.CharField(required=False, allow_blank=True, default='')
    total_payment = serializers.CharField(required=False, allow_blank=True, default='')
    total_payment_paise = serializers.IntegerField(required=True, min_value=1)
    status = serializers.ChoiceField(choices=[choice[0] for choice in Booking.STATUS_CHOICES], required=False, default='new')
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_id',
            'provider_id',
            'provider_email',
            'provider_name',
            'user_name',
            'user_email',
            'user_mobile',
            'user_location',
            'drop_location',
            'cargo_weight_kg',
            'cargo_space',
            'total_payment',
            'total_payment_paise',
            'status',
            'created_at',
            'payment_status',
            'amount',
            'currency',
            'razorpay_order_id',
            'razorpay_payment_id',
            'razorpay_signature',
            'user_id',
            'item_id',
            'booking_date',
            'start_date',
            'end_date',
        ]
        read_only_fields = [
            'id',
            'payment_status',
            'amount',
            'currency',
            'razorpay_order_id',
            'razorpay_payment_id',
            'razorpay_signature',
            'user_id',
            'item_id',
            'booking_date',
            'start_date',
            'end_date',
        ]

    def validate(self, attrs):
        errors = {}
        required_fields = [
            'booking_id',
            'provider_id',
            'provider_email',
            'provider_name',
            'user_name',
            'user_email',
            'user_mobile',
            'user_location',
            'total_payment_paise',
        ]

        for field_name in required_fields:
            value = attrs.get(field_name)
            if value in [None, '']:
                errors[field_name] = ['This field is required.']

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        validated_data.pop('total_payment', None)
        validated_data.pop('total_payment_paise', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('total_payment', None)
        validated_data.pop('total_payment_paise', None)
        return super().update(instance, validated_data)

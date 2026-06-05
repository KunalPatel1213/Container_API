from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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
    total_payment = serializers.CharField(required=False, allow_blank=True, default='', write_only=True)
    total_payment_paise = serializers.IntegerField(required=False, min_value=1, write_only=True)
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
            'gowquick_order_id',
            'gowquick_status',
            'gowquick_tracking_url',
            'gowquick_response',
            'gowquick_error',
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
            'gowquick_order_id',
            'gowquick_status',
            'gowquick_tracking_url',
            'gowquick_response',
            'gowquick_error',
            'user_id',
            'item_id',
            'booking_date',
            'start_date',
            'end_date',
        ]

    def validate(self, attrs):
        errors = {}

        # On partial update, validate only provided fields.
        if self.instance is not None and self.partial:
            return attrs

        required_fields = [
            'booking_id',
            'provider_id',
            'provider_email',
            'provider_name',
            'user_name',
            'user_email',
            'user_mobile',
            'user_location',
        ]

        for field_name in required_fields:
            if self.instance is None:
                value = attrs.get(field_name)
                if value in [None, '']:
                    errors[field_name] = ['This field is required.']
            else:
                if field_name in attrs and attrs.get(field_name) in [None, '']:
                    errors[field_name] = ['This field may not be blank.']

        amount_paise = attrs.get('total_payment_paise')
        if amount_paise in [None, '']:
            raw_amount_paise = self.initial_data.get('amount')
            raw_total_payment = self.initial_data.get('total_payment')

            if raw_amount_paise not in [None, '']:
                try:
                    amount_paise = int(Decimal(str(raw_amount_paise)))
                except (InvalidOperation, TypeError, ValueError):
                    errors['total_payment_paise'] = ['A valid total_payment_paise or amount value is required.']
            elif raw_total_payment not in [None, '']:
                try:
                    total_rupees = Decimal(str(raw_total_payment))
                    amount_paise = int((total_rupees * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, TypeError, ValueError):
                    errors['total_payment_paise'] = ['A valid total_payment value is required.']
            elif self.instance is None:
                errors['total_payment_paise'] = ['This field is required.']

        if amount_paise not in [None, '']:
            try:
                amount_paise = int(amount_paise)
            except (TypeError, ValueError):
                errors['total_payment_paise'] = ['A valid total_payment_paise value is required.']

        if amount_paise is not None and amount_paise <= 0:
            errors['total_payment_paise'] = ['Amount must be greater than 0.']

        if amount_paise is not None:
            attrs['total_payment_paise'] = amount_paise

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

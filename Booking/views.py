import hashlib
import hmac
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

try:
    import razorpay
except ImportError:
    razorpay = None

from .models import Booking
from .serializers import BookingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    # GET (list + retrieve) → handled automatically
    # POST (create) → handled automatically
    # PUT/PATCH (update) → handled automatically
    # DELETE (destroy) → handled automatically

    # If you want to customize responses, you can override methods:
    def _validation_error_response(self, serializer):
        return Response(
            {
                'message': 'Validation failed.',
                'errors': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return self._validation_error_response(serializer)

        amount_value = serializer.validated_data.get('total_payment_paise')
        try:
            amount_paise = int(Decimal(str(amount_value)))
        except (InvalidOperation, TypeError):
            return Response(
                {
                    'message': 'Validation failed.',
                    'errors': {'total_payment_paise': ['A valid total_payment_paise value is required.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount_paise <= 0:
            return Response(
                {
                    'message': 'Validation failed.',
                    'errors': {'total_payment_paise': ['Amount must be greater than 0 to create a Razorpay order.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if razorpay is None:
            return Response(
                {
                    'detail': 'Razorpay package is not installed on the server.',
                    'error': 'ImportError',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return Response(
                {
                    'detail': 'Razorpay keys are not configured on server.',
                    'missing': [
                        name
                        for name, value in [
                            ('RAZORPAY_KEY_ID', settings.RAZORPAY_KEY_ID),
                            ('RAZORPAY_KEY_SECRET', settings.RAZORPAY_KEY_SECRET),
                        ]
                        if not value
                    ],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        currency = request.data.get('currency') or settings.RAZORPAY_CURRENCY

        try:
            with transaction.atomic():
                booking = serializer.save(amount=Decimal(amount_paise), currency=currency, payment_status='unpaid')
                razorpay_order = self._create_razorpay_order(
                    booking=booking,
                    amount_paise=amount_paise,
                    currency=currency,
                )
                booking.amount = Decimal(amount_paise)
                booking.currency = currency
                booking.payment_status = 'created'
                booking.razorpay_order_id = razorpay_order['id']
                booking.save(update_fields=['amount', 'currency', 'payment_status', 'razorpay_order_id'])
        except Exception as exc:
            return Response(
                {
                    'detail': 'Unable to create Razorpay order.',
                    'error': exc.__class__.__name__,
                    'error_message': str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': booking.razorpay_order_id,
                'amount': amount_paise,
                'currency': currency,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return self._validation_error_response(serializer)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='create-razorpay-order')
    def create_razorpay_order(self, request, pk=None):
        booking = self.get_object()
        amount_value = request.data.get('total_payment_paise', request.data.get('amount', booking.amount))

        try:
            amount_paise = int(Decimal(str(amount_value)))
        except (InvalidOperation, TypeError):
            return Response({'detail': 'Valid total_payment_paise is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if amount_paise <= 0:
            return Response({'detail': 'Amount must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return Response(
                {
                    'detail': 'Razorpay keys are not configured on server.',
                    'missing': [
                        name
                        for name, value in [
                            ('RAZORPAY_KEY_ID', settings.RAZORPAY_KEY_ID),
                            ('RAZORPAY_KEY_SECRET', settings.RAZORPAY_KEY_SECRET),
                        ]
                        if not value
                    ],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        currency = request.data.get('currency') or settings.RAZORPAY_CURRENCY

        try:
            razorpay_order = self._create_razorpay_order(booking=booking, amount_paise=amount_paise, currency=currency)
        except Exception as exc:
            return Response(
                {
                    'detail': 'Unable to create Razorpay order.',
                    'error': exc.__class__.__name__,
                    'error_message': str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        booking.amount = Decimal(amount_paise)
        booking.currency = currency
        booking.payment_status = 'created'
        booking.razorpay_order_id = razorpay_order['id']
        booking.save(update_fields=['amount', 'currency', 'payment_status', 'razorpay_order_id'])

        return Response(
            {
                'booking_id': booking.booking_id or booking.id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': razorpay_order['id'],
                'amount': amount_paise,
                'currency': currency,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='verify-razorpay-payment')
    def verify_razorpay_payment(self, request, pk=None):
        booking = self.get_object()
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'detail': 'Payment verification fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.RAZORPAY_KEY_SECRET:
            return Response(
                {'detail': 'Razorpay secret is not configured on server.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if razorpay_order_id != booking.razorpay_order_id:
            booking.payment_status = 'failed'
            booking.save(update_fields=['payment_status'])
            return Response({'detail': 'Order id does not match booking.'}, status=status.HTTP_400_BAD_REQUEST)

        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            f'{razorpay_order_id}|{razorpay_payment_id}'.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, razorpay_signature):
            booking.payment_status = 'failed'
            booking.save(update_fields=['payment_status'])
            return Response({'detail': 'Invalid payment signature.'}, status=status.HTTP_400_BAD_REQUEST)

        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        booking.razorpay_payment_id = razorpay_payment_id
        booking.razorpay_signature = razorpay_signature
        booking.save(update_fields=['payment_status', 'status', 'razorpay_payment_id', 'razorpay_signature'])

        return Response(BookingSerializer(booking).data)

    def _create_razorpay_order(self, booking, amount_paise, currency):
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        return client.order.create(
            {
                'amount': int(amount_paise),
                'currency': currency,
                'receipt': booking.booking_id or f'booking_{booking.id}',
                'notes': {
                    'booking_id': booking.booking_id or str(booking.id),
                    'provider_id': booking.provider_id or '',
                    'provider_email': booking.provider_email or '',
                    'user_email': booking.user_email or '',
                },
            }
        )

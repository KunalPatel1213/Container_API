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
from .gowquick import GowquickClient, GowquickError

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

    @action(detail=False, methods=['post'], url_path='payment-sync')
    def payment_sync(self, request):
        booking_id = request.data.get('booking_id')
        payment_status_input = request.data.get('payment_status')
        payment_provider = request.data.get('payment_provider')

        if not booking_id:
            return Response(
                {'message': 'Validation failed.', 'detail': 'booking_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not payment_status_input:
            return Response(
                {'message': 'Validation failed.', 'detail': 'payment_status is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not payment_provider:
            return Response(
                {'message': 'Validation failed.', 'detail': 'payment_provider is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider = str(payment_provider).strip().lower()
        if provider == 'gokwik':
            provider = 'gowquick'

        normalized_payment_status = str(payment_status_input).strip().lower()
        if normalized_payment_status not in {'paid', 'failed', 'pending'}:
            return Response(
                {'message': 'Validation failed.', 'detail': 'payment_status must be one of: paid, failed, pending.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'message': 'Booking not found.', 'detail': f'No booking found for booking_id={booking_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        model_payment_status = {
            'paid': 'paid',
            'failed': 'failed',
            'pending': 'created',
        }[normalized_payment_status]

        payment_id = request.data.get('payment_id') or request.data.get('gokwik_payment_id')
        order_id = request.data.get('order_id') or request.data.get('gokwik_order_id')
        payment_signature = request.data.get('payment_signature')
        payment_response = request.data.get('payment_response')

        if payment_response is not None and not isinstance(payment_response, dict):
            return Response(
                {'message': 'Validation failed.', 'detail': 'payment_response must be a JSON object.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = []

        if booking.payment_status != model_payment_status:
            booking.payment_status = model_payment_status
            update_fields.append('payment_status')

        # Keep booking lifecycle status in sync for paid/failed callbacks.
        target_booking_status = None
        if normalized_payment_status == 'paid':
            target_booking_status = 'confirmed'
        elif normalized_payment_status == 'failed':
            target_booking_status = 'pending'

        if target_booking_status and booking.status != target_booking_status:
            booking.status = target_booking_status
            update_fields.append('status')

        if payment_id and booking.razorpay_payment_id != str(payment_id):
            booking.razorpay_payment_id = str(payment_id)
            update_fields.append('razorpay_payment_id')

        if order_id and booking.razorpay_order_id != str(order_id):
            booking.razorpay_order_id = str(order_id)
            update_fields.append('razorpay_order_id')

        if payment_signature and booking.razorpay_signature != str(payment_signature):
            booking.razorpay_signature = str(payment_signature)
            update_fields.append('razorpay_signature')

        gokwik_order_id = request.data.get('gokwik_order_id')
        if gokwik_order_id and booking.gowquick_order_id != str(gokwik_order_id):
            booking.gowquick_order_id = str(gokwik_order_id)
            update_fields.append('gowquick_order_id')

        if provider == 'gowquick':
            target_gowquick_status = {
                'paid': 'paid',
                'failed': 'failed',
                'pending': 'pending',
            }[normalized_payment_status]
            if booking.gowquick_status != target_gowquick_status:
                booking.gowquick_status = target_gowquick_status
                update_fields.append('gowquick_status')

        if payment_response is not None:
            merged_response = {}
            if isinstance(booking.gowquick_response, dict):
                merged_response.update(booking.gowquick_response)

            merged_response.update(
                {
                    'payment_provider': provider,
                    'payment_status': normalized_payment_status,
                }
            )
            merged_response.update(payment_response)

            if booking.gowquick_response != merged_response:
                booking.gowquick_response = merged_response
                update_fields.append('gowquick_response')

        if update_fields:
            booking.save(update_fields=update_fields)

        return Response(
            {
                'message': 'Payment sync processed successfully.',
                'idempotent': not bool(update_fields),
                'booking': {
                    'booking_id': booking.booking_id,
                    'status': booking.status,
                    'payment_status': booking.payment_status,
                    'payment_provider': provider,
                    'payment_id': booking.razorpay_payment_id,
                    'order_id': booking.razorpay_order_id,
                    'payment_signature': booking.razorpay_signature,
                    'gokwik_order_id': booking.gowquick_order_id,
                    'gokwik_payment_id': booking.razorpay_payment_id,
                    'payment_response': booking.gowquick_response,
                },
            },
            status=status.HTTP_200_OK,
        )

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

        if settings.GOWQUICK_AUTO_CREATE_AFTER_PAYMENT:
            self._try_create_gowquick_order(booking)

        return Response(BookingSerializer(booking).data)

    @action(detail=False, methods=['post'], url_path='gowquick-quote')
    def gowquick_quote(self, request):
        client = GowquickClient()
        if not client.is_configured():
            return Response(
                {'detail': 'Gowquick API is not configured on server.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payload = {
            'pickup_location': request.data.get('pickup_location') or request.data.get('user_location') or '',
            'drop_location': request.data.get('drop_location') or '',
            'cargo': {
                'weight_kg': request.data.get('cargo_weight_kg') or '',
                'space': request.data.get('cargo_space') or '',
            },
            'customer': {
                'name': request.data.get('user_name') or '',
                'email': request.data.get('user_email') or '',
                'mobile': request.data.get('user_mobile') or '',
            },
        }

        extra_payload = request.data.get('gowquick_payload')
        if isinstance(extra_payload, dict):
            payload.update(extra_payload)

        try:
            gowquick_response = client.quote(payload)
        except GowquickError as exc:
            return Response(
                {
                    'detail': 'Unable to get Gowquick quote.',
                    'error_message': str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(gowquick_response)

    @action(detail=True, methods=['post'], url_path='create-gowquick-order')
    def create_gowquick_order(self, request, pk=None):
        booking = self.get_object()

        if booking.payment_status != 'paid':
            return Response(
                {'detail': 'Gowquick order can be created only after payment is paid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            gowquick_response = self._create_gowquick_order_for_booking(booking, request.data)
        except GowquickError as exc:
            booking.gowquick_status = 'failed'
            booking.gowquick_error = str(exc)
            booking.save(update_fields=['gowquick_status', 'gowquick_error'])
            return Response(
                {
                    'detail': 'Unable to create Gowquick order.',
                    'error_message': str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                'booking': BookingSerializer(booking).data,
                'gowquick': gowquick_response,
            },
            status=status.HTTP_201_CREATED,
        )

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

    def _try_create_gowquick_order(self, booking):
        try:
            self._create_gowquick_order_for_booking(booking)
        except GowquickError as exc:
            booking.gowquick_status = 'failed'
            booking.gowquick_error = str(exc)
            booking.save(update_fields=['gowquick_status', 'gowquick_error'])

    def _create_gowquick_order_for_booking(self, booking, extra_payload=None):
        client = GowquickClient()
        if not client.is_configured():
            raise GowquickError('Gowquick API is not configured on server.')

        payload = client.build_booking_payload(booking)
        if isinstance(extra_payload, dict):
            gowquick_payload = extra_payload.get('gowquick_payload')
            if isinstance(gowquick_payload, dict):
                payload.update(gowquick_payload)

        gowquick_response = client.create_order(payload)
        booking.gowquick_response = gowquick_response
        booking.gowquick_order_id = self._read_first_value(
            gowquick_response,
            ['order_id', 'id', 'shipment_id', 'tracking_id', 'data.order_id', 'data.id'],
        )
        booking.gowquick_status = self._read_first_value(
            gowquick_response,
            ['status', 'order_status', 'shipment_status', 'data.status'],
        ) or 'created'
        booking.gowquick_tracking_url = self._read_first_value(
            gowquick_response,
            ['tracking_url', 'track_url', 'tracking_link', 'data.tracking_url'],
        )
        booking.gowquick_error = ''
        booking.save(
            update_fields=[
                'gowquick_response',
                'gowquick_order_id',
                'gowquick_status',
                'gowquick_tracking_url',
                'gowquick_error',
            ]
        )
        return gowquick_response

    def _read_first_value(self, data, paths):
        for path in paths:
            current = data
            for key in path.split('.'):
                if not isinstance(current, dict) or key not in current:
                    current = None
                    break
                current = current[key]
            if current not in [None, '']:
                return str(current)
        return ''

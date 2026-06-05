import json
from urllib import error, request
from urllib.parse import urljoin

from django.conf import settings


class GowquickError(Exception):
    pass


class GowquickClient:
    def __init__(self):
        self.base_url = settings.GOWQUICK_BASE_URL.rstrip('/') + '/'
        self.api_token = settings.GOWQUICK_API_TOKEN
        self.quote_endpoint = settings.GOWQUICK_QUOTE_ENDPOINT.lstrip('/')
        self.order_endpoint = settings.GOWQUICK_ORDER_ENDPOINT.lstrip('/')
        self.timeout = settings.GOWQUICK_TIMEOUT_SECONDS

    def is_configured(self):
        return bool(self.base_url and self.api_token)

    def quote(self, payload):
        return self._post(self.quote_endpoint, payload)

    def create_order(self, payload):
        return self._post(self.order_endpoint, payload)

    def build_booking_payload(self, booking):
        return {
            'booking_id': booking.booking_id or str(booking.id),
            'provider': {
                'id': booking.provider_id or '',
                'name': booking.provider_name or '',
                'email': booking.provider_email or '',
            },
            'customer': {
                'name': booking.user_name or '',
                'email': booking.user_email or '',
                'mobile': booking.user_mobile or '',
            },
            'pickup_location': booking.user_location or '',
            'drop_location': booking.drop_location or '',
            'cargo': {
                'weight_kg': booking.cargo_weight_kg or '',
                'space': booking.cargo_space or '',
            },
            'payment': {
                'amount': str(booking.amount),
                'currency': booking.currency,
                'status': booking.payment_status,
                'razorpay_order_id': booking.razorpay_order_id,
                'razorpay_payment_id': booking.razorpay_payment_id,
            },
        }

    def _post(self, endpoint, payload):
        if not self.api_token:
            raise GowquickError('Gowquick API token is not configured.')

        url = urljoin(self.base_url, endpoint)
        body = json.dumps(payload).encode('utf-8')
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        req = request.Request(url, data=body, headers=headers, method='POST')
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode('utf-8')
                if not response_body:
                    return {}
                return json.loads(response_body)
        except error.HTTPError as exc:
            response_body = exc.read().decode('utf-8', errors='replace')
            raise GowquickError(f'Gowquick API returned {exc.code}: {response_body}') from exc
        except error.URLError as exc:
            raise GowquickError(f'Unable to reach Gowquick API: {exc.reason}') from exc
        except json.JSONDecodeError as exc:
            raise GowquickError('Gowquick API returned invalid JSON.') from exc

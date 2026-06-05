from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('payment-sync/', BookingViewSet.as_view({'post': 'payment_sync'}), name='booking-payment-sync'),
    path('', include(router.urls)),
]

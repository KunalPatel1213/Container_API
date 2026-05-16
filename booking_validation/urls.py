from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingValidationViewSet

router = DefaultRouter()
router.register(r'booking-validation', BookingValidationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

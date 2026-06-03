from rest_framework.routers import DefaultRouter

from .views import ServiceProviderAvailabilityViewSet


router = DefaultRouter()
router.register(r"availability", ServiceProviderAvailabilityViewSet, basename="serviceproviderdashboard-availability")

urlpatterns = router.urls

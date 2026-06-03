from rest_framework.routers import DefaultRouter

from .views import ServiceProviderViewSet


router = DefaultRouter()
router.register(r"serviceproviders", ServiceProviderViewSet, basename="serviceprovider")

urlpatterns = router.urls

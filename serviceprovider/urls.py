from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ServiceProviderLoginView, ServiceProviderViewSet


router = DefaultRouter()
router.register(r"serviceproviders", ServiceProviderViewSet, basename="serviceprovider")

urlpatterns = router.urls + [
	path("login/", ServiceProviderLoginView.as_view(), name="serviceprovider-login"),
]

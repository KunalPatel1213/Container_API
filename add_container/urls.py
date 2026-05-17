from rest_framework.routers import DefaultRouter
from .views import ContainerViewSet

router = DefaultRouter()
router.register(r'containers', ContainerViewSet, basename='container')

urlpatterns = router.urls

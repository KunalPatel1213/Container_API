from rest_framework import permissions, viewsets

from .models import ServiceProvider
from .serializers import ServiceProviderSerializer, ServiceProviderUpdateSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj.user_id == request.user.id))


class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.select_related("user").all()

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return ServiceProviderUpdateSerializer
        return ServiceProviderSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

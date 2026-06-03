from rest_framework import exceptions, permissions, viewsets

from .models import ServiceProviderAvailability
from .serializers import ServiceProviderAvailabilitySerializer


class IsAvailabilityOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj.user_id == request.user.id))


class ServiceProviderAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderAvailability.objects.select_related("user", "service_provider").all()
    serializer_class = ServiceProviderAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAvailabilityOwnerOrAdmin]

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAvailabilityOwnerOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
            return

        service_provider = serializer.validated_data.get("service_provider")
        if not service_provider:
            raise exceptions.NotAuthenticated("Login or select a service provider to add availability.")
        serializer.save(user=service_provider.user)

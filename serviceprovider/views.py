from django.contrib.auth import login as django_login
from rest_framework import status
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service_provider = serializer.save()
        django_login(request, service_provider.user)
        refresh = RefreshToken.for_user(service_provider.user)
        return Response({
            "success": True,
            "message": "Service provider registered successfully.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "data": serializer.data,
        }, status=status.HTTP_201_CREATED)

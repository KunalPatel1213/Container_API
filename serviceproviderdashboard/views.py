from django.core.cache import cache
from rest_framework import exceptions, permissions, viewsets
from rest_framework.response import Response

from .models import ServiceProviderAvailability
from .serializers import ServiceProviderAvailabilitySerializer

DASHBOARD_CACHE_TIMEOUT = 60 * 5
DASHBOARD_VERSION_KEY = "serviceproviderdashboard:availability:version"


def _get_dashboard_cache_version():
    version = cache.get(DASHBOARD_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(DASHBOARD_VERSION_KEY, version, None)
    return version


def _bump_dashboard_cache_version():
    cache.set(DASHBOARD_VERSION_KEY, _get_dashboard_cache_version() + 1, None)


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

    def _list_cache_key(self):
        user = self.request.user
        query_string = self.request.query_params.urlencode()
        scope = "staff" if user.is_staff else f"user:{user.id}"
        return f"serviceproviderdashboard:availability:list:{_get_dashboard_cache_version()}:{scope}:{query_string}"

    def _detail_cache_key(self, obj):
        user = self.request.user
        scope = "staff" if user.is_staff else f"user:{user.id}"
        return f"serviceproviderdashboard:availability:detail:{_get_dashboard_cache_version()}:{scope}:{obj.pk}"

    def list(self, request, *args, **kwargs):
        cache_key = self._list_cache_key()
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            cache.set(cache_key, response.data, DASHBOARD_CACHE_TIMEOUT)
            return response

        serializer = self.get_serializer(queryset, many=True)
        response_data = list(serializer.data)
        cache.set(cache_key, response_data, DASHBOARD_CACHE_TIMEOUT)
        return Response(response_data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = self._detail_cache_key(instance)
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        serializer = self.get_serializer(instance)
        response_data = dict(serializer.data)
        cache.set(cache_key, response_data, DASHBOARD_CACHE_TIMEOUT)
        return Response(response_data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code < 400:
            _bump_dashboard_cache_version()
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code < 400:
            _bump_dashboard_cache_version()
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if response.status_code < 400:
            _bump_dashboard_cache_version()
        return response

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
            return

        service_provider = serializer.validated_data.get("service_provider")
        if not service_provider:
            raise exceptions.NotAuthenticated("Login or select a service provider to add availability.")
        serializer.save(user=service_provider.user)

from django.contrib.auth import get_user_model, login as django_login, logout as django_logout
from django.core.cache import cache
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Register
from .serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer


User = get_user_model()

PROFILE_CACHE_TIMEOUT = 60 * 15
USER_LIST_CACHE_TIMEOUT = 60 * 5
USER_LIST_VERSION_KEY = "accounts:user-list:version"


def _get_user_list_cache_version():
    version = cache.get(USER_LIST_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(USER_LIST_VERSION_KEY, version, None)
    return version


def _bump_user_list_cache_version():
    cache.set(USER_LIST_VERSION_KEY, _get_user_list_cache_version() + 1, None)


def _profile_cache_key(user_id):
    return f"accounts:profile:{user_id}"


def _profile_payload(user):
    cached_profile = cache.get(_profile_cache_key(user.id))
    if cached_profile is not None:
        return cached_profile

    profile = Register.objects.filter(user_id=user.id).first()
    payload = {
        "id": user.id,
        "fullname": profile.fullname if profile else user.get_full_name(),
        "company": profile.company if profile else "",
        "email": user.email,
    }
    cache.set(_profile_cache_key(user.id), payload, PROFILE_CACHE_TIMEOUT)
    return payload


def _cache_profile(profile):
    payload = {
        "id": profile.user_id,
        "fullname": profile.fullname,
        "company": profile.company,
        "email": profile.email,
    }
    cache.set(_profile_cache_key(profile.user_id), payload, PROFILE_CACHE_TIMEOUT)
    return payload


def add_user(request):
    success = False
    error = None

    if request.method == "POST":
        data = {
            "fullname": request.POST.get("fullname"),
            "company": request.POST.get("company") or "Unknown",
            "email": request.POST.get("email"),
            "password": request.POST.get("password"),
            "confirm_password": request.POST.get("password"),
        }
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return render(request, "accounts/add_user.html", {"success": True})
        error = serializer.errors

    return render(request, "accounts/add_user.html", {"success": success, "error": error})


def users_page(request):
    users = Register.objects.select_related("user").all()
    return render(request, "accounts/users_page.html", {"users": users})


class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        cache_key = f"accounts:user-list:{_get_user_list_cache_version()}"
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        users = Register.objects.select_related("user").all()
        serializer = UserProfileSerializer(users, many=True)
        response_data = {
            "success": True,
            "total_users": users.count(),
            "data": serializer.data,
        }
        cache.set(cache_key, response_data, USER_LIST_CACHE_TIMEOUT)
        return Response(response_data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            user = profile.user
            _cache_profile(profile)
            _bump_user_list_cache_version()
            django_login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                "success": True,
                "message": "User registered successfully.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "data": UserProfileSerializer(profile).data,
            }, status=status.HTTP_201_CREATED)

        response_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "email" in serializer.errors:
            response_status = status.HTTP_409_CONFLICT

        return Response({
            "success": False,
            "errors": serializer.errors,
        }, status=response_status)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors,
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data["user"]
        django_login(request, user)
        refresh = RefreshToken.for_user(user)
        profile_data = _profile_payload(user)

        return Response({
            "success": True,
            "message": "Login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "data": profile_data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                return Response({
                    "success": False,
                    "message": "Invalid or expired refresh token.",
                }, status=status.HTTP_400_BAD_REQUEST)

        django_logout(request)

        return Response({
            "success": True,
            "message": "Logout successful.",
        }, status=status.HTTP_205_RESET_CONTENT)

from django.contrib.auth import get_user_model, login as django_login, logout as django_logout
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
        users = Register.objects.select_related("user").all()
        serializer = UserProfileSerializer(users, many=True)
        return Response({
            "success": True,
            "total_users": users.count(),
            "data": serializer.data,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            user = profile.user
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
        profile = getattr(user, "profile", None)

        return Response({
            "success": True,
            "message": "Login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "data": {
                "id": user.id,
                "fullname": profile.fullname if profile else user.get_full_name(),
                "company": profile.company if profile else "",
                "email": user.email,
            },
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

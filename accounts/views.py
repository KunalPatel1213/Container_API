# Add user from web page
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
# JWT imports
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Register
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
# Web page view to show all users

def add_user(request):
    from django.shortcuts import redirect
    success = False
    error = None
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not (fullname and email and password):
            error = 'All fields are required.'
        elif Register.objects.filter(email=email).exists():
            error = 'Email already exists.'
        else:
            user = Register(fullname=fullname, email=email)
            user.set_password(password)
            user.save()
            return render(request, 'accounts/add_user.html', {'success': True})
    return render(request, 'accounts/add_user.html', {'success': success, 'error': error})

def users_page(request):
    users = Register.objects.all()
    return render(request, 'accounts/users_page.html', {'users': users})


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = Register.objects.all().values('id', 'fullname', 'email')
        return Response({
            "success": True,
            "total_users": users.count(),
            "data": list(users)
        })

class RegisterView(APIView):
    permission_classes = [AllowAny]    

    def get(self, request):
        users = Register.objects.all().values('id', 'fullname', 'email')
        return Response({
            "success": True,
            "total_users": users.count(),
            "data": list(users)
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            users = Register.objects.all().values('id', 'fullname', 'email')
            return Response({
                "success": True,
                "message": "User registered successfully!",
                "total_users": users.count(),
                "data": list(users)
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors,
            "data": request.data
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                "success": False,
                "message": "Email and password are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid email or password."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check password using Django's check_password
        
        if check_password(password, user.password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "success": True,
                "message": "Login successful!",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "data": {
                    "id": user.id,
                    "fullname": user.fullname,
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": "Invalid email or password."
            }, status=status.HTTP_401_UNAUTHORIZED)
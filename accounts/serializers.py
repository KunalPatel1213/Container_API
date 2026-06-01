from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Register


User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Register
        fields = ["id", "fullname", "company", "email", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RegisterSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=50)
    company = serializers.CharField(max_length=100, required=False, default="Unknown")
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(username__iexact=email).exists() or Register.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Email already exists.")
        return email

    def validate(self, attrs):
        confirm_password = attrs.get("confirm_password") or attrs["password"]
        if attrs["password"] != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        attrs["confirm_password"] = confirm_password
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        fullname = validated_data["fullname"].strip()
        email = validated_data["email"]
        company = validated_data.get("company", "Unknown").strip() or "Unknown"

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=fullname,
        )
        return Register.objects.create(
            user=user,
            fullname=fullname,
            company=company,
            email=email,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower()
        password = attrs["password"]
        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")

        attrs["user"] = user
        return attrs

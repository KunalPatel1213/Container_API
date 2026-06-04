from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import ServiceProvider


User = get_user_model()


class ServiceProviderSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "name",
            "mobile_number",
            "otp_verified",
            "email",
            "password",
            "payment_setup",
            "profile_photo",
            "payment_setup_image",
            "allow_location_access",
            "enable_gps_tracking",
            "allow_contacts_access",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "otp_verified", "is_active", "created_at", "updated_at"]

    def validate_email(self, value):
        email = value.lower()
        instance = self.instance

        user_query = User.objects.filter(username__iexact=email)
        provider_query = ServiceProvider.objects.filter(email__iexact=email)
        if instance:
            user_query = user_query.exclude(pk=instance.user_id)
            provider_query = provider_query.exclude(pk=instance.pk)

        if user_query.exists() or provider_query.exists():
            raise serializers.ValidationError("Email already exists.")
        return email

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data["email"]
        name = validated_data.pop("name").strip()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )
        return ServiceProvider.objects.create(user=user, name=name, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        email = validated_data.get("email", instance.email)
        name = validated_data.get("name", instance.name).strip()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.name = name
        instance.save()

        user = instance.user
        user.username = email
        user.email = email
        user.first_name = name
        if password:
            user.set_password(password)
        user.save()
        return instance


class ServiceProviderUpdateSerializer(ServiceProviderSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_password(self, value):
        if not value:
            return value
        return super().validate_password(value)

class ServiceProviderLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, allow_blank=False, trim_whitespace=False)

    def validate(self, attrs):
        username = attrs.get("username", "").strip()
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        provider = (
            ServiceProvider.objects.select_related("user")
            .filter(email__iexact=email)
            .first()
        )

        if provider is None:
            provider = (
                ServiceProvider.objects.select_related("user")
                .filter(name__iexact=username)
                .first()
            )

        if provider is None:
            raise serializers.ValidationError({"message": "Invalid email/name or password."})

        if not provider.user.check_password(password):
            raise serializers.ValidationError({"message": "Invalid email/name or password."})

        if username.lower() not in {provider.email.lower(), provider.name.lower()}:
            raise serializers.ValidationError({"message": "Invalid email/name or password."})

        attrs["service_provider"] = provider
        attrs["user"] = provider.user
        return attrs

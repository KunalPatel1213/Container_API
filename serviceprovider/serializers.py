from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import ServiceProvider


User = get_user_model()


class ServiceProviderSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    location_access = serializers.BooleanField(write_only=True, required=False)
    gps_tracking = serializers.BooleanField(write_only=True, required=False)
    contacts_access = serializers.BooleanField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "full_name",
            "name",
            "mobile_number",
            "phone",
            "email",
            "password",
            "confirm_password",
            "account_type",
            "payment_setup",
            "billing_address",
            "location_access",
            "gps_tracking",
            "contacts_access",
            "profile_photo_name",
            "auth_provider",
            "profile_photo",
            "payment_setup_image",
            "allow_location_access",
            "enable_gps_tracking",
            "allow_contacts_access",
            "otp_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "otp_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
            "mobile_number": {"required": False, "allow_blank": True},
            "account_type": {"required": False, "allow_blank": True},
            "payment_setup": {"required": False, "allow_blank": True},
            "billing_address": {"required": False, "allow_blank": True},
            "profile_photo_name": {"required": False, "allow_blank": True},
            "auth_provider": {"required": False, "allow_blank": True},
            "allow_location_access": {"required": False},
            "enable_gps_tracking": {"required": False},
            "allow_contacts_access": {"required": False},
            "profile_photo": {"required": False},
            "payment_setup_image": {"required": False},
        }

    def validate_email(self, value):
        email = value.strip().lower()
        instance = self.instance

        user_query = User.objects.filter(username__iexact=email)
        provider_query = ServiceProvider.objects.filter(email__iexact=email)
        if instance:
            user_query = user_query.exclude(pk=instance.user_id)
            provider_query = provider_query.exclude(pk=instance.pk)

        if user_query.exists() or provider_query.exists():
            raise serializers.ValidationError("Email already exists.")
        return email

    def validate_mobile_number(self, value):
        mobile_number = value.strip()
        instance = self.instance

        provider_query = ServiceProvider.objects.filter(mobile_number=mobile_number)
        if instance:
            provider_query = provider_query.exclude(pk=instance.pk)

        if provider_query.exists():
            raise serializers.ValidationError("Mobile number already exists.")
        return mobile_number

    def validate(self, attrs):
        full_name = attrs.pop("full_name", "")
        phone = attrs.pop("phone", "")
        confirm_password = attrs.pop("confirm_password", None)
        location_access = attrs.pop("location_access", None)
        gps_tracking = attrs.pop("gps_tracking", None)
        contacts_access = attrs.pop("contacts_access", None)

        name = (attrs.get("name") or full_name or "").strip()
        mobile_number = (attrs.get("mobile_number") or phone or "").strip()
        password = attrs.get("password")

        errors = {}
        if not name:
            errors["full_name"] = "full_name or name is required."
        if not mobile_number:
            errors["mobile_number"] = "mobile_number is required."
        if not attrs.get("email"):
            errors["email"] = "email is required."
        if not password and self.instance is None:
            errors["password"] = "password is required."
        if password and password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            raise serializers.ValidationError(errors)

        attrs["name"] = name
        attrs["mobile_number"] = mobile_number
        attrs["account_type"] = attrs.get("account_type") or "serviceProvider"
        attrs["payment_setup"] = attrs.get("payment_setup") or ServiceProvider.PAYMENT_UPI
        attrs["auth_provider"] = attrs.get("auth_provider") or "email"

        if location_access is not None:
            attrs["allow_location_access"] = location_access
        if gps_tracking is not None:
            attrs["enable_gps_tracking"] = gps_tracking
        if contacts_access is not None:
            attrs["allow_contacts_access"] = contacts_access

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data["email"]
        name = validated_data["name"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )
        return ServiceProvider.objects.create(user=user, **validated_data)

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = instance.name
        data["mobile_number"] = instance.mobile_number
        data["email"] = instance.email
        data["account_type"] = instance.account_type
        return data


class ServiceProviderUpdateSerializer(ServiceProviderSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=False)

    def validate(self, attrs):
        if not attrs.get("password") and "confirm_password" in attrs:
            attrs.pop("confirm_password", None)
        return super().validate(attrs)


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

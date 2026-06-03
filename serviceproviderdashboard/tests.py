from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from serviceprovider.models import ServiceProvider

from .models import ServiceProviderAvailability


User = get_user_model()


class ServiceProviderAvailabilityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPass123!",
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            name="Test Provider",
            mobile_number="+919876543210",
            email="provider@example.com",
            payment_setup=ServiceProvider.PAYMENT_UPI,
        )
        self.url = reverse("serviceproviderdashboard-availability-list")

    def test_create_availability_attaches_provider_from_signal(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        availability = ServiceProviderAvailability.objects.get()
        self.assertEqual(availability.user, self.user)
        self.assertEqual(availability.service_provider, self.provider)

    def test_create_availability_accepts_own_service_provider(self):
        self.client.force_authenticate(user=self.user)
        payload = self.payload()
        payload["service_provider"] = self.provider.pk
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        availability = ServiceProviderAvailability.objects.get()
        self.assertEqual(availability.service_provider, self.provider)

    def test_create_availability_without_login_uses_selected_service_provider(self):
        payload = self.payload()
        payload["service_provider"] = self.provider.pk
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        availability = ServiceProviderAvailability.objects.get()
        self.assertEqual(availability.user, self.user)
        self.assertEqual(availability.service_provider, self.provider)

    def test_create_availability_without_login_requires_service_provider(self):
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_see_other_users_availability(self):
        ServiceProviderAvailability.objects.create(user=self.user, **self.payload())

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_user_can_retrieve_own_availability(self):
        availability = ServiceProviderAvailability.objects.create(user=self.user, **self.payload())

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("serviceproviderdashboard-availability-detail", kwargs={"pk": availability.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], availability.pk)

    def test_user_can_update_own_availability(self):
        availability = ServiceProviderAvailability.objects.create(user=self.user, **self.payload())

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse("serviceproviderdashboard-availability-detail", kwargs={"pk": availability.pk}),
            {"current_location": "Updated location, Delhi"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        availability.refresh_from_db()
        self.assertEqual(availability.current_location, "Updated location, Delhi")

    def test_user_cannot_use_another_users_service_provider(self):
        other_provider = ServiceProvider.objects.create(
            user=self.other_user,
            name="Other Provider",
            mobile_number="+919876543211",
            email="other@example.com",
            payment_setup=ServiceProvider.PAYMENT_UPI,
        )
        self.client.force_authenticate(user=self.user)
        payload = self.payload()
        payload["service_provider"] = other_provider.pk

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_delete_own_availability(self):
        availability = ServiceProviderAvailability.objects.create(user=self.user, **self.payload())

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("serviceproviderdashboard-availability-detail", kwargs={"pk": availability.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ServiceProviderAvailability.objects.filter(pk=availability.pk).exists())

    def payload(self):
        return {
            "current_location": "Pickup stand, Delhi NCR",
            "vehicle_type": ServiceProviderAvailability.VEHICLE_TRUCK,
            "weight_capacity_kg": "500.00",
            "empty_space": "8 ft / 12 boxes / 20 sq ft",
            "can_travel_upto": "Delhi NCR, 80 km radius",
            "price_per_km": "25.00",
            "available_until": (timezone.now() + timedelta(days=1)).isoformat(),
            "notes": "Loading help, cold storage, route details.",
        }

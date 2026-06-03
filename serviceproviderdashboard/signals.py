from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import ServiceProviderAvailability


@receiver(pre_save, sender=ServiceProviderAvailability)
def attach_service_provider(sender, instance, **kwargs):
    if instance.service_provider_id or not instance.user_id:
        return

    profile = getattr(instance.user, "service_provider_profile", None)
    if profile:
        instance.service_provider = profile

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Order
from .services.delivery import generate_google_maps_link


@receiver(pre_save, sender=Order)
def set_maps_link(sender, instance: Order, **kwargs):
    """Ensure maps_link is generated server-side when coordinates are present."""
    if instance.maps_link:
        return
    if instance.latitude is not None and instance.longitude is not None:
        instance.maps_link = generate_google_maps_link(float(instance.latitude), float(instance.longitude))

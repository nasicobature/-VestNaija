from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallet.models import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)

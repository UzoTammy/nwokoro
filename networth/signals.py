from django.db.models.signals import post_save
from django.dispatch import receiver
from networth.models import Saving, Investment, Stock

@receiver(post_save, sender=Saving)
def update_savings_holders(sender, instance, created, **kwargs):
    if created:
        instance.update_holders()

@receiver(post_save, sender=Investment)
def update_investment_holders(sender, instance, created, **kwargs):
    if created:
        instance.update_holders()

@receiver(post_save, sender=Stock)
def update_stock_holders(sender, instance, created, **kwargs):
    if created:
        instance.update_holders()
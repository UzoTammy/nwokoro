from django.db.models.signals import post_save
from django.dispatch import receiver
from networth.models import Saving, Investment, Stock

@receiver(post_save, sender=Saving)
def update_savings_holders(sender, instance, created, **kwargs):
    # update preference for both create and update of savings
        instance.update_holders()

@receiver(post_save, sender=Investment)
def update_investment_holders(sender, instance, created, **kwargs):
    # update preference for both create and update of Investment
        instance.update_holders()

@receiver(post_save, sender=Stock)
def update_stock_holders(sender, instance, created, **kwargs):
    # update preference for both create and update of Stock
    instance.update_holders()
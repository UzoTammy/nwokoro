from django.db.models.signals import post_save
from django.dispatch import receiver

from networth.models import (
    BorrowedFund, Business, FixedAsset, Investment, Saving, Stock,
)


@receiver(post_save, sender=Investment)
def update_investment_holders(sender, instance, created, **kwargs):
    instance.update_holders()


@receiver(post_save, sender=Stock)
def update_stock_holders(sender, instance, created, **kwargs):
    instance.update_holders()


@receiver(post_save, sender=Saving)
@receiver(post_save, sender=Investment)
@receiver(post_save, sender=Stock)
@receiver(post_save, sender=Business)
@receiver(post_save, sender=FixedAsset)
@receiver(post_save, sender=BorrowedFund)
def recalculate_networth(sender, instance, **kwargs):
    from networth.tools import get_user_finances
    fr = get_user_finances(instance.owner.username)
    if fr is not None:
        fr.save_report()

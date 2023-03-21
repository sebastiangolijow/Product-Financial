from typing import Optional

from django.db import models
from django.dispatch import receiver

from cashflow.bill.models import Bill
from cashflow.cashcalls.models import CashCall


def _update_cashcall_amounts(instance: "Bill") -> None:
    cash_call: Optional[CashCall] = instance.cashcalls.last()
    if not instance.can_update_cashcall(cash_call):
        return
    instance.update_related_cashcall_amounts(cash_call)


@receiver(models.signals.post_save, sender=Bill)
def update_cashcall_amounts(sender, instance, created=False, **kwargs) -> None:
    _update_cashcall_amounts(instance)

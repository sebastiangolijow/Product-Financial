import random

import factory
from django.db.models import signals
from factory import LazyAttribute

from cashflow.bill.fakers.fakers import BillFaker
from cashflow.cashcalls.models import CashCall


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class CashCallFaker(factory.django.DjangoModelFactory):
    class Meta:
        model = CashCall

    bill = factory.SubFactory(BillFaker)
    committed_amount = factory.Faker(
        "pydecimal", positive=True, min_value=300, max_value=5000, right_digits=2
    )
    fees_amount = factory.Faker(
        "pydecimal", positive=True, min_value=30000, max_value=500000, right_digits=2
    )

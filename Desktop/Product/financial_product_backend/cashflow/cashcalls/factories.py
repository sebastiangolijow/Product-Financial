import factory
from django.db.models import signals

from cashflow.cashcalls.models import CashCall


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class CashCallFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashCall

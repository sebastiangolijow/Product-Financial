import factory
from django.db.models import signals

from cashflow.bill.models import Bill
from core_management.fakers.fakers import InvestmentFaker
from core_management.fakers.fakers import InvestorFaker


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class BillFaker(factory.django.DjangoModelFactory):
    class Meta:
        model = Bill

    last_sent = factory.Faker("date_time_this_year")
    investor = factory.SubFactory(InvestorFaker)
    investment = factory.SubFactory(InvestmentFaker)

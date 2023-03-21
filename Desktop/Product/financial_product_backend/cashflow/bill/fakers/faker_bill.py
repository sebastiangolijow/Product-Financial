import factory
from django.db.models import signals

from cashflow.bill.models import Bill
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from dealflow.investment.faker_investment import InvestmentFaker
from entities.investor.fakers.faker_investor import InvestorFaker


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class BillFaker(factory.django.DjangoModelFactory):
    class Meta:
        model = Bill

    investor = factory.SubFactory(InvestorFaker)
    investment = factory.SubFactory(
        InvestmentFaker,
        investor=factory.LazyAttribute(lambda obj: obj.factory_parent.investor),
    )


class BillWithCashCallFaker(BillFaker):
    cashcall = factory.SubFactory(
        CashCallFaker,
        investor=factory.LazyAttribute(lambda obj: obj.factory_parent.investor),
    )


class BillWithFileFaker(BillFaker):
    file = factory.django.FileField(data=b"Bill File")

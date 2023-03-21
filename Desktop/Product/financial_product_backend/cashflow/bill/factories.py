import factory
from django.db.models import signals
from django.utils import timezone

from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.bill.models import Bill
from cashflow.cashcalls.factories import CashCallFactory
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from dealflow.investment.models.models import Investment


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class BillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bill


@factory.django.mute_signals(signals.pre_save, signals.post_save)
class ManagmentFeesBillFactory(factory.django.DjangoModelFactory):
    type = "management_fees"
    sendinblue_template_id = 364

    class Meta:
        model = Bill


def create_management_fees_bill(
    investment: Investment, year: int = timezone.now().year
) -> Bill:
    fees, percentage = calculate_management_fees(investment)
    fees_percentage = percentage * 100
    bill = ManagmentFeesBillFactory(
        investment=investment,
        investor=investment.investor,
        amount_due=investment.committed_amount,
        fees_amount_due=fees,
        year=year,
    )
    cash_call = CashCallFaker(bill=bill)
    return bill

from decimal import Decimal

import pytest
from django.db.models import Sum

from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.factories import BillFactory
from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.bill.models import Bill
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from core_management.factories.factory_payin import PayInFactory
from core_management.models import PayIn
from core_management.signals.signals_utils import check_bill_investment_type
from dealflow.investment.faker_investment import InvestmentWithDocumentFaker
from utilities.exceptions import ForbiddenUpdateError


@pytest.fixture(scope="class")
def bill_with_related_cashcaslls(django_db_blocker):
    with django_db_blocker.unblock():
        amount_due = Decimal("10000.00")
        fees_amount_due = Decimal("100.00")
        bill = BillFaker(amount_due=amount_due, fees_amount_due=fees_amount_due)
        cash_call = CashCallFaker(
            status=CashCallStatus.PAID.value,
            bill=bill,
            committed_amount=amount_due,
            fees_amount=fees_amount_due,
        )
        return bill, cash_call


@pytest.mark.django_db
class TestBillStateManagement:
    def test_we_bill_object_is_locked_after_payment(self):
        with pytest.raises(ForbiddenUpdateError):
            bill = BillFaker(status=BillStatusChoices.PAID.value)
            bill.amount_due = Decimal("100.00")
            bill.save()

    @pytest.mark.skip(reason="We don't support this functionality currently")
    def test_we_bill_object_is_locked_after_cashcalled(self):
        with pytest.raises(ForbiddenUpdateError):
            bill = BillFaker(status=BillStatusChoices.PENDING.value)
            bill.amount_due = Decimal("100.00")
            bill.save()

    def test_we_bill_object_is_locked_after_paid_incorrectly(self):
        with pytest.raises(ForbiddenUpdateError):
            bill = BillFaker(status=BillStatusChoices.PAID_INCORRECTLY.value)
            bill.amount_due = Decimal("100.00")
            bill.save()

    def test_amount_paid(self, bill_with_related_cashcaslls):
        bill, cash_call = bill_with_related_cashcaslls
        assert bill.status == BillStatusChoices.CREATED.value
        bill.add_cashcall_payment(cash_call)
        bill.save()
        bill.refresh_from_db()
        assert bill.amount_paid == Decimal("10000.00")
        assert bill.fees_amount_paid == Decimal("100.00")
        assert bill.status == BillStatusChoices.PAID.value

    def test_paid_incorrectly_case(self, bill_with_related_cashcaslls):
        bill, cash_call = bill_with_related_cashcaslls
        second_cash_call = CashCallFaker(
            status=CashCallStatus.PAID.value,
            bill=bill,
            committed_amount=Decimal("1000.00"),
            fees_amount=("10.00"),
        )
        bill.add_cashcall_payment(second_cash_call)
        bill.save()
        bill.refresh_from_db()
        assert bill.amount_paid == Decimal("11000.00")
        assert bill.fees_amount_paid == Decimal("110.00")
        assert bill.status == BillStatusChoices.PAID_INCORRECTLY.value

    def test_bill_is_updated_after_investment_update(self):
        investment = InvestmentWithDocumentFaker(
            committed_amount=Decimal("1000.00"),
            status="sa_signed",
            fees_percentage=Decimal("12.00"),
        )
        check_bill_investment_type(investment)
        bill = investment.bills.last()
        assert bill.amount_due == Decimal("1000.00")
        assert bill.fees_amount_due == Decimal("120.00")
        investment.committed_amount = Decimal("1500.00")
        investment.save()
        bill.refresh_from_db()
        check_bill_investment_type(investment)
        bill = investment.bills.last()
        assert bill.amount_due == Decimal("1500.00")
        assert bill.fees_amount_due == Decimal("180.00")
        assert investment.bills.aggregate(amount_billed=Sum("amount_due"))[
            "amount_billed"
        ] == Decimal("1500.00")

    def test_bill_get_payin(self) -> None:
        bill: Bill = BillFactory()
        assert None == bill.get_payin()
        payin: PayIn = PayInFactory(bill=bill)
        assert payin == bill.get_payin()

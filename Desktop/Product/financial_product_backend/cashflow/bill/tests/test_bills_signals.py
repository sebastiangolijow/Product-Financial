from decimal import Decimal
from unittest.mock import patch

import pytest

from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.bill.signals import _update_cashcall_amounts
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker


@pytest.mark.django_db
class TestBillSignals:
    def test_cash_call_updating_functionality(self):
        amount_due = Decimal("100.00")
        fees_amount_due = Decimal("10.00")
        bill = BillFaker(
            amount_due=amount_due,
            fees_amount_due=fees_amount_due,
            investment__fees_percentage=Decimal("10.00"),
        )

        cash_call = CashCallFaker(
            bill=bill,
            status=CashCallStatus.CREATED.value,
        )

        cash_call.refresh_from_db()
        assert cash_call.committed_amount == amount_due
        assert cash_call.fees_amount == fees_amount_due
        new_amount_due = Decimal("200.00")
        bill.amount_due = new_amount_due
        bill.save()
        _update_cashcall_amounts(bill)
        cash_call.refresh_from_db()
        assert cash_call.committed_amount == new_amount_due
        assert cash_call.fees_amount == Decimal("20.00")

    @patch("cashflow.bill.signals._update_cashcall_amounts", autospec=True)
    def test_signal_is_being_called(self, mocked_signal):
        amount_due = Decimal("100.00")
        fees_amount_due = Decimal("10.00")
        bill = BillFaker(
            amount_due=amount_due,
            fees_amount_due=fees_amount_due,
            investment__fees_percentage=Decimal("10.00"),
        )

        cash_call = CashCallFaker(
            bill=bill,
            status=CashCallStatus.CREATED.value,
        )
        new_amount_due = Decimal("200.00")
        bill.amount_due = new_amount_due
        bill.save()
        mocked_signal.assert_called_once()

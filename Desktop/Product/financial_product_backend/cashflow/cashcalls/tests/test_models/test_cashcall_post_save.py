from decimal import Decimal
from unittest import mock
from unittest.mock import patch

import pytest

from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from cashflow.cashcalls.models import CashCall


@pytest.mark.django_db
class TestCashCallPostSave:
    def test_setting_cashcall_amounts_after_creation(self):
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
        cash_call.save()
        cash_call.refresh_from_db()

        assert cash_call.committed_amount == amount_due
        assert cash_call.fees_amount == fees_amount_due

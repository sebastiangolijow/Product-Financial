import pytest

from cashflow.cashcalls.fakers.fakers import CashCallFaker
from cashflow.cashcalls.models import CashCall


@pytest.mark.django_db
class TestCashCall:
    def test_history_behavior(self):
        CashCall.objects.all().delete()
        cash_call = CashCallFaker(
            bill__amount_due=10000,
            bill__fees_amount_due=12,
        )
        cash_call.history.all().delete()
        assert cash_call.history.count() == 0
        cash_call.bill.amount_due = 2000
        cash_call.bill.save()
        assert cash_call.history.count() == 1
        cash_call.bill.refresh_from_db()
        cash_call.refresh_from_db()
        assert cash_call.history.count() == 1
        cash_call.bill.amount_due = 3000
        cash_call.bill.save()
        cash_call.bill.refresh_from_db()
        cash_call.refresh_from_db()
        assert cash_call.history.count() == 2
        history = cash_call.history.all()
        # newest changes first
        assert history[0].committed_amount == 3000
        assert history[1].committed_amount == 2000

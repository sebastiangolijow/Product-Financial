from decimal import Decimal

import pytest

from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker


@pytest.fixture(scope="class")
def cash_call_post_data():
    post_data = {
        "investor_name": "My Unique Investor",
        "committed_amount": "25000.00",
        "fees_type": "upfront_fees",
        "fees_percentage": "12.00",
        "cc_emails": ["test@email.com"],
        "fees_amount": "3000.00",
    }
    return post_data


@pytest.mark.django_db
class TestCashCallViewset:
    def get_url(self):
        return "/api/v3/bills/cash_calls/"

    def test_create_cash_call(self, client, ortstaff_user, cash_call_post_data):
        bill = BillFaker(status=BillStatusChoices.CREATED.value)
        payload = cash_call_post_data
        payload["bill"] = bill.id
        client.force_authenticate(user=ortstaff_user)
        response = client.post(self.get_url(), payload)
        assert response.status_code == 201

    def test_update_cash_call(self, client, ortstaff_user, cash_call_post_data):
        bill = BillFaker(
            status=BillStatusChoices.CREATED.value,
        )
        CashCallFaker(bill=bill, status=CashCallStatus.CREATED.value)
        payload = cash_call_post_data
        payload["bill"] = bill.id
        client.force_authenticate(user=ortstaff_user)
        response = client.post(self.get_url(), payload)
        assert response.status_code == 200
        bill.refresh_from_db()
        assert bill.cc_emails.split(",") == payload["cc_emails"]
        assert bill.investor_name == payload["investor_name"]
        assert response.data == {
            "status": "updated",
            "cc_emails": "test@email.com",
            "investor_name": "My Unique Investor",
            "bill_id": bill.id,
        }

    def test_try_to_create_already_sent_cash_call(
        self, client, ortstaff_user, cash_call_post_data
    ):
        bill = BillFaker(status=BillStatusChoices.PENDING.value)
        cash_call = CashCallFaker(
            bill=bill,
            status=CashCallStatus.PENDING.value,
            committed_amount=Decimal("1000.00"),
        )
        payload = cash_call_post_data
        payload["bill"] = bill.id
        client.force_authenticate(user=ortstaff_user)
        response = client.post(self.get_url(), payload)
        assert response.status_code == 200
        assert cash_call.committed_amount != payload["committed_amount"]
        assert response.data == {"status": "already_sent"}

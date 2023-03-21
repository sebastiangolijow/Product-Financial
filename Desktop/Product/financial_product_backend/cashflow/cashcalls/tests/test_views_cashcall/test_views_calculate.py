from decimal import Decimal

import pytest
from django.urls import reverse

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fakers.faker_bill import BillFaker


@pytest.mark.django_db
class TestCashCallsCalculate:
    def url(self, id: int) -> str:
        return reverse("cashcalls:cash_call_calculate_amounts", kwargs={"bill_id": id})

    def test_bill_upfront(self, client, ortstaff_user):
        bill_upfront = BillFaker(type=BillTypeChoices.upfront_fees.name)
        params = {"amount": 30000.00, "fees_percentage": 12.00}
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url(bill_upfront.id), params)
        percentage: Decimal = response.data.get("percentage")
        fees_amount: Decimal = response.data.get("fees_amount")
        assert response.status_code == 200
        assert percentage.quantize(Decimal(".01")) == Decimal(12).quantize(
            Decimal(".01")
        )
        assert fees_amount.quantize(Decimal(".01")) == Decimal(3600).quantize(
            Decimal(".01")
        )

    def test_management_bill(self, client, ortstaff_user):
        bill_upfront = BillFaker(type=BillTypeChoices.management_fees.name)
        params = {"amount": 30000.00, "fees_percentage": 5.00}
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url(bill_upfront.id), params)
        percentage: Decimal = response.data.get("percentage")
        fees_amount: Decimal = response.data.get("fees_amount")
        assert response.status_code == 200
        assert percentage.quantize(Decimal(".01")) == Decimal(2).quantize(
            Decimal(".01")
        )
        assert fees_amount.quantize(Decimal(".01")) == Decimal(600).quantize(
            Decimal(".01")
        )

    def test_rhapsody_bill(self, client, ortstaff_user):
        bill_upfront = BillFaker(type=BillTypeChoices.rhapsody_fees.name)
        params = {"amount": 30000.00, "fees_percentage": 5.00}
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url(bill_upfront.id), params)
        percentage: Decimal = response.data.get("percentage")
        fees_amount: Decimal = response.data.get("fees_amount")
        assert response.status_code == 200
        assert percentage.quantize(Decimal(".01")) == Decimal(5).quantize(
            Decimal(".01")
        )
        assert fees_amount.quantize(Decimal(".01")) == Decimal(1500).quantize(
            Decimal(".01")
        )

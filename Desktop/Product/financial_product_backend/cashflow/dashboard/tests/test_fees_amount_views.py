from datetime import datetime

import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fakers.fakers import BillFaker
from cashflow.bill.models import Bill
from core_auth.models import CustomUser


@pytest.mark.django_db
class TestDashboardFeesAmount:
    def setup_method(self):
        Bill.objects.all().delete()

    def url(self) -> str:
        return reverse("api:dashboard-fees-amount")

    def test_url(self) -> None:
        assert self.url() == "/api/v2/dashboard/fees-amount"

    def test_endpoint_as_unauthenticated_user(self, client: APIClient) -> None:
        response: Response = client.get(self.url())
        assert response.status_code == 401

    def test_endpoint_as_unauthorized_user(
        self, client: APIClient, user: CustomUser
    ) -> None:
        client.force_authenticate(user=user)
        response: Response = client.get(self.url())
        assert response.status_code == 403

    def test_endpoint_works_as_admin(
        self, client: APIClient, ortstaff_user: CustomUser
    ) -> None:
        client.force_authenticate(user=ortstaff_user)
        response: Response = client.get(self.url())
        assert response.status_code == 200

    def test_endpoint_returns_right_data(
        self, client: APIClient, ortstaff_user: CustomUser
    ) -> None:
        no_sent_bill: Bill = BillFaker(
            last_sent=None,
            fees_amount_due=10000,
        )
        sent_bill_upfront: Bill = BillFaker(
            type=BillTypeChoices.upfront_fees.name,
            last_sent=datetime(2020, 6, 15, 12, 24, 20, 707000),
            fees_amount_due=10000,
        )
        sent_bill_upfront_2: Bill = BillFaker(
            type=BillTypeChoices.upfront_fees.name,
            last_sent=datetime(2020, 6, 15, 12, 24, 20, 707000),
            fees_amount_due=20000,
        )
        sent_bill_upfront_3: Bill = BillFaker(
            type=BillTypeChoices.upfront_fees.name,
            last_sent=datetime(2020, 7, 15, 12, 24, 20, 707000),
            fees_amount_due=40000,
        )
        sent_bill_management: Bill = BillFaker(
            type=BillTypeChoices.management_fees.name,
            last_sent=datetime(2021, 6, 15, 12, 24, 20, 707000),
            fees_amount_due=50000,
        )
        client.force_authenticate(user=ortstaff_user)
        response: Response = client.get(self.url())
        assert response.status_code == 200
        assert len(response.data) == 3
        assert response.data[0]["year"] == 2020
        assert response.data[0]["month"] == 6
        assert (
            response.data[0]["amount"]
            == sent_bill_upfront.fees_amount_due + sent_bill_upfront_2.fees_amount_due
        )
        assert response.data[1]["year"] == 2020
        assert response.data[1]["month"] == 7
        assert response.data[1]["amount"] == sent_bill_upfront_3.fees_amount_due
        assert response.data[2]["year"] == 2021
        assert response.data[2]["month"] == 6
        assert response.data[2]["amount"] == sent_bill_management.fees_amount_due

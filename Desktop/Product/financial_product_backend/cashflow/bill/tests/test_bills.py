from decimal import Decimal

import pytest
from django.urls import reverse
from pytest_django.asserts import assertNumQueries

from cashflow.bill.fakers.fakers import BillFaker


@pytest.mark.django_db
class TestExportBills:  # TODO to be deprecated

    URL: str = reverse("bill:finance-table")

    def test_endpoint_list(self, client, ortstaff_user):

        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.URL)

        assert response.status_code == 200

    def test_endpoint_list_permission_wrong_user(self, client, user):

        client.force_authenticate(user=user)
        response = client.get(self.URL)

        assert response.status_code == 403

    def test_endpoint_list_permission_unauth(self, client):

        response = client.get(self.URL)

        assert response.status_code == 401

    def test_user_without_special_permission(self, client, user):

        client.force_authenticate(user=user)
        response = client.get(self.URL)

        assert response.status_code == 403

    def test_data_structure(self, client, ortstaff_user):

        BillFaker()

        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.URL)
        result = response.data[0]
        assert len(result.keys()) == 13
        assert "id" in result.keys()
        assert "investor_name" in result.keys()
        assert "fundraising_name" in result.keys()
        assert "amount" in result.keys()
        assert "fees_percentage" in result.keys()
        assert "fees" in result.keys()
        assert "fees_type" in result.keys()
        assert "payment_status" in result.keys()
        assert "payment_sent_date" in result.keys()
        assert "payment_paid_date" in result.keys()
        assert "bill_number" in result.keys()
        assert "deprecated_bill_number" in result.keys()
        assert "bill_year" in result.keys()

    def test_number_queries(self, client, user):

        client.force_authenticate(user=user)
        with assertNumQueries(1):
            client.get(self.URL)


@pytest.mark.django_db
class TestExportBills:

    URL = reverse("bill:finance-table")

    def test_endpoint_list(self, client, ortstaff_user):

        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.URL)

        assert response.status_code == 200

    def test_endpoint_list_permission_wrong_user(self, client, user):

        client.force_authenticate(user=user)
        response = client.get(self.URL)

        assert response.status_code == 403

    def test_endpoint_list_permission_unauth(self, client):

        response = client.get(self.URL)

        assert response.status_code == 401

    def test_user_without_special_permission(self, client, user):

        client.force_authenticate(user=user)
        response = client.get(self.URL)

        assert response.status_code == 403

    def test_data_structure(self, client, ortstaff_user):

        bill = BillFaker()
        currency = bill.investment.fundraising.currency.name
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.URL)
        result = response.data["results"][0]
        assert len(result.keys()) == 15
        assert "id" in result.keys()
        assert "investor_name" in result.keys()
        assert "investor_id" in result.keys()
        assert int(response.data["results"][0]["investor_id"]) == bill.get_investor().id
        assert "fundraising_name" in result.keys()
        assert "amount" in result.keys()
        assert "fees_percentage" in result.keys()
        assert "fees" in result.keys()
        assert "fees_type" in result.keys()
        assert "payment_status" in result.keys()
        assert "payment_sent_date" in result.keys()
        assert "payment_paid_date" in result.keys()
        assert "bill_number" in result.keys()
        assert "deprecated_bill_number" in result.keys()
        assert "bill_year" in result.keys()
        assert "currency" in result.keys()
        assert result["payment_status"] == bill.status
        response = client.get(self.URL + "?format=csv")
        assert currency == result["currency"]
        assert response.status_code == 200

    def test_number_queries(self, client, user):

        client.force_authenticate(user=user)
        with assertNumQueries(1):
            client.get(self.URL)

    @pytest.mark.skip(
        "To be modified because we don't want paigination when we export to csv "
    )
    def test_pagination(self, client, ortstaff_user):
        BillFaker.create_batch(10)
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.URL)
        assert "count" in response.data.keys()
        assert "next" in response.data.keys()
        assert "previous" in response.data.keys()
        assert "results" in response.data.keys()
        assert response.data.get("count") == 10
        assert response.data.get("previous") is None
        assert response.data.get("next") == 2
        assert isinstance(response.data.get("results"), list)
        assert len(response.data.get("results")) == 2

from datetime import datetime

import pytest
from django.urls import reverse
from requests import get

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.factories import BillFactory
from cashflow.bill.models import Bill
from cashflow.dashboard.serializers import BillFeesAmountSerializer
from cashflow.dashboard.views import GetFeesAmountsView


@pytest.mark.django_db()
class TestDashboardFeesAmount:
    def assert_keys_in_list(self, list_of_keys: list):
        assert "year" in list_of_keys
        assert "month" in list_of_keys
        assert "amount" in list_of_keys

    def test_response_data_structure(self):
        """
        the test is aimed at comparing the data structure of
        stub server and a generic response from backend for the specific endpoint
        """
        results = get("https://stub.oneragtime.com/fees_amount").json()
        assert type(results) == list
        assert len(results) > 0

        keys_from_stub = results[0].keys()
        self.assert_keys_in_list(keys_from_stub)
        keys_from_serializer_views = GetFeesAmountsView.serializer_class.Meta.fields
        self.assert_keys_in_list(keys_from_serializer_views)

    def test_values_view(self):
        """
        Ensure that the queryset is filtering correctly and the
        """
        amount_management_fees = 2300
        amount_upfront_fees = 5300
        bill_managemement_fees: Bill = BillFactory(
            last_sent=datetime(year=2023, month=1, day=1),
            type=BillTypeChoices.management_fees.name,
            fees_amount_due=amount_management_fees,
        )
        bill_upfront_fees: Bill = BillFactory(
            last_sent=datetime(year=2023, month=1, day=1),
            type=BillTypeChoices.upfront_fees.name,
            fees_amount_due=amount_upfront_fees,
        )
        queryset = GetFeesAmountsView().get_queryset()
        serializers_data = BillFeesAmountSerializer(instance=queryset, many=True).data
        bills_jan_2023 = [
            d for d in serializers_data if (d["year"] == 2023 and d["month"] == 1)
        ][0]
        assert (
            bills_jan_2023.get("amount") == amount_management_fees + amount_upfront_fees
        )

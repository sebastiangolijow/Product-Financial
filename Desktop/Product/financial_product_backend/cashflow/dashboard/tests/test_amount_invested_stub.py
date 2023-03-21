from datetime import datetime
from datetime import timedelta

import pytest
from django.urls import reverse
from requests import get

from core_management.fakers.fakers import FundraisingFaker
from core_management.fakers.fakers import InvestorFaker
from core_management.fakers.fakers import StartupFaker
from core_management.models import Fundraising
from dealflow.investment.faker_investment import InvestmentFakerWithoutDocuments
from entities.investor.models.models import Investor
from entities.startup.models.models import Startup


@pytest.mark.django_db()
class TestDashboardAmountInvested:
    def url(self) -> str:
        return reverse("api:dashboard-amount-invested")

    def test_url(self) -> None:
        assert self.url() == "/api/v2/dashboard/amount-invested"

    def assert_keys_in_list(self, list_of_keys: list):
        assert "fund" in list_of_keys
        assert "amount_invested" in list_of_keys
        assert "amount_to_reach" in list_of_keys
        assert "amount_invested_year" in list_of_keys
        assert "amount_invested_month" in list_of_keys

    def test_response_data_structure(self, client, ortstaff_user):
        """
        the test is aimed at comparing the data structure of
        stub server and a generic response from backend for the specific endpoint
        """
        Investor.objects.all().delete()
        client.force_authenticate(ortstaff_user)
        now: datetime = datetime.now()
        fund: Startup = StartupFaker(is_fund=True)
        startup: Startup = StartupFaker(is_fund=False)
        testing_investor: Investor = InvestorFaker(name="Testing")
        normal_investor: Investor = InvestorFaker(name="Normal")
        fund_fundraising: Fundraising = FundraisingFaker(
            startup=fund, oneragtime_round=3
        )
        startup_fundraising: Fundraising = FundraisingFaker(startup=startup)
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising,
            investor=normal_investor,
            creation_datetime=now,
            committed_amount=10,
        )
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising,
            investor=normal_investor,
            committed_amount=9,
            creation_datetime=now.replace(day=2, hour=0, minute=0, second=0),
        )
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising,
            investor=normal_investor,
            committed_amount=8,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0),
        )
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising,
            investor=normal_investor,
            committed_amount=6,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0)
            - timedelta(days=1),
        )
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, status="rejected", investor=normal_investor
        )  ## Rejected investment
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, investor=testing_investor
        )  ## Testing investor
        InvestmentFakerWithoutDocuments(
            fundraising=startup_fundraising, investor=normal_investor
        )
        results = get("https://stub.oneragtime.com/amount_invested").json()
        assert type(results) == list
        assert len(results) > 0

        keys_from_stub = results[0].keys()
        keys_from_serializer_views = client.get(self.url(), format="json")
        self.assert_keys_in_list(keys_from_stub)

        self.assert_keys_in_list(keys_from_serializer_views.data[0].keys())

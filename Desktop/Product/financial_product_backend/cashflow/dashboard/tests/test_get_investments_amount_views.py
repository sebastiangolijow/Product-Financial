from datetime import datetime
from datetime import timedelta

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.test import APIClient

from core_auth.models import CustomUser
from core_management.fakers.fakers import StartupFaker
from core_management.models import Fundraising
from dealflow.fundraising.fakers.faker_fundraising import FundraisingFaker
from dealflow.investment.faker_investment import InvestmentFakerWithoutDocuments
from entities.investor.fakers.faker_investor import InvestorFaker
from entities.investor.models.models import Investor
from entities.startup.models.models import Startup
from entities.startup.tests.fakers.faker_startup import StartupFaker


@pytest.mark.django_db
class TestDashboardView:
    def url(self) -> str:
        return reverse("api:dashboard-amount-invested")

    def test_url(self) -> None:
        assert self.url() == "/api/v2/dashboard/amount-invested"

    def test_endpoint_fails_as_unauthenticated(self, client: APIClient) -> None:
        response = client.get(self.url())
        assert response.status_code == 401

    def test_endpoint_fails_as_unauthorized(
        self, client: APIClient, user: CustomUser
    ) -> None:
        client.force_authenticate(user)
        response = client.get(self.url())
        assert response.status_code == 403

    @freeze_time("2022-08-15")
    def test_endpoint_data(self, client: APIClient, ortstaff_user: CustomUser) -> None:
        client.force_authenticate(ortstaff_user)
        now: datetime = datetime.now()

        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        startup: Startup = StartupFaker(is_fund=False)
        startup_fundraising: Fundraising = FundraisingFaker(startup=startup)

        normal_investor: Investor = InvestorFaker(name="Normal")
        testing_investor: Investor = InvestorFaker(name="Testing")
        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")

        # investment OF fund investor entity 1
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            creation_datetime=now,
            committed_amount=10,
        )
        # investment OF fund investor entity 2
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=9,
            creation_datetime=now.replace(day=2, hour=0, minute=0, second=0),
        )
        # investment OF fund investor entity 3
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=8,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0),
        )
        # investment OF fund investor entity 4
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=6,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0)
            - timedelta(days=1),
        )

        # investment IN fund
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising,
            investor=normal_investor,
            committed_amount=50,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0)
            - timedelta(days=1),
        )

        ## Rejected investment
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, status="rejected", investor=normal_investor
        )
        ## Testing investor
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, investor=testing_investor
        )
        ## Startup fundraising
        InvestmentFakerWithoutDocuments(
            fundraising=startup_fundraising, investor=normal_investor
        )

        response = client.get(self.url())
        assert response.status_code == 200
        assert response.json() == [
            {
                "fund": fund.name,
                "amount_invested": 33.00,  ## 10 + 9 + 8 + 6
                "amount_to_reach": 50.00,  ## 50
                "amount_invested_year": 27.00,  ## 10 + 9 + 8
                "amount_invested_month": 19.00,  ## 10 + 9
            }
        ]

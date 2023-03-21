import pytest
from django.urls import reverse

from core_management.fakers.fakers import FundraisingFaker
from core_management.fakers.fakers import InvestmentFaker
from core_management.fakers.fakers import InvestorFaker
from core_management.fakers.fakers import StartupFaker
from dealflow.investment.faker_investment import InvestmentFaker
from dealflow.valuations.faker_valuation import ValuationFaker
from dealflow.valuations.models.models import Valuation
from entities.investor.fakers.faker_investor import InvestorExitValueFaker
from entities.investor.fakers.faker_investor import InvestorFaker
from entities.investor.models.models import Investor
from entities.startup.tests.fakers.faker_startup import StartupFundFaker


@pytest.mark.django_db
class TestValuationFundsDashboard:
    def url(self):
        return reverse("api-v2:dashboard_fund_valuations")

    def test_url(self):
        assert self.url() == "/api/v2/dashboard/fund-valuations"

    def test_endpoint_list(self, client, ortstaff_user):

        client.force_authenticate(user=ortstaff_user)
        startup = StartupFaker(is_fund=True)
        FundraisingFaker(startup=startup)
        ValuationFaker(startup=startup)
        response = client.get(self.url())
        keys = response.json()[0].keys()
        assert response.status_code == 200
        assert "investment_offer" in keys
        assert "invested" in keys
        assert "current_net_fair_value" in keys
        assert "net_multiple" in keys
        assert "manual_exited_value" in keys

    def test_endpoint_list_permission_unauthenticated(self, client):
        valuation: Valuation = ValuationFaker()
        response = client.get(self.url())
        assert response.status_code == 401


@pytest.mark.django_db
class TestInvestorCorporateDashboard:
    def url(self):
        return reverse("api-v2:dashboard_corporate_valuations")

    def test_url(self):
        assert self.url() == "/api/v2/dashboard/corporate-valuations"

    def test_endpoint_list(self, client, ortstaff_user):
        client.force_authenticate(user=ortstaff_user)
        investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFaker(investor=investor)
        InvestmentFaker(investor=investor)
        response = client.get(self.url())
        keys = response.json()[0].keys()
        assert response.status_code == 200
        assert "investment_offer" in keys
        assert "invested" in keys
        assert "current_net_fair_value" in keys
        assert "net_multiple" in keys
        assert "manual_exited_value" in keys

    def test_endpoint_list_permission_unauthenticated(self, client):
        InvestorFaker(name="OneRagtime Aria")
        response = client.get(self.url())
        assert response.status_code == 401


@pytest.mark.django_db
class TestInvestmentClubDealDashboard:
    def url(self):
        return reverse("api-v2:dashboard-clubdeal-valuations")

    def test_url(self):
        assert self.url() == "/api/v2/dashboard/clubdeal-valuations"

    def test_endpoint_list(self, client, ortstaff_user):
        client.force_authenticate(user=ortstaff_user)
        startup = StartupFundFaker(is_fund=False)
        fund = FundraisingFaker(startup=startup)
        investor: Investor = InvestorFaker()
        InvestorExitValueFaker(investor=investor)
        InvestorExitValueFaker(investor=investor)
        InvestmentFaker(fundraising=fund, investor=investor)
        response = client.get(self.url())
        keys = response.json().keys()
        assert response.status_code == 200
        assert "investment_offer" in keys
        assert "invested" in keys
        assert "current_net_fair_value" in keys
        assert "net_multiple" in keys
        assert "manual_exited_value" in keys

    def test_endpoint_list_permission_unauthenticated(self, client):
        startup = StartupFundFaker(is_fund=True)
        fund = FundraisingFaker(startup=startup)
        InvestmentFaker(fundraising=fund)
        InvestmentFaker(fundraising=fund)
        response = client.get(self.url())
        assert response.status_code == 401

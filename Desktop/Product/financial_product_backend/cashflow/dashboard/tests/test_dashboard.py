from datetime import datetime

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.test import APIClient

from core_auth.models import CustomUser
from core_management.fakers.fakers import Fundraising
from core_management.fakers.fakers import StartupFaker
from dealflow.fundraising.fakers.faker_fundraising import FundraisingFaker
from dealflow.investment.faker_investment import InvestmentFakerWithoutDocuments
from dealflow.investment.models.models import Investment
from entities.investor.fakers.faker_investor import InvestorFaker
from entities.investor.models.models import Investor
from entities.startup.models.models import Startup


@pytest.mark.django_db
class TestClubDealDashboardView:
    def setup_method(self):
        Investment.objects.all().delete()

    def url_clubdeal(self):
        return reverse("api:dashboard_amounts_clubdeal")

    def test_url_clubdeal(self):
        assert "/api/v2/dashboard/amount-raised-clubdeal" == self.url_clubdeal()

    def test_endpoint_fails_as_unauthenticated_user(self, client: APIClient):
        response = client.get(self.url_clubdeal())
        assert response.status_code == 401

    def test_endpoint_fails_as_unauthorized_user(
        self, client: APIClient, user: CustomUser
    ):
        client.force_authenticate(user=user)
        response = client.get(self.url_clubdeal())
        assert response.status_code == 403

    def test_endpoint_structure(
        self, client: APIClient, ortstaff_user: CustomUser
    ) -> None:
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url_clubdeal())
        assert response.status_code == 200
        assert len(response.json().keys()) == 7
        assert "total" in response.json().keys()
        assert "current_year" in response.json().keys()
        assert "previous_year" in response.json().keys()
        assert "current_month" in response.json().keys()
        assert "previous_month" in response.json().keys()
        assert "current_week" in response.json().keys()
        assert "previous_week" in response.json().keys()

    @freeze_time("2023-02-25")
    def test_dashboard_clubdeal_return_right_data_for_weeks(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This week
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last week
        )
        response = client.get(self.url_clubdeal())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_week"] == 1500
        assert response.json()["previous_week"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_clubdeal_return_right_data_for_months(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This month
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/30 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last month
        )
        response = client.get(self.url_clubdeal())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_month"] == 1500
        assert response.json()["previous_month"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_clubdeal_return_right_data_for_years(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This year
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "22/12/31 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last year
        )
        response = client.get(self.url_clubdeal())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_year"] == 1500
        assert response.json()["previous_year"] == 100


class TestCorporateDashboardView:
    def setup_method(self):
        Investment.objects.all().delete()

    def url_corporate(self):
        return reverse("api:dashboard_amounts_corporate")

    def test_url_corporate(self):
        assert "/api/v2/dashboard/amount-raised-corporate" == self.url_corporate()

    def test_endpoint_fails_as_unauthenticated_user(self, client: APIClient):
        response = client.get(self.url_corporate())
        assert response.status_code == 401

    def test_endpoint_fails_as_unauthorized_user(
        self, client: APIClient, user: CustomUser
    ):
        client.force_authenticate(user=user)
        response = client.get(self.url_corporate())
        assert response.status_code == 403

    def test_endpoint_structure(
        self, client: APIClient, ortstaff_user: CustomUser
    ) -> None:
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url_corporate())
        assert response.status_code == 200
        assert len(response.json().keys()) == 7
        assert "total" in response.json().keys()
        assert "current_year" in response.json().keys()
        assert "previous_year" in response.json().keys()
        assert "current_month" in response.json().keys()
        assert "previous_month" in response.json().keys()
        assert "current_week" in response.json().keys()
        assert "previous_week" in response.json().keys()

    @freeze_time("2023-02-25")
    def test_dashboard_corporate_return_right_data_for_weeks(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This week
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last week
        )
        response = client.get(self.url_corporate())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_week"] == 1500
        assert response.json()["previous_week"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_corporate_return_right_data_for_months(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This month
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/30 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last month
        )
        response = client.get(self.url_corporate())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_month"] == 1500
        assert response.json()["previous_month"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_corporate_return_right_data_for_years(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=False)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This year
        )
        investor: Investor = InvestorFaker(name="OneRagtime Aria")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "22/12/31 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last year
        )
        response = client.get(self.url_corporate())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_year"] == 1500
        assert response.json()["previous_year"] == 100


@pytest.mark.django_db
class TestFundDashboardView:
    def setup_method(self):
        Investment.objects.all().delete()

    def url_fund(self):
        return reverse("api:dashboard_amounts_fund")

    def test_url_fund(self):
        assert "/api/v2/dashboard/amount-raised-fund" == self.url_fund()

    def test_endpoint_fails_as_unauthenticated_user(self, client: APIClient):
        response = client.get(self.url_fund())
        assert response.status_code == 401

    def test_endpoint_fails_as_unauthorized_user(
        self, client: APIClient, user: CustomUser
    ):
        client.force_authenticate(user=user)
        response = client.get(self.url_fund())
        assert response.status_code == 403

    def test_endpoint_structure(
        self, client: APIClient, ortstaff_user: CustomUser
    ) -> None:
        client.force_authenticate(user=ortstaff_user)
        response = client.get(self.url_fund())
        assert response.status_code == 200
        assert len(response.json().keys()) == 7
        assert "total" in response.json().keys()
        assert "current_year" in response.json().keys()
        assert "previous_year" in response.json().keys()
        assert "current_month" in response.json().keys()
        assert "previous_month" in response.json().keys()
        assert "current_week" in response.json().keys()
        assert "previous_week" in response.json().keys()

    @freeze_time("2023-02-25")
    def test_dashboard_fund_return_right_data_for_weeks(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=True)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/23 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This week
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last week
        )
        response = client.get(self.url_fund())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_week"] == 1500
        assert response.json()["previous_week"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_fund_return_right_data_for_months(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=True)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This month
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/30 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last month
        )
        response = client.get(self.url_fund())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_month"] == 1500
        assert response.json()["previous_month"] == 100

    @freeze_time("2023-02-25")
    def test_dashboard_fund_return_right_data_for_years(
        self, client: APIClient, ortstaff_user: CustomUser
    ):
        client.force_authenticate(user=ortstaff_user)
        startup: Startup = StartupFaker(is_fund=True)
        fundraising: Fundraising = FundraisingFaker(startup=startup)
        rhapsody_investor: Investor = InvestorFaker(name="Rhapsody")
        InvestmentFakerWithoutDocuments(
            investor=rhapsody_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/03 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        testing_investor: Investor = InvestorFaker(name="Testing")
        InvestmentFakerWithoutDocuments(
            investor=testing_investor,  ## Should not be counted
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1000,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/02/15 00:00:00", "%y/%m/%d %H:%M:%S"
            ),
            status="Rejected",  ## Should not be counted
        )
        investor: Investor = InvestorFaker(name="Investor")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=1500,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "23/01/01 00:00:00", "%y/%m/%d %H:%M:%S"
            ),  ## This year
        )
        investor: Investor = InvestorFaker(name="Investor 2")
        InvestmentFakerWithoutDocuments(
            investor=investor,
            committed_amount=100,
            fundraising=fundraising,
            creation_datetime=datetime.strptime(
                "22/12/31 23:59:59", "%y/%m/%d %H:%M:%S"
            ),  ## Last year
        )
        response = client.get(self.url_fund())
        assert response.status_code == 200
        assert response.json()["total"] == 1600
        assert response.json()["current_year"] == 1500
        assert response.json()["previous_year"] == 100

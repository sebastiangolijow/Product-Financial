from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
from pytest import mark

from cashflow.dashboard.utils import GetInvestmentsAmountsForFund
from core_management.models import Fundraising
from core_utils.faker_currency import DollarCurrencyFaker
from dealflow.fundraising.fakers.faker_fundraising import FundraisingFaker
from dealflow.investment.faker_investment import InvestmentFakerWithoutDocuments
from dealflow.investment.models.models import Investment
from entities.investor.fakers.faker_investor import InvestorFaker
from entities.investor.models.models import Investor
from entities.startup.models.models import Startup
from entities.startup.tests.fakers.faker_startup import StartupFaker


@mark.django_db
class TestGetInvestmentsAmountsForFundUtil:
    def test_excluded_investments_works(self) -> None:
        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        normal_investor: Investor = InvestorFaker(name="Normal")
        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")

        normal_fund_investment: Investment = InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity
        )
        rejected_fund_investment: Investment = InvestmentFakerWithoutDocuments(
            status="rejected", investor=fund_investor_entity
        )
        startup_investment: Investment = InvestmentFakerWithoutDocuments(
            investor=normal_investor
        )
        assert GetInvestmentsAmountsForFund(fund).investments.count() == 1
        assert GetInvestmentsAmountsForFund(
            fund
        ).investments.first() == Investment.objects.get(id=normal_fund_investment.id)

    def test_get_total_invested_filtered_amount(self) -> None:
        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        normal_investor: Investor = InvestorFaker(name="Normal")
        fund_investor_investor: Investor = InvestorFaker(name="Fund Entity")

        InvestmentFakerWithoutDocuments(
            investor=fund_investor_investor, committed_amount=60
        )
        InvestmentFakerWithoutDocuments(
            status="rejected", investor=fund_investor_investor
        )
        InvestmentFakerWithoutDocuments(
            investor=normal_investor,
            committed_amount=1,
        )
        assert GetInvestmentsAmountsForFund(fund).get_total_invested_amount() == 60

    def test_get_total_invested_amount(self) -> None:
        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity, committed_amount=5
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity, committed_amount=10
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity, committed_amount=15
        )
        assert GetInvestmentsAmountsForFund(fund).get_total_invested_amount() == 30

    @freeze_time("2022-08-15")
    def test_get_total_invested_amount_including_usd_investments(self) -> None:
        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)
        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")
        usd_fund_fundraising: Fundraising = FundraisingFaker(
            startup=fund, currency=DollarCurrencyFaker()
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=5,
            fundraising=fund_fundraising,
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=10,
            fundraising=fund_fundraising,
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=15,
            fundraising=usd_fund_fundraising,
        )
        assert GetInvestmentsAmountsForFund(
            fund
        ).get_total_invested_amount() == 5 + 10 + (
            15 / 1.18
        )  # Conversion rate for 2022

    def test_get_ORT_round(self) -> None:
        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising = FundraisingFaker(startup=fund)

        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, committed_amount=15
        )
        InvestmentFakerWithoutDocuments(
            fundraising=fund_fundraising, committed_amount=7
        )

        assert GetInvestmentsAmountsForFund(fund).get_committed_amount_in_fund() == 22

    @freeze_time("2022-08-15")
    def test_amount_invested_year(self) -> None:
        now: datetime = datetime.now()
        year_ago: datetime = now.replace(year=now.year - 1)

        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")

        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=1,
            creation_datetime=year_ago,
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=5,
            creation_datetime=now.replace(month=1, day=1, hour=0, minute=0, second=0),
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=3,
            creation_datetime=now,
        )
        assert GetInvestmentsAmountsForFund(fund).amount_invested_current_year == 8

    @freeze_time("2022-08-15")
    def test_amount_invested_month(self) -> None:
        now: datetime = datetime.now()
        first = now.replace(day=1)
        last_month = first - timedelta(days=2)

        fund: Startup = StartupFaker(is_fund=True, name="Fund Entity")
        fund_fundraising: Fundraising = FundraisingFaker(startup=fund)

        fund_investor_entity: Investor = InvestorFaker(name="Fund Entity")

        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=4,
            creation_datetime=last_month,
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=3,
            creation_datetime=now,
        )
        InvestmentFakerWithoutDocuments(
            investor=fund_investor_entity,
            committed_amount=7,
            creation_datetime=now.replace(day=2, hour=0, minute=0, second=0),
        )
        assert GetInvestmentsAmountsForFund(fund).amount_invested_current_month == 10

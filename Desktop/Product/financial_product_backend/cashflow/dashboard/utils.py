import datetime as dates
from abc import ABC
from datetime import datetime
from decimal import Decimal
from functools import reduce

from django.db.models import Case
from django.db.models import F
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Sum
from django.db.models import When
from django.utils.functional import cached_property

from cashflow.currency.conversion_rate import ConversionRatesFromUSD
from dealflow.investment.models.model_investhistvalue import InvestmentHistoricalValue
from dealflow.investment.models.models import Investment
from entities.investor.models.models import InvestorExitValue
from entities.startup.models.models import Startup
from utilities.decorators import round_result_by_2
from utilities.decorators import round_result_by_3


class AbstractGetInvestmentsAmount(ABC):
    excluded_investors_names: list = [
        "Testing",
        "Paragon",
        "Rhapsody",
    ]

    EXCLUDE_NAMES_QUERY: Q = reduce(
        lambda previous_query, current_query: previous_query | current_query,
        (Q(investor__name__contains=name) for name in excluded_investors_names),
    )

    EXCLUDE_QUERY: Q = (
        EXCLUDE_NAMES_QUERY
        | Q(status="rejected")
        | Q(status="intentional")
        | Q(fundraising__name__contains="Medium")
    )

    @cached_property
    def now(self) -> datetime:
        return datetime.now()

    def aggregate_query(self, query: QuerySet) -> Decimal:
        return query.annotate(
            invested_amount=Case(
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2016"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2016"),
                ),
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2017"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2017"),
                ),
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2018", "2021", "2022"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2018"),
                ),
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2019"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2019"),
                ),
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2020"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2020"),
                ),
                When(
                    fundraising__currency__name__exact="USD",
                    creation_datetime__year__in=["2023"],
                    then=F("committed_amount")
                    / ConversionRatesFromUSD.get_value("_2023"),
                ),
                default=F("committed_amount"),
            )
        ).aggregate(committed_amount__sum=Sum("invested_amount"))

    def get_total_invested_amount(self) -> Decimal:
        aggregated_query: QuerySet = self.aggregate_query(self.investments)
        return aggregated_query.get("committed_amount__sum")

    def get_invested_amount_in_given_period(
        self, begin: datetime, end: datetime
    ) -> Decimal:
        query: QuerySet = self.investments.filter(
            Q(creation_datetime__gte=begin) & Q(creation_datetime__lte=end)
        )
        aggregated_query: QuerySet = self.aggregate_query(query)
        return aggregated_query.get("committed_amount__sum")


class AbstractGetInvestedAmountForCurrentPeriods(AbstractGetInvestmentsAmount):
    @property
    def amount_invested_in_total(self) -> Decimal:
        return self.get_total_invested_amount()

    @property
    def amount_invested_current_year(self) -> Decimal:
        current_year: int = self.now.replace(month=1, day=1, hour=0, minute=0, second=0)
        return self.get_invested_amount_in_given_period(current_year, self.now)

    @property
    def amount_invested_current_month(self) -> Decimal:
        current_month: int = self.now.replace(day=1, hour=0, minute=0, second=0)
        return self.get_invested_amount_in_given_period(current_month, self.now)

    @property
    def amount_invested_current_week(self) -> Decimal:
        current_day: int = self.now.weekday()
        week_start: datetime.datetime = self.now.replace(
            hour=0, minute=0, second=0
        ) - dates.timedelta(days=current_day)
        return self.get_invested_amount_in_given_period(week_start, self.now)

    @property
    def amount_invested_today(self) -> Decimal:
        day_start: datetime.datetime = self.now.replace(hour=0, minute=0, second=0)
        return self.get_invested_amount_in_given_period(day_start, self.now)


class AbstractInvestedAmountForPastPeriods(AbstractGetInvestmentsAmount):
    @property
    def amount_invested_previous_year(self) -> Decimal:
        previous_year_start: datetime = self.now.replace(
            day=1, month=1, year=self.now.year - 1, hour=0, minute=0, second=0
        )
        previous_year_end: datetime = self.now.replace(
            day=31, month=12, year=self.now.year - 1, hour=23, minute=59, second=59
        )
        return self.get_invested_amount_in_given_period(
            previous_year_start, previous_year_end
        )

    @property
    def amount_invested_previous_month(self) -> Decimal:
        start_current_month: datetime = self.now.replace(day=1)
        previous_month_end: datetime = start_current_month - dates.timedelta(days=1)
        previous_month_end: datetime = previous_month_end.replace(
            hour=23, minute=59, second=59
        )
        previous_month_start: datetime = previous_month_end.replace(
            day=1, hour=0, minute=0, second=0
        )
        return self.get_invested_amount_in_given_period(
            previous_month_start, previous_month_end
        )

    @property
    def amount_invested_previous_week(self) -> Decimal:
        today: int = self.now.weekday()
        previous_week_end: datetime.datetime = self.now - dates.timedelta(days=today)
        previous_week_end: datetime = previous_week_end.replace(
            hour=23, minute=59, second=59
        )
        previous_week_start: datetime = previous_week_end - dates.timedelta(days=7)
        previous_week_start: datetime = previous_week_start.replace(
            hour=0, minute=0, second=0
        )
        return self.get_invested_amount_in_given_period(
            previous_week_start, previous_week_end
        )


class GetInvestedAmountsForAllPeriods(
    AbstractGetInvestedAmountForCurrentPeriods, AbstractInvestedAmountForPastPeriods
):
    pass


class GetInvestedAmountsForInvestments(GetInvestedAmountsForAllPeriods):
    def __init__(self, investments: QuerySet) -> None:
        self.passed_investments = investments

    @cached_property
    def investments(self) -> QuerySet:
        ## Do it this way in order to cache the investments inside this class.
        return self.passed_investments.exclude(self.EXCLUDE_QUERY)

    @property
    def data(self) -> dict:
        return {
            "total": self.amount_invested_in_total,
            "current_year": self.amount_invested_current_year,
            "previous_year": self.amount_invested_previous_year,
            "current_month": self.amount_invested_current_month,
            "previous_month": self.amount_invested_previous_month,
            "current_week": self.amount_invested_current_week,
            "previous_week": self.amount_invested_previous_week,
        }


class GetInvestmentsAmountsForFund(AbstractGetInvestedAmountForCurrentPeriods):
    percentage_fees: dict = {
        "Paragon": 0.275,
        "Rhapsody II": 0.22,
    }

    manual_increase_amount: dict = {
        "Rhapsody I": 457447,
    }

    def __init__(self, fund: Startup) -> None:
        self.fund = fund

    @cached_property
    def investments(self) -> QuerySet:
        return Investment.objects.filter(investor__name=self.fund.name).exclude(
            Q(status="rejected")
        )

    @property
    def amount_to_reach(self) -> Decimal:
        return self.get_committed_amount_in_fund()

    @property
    def data(self) -> dict:
        return {
            "fund": self.fund.name,
            "amount_invested": self.amount_invested_in_total,
            "amount_to_reach": self.amount_to_reach,
            "amount_invested_year": self.amount_invested_current_year,
            "amount_invested_month": self.amount_invested_current_month,
        }

    def get_committed_amount_in_fund(self):
        query: QuerySet = Investment.objects.filter(
            fundraising__startup=self.fund
        ).exclude(self.EXCLUDE_QUERY)
        amount: int = (
            query.aggregate(Sum("committed_amount")).get("committed_amount__sum") or 0
        )

        if self.fund.name in self.percentage_fees:
            return amount * Decimal(1 - self.percentage_fees[self.fund.name])

        if self.fund.name in self.manual_increase_amount:
            return amount + self.manual_increase_amount[self.fund.name]

        return amount


class GetInvestmentClubDealValuationsAmount(AbstractGetInvestmentsAmount):
    def __init__(self, investors: QuerySet) -> None:
        self.passed_investors = investors

    @cached_property
    def investors(self) -> QuerySet:
        return self.passed_investors

    @cached_property
    def investments(self) -> QuerySet:
        return (
            Investment.objects.get_clubdeal_investments()
            .filter(investor__in=self.investors)
            .distinct()
        )

    @property
    def data(self) -> dict:
        return {
            "investment_offer": self.investment_offer,
            "invested": self.invested,
            "current_net_fair_value": self.current_net_fair_value,
            "net_multiple": self.net_multiple,
            "manual_exited_value": self.manual_exited_value,
        }

    @property
    def investment_offer(self) -> Decimal:
        return "Club Deal"

    @property
    def invested(self) -> Decimal:
        return self.aggregate_query(self.investments).get("committed_amount__sum") or 0

    @property
    def current_net_fair_value(self) -> Decimal:
        return (
            InvestmentHistoricalValue.objects.filter(investment__in=self.investments)
            .annotate(
                gross_value=Case(
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2016"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2016"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2017"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2017"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=[
                            "2018",
                            "2021",
                            "2022",
                        ],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2018"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2019"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2019"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2020"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2020"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2023"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2023"),
                    ),
                    When(
                        investment__fundraising__currency__name__exact="USD",
                        investment__creation_datetime__year__in=["2016"],
                        then=F("unrealized_gross_value")
                        / ConversionRatesFromUSD.get_value("_2016"),
                    ),
                )
            )
            .aggregate(gross_value__sum=Sum("gross_value"))
            .get("gross_value__sum")
        )

    @property
    @round_result_by_2
    def net_multiple(self) -> Decimal:
        if self.current_net_fair_value and self.invested:
            return self.current_net_fair_value / self.invested
        return 0

    @property
    @round_result_by_3
    def manual_exited_value(self) -> Decimal:
        return (
            InvestorExitValue.objects.filter(investor__in=self.investors)
            .aggregate(Sum("exit_value"))
            .get("exit_value__sum")
            / Decimal(1.18)
            or 0
        )

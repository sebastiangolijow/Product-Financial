from decimal import Decimal
from typing import Tuple

from django.utils import timezone

from cashflow.currency.conversion_rate import convert_dollar_to_euro
from dealflow.investment.models.models import Investment


def calculate_management_fees(
    investment: Investment,
    year: int = timezone.now().year,
    invested_amount: Decimal = None,
    investment_year: int = None,
) -> Tuple[Decimal, Decimal]:
    if not invested_amount:
        invested_amount = investment.committed_amount
    if not investment_year:
        investment_year = investment.get_invest_date().year

    fees_amount = Decimal(0)
    acceleration_percentage = Decimal(0.02)

    investment_management_years = year - investment_year
    # a startup can be set as a fund (example :rhapsody)
    startup_is_fund = investment.fundraising.startup.is_fund
    if startup_is_fund:
        if investment_management_years > 2:
            acceleration_percentage = Decimal(0.0225)
            fees_amount = Decimal(invested_amount) * acceleration_percentage
    else:
        if investment_management_years <= 4:
            acceleration_percentage = Decimal(0.02)
            fees_amount = Decimal(invested_amount) * acceleration_percentage
        else:
            acceleration_percentage = Decimal(0.01)
            fees_amount = Decimal(invested_amount) * acceleration_percentage
        ### Merit Ventures Holding Hoomano-Fundraising, Special cases that are exceptions
        if investment.id == 593 or investment.id == 525:
            acceleration_percentage = Decimal(0.01 if investment.id == 593 else 0.02)
            fees_amount = Decimal(invested_amount) * acceleration_percentage
        if investment.fundraising.currency.name == "USD":
            fees_amount = convert_dollar_to_euro(fees_amount)
    return fees_amount, acceleration_percentage

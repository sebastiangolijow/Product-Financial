from decimal import Decimal
from typing import Tuple

from django.utils import timezone

from dealflow.investment.models.models import Investment


def calculate_rhapsody_fees(
    investment: Investment,
    year: int = timezone.now().year,
    invested_amount: Decimal = None,
) -> Tuple[Decimal, Decimal]:
    if not invested_amount:
        invested_amount = Decimal(investment.committed_amount)
    fees_amount = Decimal(0)
    acceleration_percentage = Decimal(0)
    investment_management_years = year - investment.get_invest_date().year
    if investment_management_years == 0:
        acceleration_percentage = Decimal(investment.fees_percentage) / 100
        fees_amount = Decimal(invested_amount) * acceleration_percentage
    if investment_management_years >= 1:
        acceleration_percentage = Decimal(0.0225)
        fees_amount = Decimal(invested_amount) * acceleration_percentage
    return fees_amount, acceleration_percentage

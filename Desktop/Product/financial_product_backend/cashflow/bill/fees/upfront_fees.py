from decimal import Decimal
from typing import Tuple

from dealflow.investment.models.models import Investment


def calculate_upfront_fees(
    investment: Investment, invested_amount: Decimal = None, *args, **kwargs
) -> Tuple[Decimal, Decimal]:
    # convert_dollart_to_euro was removed because we want to keep USD and EUR separately for upfront fees investments
    if not invested_amount:
        invested_amount = Decimal(investment.committed_amount)
    fees_percentage = Decimal(investment.fees_percentage) / 100
    fees_amount = Decimal(0)
    fees_amount = Decimal(invested_amount) * fees_percentage
    return fees_amount, fees_percentage

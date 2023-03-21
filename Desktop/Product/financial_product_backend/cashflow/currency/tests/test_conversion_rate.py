from decimal import Context
from decimal import Decimal

import pytest

from cashflow.currency.conversion_rate import convert_dollar_to_euro
from cashflow.currency.conversion_rate import convert_euro_to_dollar


@pytest.mark.parametrize(
    "euro,dollar",
    [
        (350, 360.50),
        (500, 515.00),
        (550, 566.50),
    ],
)
def test_convert_euro_to_dollar(euro, dollar):

    dollar_converted = convert_euro_to_dollar(euro)

    assert dollar_converted.quantize(Decimal(".01")) == Decimal(dollar).quantize(
        Decimal(".01")
    )


@pytest.mark.parametrize(
    "dollar,euro",
    [
        (350, 339.81),
        (500, 485.44),
        (540.49, 524.75),
    ],
)
def test_convert_dollar_to_euro(euro, dollar):

    euro_converted = convert_dollar_to_euro(dollar)
    assert euro_converted.quantize(Decimal(".01")) == Decimal(euro).quantize(
        Decimal(".01")
    )

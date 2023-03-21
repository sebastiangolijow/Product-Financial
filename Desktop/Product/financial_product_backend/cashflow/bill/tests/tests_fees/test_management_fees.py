from datetime import datetime
from decimal import Decimal

import pytest
from django.utils.timezone import now

from cashflow.bill.factories import create_management_fees_bill
from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from dealflow.investment.faker_investment import InvestmentFaker


PARAMETERIZE = [
    (
        {
            "fundraising__spv_country_code": "UK",
            "status": "validated",
            "creation_datetime": datetime.strptime(
                "2019-09-13 21:16:31", "%Y-%m-%d %H:%M:%S"
            ),
            "committed_amount": 29952,
        },
        2021,
        Decimal(599.04),
        Decimal(0.02),
    ),
    (
        {
            "fundraising__spv_country_code": "UK",
            "status": "validated",
            "creation_datetime": datetime.strptime(
                "2019-09-13 21:16:31", "%Y-%m-%d %H:%M:%S"
            ),
            "committed_amount": 29952,
        },
        2022,
        Decimal(599.04),
        Decimal(0.02),
    ),
    (
        {
            "fundraising__spv_country_code": "UK",
            "status": "validated",
            "creation_datetime": datetime.strptime(
                "2019-09-13 21:16:31", "%Y-%m-%d %H:%M:%S"
            ),
            "committed_amount": 29952,
        },
        2023,
        Decimal(599.04),
        Decimal(0.02),
    ),
]


@pytest.mark.django_db
class TestManagementFees:
    @pytest.mark.parametrize(
        "investment_kwargs,year,fees_amount,acceleration_percenatage", PARAMETERIZE
    )
    def test_calculate_management_fees(
        self, investment_kwargs, year, fees_amount, acceleration_percenatage
    ):
        investment = InvestmentFaker(**investment_kwargs)
        (
            calculated_fees_amount,
            calculated_acceleration_percenatage,
        ) = calculate_management_fees(investment, year)

        assert calculated_acceleration_percenatage == acceleration_percenatage
        assert calculated_fees_amount.quantize(Decimal(".01")) == fees_amount.quantize(
            Decimal(".01")
        )

    @pytest.mark.parametrize(
        "investment_kwargs,year,fees_amount,acceleration_percenatage", PARAMETERIZE
    )
    def test_create_management_fees_bill(
        self, investment_kwargs, year, fees_amount, acceleration_percenatage
    ):
        investment = InvestmentFaker(**investment_kwargs)
        bill = create_management_fees_bill(investment, year)
        cash_call = CashCallFaker(
            bill=bill,
            fees_amount=bill.fees_amount_due,
            committed_amount=bill.amount_due,
        )

        assert cash_call.fees_amount.quantize(Decimal("0.01")) == fees_amount.quantize(
            Decimal("0.01")
        )

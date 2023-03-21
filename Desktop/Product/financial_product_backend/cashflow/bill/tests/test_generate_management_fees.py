from datetime import datetime

import pytest
from django.utils.timezone import now

from cashflow.bill.factories import create_management_fees_bill
from dealflow.investment.faker_investment import InvestmentFaker


@pytest.mark.django_db
class TestManagementFees:
    def test_generate_from_investment(self):
        investment = InvestmentFaker(
            fundraising__spv_country_code="UK",
            status="validated",
            creation_datetime=datetime.strptime(
                "2019-09-13 21:16:31", "%Y-%m-%d %H:%M:%S"
            ),
            committed_amount=29952,
        )

        bill = create_management_fees_bill(investment, 2021)

        assert bill.type == "management_fees"
        assert bill.year == 2021
        assert bill.investment_id == investment.id
        assert bill.file is not None
        assert bill.investor_id == investment.investor.id
        assert bill.invoice_number_deprecated is not None
        assert bill.invoice_number is None

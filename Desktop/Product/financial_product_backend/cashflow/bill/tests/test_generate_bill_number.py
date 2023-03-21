from datetime import datetime

import pytest
from django.urls import reverse
from django.utils.timezone import now

from cashflow.bill.choices import BillNumberChoices
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.bill.models import Bill
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from core_auth.factories import UserFactory
from core_management.factories.factory_kyc import KYCFactory
from core_management.fakers.faker_relationships import UserInvestorRelationshipFaker
from dealflow.fundraising.fakers.faker_fundraising import FundraisingFaker
from dealflow.investment.faker_investment import InvestmentFaker
from entities.investor.fakers.faker_investor import InvestorFaker


@pytest.mark.django_db
class TestExportBills:
    def url(self, id_: int) -> str:
        return reverse("cashcalls:cash_call-send", kwargs={"pk": id_})

    @pytest.mark.skip(reason="cloudconvert")
    # @patch("ort_files.documentbuilder.utils.utils_file.convert_to_pdf", autospec=True)
    def test_function(self, mocked):
        # First we create our cashcalls and relations
        investor = InvestorFaker(status="pending", kyc=KYCFactory(type="legal"))

        fundraising = FundraisingFaker()
        investment = InvestmentFaker(
            subscription_agreement_signed_date=datetime.now(),
            fees_percentage="10",
            committed_amount="20000",
            investor=investor,
            fundraising=fundraising,
        )
        bill = BillFaker(
            type=BillTypeChoices.management_fees.name,
            investor=investor,
            investment=investment,
            file="hello",
        )
        cash_call = CashCallFaker(bill=bill)
        UserInvestorRelationshipFaker(
            investor=investor,
            account=UserFactory(email="cashcall_investor@test.com"),
            is_owner=True,
        )

        # We make sure that the bill number is not yet created
        assert Bill.objects.count() == 1
        bill = Bill.objects.first()
        assert bill.invoice_number_deprecated != None
        assert bill.invoice_number == None

        # We then call the function
        payin = {"wire-reference": "test_wire_reference"}
        bill.generate(payin)
        mocked.assert_called_once()
        bill = Bill.objects.first()

        # Finally we make sure that a new bill number is created with the expected values
        assert bill.invoice_number_deprecated != None
        assert bill.invoice_number != None
        bill_number = [str(now().year), BillNumberChoices.management_fees.value]
        assert bill.invoice_number.split("_")[:-1] == bill_number

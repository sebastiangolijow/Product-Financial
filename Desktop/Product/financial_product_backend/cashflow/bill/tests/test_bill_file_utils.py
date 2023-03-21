import decimal
import os
from datetime import datetime

import pytest
from docxtpl import DocxTemplate

from cashflow.bill.fakers.fakers import BillFaker
from cashflow.bill.utils import generate_bill_template
from cashflow.bill.utils import get_conversion_rate
from cashflow.bill.utils import get_document_context
from cashflow.bill.utils import get_document_template
from cashflow.bill.utils import get_investment_date
from cashflow.bill.utils import get_investment_fees
from cashflow.bill.utils import get_invoice_data
from cashflow.bill.utils import get_invoice_taxes
from cashflow.bill.utils import get_output_path
from cashflow.bill.utils import get_owner_country
from cashflow.cashcalls.fakers.faker_kyc import KYCFaker
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from cashflow.currency.conversion_rate import get_conversion_rate_from_eur
from core_management.factories.factory_currency import CurrencyEURFactory
from core_management.factories.factory_currency import CurrencyUSDFactory
from core_management.fakers.faker_account import UserFaker
from core_management.fakers.fakers import FundraisingFaker
from core_management.fakers.fakers import InvestmentFaker
from core_management.fakers.fakers import InvestorFaker
from core_management.models import UserInvestorRelationship


@pytest.mark.django_db
class TestBillFileUtils:
    def test_get_context_on_euro_investment(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="natural")
        kyc.representative_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )

        currency = CurrencyEURFactory()
        fundraising = FundraisingFaker(currency=currency)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            investment=investment,
            type="management_fees",
        )
        cashcall = CashCallFaker(bill=bill)
        payin = {"wire-reference": "test_wire_ref"}
        actual_context = get_document_context(bill, payin)
        assert "50 000.00 €" == actual_context["committed_amount"]

    def test_get_context_on_dollar_investment(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="natural")
        kyc.representative_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )

        currency = CurrencyUSDFactory()
        fundraising = FundraisingFaker(currency=currency)
        investment = InvestmentFaker(investor=investor, fundraising=fundraising)
        bill = BillFaker(
            investor=investor,
            investment=investment,
            type="management_fees",
        )
        cashcall = CashCallFaker(bill=bill)
        payin = {"wire-reference": "test_wire_ref"}

        actual_context = get_document_context(bill, payin)
        assert "50 000.00 $" == actual_context["committed_amount"]

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_generate_bill_template_on_natural_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="natural")
        kyc.representative_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        if os.path.isfile("/tmp/generated_invoice.docx"):
            os.remove("/tmp/generated_invoice.docx")
        payin = {"wire_reference": "test_wire_reference"}
        generate_bill_template(bill, payin)
        assert True == os.path.isfile("/tmp/generated_invoice.docx")
        os.remove("/tmp/generated_invoice.docx")
        assert False == os.path.isfile("/tmp/generated_invoice.docx")

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_generate_bill_template_on_legal_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="legal")
        kyc.business_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        if os.path.isfile("/tmp/generated_invoice.docx"):
            os.remove("/tmp/generated_invoice.docx")
        payin = {"wire_reference": "test_wire_reference"}
        generate_bill_template(bill, payin)
        assert True == os.path.isfile("/tmp/generated_invoice.docx")
        os.remove("/tmp/generated_invoice.docx")
        assert False == os.path.isfile("/tmp/generated_invoice.docx")

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_template_on_natural_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "Mexico"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        actual_template = get_document_template(bill)
        assert type(actual_template) == DocxTemplate

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_template_on_legal_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "Mexico"
        investor.kyc.type = "legal"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        actual_template = get_document_template(bill)
        assert type(actual_template) == DocxTemplate

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_context_on_natural_french_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="natural")
        kyc.representative_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_content = {
            "acceleration_percentage": round(decimal.Decimal(0.02), 2),
            "address": investor.get_address(),
            "company": investment.investor.name,
            "conversion_rate": 1,
            "current_year": str(datetime.today().year),
            "committed_amount": investment.get_formatted_committed_amount(),
            "date": {
                "month": investment.get_invest_date().month,
                "year": investment.get_invest_date().year,
            },
            "email": bill.get_owner_email(),
            "fees": {
                "stotal": decimal.Decimal(1000.00),
                "tax": decimal.Decimal(0.00),
                "total": decimal.Decimal(1000.00),
            },
            "fundraising": investment.fundraising.name,
            "investor": investor,
            "invoice": {"num": "2022_OF_0000001", "tax": 0},
            "payin": bill.get_payin(),
        }
        actual_context = get_document_context(bill)
        assert expected_content == actual_context

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_context_on_legal_french_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="legal")
        kyc.business_address.country.name = "France"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_content = {
            "acceleration_percentage": round(decimal.Decimal(0.02), 2),
            "address": investor.get_address(),
            "company": investment.investor.name,
            "conversion_rate": 1,
            "current_year": str(datetime.today().year),
            "committed_amount": investment.get_formatted_committed_amount(),
            "date": {
                "month": investment.get_invest_date().month,
                "year": investment.get_invest_date().year,
            },
            "email": bill.get_owner_email(),
            "fees": {
                "stotal": decimal.Decimal(1000.00),
                "tax": decimal.Decimal(0.00),
                "total": decimal.Decimal(1000.00),
            },
            "fundraising": investment.fundraising.name,
            "investor": investor,
            "invoice": {"num": "2022_OF_0000001", "tax": 0},
            "payin": bill.get_payin(),
        }
        actual_context = get_document_context(bill)
        assert expected_content == actual_context

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_context_on_natural_non_french_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="natural")
        kyc.representative_address.country.name = "Mexico"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_content = {
            "acceleration_percentage": round(decimal.Decimal(0.02), 2),
            "address": investor.get_address(),
            "company": investment.investor.name,
            "conversion_rate": 1,
            "current_year": str(datetime.today().year),
            "committed_amount": investment.get_formatted_committed_amount(),
            "date": {
                "month": investment.get_invest_date().month,
                "year": investment.get_invest_date().year,
            },
            "email": bill.get_owner_email(),
            "fees": {
                "stotal": decimal.Decimal(1000.00),
                "tax": decimal.Decimal(0.00),
                "total": decimal.Decimal(1000.00),
            },
            "fundraising": investment.fundraising.name,
            "investor": investor,
            "invoice": {"num": "2022_OF_0000001", "tax": 0},
            "payin": bill.get_payin(),
        }
        actual_context = get_document_context(bill)
        assert expected_content == actual_context

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_document_context_on_legal_non_french_user(self):
        custom_user = UserFaker()
        kyc = KYCFaker(type="legal")
        kyc.business_address.country.name = "Mexico"
        kyc.save()
        investor = InvestorFaker(name="Alejandro", kyc=kyc)
        relation = UserInvestorRelationship.objects.create(
            investor=investor, account=custom_user, is_owner=True
        )
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_content = {
            "acceleration_percentage": round(decimal.Decimal(0.02), 2),
            "address": investor.get_address(),
            "company": investment.investor.name,
            "conversion_rate": 1,
            "current_year": str(datetime.today().year),
            "committed_amount": investment.get_formatted_committed_amount(),
            "date": {
                "month": investment.get_invest_date().month,
                "year": investment.get_invest_date().year,
            },
            "email": bill.get_owner_email(),
            "fees": {
                "stotal": decimal.Decimal(1000.00),
                "tax": decimal.Decimal(0.00),
                "total": decimal.Decimal(1000.00),
            },
            "fundraising": investment.fundraising.name,
            "investor": investor,
            "invoice": {"num": "2022_OF_0000001", "tax": 0},
            "payin": bill.get_payin(),
        }
        actual_context = get_document_context(bill)
        assert expected_content == actual_context

    def test_get_conversion_rate_for_USD_currency(self):
        investment = InvestmentFaker()
        investment.fundraising.currency.name = "USD"
        investment.save()
        actual_conversion_rate = get_conversion_rate(investment)
        expected_conversion_rate = round(
            decimal.Decimal(1 / get_conversion_rate_from_eur("USD")), 2
        )
        assert actual_conversion_rate == expected_conversion_rate

    def test_get_conversion_rate_for_EUR_currency(self):
        investment = InvestmentFaker()
        investment.fundraising.currency.name = "EUR"
        investment.save()
        actual_conversion_rate = get_conversion_rate(investment)
        expected_conversion_rate = 1
        assert actual_conversion_rate == expected_conversion_rate

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_invoice_data_for_natural_french_investor(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.representative_address.country.name = "France"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_invoice_data = {"tax": 0, "num": f"{datetime.today().year}_OF_0000001"}
        actual_invoice_data = get_invoice_data(bill)
        assert expected_invoice_data == actual_invoice_data

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_invoice_data_for_legal_french_investor(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "France"
        investor.kyc.type = "legal"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_invoice_data = {"tax": 0, "num": f"{datetime.today().year}_OF_0000001"}
        actual_invoice_data = get_invoice_data(bill)
        assert expected_invoice_data == actual_invoice_data

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_invoice_data_for_natural_non_french_investor(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.representative_address.country.name = "Mexico"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_invoice_data = {"tax": 0, "num": f"{datetime.today().year}_OF_0000001"}
        actual_invoice_data = get_invoice_data(bill)
        assert expected_invoice_data == actual_invoice_data

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_invoice_data_for_legal_non_french_investor(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "Mexico"
        investor.kyc.type = "legal"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_invoice_data = {"tax": 0, "num": f"{datetime.today().year}_OF_0000001"}
        actual_invoice_data = get_invoice_data(bill)
        assert expected_invoice_data == actual_invoice_data

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_no_invoice_taxes_on_legal_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "Mexico"
        investor.kyc.type = "legal"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_innvoice_taxes = 0
        actual_invoice_taxes = get_invoice_taxes(bill)
        assert actual_invoice_taxes == expected_innvoice_taxes

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_french_invoice_taxes_on_legal_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.business_address.country.name = "France"
        investor.kyc.type = "legal"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_innvoice_taxes = 0
        actual_invoice_taxes = get_invoice_taxes(bill)
        assert actual_invoice_taxes == expected_innvoice_taxes

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_no_invoice_taxes_on_natural_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.representative_address.country.name = "Mexico"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_innvoice_taxes = 0
        actual_invoice_taxes = get_invoice_taxes(bill)
        assert actual_invoice_taxes == expected_innvoice_taxes

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_french_invoice_taxes_on_natural_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.representative_address.country.name = "France"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_innvoice_taxes = 0
        actual_invoice_taxes = get_invoice_taxes(bill)
        assert actual_invoice_taxes == expected_innvoice_taxes

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_owner_country_on_none_type(self):
        investor = InvestorFaker(name="Alejandro")
        investment = InvestmentFaker(investor=investor)
        expected_country = None
        actual_country = get_owner_country(investment)
        assert actual_country == expected_country

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_owner_country_on_natural_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.type = "legal"
        investor.kyc.business_address.country.name = "Mexico"
        investor.kyc.save()
        investment = InvestmentFaker(investor=investor)
        expected_country = "Mexico"
        actual_country = get_owner_country(investment)
        assert actual_country == expected_country

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_owner_country_on_natural_user(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.type = "natural"
        investor.kyc.representative_address.country.name = "Mexico"
        investor.kyc.save()
        investment = InvestmentFaker(investor=investor)
        expected_country = "Mexico"
        actual_country = get_owner_country(investment)
        assert actual_country == expected_country

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_investment_fees_without_french_taxes(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        fees = decimal.Decimal(1000.003)
        expected_investment_fees = {
            "stotal": decimal.Decimal(1000.00),
            "tax": decimal.Decimal(0.00),
            "total": decimal.Decimal(1000.00),
        }
        actual_fees = get_investment_fees(bill, fees)
        assert actual_fees == expected_investment_fees

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_investment_fees_with_french_taxes(self):
        investor = InvestorFaker(name="Alejandro")
        investor.kyc.representative_address.country.name = "France"
        investor.kyc.type = "natural"
        investor.kyc.save()
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        fees = decimal.Decimal(1000.003)
        expected_investment_fees = {
            "stotal": decimal.Decimal(1000.00),
            "tax": decimal.Decimal(0.00),
            "total": decimal.Decimal(1000.00),
        }
        actual_fees = get_investment_fees(bill, fees)
        assert actual_fees == expected_investment_fees

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_investment_date(self):
        investor = InvestorFaker(name="Alejandro")
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
        )
        expected_dates = {
            "month": investment.get_invest_date().month,
            "year": investment.get_invest_date().year,
        }
        actual_date = get_investment_date(bill)
        assert expected_dates == actual_date

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_output_path_with_docx_extension(self):
        investor = InvestorFaker(name="Alejandro")
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
            invoice_number="9999",
        )
        doc_path = get_output_path("doc", bill)
        expected_doc_path = "/tmp/Fees_invoice/Alejandro_2022_9999.docx"
        assert expected_doc_path == doc_path

    @pytest.mark.skip(
        reason="This test needs to be reviewed according to hurry changes made"
    )
    def test_get_output_path_with_pdf_extension(self):
        investor = InvestorFaker(name="Alejandro")
        cashcall = CashCallFaker(investor=investor)
        investment = InvestmentFaker(investor=investor)
        bill = BillFaker(
            investor=investor,
            cashcall=cashcall,
            investment=investment,
            type="management_fees",
            invoice_number="9999",
        )
        pdf_path = get_output_path("pdf", bill)
        expected_pdf_path = "/tmp/Fees_invoice/Alejandro_2022_9999.pdf"
        assert expected_pdf_path == pdf_path

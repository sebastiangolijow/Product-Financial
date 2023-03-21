import os
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response

from api_mangopay.publisher import MangoPay
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.models import Bill
from cashflow.bill.utils import generate_bill_number
from cashflow.cashcalls.models import CashCall
from cashflow.currency.conversion_rate import convert_dollar_to_euro
from core_management.models import MangoPayRelation
from core_management.models import PayIn
from ort_files.documentbuilder.utils.utils_file import convert_to_pdf
from ort_files.general.utils.filefield_utils import get_fees_invoice_template
from ort_files.general.utils.filefield_utils import get_file
from ort_files.general.utils.s3_utils import get_s3_presigned_url
from ort_files.general.utils.s3_utils import save_to_s3


class CashCallUtils:
    def __init__(self, cashcall):
        self.cashcall: CashCall = cashcall
        self.investment = None
        self.payin = None
        self.publish_response = None

    def set_sendinblue_amount_totals(self):
        if not self.cashcall.sendinblue_template_id:
            self.cashcall.set_sendinblue_template_id()
        if not self.cashcall.committed_amount or not self.cashcall.fees_amount:
            self.cashcall.set_amount_totals()
        return self.cashcall

    def get_investment_and_bill(self):
        bill = None
        related_bills = self.cashcall.bills.all()
        if related_bills.count() == 1:
            bill = related_bills.first()
            if bill.investment:
                self.investment = bill.investment
        return self.investment, bill

    def fundraising_in_dollars(self):
        investment, _ = self.get_investment_and_bill()
        if (
            investment
            and investment.fundraising
            and investment.fundraising.currency == "USD"
        ):
            return True
        return False

    def bill_is_management_fees(self):
        has_bills = self.cashcall.bills and self.cashcall.bills.first()
        if has_bills:
            bill: Bill = self.cashcall.bills.first()
            if bill.type == BillTypeChoices.management_fees.name:
                return True
        return False

    def compute_amount_payin(self):
        ### Now the sum of the committed amount and fees is done in MangoPay_microservice, so is not needed to do it here anymore.
        amount = self.cashcall.committed_amount
        if self.bill_is_management_fees():
            amount = Decimal(0)
        if self.fundraising_in_dollars():
            amount = convert_dollar_to_euro(amount)
        return amount

    def compute_fees_payin(self):
        fees = self.cashcall.total_fees_amount
        if self.bill_is_management_fees():
            return 0
        if self.fundraising_in_dollars():
            fees = convert_dollar_to_euro(fees)
        return fees

    def create_payin_and_publish_it(self):
        self.payin = PayIn.objects.create(
            amount=self.compute_amount_payin(),
            fees=self.compute_fees_payin(),
            investor=self.cashcall.investor,
            investment=self.investment,
        )
        try:
            self.publish_response = MangoPay.publish(
                "cash_call_payins", self.payin.id, True
            )
        except Exception as e:
            return None, Response(
                f"[CASHCALL] Error while publishing to MangoPay: {e}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        self.cashcall.payin = self.payin
        self.cashcall.save()
        return self.payin, None

    def set_mangopay_relationships(self):
        if self.publish_response:
            for elem in self.publish_response.data:
                if "id_mangopay" in elem:
                    mangopay_relation = MangoPayRelation.objects.get(
                        id_mangopay=elem["id_mangopay"], entity="payins"
                    )
                    mangopay_relation.payin = self.payin
                    mangopay_relation.save()


class InvoicesUtils:
    def __init__(self, cash_call: CashCall):
        self.cash_call = cash_call

    def generate(self):

        self.validate()

        language = self.get_owner_language()

        for bill in self.cash_call.bills.all():
            generate_bill_number(bill)

            bill_no_file = not bill.file

            if bill_no_file and bill.type != BillTypeChoices.management_fees.name:
                bill_file = self.generate_bill_pdf(
                    self.cash_call.investor, bill, language
                )
                self.save_invoice(bill, self.get_investor_name(), bill_file)

    def validate(self):
        if self.cash_call.investor is None:
            raise Exception(
                f"unvalid cashcall {self.cash_call.id}: no investor in cashcall"
            )

        if self.cash_call.bills.all().exists() is False:
            raise Exception(f"unvalid cashcall {self.cash_call.id}: no bills assigned")

    def get_owner_language(self):

        user = self.cash_call.investor.get_owner_user()
        if user and user.settings and user.settings.preferred_language == "FR":
            language = user.settings.preferred_language
        else:
            language = "EN"

        return language

    def get_investor_name(self):
        return self.cash_call.investor.name.replace(" ", "_")

    def generate_bill_pdf(self, investor, bill: Bill, language: str):

        doc = get_fees_invoice_template(investor, bill, language)
        context = bill.format_invoice()
        doc.render(context)
        input_file_name = f"generated_invoice_bill_{bill.id}.docx"
        doc.save(input_file_name)

        return input_file_name

    def save_invoice(self, bill: Bill, investor_name: str, input_file_name):

        output_file_name_path = f"tmp/Invoice_{investor_name}_{bill.id}.docx"
        output_pdf_file_name = f"Invoice_{investor_name}_{bill.id}.pdf"
        output_pdf_file_name_s3_absolute_path = f"tmp/{output_pdf_file_name}"

        save_to_s3(input_file_name, output_file_name_path)
        convert_to_pdf(output_file_name_path, output_pdf_file_name_s3_absolute_path)
        presigned_url = get_s3_presigned_url(output_pdf_file_name_s3_absolute_path)
        file_content = get_file(presigned_url)
        bill.file.save(name=output_pdf_file_name, content=file_content)
        os.remove(input_file_name)

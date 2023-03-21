from datetime import datetime

from django.core.management.base import BaseCommand

from api_mangopay.utils.mangopay_api_requests import MangoPayRequest
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.models import Bill
from cashflow.cashcalls.models import CashCall
from cashflow.cashcalls.utils.view_utils import CashCallUtils
from core_management.models import MangoPayRelation
from core_management.models import PayIn


mp_request = MangoPayRequest()


class Command(BaseCommand):

    help = """
    We had an issue with the Payins created for the 2022.
    See https://gitlab.com/app-oneragtime/platform-core/core-backend/-/issues/330
    TO DELETE ONCE IT IS FINISHED"""

    bill_numbers_sent = {
        "2022_OF_0000019": {"correct_payin_id": "2118722960"},
        "2022_OF_0000021": {"correct_payin_id": "2119215651"},
        "2022_OF_0000075": {"correct_payin_id": "2118737073"},
        "2022_OF_0000036": {"correct_payin_id": "2118745585"},
        "2022_OF_0000029": {"correct_payin_id": "2118748945"},
        "2022_OF_0000012": {"correct_payin_id": "2118751820"},
    }

    def handle(self, *args, **options):
        management_bills_2022 = Bill.objects.filter(
            type=BillTypeChoices.management_fees.name, year=2022
        )
        for bill in management_bills_2022:
            bill_identification = "ID " + str(bill.pk)
            if bill.invoice_number:
                bill_identification = "Invoice Number " + bill.invoice_number
            print("------- START PROCESS FOR BILL " + bill_identification + " -------")

            is_bill_sent = str(bill.invoice_number) in self.bill_numbers_sent
            if is_bill_sent:
                print("BILL IN LIST")
                bill_mp_payin_id = self.bill_numbers_sent[bill.invoice_number][
                    "correct_payin_id"
                ]
                self.create_payin_from_mangopay_data(bill, bill_mp_payin_id)
            else:
                print("BILL NOT IN LIST")
                self.create_correct_payin(bill)

            print("------- END OF PROCESS FOR BILL " + bill_identification + " -------")
        return None

    def create_correct_payin(self, bill):
        cash_call = bill.cashcall
        utils = CashCallUtils(cash_call)
        utils.create_payin_and_publish_it()
        utils.set_mangopay_relationships()
        print("SUCCESS PUBLISHING PAYIN")
        return

    def create_payin_from_mangopay_data(self, bill: Bill, payin_ids):
        id_in_mangopay = self.get_payin_id_mangopay_from_bill(bill)
        endpoint = f"payin/{id_in_mangopay}/"
        patch_data = {"ids": payin_ids}
        mp_request.mangopay_ms_patch_request(endpoint, patch_data)
        print("SUCCESS EDITING PAYIN")
        return

    def get_payin_id_mangopay_from_bill(self, bill):
        cashcall: CashCall = bill.cashcall
        if cashcall:
            payin: PayIn = cashcall.payin
            if payin:
                mp_relation: MangoPayRelation = payin.mangopay_relation
                if mp_relation:
                    return mp_relation.id_mangopay
                raise Exception("No MP relation")
            raise Exception("No Payin")
        raise Exception("No caschall")

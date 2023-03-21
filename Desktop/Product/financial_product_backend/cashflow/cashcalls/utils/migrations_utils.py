from decimal import Decimal
from typing import Optional

from django.db import connection

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.bill.fees.membership_fees import calculate_membership_fees
from cashflow.bill.fees.rhapsody_fees import calculate_rhapsody_fees
from cashflow.bill.fees.upfront_fees import calculate_upfront_fees
from cashflow.cashcalls.choices import CashCallStatus


CASHCALL_BILL_STATUS_MAP = {
    "CREATED": CashCallStatus.PENDING.value,
    "FAILED": CashCallStatus.FAILED.value,
    "SUCCEEDED": CashCallStatus.PAID.value,
}


def get_fee_function_by_type(bill):
    bill_type = bill.type
    fees_functions = {
        BillTypeChoices.upfront_fees.name: calculate_upfront_fees,
        BillTypeChoices.management_fees.name: calculate_management_fees,
        BillTypeChoices.rhapsody_fees.name: calculate_rhapsody_fees,
        BillTypeChoices.membership_fees.name: calculate_membership_fees,
    }
    return fees_functions.get(bill_type)


def get_fees(bill: "Bill") -> Optional[Decimal]:
    cashcall: "CashCall" = bill.cashcall
    if cashcall and cashcall.fees_amount:
        return cashcall.fees_amount
    return None


def get_fees_percentage(bill: "Bill") -> Optional[Decimal]:
    investment: "Investment" = bill.investment
    cashcall: "CashCall" = bill.cashcall
    if cashcall and cashcall.total_fees_amount:
        return cashcall.fees_percentage
    if investment:
        return investment.fees_percentage
    return None


def get_amount(bill: "Bill") -> Optional[Decimal]:
    cashcall: "CashCall" = bill.cashcall
    investment: "Investment" = bill.investment
    if investment and investment.committed_amount:
        return investment.committed_amount
    if cashcall and cashcall.committed_amount:
        return cashcall.committed_amount
    return None


def move_payin_to_cashcall(apps, schema):
    CashCall: "CashCall" = apps.get_model("cashcalls", "cashcall")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT cc.id as cashcall_id, cp.*  from cashcalls_cashcall as cc  LEFT JOIN core_management_payin as cp  on cc.payin_id = cp.id where cc.payin_id  is not NULL"
        )
        columns = [column[0] for column in cursor.description]
        columns[0] = "cashcall_id"
        for row in cursor.fetchall():

            payin = dict(zip(columns, row))
            cashcall: "Cashcall" = CashCall.objects.get(pk=payin["cashcall_id"])
            payin["core_id"] = payin["id"]
            payin["amount"] = str(payin["amount"])
            payin["fees"] = str(payin["fees"])
            payin["creation_date"] = (
                str(payin["creation_date"]) if payin["creation_date"] else None
            )
            payin["execution_date"] = (
                str(payin["execution_date"]) if payin["execution_date"] else None
            )
            payin.pop("id", None)
            payin.pop("payin_id", None)
            payin.pop("cashcall_id", None)
            payin = {k: v for k, v in payin.items() if v}
            cashcall.response = payin
            cashcall.status = CASHCALL_BILL_STATUS_MAP.get(
                payin.get("status"), CashCallStatus.FAILED.value
            )
            cashcall.save()


def reverse_move_payin_to_cashcall(apps, schema):
    pass


def migrate_data_from_cashcall_to_bill(apps, schema):
    CashCall: "CashCall" = apps.get_model("cashcalls", "cashcall")
    Bill: "Bill" = apps.get_model("bill", "bill")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT bb.id as bill_id, cc.* from bill_bill bb LEFT  JOIN cashcalls_cashcall cc  on bb.cashcall_id  = cc.id  where bb.cashcall_id is not NULL ;"
        )
        columns = [column[0] for column in cursor.description]
        columns[0] = "_bill_id"
        for row in cursor.fetchall():
            cashcall = dict(zip(columns, row))
            bill: "Bill" = Bill.objects.get(pk=cashcall["_bill_id"])
            bill.cc_emails = cashcall["cc_emails"]
            bill.last_sent = cashcall["last_sent"]
            bill.investor_name = cashcall["investor_name"]
            bill.sendinblue_template_id = cashcall["sendinblue_template_id"]
            bill.status = cashcall["status"]
            bill.amount_due = get_amount(bill)
            bill.fees_amount_due = get_fees(bill)
            bill.save()


def reverse_migrate_data_from_cashcall_to_bill(apps, schema):
    pass

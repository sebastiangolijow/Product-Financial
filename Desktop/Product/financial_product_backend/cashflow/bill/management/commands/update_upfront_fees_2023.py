from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from tqdm import tqdm

from cashflow.bill.choices import BillNumberChoices
from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.models import Bill
from cashflow.cashcalls.models import CashCall
from dealflow.investment.models.models import Investment
from entities.investor.models.models import Investor


bucket_name = settings.AWS_STORAGE_BUCKET_NAME
CURRENT_YEAR = 2023


def write_to_log(message, logfile="update_investors.log"):
    f = open(logfile, "a")
    f.write(message)
    f.close()


def get_local_path(bill: Bill) -> str:
    file_name = bill.file.name.split("/")[-1]
    file_type = "unknown"
    if bill.invoice_number:
        file_type = bill.invoice_number[0:7]
    elif bill.invoice_number_deprecated:
        file_type = bill.invoice_number_deprecated[0:7]
    return f"./bill_export/{file_type}/{file_name}"


class Command(BaseCommand):
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start 1 of 2: Update Up Front Bills ")
        # Create bill for each investment
        bills: QuerySet = Bill.objects.filter(type="upfront_fees", year=2023)
        for bill in tqdm(bills):
            cc: CashCall = CashCall.objects.get(bill_id=bill.id)
            generate_bill_number(bill)
            bill.generate(cc.response, 2023)
            bill.save()


def generate_bill_number(bill) -> None:
    current_year = 2023
    type = "UF"
    number = (
        Bill.objects.filter(type="upfront_fees", year=2023)
        .exclude(invoice_number="")
        .count()
    )
    number = str(number).zfill(7)
    bill.invoice_number = f"{current_year}_{type}_{number}"
    bill.save(update_fields=["invoice_number"])

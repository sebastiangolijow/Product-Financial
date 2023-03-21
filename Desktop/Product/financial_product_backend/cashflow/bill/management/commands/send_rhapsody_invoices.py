from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from cashflow.bill.management.commands.rhapsody_fees_2023 import create_lists
from cashflow.bill.models import Bill
from cashflow.cashcalls.models import CashCall
from core_management.models import UserInvestorRelationship
from core_management.utils import format_float
from dealflow.investment.models.models import Investment
from dealflow.investment.serializers.serializers_fund_portfolio import (
    FormatInvestmentSerializer,
)
from entities.investor.models.models import Investor
from services.email.sendinblue_mail import SendInBlueMail


BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME


def write_to_log(message, logfile="update_investors.log"):
    f = open(logfile, "a")
    f.write(message)
    f.close()


def get_local_path(bill: Bill) -> str:
    file_name = bill.file.name.split("/")[-1]
    if bill.invoice_number:
        file_type = bill.invoice_number[0:7]
    elif bill.invoice_number_deprecated:
        file_type = bill.invoice_number_deprecated[0:7]
    else:
        file_type = "unknown"
    return f"./bill_export/{file_type}/{file_name}"


class Command(BaseCommand):
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start 2 of 2: Sending Invoices")

        total_amount: int = 0
        df: "DataFrame" = pd.read_csv(
            "cashflow/bill/files/OneRagtime_Rhapsody_fees_test.csv"
        )
        investor_investments: dict = {}
        investor_bills: dict = {}
        create_lists(df, investor_investments)
        for investor_name, investments in tqdm(investor_investments.items()):
            print("Start 2 of 2: Send email with pdf")
            attachment: list = []
            total_fees_amount: int = 0
            for investment in investments:
                bill: Bill = Bill.objects.filter(investment_id=investment.id).last()
                bills_list: list = investor_bills.get(investor_name, [])
                bills_list.append(bill)
                cc: CashCall = CashCall.objects.filter(bill=bill).last()
                wire_ref: str = cc.response["wire_reference"]
                investor_bills[investor_name] = bills_list
                copy: str = df.loc[
                    (df["Name"] == investor_name)
                    & (df["investment"] == investment.committed_amount)
                ]["Copy"]
                copy: str = copy.to_string()
                copy = copy.split(" ")[-1]
                if "/" in copy:
                    copy = copy.split("/")
                append_attachment(bills_list, attachment)
                if len(Investor.objects.filter(name=investor_name)) > 1:
                    investor: Investor = Investor.objects.filter(
                        name=investor_name
                    ).first()
                    print("## Repeated investor:: " + investor.permaname)
                else:
                    investor: Investor = Investor.objects.get(name=investor_name)
                user_rel: UserInvestorRelationship = (
                    UserInvestorRelationship.objects.filter(
                        investor_id=investor.id, is_owner=True
                    )
                )
                total_fees_amount += bill.fees_amount_due
                total_amount += bill.fees_amount_due
                params: dict = create_params(
                    investments, user_rel, total_fees_amount, wire_ref
                )
            if copy == "None":
                send_email(params, attachment, None, user_rel)
            else:
                send_email(params, attachment, copy, user_rel)
        print(total_amount)


def create_params(investments, user_rel, total_fees_amount, wire_ref) -> dict:
    investment_dict: list = []
    for investment in investments:
        serializer = FormatInvestmentSerializer(instance=investment)
        investment_dict.append(serializer.data)
        round(total_fees_amount, 2)
    return {
        "total_fees_amount": format_float(int(total_fees_amount)),
        "user_name": user_rel[0].account.first_name,
        "investments": investment_dict,
        "wire_reference": wire_ref,
    }


def append_attachment(bills_list, attachment):
    for bill in bills_list:
        if bill.file:
            name = bill.file.name.split("/")
            attachment.append({"url": bill.file.url, "name": name[-1]})


def send_email(params, attachment, copy, user_rel):
    CC_EMAILS = [
        {"email": "stephanie@oneragtime.com", "name": "Stephanie"},
        {"email": "myriam@oneragtime.com", "name": "Myriam"},
    ]
    BCC_EMAILS = [
        {"email": "invoices@oneragtime.com", "name": "invoices"},
        {"email": "sebastian@oneragtime.com", "name": "Sebastian"},
    ]
    if type(copy) == list:
        CC_EMAILS.append({"email": copy[0], "name": format_copy(copy[0].split("@")[0])})
        CC_EMAILS.append({"email": copy[1], "name": format_copy(copy[1].split("@")[0])})
    if type(copy) == str:
        CC_EMAILS.append({"email": copy, "name": format_copy(copy.split("@")[0])}),
    SendInBlueMail().send(
        to=[
            {
                "email": user_rel[0].account.email,
                "name": user_rel[0].account.first_name
                + " "
                + user_rel[0].account.last_name,
            }
        ],
        template_name="rhapsody_management_fees",
        params=params,
        attachment=attachment,
        cc=CC_EMAILS,
        bcc=BCC_EMAILS,
    )


def format_copy(copy):
    if "." in copy.split("@")[0]:
        copy.split("@")[0].split(".")[0] + " " + copy.split("@")[0].split(".")[1]
    else:
        return copy

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from cashflow.bill.models import Bill
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
        print("Start 1 of 2: Generate Individual Bills ")

        current_year = 2023
        df: "DataFrame" = pd.read_csv(
            "cashflow/bill/files/investor_investments_test.csv"
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
                investor_bills[investor_name] = bills_list
                append_attachment(bills_list, attachment)
                investor: Investor = Investor.objects.get(name=investor_name)
                user_rel: UserInvestorRelationship = (
                    UserInvestorRelationship.objects.filter(
                        investor_id=investor.id, is_owner=True
                    )
                )
                total_fees_amount += bill.amount_due
                params: dict = create_params(investments, user_rel, total_fees_amount)
            SendInBlueMail().send(
                [
                    {"email": "sebastian@oneragtime.com", "name": "Sebastian"},
                    # {"email": "justine@oneragtime.com", "name": "Justine"},
                    {"email": "myriam@oneragtime.com", "name": "Myriam"},
                    # Take it pout to use it in prod
                    # {"email": user_rel[0].account.email, "name": user_rel[0].first_name + ' ' + user_rel[0].account.last_name}
                ],
                "cash_call_emails_management_fees",
                params,
                attachment,
            )


def create_lists(df, investor_investments) -> list:
    for _, row in df.iterrows():
        investor_investments_list: list = investor_investments.get(row["investor"], [])
        investor_investments_list.append(
            Investment.objects.get(
                fundraising__name=row["investment"], investor__name=row["investor"]
            )
        )
        investor_investments[row["investor"]] = investor_investments_list
    return investor_investments_list


def create_params(investments, user_rel, total_fees_amount) -> dict:
    investment_dict: list = []
    for investment in investments:
        serializer = FormatInvestmentSerializer(instance=investment)
        investment_dict.append(serializer.data)
    return {
        "total_fees_amount": format_float(total_fees_amount),
        "user_name": user_rel[0].account.first_name,
        "investments": investment_dict,
    }


def append_attachment(bills_list, attachment):
    for bill in bills_list:
        if bill.file:
            name = bill.file.name.split("/")
            attachment.append({"url": bill.file.url, "name": name[-1]})

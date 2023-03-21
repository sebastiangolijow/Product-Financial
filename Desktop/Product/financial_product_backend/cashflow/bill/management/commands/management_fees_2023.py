from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.bill.models import Bill
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.models import CashCall
from core_management.models import UserInvestorRelationship
from core_management.utils import format_float
from dealflow.investment.models.models import Investment
from dealflow.investment.serializers.serializers_fund_portfolio import (
    FormatInvestmentSerializer,
)
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
    SENDINDBLUE_TEMPLATE_ID = 467
    CC_EMAILS = [
        "myriam@oneragtime.com",
        # "stephanie@oneragtime.com",
        # "stephanie@oneragtime.com",
        # "justine@oneragtime.com",
        # "invoices@oneragtime.com",
        # "investors@oneragtime.com",
        "sebastian@oneragtime.com",
    ]
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start 1 of 2: Generate Individual Bills ")

        df: "DataFrame" = pd.read_csv(
            "cashflow/bill/files/investor_investments_test.csv"
        )
        investor_investments: dict = {}
        investor_bills: dict = {}
        create_lists(df, investor_investments)
        # Create bill for each investment
        for investor_name, investments in tqdm(investor_investments.items()):
            investor: Investor = Investor.objects.get(name=investor_name)
            for investment in investments:
                bills_list: list = investor_bills.get(investor_name, [])
                investment_year: str = df.loc[
                    (df["investor"] == investor_name)
                    & (df["investment"] == investment.fundraising.name)
                ]["sa_signed_date"]
                investment_year: int = int(investment_year)
                fees_amount, _ = calculate_management_fees(
                    investment, CURRENT_YEAR, investment_year=investment_year
                )
                bill: Bill = create_bill(
                    investment,
                    fees_amount,
                    CURRENT_YEAR,
                    investor,
                    investor_name,
                )
                cash_call: CashCall = create_cash_call(bill)
                validate_and_publish_mango_pay(cash_call, bill, investor)


def create_bill(
    investment: Investment,
    fees_amount: Decimal,
    CURRENT_YEAR: int,
    investor: Investor,
    investor_name: str,
) -> Bill:
    return Bill.objects.create(
        investment=investment,
        amount_due=fees_amount,
        type=BillTypeChoices.management_fees.name,
        fees_amount_due=Decimal(0),
        year=CURRENT_YEAR,
        investor=investor,
        investor_name=investor_name,
    )


def create_cash_call(bill: Bill) -> CashCall:
    return CashCall.objects.create(
        bill=bill,
        committed_amount=bill.fees_amount_due,
        fees_amount=0,
        status=CashCallStatus.CREATED.value,
    )


def validate_and_publish_mango_pay(cash_call: CashCall, bill: Bill, investor: Investor):
    is_valid, message = cash_call.can_publish_payin(return_reason=True)
    if not is_valid:
        print(f"Error for investor {investor.id} : {message}")
    else:
        cash_call.publish_payin()
        cash_call.save()
    if cash_call.status == CashCallStatus.PENDING.value:
        bill.generate(cash_call.response, CURRENT_YEAR)


def append_attachment(bills_list: list, attachment: list):
    for bill in bills_list:
        if bill.file:
            name = bill.file.name.split("/")
            attachment.append({"url": bill.file.url, "name": name[-1]})


def create_lists(df: "DataFrame", investor_investments: list) -> list:
    for _, row in df.iterrows():
        investor_investments_list: list = investor_investments.get(row["investor"], [])
        investor_investments_list.append(
            Investment.objects.get(
                fundraising__name=row["investment"], investor__name=row["investor"]
            )
        )
        investor_investments[row["investor"]] = investor_investments_list
    return investor_investments_list


def create_params(
    investments: list, user_rel: UserInvestorRelationship, total_fees_amount: int
) -> dict:
    investment_dict: list = []
    for investment in investments:
        serializer = FormatInvestmentSerializer(instance=investment)
        investment_dict.append(serializer.data)
        total_fees_amount += investment.get_fees_amount_from_bill()
    params: dict = {
        "total_fees_amount": format_float(int(total_fees_amount)),
        "user_name": user_rel[0].account.first_name,
        "investments": investment_dict,
    }
    return params

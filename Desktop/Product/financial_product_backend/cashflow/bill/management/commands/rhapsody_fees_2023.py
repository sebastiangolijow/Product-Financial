from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.fees.rhapsody_fees import calculate_rhapsody_fees
from cashflow.bill.models import Bill
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.models import CashCall
from core_management.utils import format_float
from dealflow.investment.models.models import Investment
from entities.investor.models.models import Investor


bucket_name = settings.AWS_STORAGE_BUCKET_NAME
CURRENT_YEAR = 2023
acceleration_percentage = round(Decimal(0.0225), 4)


class Command(BaseCommand):
    SENDINDBLUE_TEMPLATE_ID = 467
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start 1 of 2: Generate Individual Bills ")

        df: "DataFrame" = pd.read_csv(
            "cashflow/bill/files/OneRagtime_Rhapsody_fees_test.csv"
        )
        investor_investments: dict = {}
        create_lists(df, investor_investments)
        # Create bill for each investment
        for investor_name, investments in tqdm(investor_investments.items()):
            if len(Investor.objects.filter(name=investor_name)) > 1:
                investor: Investor = Investor.objects.filter(name=investor_name).first()
            else:
                investor: Investor = Investor.objects.get(name=investor_name)
            for investment in investments:
                investment_year: str = df.loc[
                    (df["Name"] == investor_name)
                    & (df["investment"] == investment.committed_amount)
                ]["year"]
                investment_year: int = int(investment_year)
                bill: Bill = create_bill(
                    investment,
                    CURRENT_YEAR,
                    investor,
                    investor_name,
                )
                cash_call: CashCall = create_cash_call(bill)
                validate_and_publish_mango_pay(cash_call, bill, investor)


def create_bill(
    investment: Investment,
    CURRENT_YEAR: int,
    investor: Investor,
    investor_name: str,
) -> Bill:
    return Bill.objects.create(
        investment=investment,
        amount_due=investment.committed_amount,
        type=BillTypeChoices.rhapsody_fees.name,
        fees_amount_due=investment.committed_amount * acceleration_percentage,
        year=CURRENT_YEAR,
        investor=investor,
        investor_name=investor_name,
    )


def create_cash_call(bill: Bill) -> CashCall:
    return CashCall.objects.create(
        bill=bill,
        committed_amount=bill.amount_due,
        fees_amount=bill.fees_amount_due,
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


def create_lists(df: "DataFrame", investor_investments: list) -> list:
    for _, row in df.iterrows():
        investor_investments_list: list = investor_investments.get(row["Name"], [])
        investor_investments_list.append(
            Investment.objects.filter(
                committed_amount=row["investment"], investor__name=row["Name"]
            ).first()
        ) if (
            len(
                Investment.objects.filter(
                    committed_amount=row["investment"], investor__name=row["Name"]
                )
            )
            > 1
        ) else investor_investments_list.append(
            Investment.objects.get(
                committed_amount=row["investment"], investor__name=row["Name"]
            )
        )
        investor_investments[row["Name"]] = investor_investments_list
    return investor_investments_list

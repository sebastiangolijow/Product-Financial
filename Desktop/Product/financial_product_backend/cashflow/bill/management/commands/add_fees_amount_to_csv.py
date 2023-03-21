from django.conf import settings
from django.core.management.base import BaseCommand
from pandas import read_csv
from tqdm import tqdm

from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.bill.models import Bill
from cashflow.currency.conversion_rate import convert_dollar_to_euro
from dealflow.investment.models.models import Investment


BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME


class Command(BaseCommand):
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start: Creating CSV")

        current_year = 2023
        data_frame: "data_frame" = read_csv(
            "cashflow/bill/files/investor_investments.csv"
        )
        data_frame["fees_amount"] = data_frame.index
        for index, row in tqdm(data_frame.iterrows()):
            investment: Investment = Investment.objects.get(
                fundraising__name=row["investment"], investor__name=row["investor"]
            )
            fees_amount, _ = calculate_management_fees(
                investment,
                current_year,
                investment_year=investment.get_invest_date().year,
            )
            if investment.fundraising.currency.name == "USD":
                investment.committed_amount = convert_dollar_to_euro(
                    investment.committed_amount
                )
                data_frame.iloc[index, 3] = round(investment.committed_amount, 2)
            data_frame.iloc[index, 5] = round(fees_amount, 2)
        data_frame.to_csv("./management_fees_2023_test.csv")

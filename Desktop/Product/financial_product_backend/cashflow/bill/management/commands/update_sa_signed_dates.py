from datetime import datetime
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models import F
from django.db.models import Q

from dealflow.investment.models.models import Investment


def write_to_log(message, logfile="inspect_fees.log"):
    f = open(logfile, "a")
    f.write(message)
    f.close()


def convert_to_date_object(date: str) -> datetime:
    if "/" in date:
        full_year_date = len(date) > 8
        if full_year_date:
            return datetime.strptime(date, "%d/%m/%Y")
        else:
            return datetime.strptime(date, "%d/%m/%y")
    if "-" in date:
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    write_to_log(f"no date found {date} \n", "no_date_found.log")


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("start")

        dataframe = pd.read_excel("Management_fees_SPV_UK.xlsx", skiprows=5)
        # dataframe = dataframe.iloc[4:]

        print(dataframe.head())
        print(dataframe.columns)

        for index, row in dataframe.iterrows():
            print("--------")
            investment_id = int(row["investment.id"])
            sa_signed = row["SA signed "]
            fees_2021 = row["fees 2021"]
            fees_2022 = row["fees 2022"]
            fees_2023 = row["fees 2023"]
            year = row[" SA signed (year)"]
            print("---")
            print(investment_id)
            print(year)
            print(sa_signed)
            print(fees_2021)
            print(fees_2022)
            print(fees_2023)

            investment = None

            correct_date = True
            if isinstance(sa_signed, str):

                correct_date = "non trouv" not in sa_signed

            if correct_date:

                if isinstance(sa_signed, datetime):
                    date_object = sa_signed
                else:
                    date_object = convert_to_date_object(sa_signed)

                print(date_object)

                try:
                    investment = Investment.objects.get(id=investment_id)
                except:
                    print("investment not found")
                    write_to_log(
                        f"investment not found : {investment_id} \n",
                        logfile="investment_not_found.log",
                    )

                investment.subscription_agreement_signed_date = date_object
                investment.save()

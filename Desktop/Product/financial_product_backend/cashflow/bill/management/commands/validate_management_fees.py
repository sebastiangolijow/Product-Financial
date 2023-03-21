from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models import F
from django.db.models import Q

from cashflow.bill.fees.management_fees import calculate_management_fees
from dealflow.investment.models.models import Investment


def write_to_log(message, logfile="inspect_fees.log"):
    f = open(logfile, "a")
    f.write(message)
    f.close()


def compare_fees(original, calc) -> bool:
    return Decimal(original).quantize(Decimal(".01")) == Decimal(calc).quantize(
        Decimal(".01")
    )


def error_message_wrong_fees(orginal, calc, year, investment_id, percentage) -> str:
    return f"'investment': '{investment_id}', 'year': '{year} ' 'exell_fees': '{orginal}' , 'calculated': '{calc}', '%': '{percentage}'\n"


def error_message_wrong_dates(
    excel_date,
    excel_year,
    investment,
) -> str:
    return f"'investment': '{investment.id}', 'exel_year': '{excel_year}' , 'exel_date': '{excel_date}', 'db_date': '{investment.get_invest_date()}'\n"


def compare_sign_date(excel_date, excel_year, investment):

    db_date = investment.get_invest_date()

    if db_date.year != excel_year:
        write_to_log(
            error_message_wrong_dates(
                excel_date,
                excel_year,
                investment,
            ),
            "wrong_dates.log",
        )


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

            try:
                investment = Investment.objects.get(id=investment_id)
            except:
                print("investment not found")
                write_to_log(
                    f"investment not found : {investment_id} \n",
                    logfile="investment_not_found.log",
                )

            not_skip_in_excell = not isinstance(fees_2021, str)

            if investment and not_skip_in_excell:
                calc_fees_2021, percentage_2021 = calculate_management_fees(
                    investment, 2021
                )
                calc_fees_2022, percentage_2022 = calculate_management_fees(
                    investment, 2022
                )
                calc_fees_2023, percentage_2023 = calculate_management_fees(
                    investment, 2023
                )

                if compare_fees(fees_2021, calc_fees_2021):
                    print(f"investment: {investment_id} is correct")
                else:
                    print(f"Failed investment: {investment_id}")
                    compare_sign_date(sa_signed, year, investment)
                    error_message = error_message_wrong_fees(
                        fees_2021,
                        calc_fees_2021,
                        2021,
                        investment_id,
                        percentage_2021,
                    )
                    write_to_log(
                        error_message,
                        logfile="fees_not_correct.log",
                    )
                if compare_fees(fees_2022, calc_fees_2022):
                    print(f"investment: {investment_id} is correct")
                else:
                    print(f"Failed investment: {investment_id}")
                    compare_sign_date(sa_signed, year, investment)
                    error_message = error_message_wrong_fees(
                        fees_2022,
                        calc_fees_2022,
                        2022,
                        investment_id,
                        percentage_2022,
                    )
                    write_to_log(
                        error_message,
                        logfile="fees_not_correct.log",
                    )
                if compare_fees(fees_2023, calc_fees_2023):
                    print(f"investment: {investment_id} is correct")
                else:
                    print(f"Failed investment: {investment_id}")
                    compare_sign_date(sa_signed, year, investment)
                    error_message = error_message_wrong_fees(
                        fees_2023,
                        calc_fees_2023,
                        2023,
                        investment_id,
                        percentage_2023,
                    )
                    write_to_log(
                        error_message,
                        logfile="fees_not_correct.log",
                    )

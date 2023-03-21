import boto3
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F
from django.db.models import Q

from cashflow.bill.factories import create_management_fees_bill
from cashflow.bill.models import Bill
from dealflow.investment.models.models import Investment


bucket_name = settings.AWS_STORAGE_BUCKET_NAME


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

    help = "create management_fees bills 2022"

    def handle(self, *args, **options):
        print("Start")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        current_year = "2022"
        investments_query = (
            Investment.objects.filter(fees_type="on_going")
            .exclude(investor__name__icontains="oneragtime")
            .exclude(status="rejected")
            .exclude(fundraising__startup__is_failed=True)
            .exclude(fundraising__name__icontains=current_year)
        )

        for investment in investments_query:
            bill = create_management_fees_bill(investment, 2022)

            print(f"bill created")
            if bill.file.name:

                cloud_path = bill.file.name
                print(f"download: {bill} path: {cloud_path}")
                local_path = get_local_path(bill)
                s3_client.download_file(bucket_name, cloud_path, local_path)
                print(f"download complete : {local_path}")

        investment_ids = investments_query.values_list("id", flat=True)

        bills_query = Bill.objects.filter(
            investment_id__in=investment_ids,
            year=current_year,
        ).select_related("investment", "cashcall")

        print(list(investment_ids))
        bills_query_values = list(
            bills_query.values(
                "id",
                "type",
                "file",
                "invoice_number",
                "invoice_number_deprecated",
                "year",
                "investment_id",
                "investment__committed_amount",
                "investment__fees_percentage",
                "investment__fundraising_id",
                "investment__fundraising__name",
                "investment__creation_datetime",
                "investment__subscription_agreement_signed_date",
                "cashcall__cc_emails",
                "cashcall__investor_name",
                "cashcall__last_sent",
                "cashcall__payin",
                "cashcall__committed_amount",
                "cashcall__fees_percentage",
                "cashcall__committed_amount",
                "cashcall__fees_amount",
            )
        )
        print(bills_query_values)
        df = pd.DataFrame(bills_query_values)
        df.to_csv("./management_fees_2022.csv")
        print("DONE")

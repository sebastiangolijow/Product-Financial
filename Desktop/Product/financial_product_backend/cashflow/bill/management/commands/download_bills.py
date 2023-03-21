import boto3
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from cashflow.bill.models import Bill


bucket_name = settings.AWS_STORAGE_BUCKET_NAME


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

    help = "Download bills locally"

    def handle(self, *args, **options):
        print("Start Downloading")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        search_value = "2021_"
        query = Bill.objects.filter(
            Q(invoice_number_deprecated__icontains=search_value)
            | Q(invoice_number__icontains=search_value)
        )

        query_files = query.exclude(Q(file__isnull=True) | Q(file__exact=""))

        for bill in query_files:
            cloud_path = bill.file.name
            print(f"download: {bill} path: {cloud_path}")
            local_path = get_local_path(bill)
            s3_client.download_file(bucket_name, cloud_path, local_path)
            print(f"download complete : {local_path}")

        df = pd.DataFrame(list(query.values()))

        df.to_csv("./bill_export/bills_2021.csv")

        print("DONE")

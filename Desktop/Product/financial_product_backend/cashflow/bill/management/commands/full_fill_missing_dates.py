from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from cashflow.bill.models import Bill


class Command(BaseCommand):
    help = "create management_fees bills 2023"

    def handle(self, *args, **options):
        print("Start 1 of 1: Full filling dates")
        bills: list = Bill.objects.filter(type="rhapsody_fees", year=2023)
        for bill in tqdm(bills):
            if bill.last_sent == None and bill.id == 1691:
                bill.last_sent = bill.updated_at
                bill.save()
            elif bill.id == 1691:
                bill.last_sent = bill.last_sent + timedelta(days=3)
                bill.save()

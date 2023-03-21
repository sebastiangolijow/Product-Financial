from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from django.db.models import signals
from factory.django import mute_signals

from cashflow.bill.models import Bill


class Command(BaseCommand):
    help = "copy amount_due values to fees_amount_due for management_fees 2023"

    @mute_signals(signals.pre_save, signals.post_save)
    def handle(self, *args, **options):
        bills: QuerySet = Bill.objects.filter(type="management_fees", year=2023)
        for bill in bills:
            if bill.amount_due != bill.fees_amount_due and bill.fees_amount_due == 0:
                bill.fees_amount_due = bill.amount_due
                bill.save(update_fields=["fees_amount_due"])
                print(f"Changed bill {bill.id}")
                print("------------")

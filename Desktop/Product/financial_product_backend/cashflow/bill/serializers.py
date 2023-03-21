from decimal import Decimal
from typing import Callable
from typing import Optional

from rest_framework import serializers
from rest_framework.serializers import Field

from cashflow.bill.models import Bill
from cashflow.cashcalls.models import CashCall
from dealflow.investment.models.models import Investment


class BillsExportListSerializer(serializers.ModelSerializer):
    investor_name: Field = serializers.CharField(
        source="get_investor.name", read_only=True, default=None
    )
    investor_id = serializers.CharField(
        source="get_investor.id", read_only=True, default=None
    )
    fundraising_name = serializers.CharField(
        source="investment.fundraising.name", read_only=True, default=None
    )
    amount: Field = serializers.DecimalField(
        source="amount_due", max_digits=12, decimal_places=2
    )
    fees_percentage: Field = serializers.DecimalField(
        source="investment.fees_percentage",
        max_digits=12,
        decimal_places=2,
        default=None,
    )
    fees: Field = serializers.DecimalField(
        source="fees_amount_due", max_digits=12, decimal_places=2
    )
    fees_type: Field = serializers.CharField(
        source="type", read_only=True, default=None
    )
    payment_status: Field = serializers.CharField(
        source="status", read_only=True, default=None
    )
    payment_sent_date: Field = serializers.CharField(
        source="last_sent", read_only=True, default=None
    )
    payment_paid_date: Field = serializers.CharField(
        source="get_payin.execution_date", read_only=True, default=None
    )
    deprecated_bill_number: Field = serializers.CharField(
        source="invoice_number_deprecated", read_only=True, default=None
    )
    bill_number: Field = serializers.CharField(
        source="invoice_number", read_only=True, default=None
    )
    bill_year: Field = serializers.CharField(
        source="year", read_only=True, default=None
    )
    currency = serializers.CharField(
        source="investment.fundraising.currency.name", read_only=True, default=None
    )

    class Meta:
        model = Bill
        fields = (
            "id",
            "investor_name",
            "investor_id",
            "fundraising_name",
            "amount",
            "fees_percentage",
            "fees",
            "fees_type",
            "payment_status",
            "payment_sent_date",
            "payment_paid_date",
            "bill_number",
            "deprecated_bill_number",
            "bill_year",
            "currency",
        )

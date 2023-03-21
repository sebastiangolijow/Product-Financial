from decimal import Decimal

from django.db.models import Model
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Sum
from rest_framework.fields import Field
from rest_framework.serializers import CharField
from rest_framework.serializers import FloatField
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import Serializer
from rest_framework.serializers import SerializerMethodField

from cashflow.bill.models import Bill
from cashflow.currency.conversion_rate import convert_dollar_to_euro
from cashflow.dashboard.utils import AbstractGetInvestmentsAmount
from dealflow.investment.models.models import Investment
from dealflow.valuations.models import Valuation
from entities.investor.models.models import Investor
from entities.investor.models.models import InvestorExitValue
from utilities.decorators import round_result_by_2
from utilities.decorators import round_result_by_3


class BillFeesAmountSerializer(Serializer):
    year: Field = SerializerMethodField()
    month: Field = SerializerMethodField()
    amount: Field = SerializerMethodField()

    class Meta:
        model: Model = Bill
        fields: list = ["year", "month", "amount"]

    def get_year(self, instance) -> str:
        return instance.get("last_sent__year", None)

    def get_month(self, instance) -> str:
        return instance.get("last_sent__month", None)

    def get_amount(self, instance) -> Decimal:
        fees = instance.get("fees", 0)
        return fees


class ValuationFundDashboardSerializer(ModelSerializer):
    investment_offer: str = CharField(source="name")
    invested: float = SerializerMethodField()
    current_net_fair_value: float = FloatField(source="unrealized_valuation_gross")
    net_multiple: float = FloatField()
    manual_exited_value: float = SerializerMethodField()

    class Meta:
        model: Model = Valuation
        fields: list = [
            "investment_offer",
            "invested",
            "current_net_fair_value",
            "net_multiple",
            "manual_exited_value",
        ]

    def get_invested(self, obj: Valuation) -> int:
        return obj.startup.get_fundraisings()[0].get_total_amount_committed()

    def get_manual_exited_value(self, obj: Valuation) -> None:
        return None


class InvestorCorporateValuationDashboardSerializer(ModelSerializer):
    investment_offer: str = CharField()
    invested: float = SerializerMethodField()
    current_net_fair_value: float = FloatField(source="get_portfolio_value_in_eur")
    net_multiple: float = SerializerMethodField()
    manual_exited_value: float = SerializerMethodField()

    class Meta:
        model: Model = Investor
        fields: list = [
            "investment_offer",
            "invested",
            "current_net_fair_value",
            "net_multiple",
            "manual_exited_value",
        ]

    def get_investment_offer(self) -> str:
        return "Corporate"

    def get_invested(self, obj: Investor):
        return (
            Investment.objects.filter(investor=obj)
            .exclude(status="rejected")
            .exclude(
                investor__name__in=["Paragon", "Testing", "Rhapsody I", "Rhapsody II"]
            )
            .aggregate(Sum("committed_amount"))["committed_amount__sum"]
        )

    @round_result_by_2
    def get_net_multiple(self, obj: Investor):
        if self.get_invested(obj) == 0 or obj.get_portfolio_value() == 0:
            return 0
        return obj.get_portfolio_value() / self.get_invested(obj)

    @round_result_by_3
    def get_manual_exited_value(self, obj) -> Decimal:
        investor_exit_value: InvestorExitValue = InvestorExitValue.objects.filter(
            investor_id=obj.id
        )
        if investor_exit_value.exists():
            return investor_exit_value.aggregate(Sum("exit_value"))["exit_value__sum"]
        return 0

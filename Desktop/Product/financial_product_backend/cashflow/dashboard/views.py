from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Sum
from django.db.models import Value as V
from django.db.models.functions import Coalesce
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_200_OK as OK

from cashflow.bill.models import Bill
from cashflow.dashboard.filter_sets import DashboardInvestmentFundFilterSet
from cashflow.dashboard.filter_sets import DashboardValuationFundFilterSet
from cashflow.dashboard.serializers import BillFeesAmountSerializer
from cashflow.dashboard.serializers import InvestorCorporateValuationDashboardSerializer
from cashflow.dashboard.serializers import ValuationFundDashboardSerializer
from cashflow.dashboard.utils import GetInvestedAmountsForInvestments
from cashflow.dashboard.utils import GetInvestmentClubDealValuationsAmount
from cashflow.dashboard.utils import GetInvestmentsAmountsForFund
from core_auth.permissions import IsAuthenticated
from core_auth.permissions import IsOrtStaff
from dealflow.investment.models.models import Investment
from dealflow.valuations.models import Valuation
from entities.investor.models.models import Investor
from entities.startup.models.models import Startup


@method_decorator(cache_page(60 * 10), name="dispatch")
class BaseDashboardView(ListAPIView):
    permission_classes: list = [IsAuthenticated & IsOrtStaff]

    def get(self, _) -> Response:
        investments: QuerySet = self.filter_queryset(self.get_queryset())
        data: dict = GetInvestedAmountsForInvestments(investments).data
        return Response(data=data, status=OK)

    class Meta:
        abstract: bool = True


@method_decorator(cache_page(60 * 30), name="dispatch")
class DashboardClubdealView(BaseDashboardView):
    queryset: QuerySet = Investment.objects.get_clubdeal_investments()


@method_decorator(cache_page(60 * 30), name="dispatch")
class DashboardCorporateView(BaseDashboardView):
    queryset: QuerySet = Investment.objects.get_corporate_investments()


@method_decorator(cache_page(60 * 30), name="dispatch")
class DashboardFundView(BaseDashboardView):
    filter_backends: list = [DjangoFilterBackend]
    filterset_class: FilterSet = DashboardInvestmentFundFilterSet
    queryset: QuerySet = Investment.objects.get_fund_investments()


@method_decorator(cache_page(60 * 30), name="dispatch")
class GetAmountInvestedInFundsView(GenericAPIView):
    permission_classes: list = [IsAuthenticated & IsOrtStaff]

    def get(self, _) -> Response:
        funds: QuerySet = Startup.objects.filter(is_fund=True)
        data: list = [GetInvestmentsAmountsForFund(fund).data for fund in funds]
        return Response(data=data, status=OK)


@method_decorator(cache_page(60 * 30), name="dispatch")
class GetFeesAmountsView(ListAPIView):
    permission_classes: list = [IsAuthenticated & IsOrtStaff]
    serializer_class: Serializer = BillFeesAmountSerializer

    def get_queryset(self) -> QuerySet:
        queryset = (
            Bill.objects.exclude(last_sent__isnull=True)
            .values("last_sent__year", "last_sent__month")
            .annotate(fees=Coalesce(Sum("fees_amount_due"), V(0)))
        )
        return queryset


@method_decorator(cache_page(60 * 30), name="dispatch")
class ValuationsFundsDashboard(ListAPIView):
    queryset: QuerySet = Valuation.objects.filter(startup__is_fund=True)
    filter_backends: list = [DjangoFilterBackend]
    filterset_class: FilterSet = DashboardValuationFundFilterSet
    permission_classes: list = [IsAuthenticated & IsOrtStaff]
    serializer_class: Serializer = ValuationFundDashboardSerializer


@method_decorator(cache_page(60 * 30), name="dispatch")
class InvestorCorporateValuationsDashboard(ListAPIView):
    queryset: QuerySet = Investor.objects.filter(name="OneRagtime Aria")
    permission_classes: list = [IsAuthenticated & IsOrtStaff]
    serializer_class: Serializer = InvestorCorporateValuationDashboardSerializer


@method_decorator(cache_page(60 * 30), name="dispatch")
class InvestmentClubDealValuationsDashboard(ListAPIView):
    permission_classes: list = [IsAuthenticated & IsOrtStaff]

    def get_queryset(self):
        queryset: QuerySet = (
            Investor.objects.prefetch_related(
                "investments",
                "investments__fundraising",
                "investments__fundraising__startup",
            )
            .filter(
                Q(investments__fundraising__startup__is_fund=False)
                & ~Q(investments__status="rejected")
            )
            .exclude(
                Q(investments__isnull=True)
                | Q(name__contains="Testing")
                | Q(name__contains="OneRagtime Aria")
                | Q(name__contains="Paragon")
                | Q(name__contains="Rhapsody")
            )
            .distinct()
        )
        return queryset

    def get(self, _) -> Response:
        data: dict = GetInvestmentClubDealValuationsAmount(self.get_queryset()).data
        return Response(data=data, status=OK)

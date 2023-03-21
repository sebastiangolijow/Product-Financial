from django.db.models import Model
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import FilterSet

from dealflow.investment.models.models import Investment
from dealflow.valuations.models.models import Valuation


class DashboardInvestmentFundFilterSet(FilterSet):
    fund_name: str = CharFilter(
        field_name="fundraising__startup__name", lookup_expr="icontains"
    )

    class Meta:
        model: Model = Investment
        fields: list = ["fundraising__startup__name"]


class DashboardValuationFundFilterSet(FilterSet):
    fund_name: str = CharFilter(field_name="startup__name", lookup_expr="icontains")

    class Meta:
        model: Model = Valuation
        fields: list = ["startup__name"]

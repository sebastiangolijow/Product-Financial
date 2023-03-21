from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django_filters import rest_framework as filters

from cashflow.bill.models import Bill


class BillFilter(filters.FilterSet):
    payment_status = filters.CharFilter(method="filter_payment_status")
    investor_name = filters.CharFilter(method="filter_investor_name")
    investor_id = filters.CharFilter(method="filter_investor_id")
    fundraising_name = filters.CharFilter(
        field_name="investment__fundraising__name", lookup_expr="icontains"
    )

    class Meta:
        model = Bill
        fields = (
            "type",
            "year",
            "payment_status",
            "investor_name",
            "investor_id",
        )

    def filter_payment_status(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(payin__status=value) | Q(investment__payins__status=value)
            )
        return queryset

    def filter_investor_name(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(investor__name__icontains=value)
                | Q(investment__investor__name__icontains=value)
            )
        return queryset

    def filter_investor_id(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(investor__id=value) | Q(investment__investor__id=value)
            )
        return queryset

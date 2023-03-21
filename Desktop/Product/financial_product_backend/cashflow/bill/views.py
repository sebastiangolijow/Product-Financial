import logging

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from api.paginations.pagination_bills import BillPagination
from cashflow.bill.filters import BillFilter
from cashflow.bill.models import Bill
from cashflow.bill.serializers import BillsExportListSerializer
from core_auth.permissions import IsAuthenticated
from core_auth.permissions import IsOrtStaff


logger = logging.getLogger(__name__)


class BillsExportListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated & IsOrtStaff]
    filter_backends = [DjangoFilterBackend]
    serializer_class = BillsExportListSerializer
    filterset_class = BillFilter

    def get_queryset_formatted(self) -> QuerySet:
        return (
            Bill.objects.all()
            .prefetch_related(
                "investor",
                "investment",
                "investment__fundraising",
                "payin",
            )
            .order_by("-id")
        )

    def get_queryset(self) -> QuerySet:
        format = self.request.GET.get("format", None)
        if not format:
            self.pagination_class = BillPagination
        return self.get_queryset_formatted()

from django.urls import path

from cashflow.bill.views import BillsExportListAPIView


app_name = "bill"


urlpatterns = [
    path("finance-table", BillsExportListAPIView.as_view(), name="finance-table"),
]

from django.conf.urls import include
from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from cashflow.cashcalls.views import CashCallCalculateAmountsApiView
from cashflow.cashcalls.views import CashCallViewSet


app_name = "cashcalls"

router = DefaultRouter()
router.register(r"cash_calls", CashCallViewSet, basename="cash_call")

urlpatterns = [
    path("", include(router.urls)),
    url(
        r"(?P<bill_id>\d+)/cash_call_calculate_amounts",
        CashCallCalculateAmountsApiView.as_view(),
        name="cash_call_calculate_amounts",
    ),
]

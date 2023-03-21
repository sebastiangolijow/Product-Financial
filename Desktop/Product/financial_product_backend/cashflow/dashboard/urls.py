from django.urls import path

from cashflow.dashboard.views import DashboardClubdealView
from cashflow.dashboard.views import DashboardCorporateView
from cashflow.dashboard.views import DashboardFundView
from cashflow.dashboard.views import GetAmountInvestedInFundsView
from cashflow.dashboard.views import GetFeesAmountsView
from cashflow.dashboard.views import InvestmentClubDealValuationsDashboard
from cashflow.dashboard.views import InvestorCorporateValuationsDashboard
from cashflow.dashboard.views import ValuationsFundsDashboard


urlpatterns: list = [
    path(
        "amount-raised-clubdeal",
        DashboardClubdealView.as_view(),
        name="dashboard_amounts_clubdeal",
    ),
    path(
        "amount-raised-fund",
        DashboardFundView.as_view(),
        name="dashboard_amounts_fund",
    ),
    path(
        "amount-raised-corporate",
        DashboardCorporateView.as_view(),
        name="dashboard_amounts_corporate",
    ),
    path(
        "amount-invested",
        GetAmountInvestedInFundsView.as_view(),
        name="dashboard-amount-invested",
    ),
    path(
        "fees-amount",
        GetFeesAmountsView.as_view(),
        name="dashboard-fees-amount",
    ),
    path(
        "fund-valuations",
        ValuationsFundsDashboard.as_view(),
        name="dashboard_fund_valuations",
    ),
    path(
        "corporate-valuations",
        InvestorCorporateValuationsDashboard.as_view(),
        name="dashboard_corporate_valuations",
    ),
    path(
        "clubdeal-valuations",
        InvestmentClubDealValuationsDashboard.as_view(),
        name="dashboard-clubdeal-valuations",
    ),
]

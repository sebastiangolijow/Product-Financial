from django.conf import settings


def calculate_membership_fees(investment: "Investment", *args, **kwargs):
    investor: "Investor" = investment.investor
    total_fees = 0
    total_fees += settings.MEMBERSHIP_FEES["COMMUNITY"] if investor.community_fee else 0
    total_fees += (
        settings.MEMBERSHIP_FEES["ADVANCED_INVESTMENT"]
        if investor.advanced_investment_fee
        else 0
    )
    return total_fees, 0

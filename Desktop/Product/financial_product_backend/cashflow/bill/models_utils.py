from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from cashflow.bill.fees.rhapsody_fees import calculate_rhapsody_fees
from cashflow.bill.fees.upfront_fees import calculate_upfront_fees
from core_management.exceptions import BadRequest
from core_management.models import PayIn
from core_management.utils import format_float


class BillUtils(models.Model):
    class Meta:
        abstract = True

    def _format_upfront_fees_invoice_params(self, payin: dict):
        if self.investment:
            invoice = {}
            subscription = {}
            fees = {}
            conversion_rate = 1
            today_date = timezone.now()

            invest_date = self.investment.get_invest_date()
            address = self.investment.investor.kyc.get_full_address()
            fees["stotal"], acceleration_percentage = calculate_upfront_fees(
                self.investment, invested_amount=self.amount_due
            )

            # Fixed to 0.9, might be improved in the future to conversion rate fixed to the investment date
            if self.investment.fundraising.currency.name == "USD":
                conversion_rate = 0.9

            invoice["tax"] = "0"
            fees["tax"] = 0

            # Rounding values to normal
            fees["total"] = format_float(fees["tax"] + fees["stotal"])
            fees["tax"] = format_float(fees["tax"])
            fees["stotal"] = format_float(fees["stotal"])

            invoice["num"] = self.invoice_number
            subscription["invoice_date"] = today_date.strftime("%d/%m/%Y")
            due_date = today_date
            subscription["due_date"] = due_date.strftime("%d/%m/%Y")

            invoice_context = {
                "payin": payin,
                "investor": self.investment.investor,
                "investment": self.investment,
                "conversion_rate": conversion_rate,
                "company": self.investment.investor.name,
                "invoice": invoice,
                "fees": fees,
                "email": self.investment.investor.kyc.email,
                "address": address,
                "subscription": subscription,
                "current_year": str(today_date.year),
                "year": str(invest_date.year),
                "month": invest_date.strftime("%m"),
                "fundraising": self.investment.fundraising.name,
                "wallet": self.investment.wallet,
            }
            return invoice_context
        raise BadRequest(
            "A Bill to be formatted for a CashCall upfront fees must be related to an Investment"
        )

    def _format_rhapsody_fees_invoice_params(self, payin: dict):
        if self.investment:
            invoice = {}
            subscription = {}
            fees = {}
            today_date = timezone.now()
            acceleration_percentage = 0.045

            invest_date = self.investment.get_invest_date()
            address = self.investment.investor.kyc.get_full_address()
            (fees["stotal"], acceleration_percentage,) = calculate_rhapsody_fees(
                self.investment, invested_amount=self.amount_due
            )
            invoice["tax"] = "0"
            fees["tax"] = 0
            # Rounding values to normal
            fees["total"] = format_float(fees["tax"] + fees["stotal"])
            fees["tax"] = format_float(fees["tax"])
            fees["stotal"] = format_float(fees["stotal"])

            invoice["num"] = self.invoice_number
            subscription["invoice_date"] = today_date.strftime("%d/%m/%Y")
            due_date = today_date
            subscription["due_date"] = due_date.strftime("%d/%m/%Y")

            invoice_context = {
                "payin": payin,
                "investor": self.investment.investor,
                "investment": self.investment,
                "company": self.investment.investor.name,
                "acceleration_percentage": round(acceleration_percentage, 2),
                "invoice": invoice,
                "fees": fees,
                "email": self.investment.investor.kyc.email,
                "address": address,
                "subscription": subscription,
                "current_year": str(today_date.year),
                "year": str(invest_date.year),
                "month": invest_date.strftime("%m"),
                "fundraising": self.investment.fundraising.name,
                "wallet": self.investment.wallet,
            }
            return invoice_context
        raise BadRequest(
            "A Bill to be formatted for a CashCall Rhapsody 1 fees must be related to an Investment"
        )

    def _format_membership_fees_invoice_params(self, payin: dict):
        subscription = {}
        invoice = {}
        fees = {}
        fees["stotal"] = 0
        today_date = timezone.now()
        address = self.investor.kyc.get_full_address()
        fees["advanced"] = self.investor.calculate_advanced_investment_fee_amount()
        fees["stotal"] += fees["advanced"]
        if self.investor.community_fee:
            invoice["tax"] = "20"
            fees["tax"] = (PayIn.FEES["COMMUNITY_PRE_VAT"] * 20) / 100
            fees["stotal"] += PayIn.FEES["COMMUNITY_PRE_VAT"]
            fees["community"] = format_float(PayIn.FEES["COMMUNITY_PRE_VAT"])
        else:
            fees["community"] = 0
            invoice["tax"] = "0"
            fees["tax"] = 0
        fees["total"] = format_float(round(fees["tax"] + fees["stotal"], 0))
        fees["tax"] = format_float(fees["tax"])
        fees["stotal"] = format_float(fees["stotal"])
        subscription["invoice_date"] = today_date.strftime("%d/%m/%Y")
        due_date = today_date + timedelta(days=30)
        subscription["due_date"] = due_date.strftime("%d/%m/%Y")
        invoice["num"] = self.invoice_number_deprecated
        invoice_context = {
            "payin": payin,
            "address": address,
            "company": self.investor.name,
            "contact": self.investor.kyc.first_name + " " + self.investor.kyc.last_name,
            "invoice": invoice,
            "fees": fees,
            "subscription": subscription,
            "current_year": str(today_date.year),
            "email": self.investor.kyc.email,
        }
        return invoice_context


def save_abstract(self, *args, **kwargs):
    # Generation of the invoice number if not present
    current_year = timezone.now().year
    if not self.invoice_number_deprecated and self.type:
        if self.type == "membership_fees":
            self.invoice_number_deprecated = (
                str(current_year)
                + "_MF_"
                + ("0000000" + str(self.get_next_mf_number()))[-7:]
            )
        if self.type == "upfront_fees":
            self.invoice_number_deprecated = (
                str(current_year)
                + "_UF_"
                + ("0000000" + str(self.get_next_uf_number()))[-7:]
            )
        if self.type == "management_fees":
            self.invoice_number_deprecated = (
                str(current_year)
                + "_OF_"
                + ("0000000" + str(self.get_next_of_number()))[-7:]
            )
        if self.type == "rhapsody_fees":
            self.invoice_number_deprecated = (
                str(current_year)
                + "_RF_"
                + ("0000000" + str(self.get_next_rf_number()))[-7:]
            )
        if self.type == "credit_notes":
            self.invoice_number_deprecated = (
                str(current_year)
                + "_CN_"
                + ("0000000" + str(self.get_next_cn_number()))[-7:]
            )
    return self

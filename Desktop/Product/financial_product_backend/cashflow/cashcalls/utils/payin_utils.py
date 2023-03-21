from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from api_mangopay.mangopay_ms_sdk import Money
from api_mangopay.utils.request_utils import MangoPayUtils
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.models import Bill
from cashflow.cashcalls.choices import CashCallStatus
from core_management.models import Currency


@dataclass
class PayInRequest:

    debited_funds: Money
    tag: str
    fees: Money
    credited_wallet: int
    author_legal: int = None  # author_natural
    credited_user_legal: int = None
    author_natural: int = None
    credited_user_natural: int = None

    @staticmethod
    def create_debited_funds(currency, amount):
        return Money.create(currency=currency.name, amount=amount)

    @staticmethod
    def format_tag(cashcall) -> str:
        bill: "Bill" = cashcall.bill
        if bill.investment:
            return (
                "Cash Call Pay In - "
                + bill.investment.fundraising.name
                + " - "
                + bill.get_investor().name
            )
        elif bill.type == BillTypeChoices.management_fees.name:
            return (
                "Cash call Pay In - Management fees "
                + str(date.today().year)
                + " - "
                + bill.get_investor().name
            )

        return (
            "Cash call Pay In - Membership fees "
            + str(date.today().year)
            + " - "
            + bill.get_investor().name
        )

    @staticmethod
    def get_investor_wallet_mangopay_id(
        investor: "Investor", currency: Currency
    ) -> int:
        return (
            investor.wallet_set.filter(
                currency=currency, mangopay_relation_id__isnull=False
            )
            .first()
            .mangopay_relation.id_mangopay
        )

    @classmethod
    def create_from_cashcall(cls, cashcall: "CashCall") -> "PayInRequest":
        bill: "Bill" = cashcall.bill
        investor: "Investor" = cashcall.bill.get_investor()
        kyc: "KYC" = investor.kyc
        # currency: "Currency" = bill.investment.fundraising.currency
        currency = Currency.objects.get(name="EUR")
        data = {
            f"author_{kyc.type}": investor.mangopay_relation.id_mangopay,
            f"credited_user_{kyc.type}": investor.mangopay_relation.id_mangopay,
            "tag": cls.format_tag(cashcall),
            "debited_funds": Money.create(
                amount=cashcall.committed_amount, currency=currency.name
            ),
            "fees": Money.create(amount=cashcall.fees_amount, currency=currency.name),
            "credited_wallet": cls.get_investor_wallet_mangopay_id(investor, currency),
        }
        bill = Bill.objects.get(id=cashcall.bill_id)
        if bill.type in [
            BillTypeChoices.rhapsody_fees.name,
            BillTypeChoices.management_fees.name,
        ]:
            data["debited_funds"] = Money.create(
                amount=cashcall.fees_amount, currency=currency.name
            )
            data["fees"] = Money.create(amount=Decimal(0), currency=currency.name)
        return cls(**data)

    def get_payload(self):
        return self.__dict__

    def send(self):
        return MangoPayUtils.post("payin/", self.get_payload(), return_id_only=False)

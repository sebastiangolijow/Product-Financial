import logging
from decimal import Decimal
from typing import Optional

from django.db import models
from django.db import transaction
from django_fsm import RETURN_VALUE
from django_fsm import FSMField
from django_fsm import transition
from jsonfield import JSONField
from simple_history.models import HistoricalRecords

from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.choices import BillTypeChoices
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.utils.models_utils import CashCallUtils
from cashflow.cashcalls.utils.payin_utils import PayInRequest
from core_management.models import Currency


class CashcallStateManagement(models.Model):
    status = FSMField(default="created")

    class Meta:
        abstract = True

    @transition(
        field=status,
        source=[
            CashCallStatus.CREATED.value,
            CashCallStatus.FAILED.value,
            CashCallStatus.PENDING.value,
        ],
        target=CashCallStatus.PENDING.value,
    )
    def set_pending_status(self):
        self.bill.set_pending_status()
        self.bill.save()

    @transition(
        field=status,
        source=[
            CashCallStatus.CREATED.value,
            CashCallStatus.FAILED.value,
            CashCallStatus.PENDING.value,
        ],
        target=CashCallStatus.FAILED.value,
    )
    def set_failed_status(self):
        self.bill.set_failed_status()
        self.bill.save()

    @transition(
        field=status,
        source=["*"],
        target=CashCallStatus.PAID.value,
    )
    def set_succeed_status(self):
        with transaction.atomic():
            self.bill.add_cashcall_payment(self)
            self.bill.save()

    def can_publish_payin(self, return_reason=False) -> bool:

        try:
            assert (
                self.mangopay_payin_id is None
            ), "There is already Mangopay Payin Related"
            assert self.bill, "No related bill"
            assert (
                self.bill.status != BillStatusChoices.PAID.value
            ), " You Can't cashcall paid bill "
            if self.bill.type != BillTypeChoices.management_fees.name:
                investment: "Investment" = self.bill.investment
                assert investment, "No related Investment"
                assert (
                    investment.subscription_agreement_signed_date
                    or investment.creation_datetime
                ), "Investment does not have any SA signed date nor creation date "
                currency = self.bill.investment.fundraising.currency
            else:
                currency = Currency.objects.get(name="EUR")
            assert (
                self.committed_amount or self.fees_amount
            ), "There is no amount in the cashcall"
            investor: "Investor" = self.bill.get_investor()
            assert investor, "No investor related to the cashcall bill"
            assert investor.get_owner_user(), "Investor has not related user"
            assert (
                investor.kyc is not None
            ), "No investor kyc related to the cashcall bill"
            assert (
                investor.kyc.mangopay_relation
            ), f"Investor KYC has no mangopay relation"

            wallet = investor.wallet_set.filter(
                currency=currency, mangopay_relation_id__isnull=False
            ).first()
            assert wallet, "Cashcall can't get investor wallet"
            assert (
                wallet.mangopay_relation.id_mangopay
            ), "Investor Wallet has no mangopayrelation"
            assert (
                investor.mangopay_relation.id_mangopay
            ), "Investor has no mangopay relation"
            if return_reason:
                return True, ""
            return True

        except Exception as e:
            message = f"Cannot create a Payin for Cashcall {self.id} reason: {e}"
            logging.info(message)
            if return_reason:
                return False, message
            return False

    @transition(
        field=status,
        source=[CashCallStatus.CREATED.value, CashCallStatus.FAILED.value],
        target=RETURN_VALUE(CashCallStatus.PENDING.value, CashCallStatus.FAILED.value),
        on_error=CashCallStatus.FAILED.value,
        conditions=[can_publish_payin],
    )
    def publish_payin(self):
        with transaction.atomic():

            payin_request: PayInRequest = PayInRequest.create_from_cashcall(self)
            payin: Optional[dict] = payin_request.send()
            if not payin:
                return CashCallStatus.FAILED.value
            self.mangopay_payin_id: int = payin["id"]
            self.response: dict = payin
            #
            if self.bill.type == "membership_fees":
                investor: "Investor" = self.bill.get_investor()
                investor.status = "on_trial"
                investor.save()
            return CashCallStatus.PENDING.value

    def generate_bill_pdf(self):
        if self.status == CashCallStatus.PENDING.value and not self.bill.file:
            try:
                self.bill.generate(self.response, self.bill.year)
                self.bill.set_sendinblue_template_id()
                self.bill.set_pending_status()
                self.bill.save()
            except Exception as e:
                logging.error(
                    f"We cannot generate bill pdf for bill id {self.bill.id}: {e}"
                )

    def _set_cashcall_amounts(self: "CashCall") -> None:
        is_cashcalled: bool = self.status in [
            CashCallStatus.PENDING.value,
            CashCallStatus.PAID.value,
        ]
        if self.bill and not is_cashcalled:
            self.committed_amount = self.bill.amount_due
            self.fees_amount = self.bill.fees_amount_due


# Create your models here.
class CashCall(CashCallUtils, CashcallStateManagement, models.Model):
    committed_amount = models.DecimalField(
        blank=True, null=True, decimal_places=2, max_digits=19, default=Decimal("0.00")
    )
    fees_amount = models.DecimalField(
        blank=True, null=True, decimal_places=2, max_digits=19, default=Decimal("0.00")
    )

    last_sent = models.DateTimeField(null=True, blank=True, verbose_name="Last sent")

    response = JSONField()
    log = HistoricalRecords(related_name="history")
    bill = models.ForeignKey(
        "bill.Bill",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cashcalls",
    )

    mangopay_payin_id = models.IntegerField(null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs) -> None:
        self._set_cashcall_amounts()

        return super().save(*args, **kwargs)

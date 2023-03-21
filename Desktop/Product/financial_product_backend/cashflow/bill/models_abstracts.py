import os
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django_fsm import RETURN_VALUE
from django_fsm import FSMField
from django_fsm import transition

from cashflow.bill.choices import BillNumberChoices
from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.models_utils import save_abstract
from cashflow.bill.utils import generate_bill_number
from cashflow.cashcalls.choices import CashCallStatus
from core_auth.choices import PreferredLanguageChoices
from core_auth.models import CustomUser
from entities.investor.models.models import Investor
from ort_files.documentbuilder.utils.utils_file import convert_to_pdf
from ort_files.general.utils.filefield_utils import get_fees_invoice_template
from ort_files.general.utils.filefield_utils import get_file
from ort_files.general.utils.s3_utils import get_s3_presigned_url
from ort_files.general.utils.s3_utils import save_to_s3


class BillAbstract(models.Model):
    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"
        abstract = True

    def update_investor_trail(self):
        current_year = datetime.now().year
        is_membership_fees_bill = self.type == "membership_fees"
        is_for_current_year = self.year == current_year
        if is_membership_fees_bill and is_for_current_year:
            if self.investor.trial_period:
                self.investor.trial_period.status = "pending_payment"
                self.investor.trial_period.save()

    def update_fees_amount(self):
        if not (
            self.investment and self.amount_due and self.investment.fees_percentage
        ):
            return
        fees, _ = self.calculate_fees()
        if self.type != "management_fees":
            self.fees_amount_due = fees
        if fees < 0:
            self.type = "credit_notes"

    def save(self, *args, **kwargs):
        self = save_abstract(self, *args, **kwargs)
        super(BillAbstract, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id)

    def get_next_mf_number(self):
        return self.__class__.objects.filter(type="membership_fees").count() + 1

    def get_next_uf_number(self):
        return self.__class__.objects.filter(type="upfront_fees").count() + 1

    def get_next_cn_number(self):
        return self.__class__.objects.filter(type="credit_notes").count() + 1

    def get_next_of_number(self):
        return self.__class__.objects.filter(type="management_fees").count() + 1

    def get_next_rf_number(self):
        return self.__class__.objects.filter(type="rhapsody_fees").count() + 1

    def get_next_number(self, fee_type, year):
        number = self.__class__.objects.filter(
            type=fee_type, year=year, invoice_number__isnull=False
        ).count()
        return number


class BillInvoiceManagment(models.Model):
    class Meta:
        abstract = True

    def generate(self, payin: dict, year: int) -> None:
        language = "EN"
        year = year if year else date.today().year
        if self.type != BillTypeChoices.management_fees.name:
            language = self.get_owner_language()
        if self.type == BillTypeChoices.rhapsody_fees.name:
            language = "EN"
        generate_bill_number(self, year)
        bill_file = self.generate_bill_pdf(language, payin)
        self.save_invoice(bill_file)

    def get_owner_language(self) -> PreferredLanguageChoices:
        user: CustomUser = self.get_investor().get_owner_user()
        if user and user.settings and user.settings.preferred_language:
            return user.settings.preferred_language
        return "EN"

    def get_investor_name(self) -> str:
        return self.get_investor().name.replace(" ", "_")

    def generate_bill_pdf(self, language: str, payin: dict) -> str:
        investor: Investor = self.get_investor()
        doc = get_fees_invoice_template(investor, self, language)
        context = self.format_invoice(payin)
        doc.render(context)
        input_file_name = f"generated_invoice_bill_{self.id}.docx"
        doc.save(input_file_name)
        return input_file_name

    def save_invoice(self, input_file_name) -> None:
        investor_name: str = self.get_investor_name()
        output_file_name_path = f"tmp/Invoice_{investor_name}_{self.id}.docx"
        output_pdf_file_name = f"Invoice_{investor_name}_{self.id}.pdf"
        output_pdf_file_name_s3_absolute_path = f"tmp/{output_pdf_file_name}"

        save_to_s3(input_file_name, output_file_name_path)
        convert_to_pdf(output_file_name_path, output_pdf_file_name_s3_absolute_path)
        presigned_url = get_s3_presigned_url(output_pdf_file_name_s3_absolute_path)
        file_content = get_file(presigned_url)
        self.file.save(name=output_pdf_file_name, content=file_content)
        os.remove(input_file_name)

    def generate_bill_number(self) -> None:
        if not self.invoice_number and self.type:
            current_year = timezone.now().year
            type = BillNumberChoices.get_value(self.type)
            number_ = str(self.get_next_number(self.type, current_year)).zfill(7)
            self.invoice_number = f"{current_year}_{type}_{number_}"
            self.save(update_fields=["invoice_number"])


class BillStateManagement(models.Model):
    class Meta:
        abstract = True

    @staticmethod
    def can_update_cashcall(related_cashcall: "CashCall"):
        return bool(
            related_cashcall
            and related_cashcall.status
            in [
                CashCallStatus.CREATED.value,
                CashCallStatus.FAILED.value,
            ]
        )

    def update_related_cashcall_amounts(self, related_cashcall):
        related_cashcall.committed_amount = self.amount_due
        related_cashcall.fees_amount = self.fees_amount_due
        related_cashcall.save()

    def check_status(self) -> BillStatusChoices:
        if not self.cachcalls.objects.count():
            return BillStatusChoices.CREATED.value

        paid_amount, paid_fees = (
            self.cashcalls.filter(status=CashCallStatus.PAID.value)
            .aggregate(paid_amount=Sum("amount"), paid_fees=Sum("fees_amount"))
            .values()
        )
        pending_cashcalls = self.cashcalls.filter(status="CREATED")

        if not (paid_amount or paid_fees):
            return (
                BillStatusChoices.PENDING.value
                if pending_cashcalls
                else BillStatusChoices.FAILED.value
            )

        if (paid_amount, paid_fees) == (self.amount, self.fees_amount):
            return BillStatusChoices.PAID.value

        return BillStatusChoices.PAID_INCORRECTLY

    status = FSMField(
        default=BillStatusChoices.CREATED.value,
        protected=False,
        choices=BillStatusChoices.choices(),
    )

    @transition(
        field=status,
        source=[
            BillStatusChoices.CREATED.value,
            BillStatusChoices.FAILED.value,
            BillStatusChoices.PENDING.value,
        ],
        target=BillStatusChoices.PENDING.value,
    )
    def set_pending_status(self):
        self.investment.set_cashcalled_status()
        self.investment.save()

    @transition(
        field=status,
        source=[
            BillStatusChoices.CREATED.value,
            BillStatusChoices.FAILED.value,
            BillStatusChoices.PENDING.value,
            BillStatusChoices.PAID_INCORRECTLY.value,
        ],
        target=BillStatusChoices.FAILED.value,
    )
    def set_failed_status(self):
        if self.type != "management_fees":
            self.investment.set_payment_failed_status()
            self.investment.save()

    @transition(
        field=status,
        source="*",
        target=RETURN_VALUE(
            BillStatusChoices.PAID.value, BillStatusChoices.PAID_INCORRECTLY.value
        ),
    )
    def add_cashcall_payment(
        self, cashcall: "CashCall"
    ) -> BillStatusChoices.PAID.value or BillStatusChoices.PAID_INCORRECTLY.value:
        assert self == cashcall.bill, f"Bill {self.id} should be paid be {cashcall.id}"
        # assert (
        #     cashcall.status == CashCallStatus.PAID.value
        # ), f"Bill {self.id} should be paid by a successfull payment {cashcall.id}"

        self.investment.set_transferred_status()
        self.investment.save()
        if (self.amount_due, self.fees_amount_due) == (
            cashcall.committed_amount,
            cashcall.fees_amount,
        ):
            return BillStatusChoices.PAID.value

        else:
            return BillStatusChoices.PAID_INCORRECTLY.value

    @property
    def amount_paid(self) -> Decimal:
        if not self.cashcalls:
            return Decimal("0.00")
        return self.cashcalls.filter(status=CashCallStatus.PAID.value).aggregate(
            amount=Sum("committed_amount") or Decimal("0.00")
        )["amount"]

    @property
    def fees_amount_paid(self) -> Decimal:
        if not self.cashcalls:
            return Decimal("0.00")
        return self.cashcalls.filter(status=CashCallStatus.PAID.value).aggregate(
            fees_amount=Sum("fees_amount")
        )["fees_amount"]

    def can_update(self, update_fields: list = []):
        if not self.pk:
            return True
        if update_fields == ["last_sent"]:
            return True

        old_instance = self.__class__.objects.get(pk=self.pk)
        return old_instance.status not in [
            BillStatusChoices.PAID.value,
            BillStatusChoices.PAID_INCORRECTLY.value,
        ]

    @property
    def is_cash_call_sent(self) -> bool:
        return self.status in [
            BillStatusChoices.PENDING.value,
            BillStatusChoices.PAID.value,
            BillStatusChoices.PAID_INCORRECTLY.value,
        ]

    @property
    def has_cash_call(self):
        cash_call: Optional["CashCall"] = self.cashcalls.last()
        return cash_call is not None

import os
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Any
from typing import Callable
from typing import Tuple

import arrow
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django_fsm import RETURN_VALUE
from django_fsm import FSMField
from django_fsm import transition
from simple_history.models import HistoricalRecords

from cashflow.bill.choices import BillTypeChoices
from cashflow.bill.choices import BillYearChoices
from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.bill.fees.membership_fees import calculate_membership_fees
from cashflow.bill.fees.rhapsody_fees import calculate_rhapsody_fees
from cashflow.bill.fees.upfront_fees import calculate_upfront_fees
from cashflow.bill.models_abstracts import BillAbstract
from cashflow.bill.models_abstracts import BillInvoiceManagment
from cashflow.bill.models_abstracts import BillStateManagement
from cashflow.bill.utils import generate_bill_template
from cashflow.bill.utils import get_document_context
from cashflow.bill.utils import get_output_path
from core_auth.choices import PreferredLanguageChoices
from core_management.models import CoreModel
from core_management.models import PlatformRelation
from ort_files.documentbuilder.utils.utils_file import convert_to_pdf
from ort_files.general.utils.filefield_utils import get_file
from ort_files.general.utils.s3_utils import get_s3_presigned_url
from ort_files.general.utils.s3_utils import save_to_s3
from utilities.exceptions import ForbiddenUpdateError

from .models_utils import BillUtils


def bill_upload_to(instance, filename):
    return "v2/bills/%s/%s" % (instance.id, filename)


class Bill(
    BillAbstract, BillStateManagement, BillInvoiceManagment, BillUtils, CoreModel
):
    platform_relation = models.OneToOneField(
        PlatformRelation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Platform relation",
    )
    updated_at = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name="Updated at"
    )
    updated_by = models.ForeignKey(
        "core_auth.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bills_updated",
        verbose_name="Updated by",
    )
    type = models.CharField(
        max_length=140,
        null=True,
        blank=True,
        choices=BillTypeChoices.choices(),
        default="upfront_fees",
        verbose_name="Bill type",
    )

    year = models.IntegerField(
        null=True,
        blank=True,
        choices=BillYearChoices,
        default=datetime.now().year,
        verbose_name=_("Issuing year"),
    )
    invoice_number_deprecated = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Invoice number Deprecated"
    )

    invoice_number = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Invoice number"
    )
    investor_name = models.CharField(max_length=255, blank=True, null=True)
    cc_emails = models.TextField(blank=True, null=True)
    sendinblue_template_id = models.IntegerField(blank=False, null=True)
    last_sent = models.DateTimeField(null=True, blank=True, verbose_name="Last sent")
    # File fields
    file = models.FileField(
        null=True, blank=True, upload_to=bill_upload_to, verbose_name=_("Issuing file")
    )

    # # Relations
    investment = models.ForeignKey(
        "investment.Investment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bills",
        verbose_name="Investment",
    )
    investor = models.ForeignKey(
        "investor.Investor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bills",
        verbose_name="Investor",
    )

    amount_due = models.DecimalField(
        max_digits=19,
        null=True,
        blank=True,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Amount due"),
    )
    fees_amount_due = models.DecimalField(
        max_digits=19,
        null=True,
        blank=True,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Fees Amount Due"),
    )

    log = HistoricalRecords(related_name="history")

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"

    def save(self, *args, **kwargs):
        if not self.can_update(kwargs.get("update_fields", [])):
            raise ForbiddenUpdateError(f"Cannot Update {self.status} bill ")
        if self.type != BillTypeChoices.rhapsody_fees.name:
            self.update_fees_amount()
        self.update_investor_trail()
        super(Bill, self).save(*args, **kwargs)

    def get_cash_call(self) -> "CashCall":
        return self.cashcalls.last()

    def get_investor(self):
        return self.investment.investor if self.investment else self.investor

    def get_payin(self):
        return getattr(self, "payin", None)

    def get_fundraising(self):
        return self.investment.fundraising if self.investment else None

    def get_owner_email(self):
        investor = (
            self.investor
            if self.investor
            else self.investment.investor
            if self.investment
            else None
        )
        if investor:
            owner = investor.get_owner_user()
            return owner.email if owner else None
        return None

    def format_invoice(self, payin: dict):
        formatter_function_by_type: dict = {
            "management_fees": partial(get_document_context, self),
            "upfront_fees": self._format_upfront_fees_invoice_params,
            "credit_notes": self._format_upfront_fees_invoice_params,
            "rhapsody_fees": self._format_rhapsody_fees_invoice_params,
            "membership_fees": self._format_membership_fees_invoice_params,
        }
        formatter_function: Callable = formatter_function_by_type[self.type]
        return formatter_function(payin)

    def get_fee_function_by_type(self):
        bill_type = self.type
        fees_functions = {
            BillTypeChoices.upfront_fees.name: calculate_upfront_fees,
            BillTypeChoices.management_fees.name: calculate_management_fees,
            BillTypeChoices.rhapsody_fees.name: calculate_rhapsody_fees,
            BillTypeChoices.membership_fees.name: calculate_membership_fees,
        }
        return fees_functions.get(bill_type)

    def calculate_fees(self) -> Tuple[Decimal, Decimal]:
        fee_function = self.get_fee_function_by_type()
        return fee_function(self.investment, invested_amount=self.amount_due)

    def create_bill_file(self, payin: dict):
        if self.type == "management_fees":
            if self.file:
                self.file.delete()
            self.set_sendinblue_template_id()
            current_path, file = generate_bill_template(self, payin)
            output_path = get_output_path("docx", self)
            pdf_output_path = get_output_path("pdf", self)
            save_to_s3(current_path, output_path)
            convert_to_pdf(output_path, pdf_output_path)
            presigned_url = get_s3_presigned_url(pdf_output_path)
            file_content = get_file(presigned_url)
            self.file.save(name=pdf_output_path, content=file_content)
            os.remove(current_path)
        return self.file

    def set_sendinblue_template_id(self) -> None:
        preferred_language: PreferredLanguageChoices = self.get_owner_language()
        self.sendinblue_template_id = settings.SENDINBLUE_TEMPLATES_IDS[self.type][
            preferred_language
        ]
        self.save()

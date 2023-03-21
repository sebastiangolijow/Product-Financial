import os
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core_management.exceptions import BadRequest
from core_management.utils import format_float
from core_management.utils import get_email_recipient
from services.email.sendinblue_mail import SendInBlueMail


class CashCallUtils(models.Model):
    class Meta:
        abstract = True

    def format_email(self, payin: dict):
        params = {
            "user_name": self.bill.investor_name or "investor",
            "total_committed_amount": format_float(self.committed_amount),
            "total_fees_amount": format_float(self.fees_amount),
            "transferred_amount": format_float(
                self.committed_amount + self.fees_amount
            ),
            "wire_reference": self.response.get("wire_reference"),
        }
        bill = self.bill
        if bill and bill.type == "management_fees":
            params["investments"] = []
            total_fees = 0
            total_fees = (bill.investment.committed_amount * 2) / 100
            if bill.investment.fundraising.currency.name == "USD":
                total_fees = (total_fees * 90) / 100
            params["investments"].append(
                {
                    "fundraising_name": bill.investment.fundraising.name,
                    "committed_amount": format_float(bill.investment.committed_amount),
                    "total_fees": format_float(total_fees),
                }
            )
        if bill and bill.type == "upfront_fees":
            params["startup_name"] = bill.investment.fundraising.startup.name
        if bill and bill.type == "membership_fees":
            end_date = timezone.now() + timedelta(days=30)
            params["end_date"] = end_date.strftime("%d/%m/%Y")
            if bill.investor.is_distributed():
                params["membership_type"] = "advanced_investment_distributor"
                params["distributor_name"] = bill.investor.distributor.name
            elif (
                bill.investor.advanced_investment_fee
                and not bill.investor.community_fee
            ):
                params["membership_type"] = "advanced_investment_only"
            elif (
                bill.investor.community_fee
                and not bill.investor.advanced_investment_fee
            ):
                params["membership_type"] = "community_only"
            else:
                params["membership_type"] = "full_membership"
        attachments = self.generate_attachments(payin)
        return params, attachments

    def generate_attachments(self, payin: dict):
        attachments = []
        bill: "Bill" = self.bill
        if bill.type == "management_fees":
            bill.create_bill_file(payin)
        attachment = {
            "url": str(bill.file.url),
            "name": os.path.basename(bill.file.name),
        }
        attachments.append(attachment)
        return attachments

    def send_email(self, payin: dict):
        user = self.bill.investor.get_owner_user()
        if not user:
            raise BadRequest("The related Investor does not have a valid owner user.")

        if not self.response.get("wire_reference"):
            raise BadRequest(
                "The wire reference has not been generated yet. You can retry in a few minutes."
            )

        sender = SendInBlueMail()
        to = [
            {
                "email": get_email_recipient(user.email)[0],
                "name": user.contact_info.first_name,
            }
        ]
        cc = []
        if settings.PROD_SETTINGS:
            cc = [
                {"email": "stephanie@oneragtime.com", "name": "Stephanie"},
                {"email": "myriam@oneragtime.com", "name": "Myriam"},
            ]
        if self.bill.cc_emails:
            for email in self.bill.cc_emails.split(","):
                email = email.replace("[", "").replace("]", "").replace('"', "")
                email_object = {"email": get_email_recipient(email)[0]}
                if email_object not in cc:
                    cc.append(email_object)
        bcc = []
        params, attachments = self.format_email(payin)
        template_name = ""  # TODO missing template name, breaks here
        template_id = (
            self.bill.sendinblue_template_id
            if self.bill.sendinblue_template_id
            else 364
        )
        response = sender.send(
            to, template_name, params, attachments, cc, bcc, template_id=template_id
        )
        if response.status_code in [200, 201]:
            current_date = timezone.now()
            self.__class__.objects.filter(id=self.id).update(last_sent=current_date)
            self.bill.last_sent = current_date
            self.bill.save(update_fields=["last_sent"])
        else:
            raise Exception(
                "There was an error when sending the email through SendInBlue"
            )

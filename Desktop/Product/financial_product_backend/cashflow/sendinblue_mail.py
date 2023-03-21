import json
import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class SendInBlueMail(object):
    """
    Send email template via sendinblue
    """

    template_names = {
        "platform_invitation_investors_fr": 70,
        "platform_invitation_investors_eng": 38,
        "platform_invitation_partners_eng": 99,
        "platform_invitation_partners_fr": 131,
        "platform_invitation_startup_eng": 306,
        "platform_invitation_startup_fr": 305,
        "platform_re_invitation_eng": 301,
        "platform_re_invitation_fr": 302,
        "platform_invitation_investor_to_investor_fr": 200,
        "platform_invitation_investor_to_investor_eng": 199,
        "platform_reset_password_eng": 236,
        "platform_reset_password_fr": 237,
        "user_already_has_account_en": 282,
        "user_already_has_account_fr": 283,
        "platform_confirmation_email_en": 289,
        "user_requested_membership_investor_en": 495,
        "user_requested_membership_team_en": 494,
        "investment_subscription_rhapsody-ii_fr": 479,
        "investment_subscription_rhapsody-ii_en": 478,
        "investment_subscription_paragon_en": 481,
        "investment_subscription_paragon_fr": 480,
        "investment_subscription_generic_en": 61,
        "investment_subscription_generic_fr": 75,
        "investment_request_deep_analysis": 489,
        "new_reporting_clubdeal_en": 63,
        "new_reporting_clubdeal_fr": 76,
        "new_reporting_fund_en": 556,
        "new_reporting_fund_fr": 555,
        "cash_call_emails_management_fees": 507,
        "kyc_status_update": 515,
        "kyc_submission": 514,
        "investment_creation": 513,
        "investor_creation": 512,
        "startup_creation": 511,
        "user_activation": 510,
        "rhapsody_management_fees": 553,
        "partner_requested_a_call": 549,
    }

    def send(
        self,
        to: list,
        template_name: str,
        params: dict = {},
        attachment: list = [],
        cc: list = [],
        bcc: list = [],
        template_id: int = 0,
    ) -> requests.Response:
        """
        Required args:
            to: list of addresses, example
                [{'email': 'user@fake.com', 'name': 'User Name'}]
            template_name: as defined in the template_names dict
        Optional kwargs:
            params: template config & variables
            attachment: list of attachment dicts, as defined in
                https://developers.sendinblue.com/reference/sendtransacemail
                {"name":"File Name.pdf", "content":"base64content"}
                or
                {"url":"bucket_url"}
            cc: list of addresses in copy
            bcc: list of addresses in hidden copy
            template_id: overrides template id. Not recommended. Backward compatibility only.
        """
        if settings.ENVIRONMENT_NAME in ["local", "test"] or settings.TESTING_ENV:
            return requests.Response

        post_data = {
            "to": to,
            "templateId": self.__get_template_id(template_name, template_id),
            "params": params,
        }
        if cc:
            post_data["cc"] = cc
        if bcc:
            post_data["bcc"] = bcc
        if attachment:
            post_data["attachment"] = attachment
        return self.__post(post_data)

    def __get_template_id(self, template_name: str, template_id: int) -> int:
        return template_id if template_id else self.template_names[template_name]

    def __post(self, post_data: dict) -> requests.Response:
        response: requests.Response = requests.post(
            settings.SENDINBLUE_URL,
            json.dumps(post_data),
            headers={
                "Content-Type": "application/json",
                "api-key": settings.SENDINBLUE_API_TOKEN,
            },
        )
        logger.info(f"SendInBlueMail {post_data['templateId']} : {response.json()}")
        return response

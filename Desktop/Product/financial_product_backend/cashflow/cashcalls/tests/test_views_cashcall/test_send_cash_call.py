from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from django_fsm import TransitionNotAllowed

from api_mangopay.mangopay_ms_sdk import Money
from api_mangopay.tasks import set_status_payin
from api_mangopay.utils.request_utils import MangoPayUtils
from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.bill.fakers.faker_bill import BillWithFileFaker
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from core_management.factories.factory_kyc import MangoPayRelationFactory
from core_management.fakers.factory_wallet import WalletFactory
from core_management.fakers.faker_account import UserFaker
from core_management.fakers.faker_relationships import UserInvestorRelationshipFaker
from core_management.models import Currency
from core_utils.faker_currency import CurrencyFaker
from dealflow.investment.models.models_choices import InvestmentStatusChoices


@pytest.fixture(scope="class")
def cash_call(django_db_blocker):
    with django_db_blocker.unblock():

        print("\nCREATE FUNCTION FIXTURE : cash call")
        cash_call = CashCallFaker(
            committed_amount=10000,
            fees_amount=12,
        )

        yield cash_call
        print("\nTEARDOWN FUNCTION FIXTURE : cash call")
        cash_call.delete()


@pytest.mark.django_db
class TestCashCalls:
    def get_url(self, id: int) -> str:
        return reverse("cashcalls:cash_call-send", kwargs={"pk": id})

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_cashcall_send_view(
        self,
        money_create_mock,
        mp_post_mock,
        client,
        ortstaff_user,
        publishable_cashcall,
    ):
        bill, cash_call = publishable_cashcall
        bill_fake = BillWithFileFaker()
        bill.file = bill_fake.file
        bill.file.name = "example.pdf"
        bill.save()
        cash_call.bill = bill
        cash_call.committed_amount = 35000
        cash_call.save()
        money_create_mock.return_value = 12
        mp_post_mock.return_value = {
            "id": 1,
            "wire_reference": "test-wire-refrence",
            "status": "CREATED",
        }

        client.force_authenticate(user=ortstaff_user)
        url = self.get_url(cash_call.id)
        response = client.post(url)
        assert response.status_code == 200
        cash_call.refresh_from_db()
        assert cash_call.mangopay_payin_id
        assert cash_call.bill.file
        assert cash_call.status == CashCallStatus.PENDING.value
        # Secoend request
        response = client.post(url)
        assert response.status_code == 200
        assert response.data == "Cash call successfully sent to all recipients"

    def test_un_auth_endpoint(self, client, user, cash_call):

        cash_call_id = cash_call.id

        client.force_authenticate(user=user)
        response = client.post(self.get_url(cash_call_id))

        assert response.status_code == 403

    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_cashcall_send_failed_cashcall(
        self,
        money_create_mock,
        mp_post_mock,
        client,
        ortstaff_user,
        publishable_cashcall,
    ):
        bill, cash_call = publishable_cashcall
        money_create_mock.return_value = 12
        mp_post_mock.return_value = None

        client.force_authenticate(user=ortstaff_user)
        url = self.get_url(cash_call.id)
        response = client.post(url)
        assert response.status_code == 400
        cash_call.refresh_from_db()
        assert not cash_call.mangopay_payin_id
        assert not cash_call.bill.file
        assert cash_call.status == CashCallStatus.FAILED.value

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_recieve_successful_payment_from_mp_service(
        self,
        money_create_mock,
        mp_post_mock,
        publishable_cashcall,
        client,
        ortstaff_user,
    ):
        money_create_mock.return_value = 12
        mp_post_mock.return_value = {
            "id": 1,
            "wire_reference": "test-wire-refrence",
            "status": "CREATED",
        }
        bill, cash_call = publishable_cashcall

        cash_call.publish_payin()
        cash_call.save()

        success_payload = {"payin_id": 1, "payin_status": "SUCCEEDED"}

        set_status_payin(success_payload)

        cash_call.refresh_from_db()
        bill.refresh_from_db()
        assert bill.status == BillStatusChoices.PAID.value
        assert bill.investment.fsm_status == InvestmentStatusChoices.transfered.name
        assert cash_call.status == CashCallStatus.PAID.value
        client.force_authenticate(user=ortstaff_user)
        url = self.get_url(cash_call.id)
        response = client.post(url)
        assert response.status_code == 200
        assert response.data == "Cashcall Already Sent"

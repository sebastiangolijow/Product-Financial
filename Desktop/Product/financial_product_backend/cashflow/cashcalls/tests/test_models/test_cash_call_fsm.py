from unittest.mock import patch

import pytest
from django_fsm import TransitionNotAllowed

from api_mangopay.tasks import set_status_payin
from cashflow.bill.choices import BillStatusChoices
from cashflow.bill.fakers.faker_bill import BillFaker
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.fakers.fakers import CashCallFaker
from ort.models import InvestmentStatusChoices


@pytest.mark.django_db
class TestCashCallStateManagment:
    def test_we_cannot_publish_unvalid_cashcall(self):
        with pytest.raises(TransitionNotAllowed):
            cash_call = CashCallFaker()
            cash_call.publish_payin()

    def test_we_cannot_publish_paid_or_pending_cash_call(self):
        with pytest.raises(TransitionNotAllowed):
            bill = BillFaker()
            cash_call = CashCallFaker(bill=bill, status=CashCallStatus.PAID.value)
            cash_call.publish_payin()

    def test_we_cannot_publish_pending_cash_call(self):
        with pytest.raises(TransitionNotAllowed):
            bill = BillFaker()
            cash_call = CashCallFaker(bill=bill, status=CashCallStatus.PENDING.value)
            cash_call.publish_payin()

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_publishing_cachcall_payin(
        self, money_create_mock, mp_post_mock, publishable_cashcall
    ):
        money_create_mock.return_value = 12
        mp_post_mock.return_value = {
            "id": 1,
            "wire_reference": "test-wire-refrence",
            "status": "CREATED",
        }
        bill, cash_call = publishable_cashcall
        cash_call.publish_payin()

        exptected_payload = {
            "debited_funds": 12,
            "tag": f"Cash Call Pay In - {bill.investment.fundraising.name} - {bill.investor.name}",
            "fees": 12,
            "credited_wallet": 21,
            "author_legal": 20,
            "credited_user_legal": 20,
            "author_natural": None,
            "credited_user_natural": None,
        }
        url = "payin/"
        cash_call.save()
        assert cash_call.status == CashCallStatus.PENDING.value
        mp_post_mock.assert_called_once()
        mp_post_mock.assert_called_with(url, exptected_payload, return_id_only=False)

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_cashcall_is_failed_when_we_cannot_reach_mangopay(
        self, money_create_mock, mp_post_mock, publishable_cashcall
    ):
        mp_post_mock.return_value = None
        money_create_mock.return_value = 12
        bill, cash_call = publishable_cashcall

        cash_call.publish_payin()

        exptected_payload = {
            "debited_funds": 12,
            "tag": f"Cash Call Pay In - {bill.investment.fundraising.name} - {bill.investor.name}",
            "fees": 12,
            "credited_wallet": 21,
            "author_legal": 20,
            "credited_user_legal": 20,
            "author_natural": None,
            "credited_user_natural": None,
        }
        url = "payin/"
        cash_call.save()
        assert cash_call.status == CashCallStatus.FAILED.value
        mp_post_mock.assert_called_once()
        mp_post_mock.assert_called_with(url, exptected_payload, return_id_only=False)


@pytest.mark.django_db
class TestUpdatingStatusAfterPaymentsChange:
    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_recieve_successful_payment_from_mp_service(
        self, money_create_mock, mp_post_mock, publishable_cashcall
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

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_recieve_pending_payment_from_mp_service(
        self, money_create_mock, mp_post_mock, publishable_cashcall
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

        success_payload = {"payin_id": 1, "payin_status": "CRAETED"}

        set_status_payin(success_payload)

        cash_call.refresh_from_db()
        bill.refresh_from_db()
        assert bill.status == BillStatusChoices.PENDING.value
        assert bill.investment.fsm_status == InvestmentStatusChoices.cash_called.name
        assert cash_call.status == CashCallStatus.PENDING.value

    @pytest.mark.skip(reason="Fails randomly")
    @patch("api_mangopay.utils.request_utils.MangoPayUtils.post", autospec=True)
    @patch("api_mangopay.mangopay_ms_sdk.Money.create", autospec=True)
    def test_recieve_failed_payment_from_mp_service(
        self, money_create_mock, mp_post_mock, publishable_cashcall
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

        success_payload = {"payin_id": 1, "payin_status": "FAILED"}

        set_status_payin(success_payload)

        cash_call.refresh_from_db()
        bill.refresh_from_db()

        assert bill.status == BillStatusChoices.FAILED.value
        assert bill.investment.fsm_status == InvestmentStatusChoices.payment_failed.name
        assert cash_call.status == CashCallStatus.FAILED.value

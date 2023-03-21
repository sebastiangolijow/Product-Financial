from unittest import TestCase
from unittest.mock import patch

import pytest
from django.db.models import Model
from rest_framework import status

from cashflow.bill.tasks import _task_sync_with_mangopay_for_bill_status
from core_management.fakers.faker_payins import PayInFaker
from core_management.models import MangoPayRelation
from core_management.models import PayIn


@pytest.mark.django_db
class TestMocking(TestCase):
    @patch(
        "cashflow.bill.tasks._task_sync_with_mangopay_for_bill_status",
        return_value=status.HTTP_404_NOT_FOUND,
    )
    def test_task_sync_with_mangopay_for_bill_status_returns_404(
        self, task_sync_with_mangopay_for_bill_status
    ):
        self.assertEqual(
            task_sync_with_mangopay_for_bill_status(), status.HTTP_404_NOT_FOUND
        )


@pytest.mark.django_db
class MockCeleryTask(TestCase):
    @patch("cashflow.bill.tasks.return_mangopay_bill_status")
    def test_task_sync_with_mangopay_for_bill_status_return_nothing(self, test_patch):
        mangopay_rel: Model = MangoPayRelation.objects.create()
        payin: PayIn = PayInFaker(status="CREATED", mangopay_relation=mangopay_rel)
        test_patch.return_value = "SUCCEEDED"
        _task_sync_with_mangopay_for_bill_status()

        payin.refresh_from_db()
        assert payin.status == "SUCCEEDED"
        test_patch.assert_called_once()

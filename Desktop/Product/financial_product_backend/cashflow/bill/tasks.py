import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.response import Response

from api_mangopay.utils.request_utils import MangoPayUtils
from core_management.models import PayIn
from settings.celery import app


logger: logging.Logger = logging.getLogger(__name__)


@app.task()
def task_sync_with_mangopay_for_bill_status() -> Response:
    return _task_sync_with_mangopay_for_bill_status()


def _task_sync_with_mangopay_for_bill_status() -> Response:
    pending_entities: QuerySet = PayIn.objects.filter(
        Q(status="CREATED") & Q(mangopay_relation__isnull=False)
    )
    for entity in pending_entities:
        try:
            mangopay_status = return_mangopay_bill_status(entity=entity)
            entity.status: str = mangopay_status
            entity.save(update_fields=["status"])
        except ObjectDoesNotExist:
            return Response(
                {"message": "Investor not found."}, status=status.HTTP_404_NOT_FOUND
            )


def return_mangopay_bill_status(entity) -> str:

    id_mangopay: int = entity.mangopay_relation.id_mangopay
    mangopay_status: str = MangoPayUtils.get("payin/" + str(id_mangopay))["status"]
    return mangopay_status

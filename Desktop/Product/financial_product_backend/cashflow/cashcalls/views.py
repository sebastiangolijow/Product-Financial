import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from cashflow.bill.models import Bill
from cashflow.cashcalls.choices import CashCallStatus
from cashflow.cashcalls.models import CashCall
from cashflow.cashcalls.serializers import CashCallSerializer
from core_auth.permissions import IsAuthenticated
from core_auth.permissions import IsOrtStaff
from dealflow.investment.models.models import Investment


logger = logging.getLogger(__name__)


class CashCallViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CashCall entities.
    """

    queryset = CashCall.objects.all()
    serializer_class = CashCallSerializer
    permission_classes = [IsAuthenticated & IsOrtStaff]

    def create(self, request, *args, **kwargs):
        payload: dict = request.data
        bill = get_object_or_404(Bill, pk=payload["bill"])
        if bill.is_cash_call_sent:
            return Response({"status": "already_sent"}, status=status.HTTP_200_OK)

        self.update_related_bill(bill, payload)
        if bill.has_cash_call:
            return Response(
                {
                    "status": "updated",
                    "cc_emails": bill.cc_emails,
                    "investor_name": bill.investor_name,
                    "bill_id": bill.id,
                },
                status=status.HTTP_200_OK,
            )

        return super(CashCallViewSet, self).create(request, *args, **kwargs)

    @action(
        methods=["post"], detail=True, permission_classes=[IsAuthenticated & IsOrtStaff]
    )
    def send(self, request, pk=None, send_email=True, *args, **kwargs):
        """
        Endpoint that will fire the process of sending the CashCall to the chosen email recipients
        """
        cash_call: CashCall = get_object_or_404(CashCall, pk=pk)
        if not cash_call.mangopay_payin_id:
            is_valid, message = cash_call.can_publish_payin(return_reason=True)
            if not is_valid:
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            cash_call.publish_payin()
            cash_call.save()
        cash_call.generate_bill_pdf()
        if cash_call.status == CashCallStatus.FAILED.value:
            return Response(
                "Mangopay response error", status=status.HTTP_400_BAD_REQUEST
            )
        if send_email and cash_call.status == CashCallStatus.PENDING.value:
            cash_call.send_email(cash_call.response)
            return Response(
                "Cash call successfully sent to all recipients",
                status=status.HTTP_200_OK,
            )
        return Response("Cashcall Already Sent", status=status.HTTP_200_OK)

    @staticmethod
    def update_related_bill(bill: Bill, payload: dict) -> None:
        bill_model_fields: list = [
            "cc_emails",
            "investor_name",
        ]
        bill_payload: dict = {
            k: v for k, v in payload.items() if k in bill_model_fields
        }
        bill.__dict__.update(**bill_payload)
        bill.save()

    @staticmethod
    def update_related_bill(bill: Bill, payload: dict) -> None:
        bill_model_fields: list = [
            "cc_emails",
            "investor_name",
        ]
        bill_payload: dict = {
            k: v for k, v in payload.items() if k in bill_model_fields
        }
        bill.__dict__.update(**bill_payload)
        bill.save()


class CashCallCalculateAmountsApiView(GenericAPIView):
    """
    APIView to retrieve the fees amount and percentage from custom values
    """

    queryset = CashCall.objects.all()
    permission_classes = [IsAuthenticated & IsOrtStaff]

    def get_bill_amounts(self, bill, investment):
        fees_amount = 0
        percentage = 0
        calculate_fees_function = bill.get_fee_function_by_type()
        fees_amount, percentage = calculate_fees_function(
            investment, invested_amount=bill.amount_due
        )
        percentage = percentage * 100
        return fees_amount, percentage

    def get(self, request, *args, **kwargs):
        bill_id = kwargs.get("bill_id")
        bill: Bill = Bill.objects.get(id=bill_id)
        investment = bill.investment
        query_params = request.query_params.dict()

        is_amount_present = "amount" in query_params and query_params["amount"]
        are_fees_present = (
            "fees_percentage" in query_params and query_params["fees_percentage"]
        )

        committed_amount = (
            query_params["amount"] if is_amount_present else investment.committed_amount
        )
        fees_percentage = (
            query_params["fees_percentage"]
            if are_fees_present
            else investment.fees_percentage
        )

        if investment:

            investment_to_calculate = Investment(
                creation_datetime=investment.creation_datetime or timezone.now(),
                fundraising=investment.fundraising,
                committed_amount=float(committed_amount),
                fees_percentage=float(fees_percentage),
            )

            fees_amount, percentage = self.get_bill_amounts(
                bill, investment_to_calculate
            )

            return Response(
                {"fees_amount": fees_amount, "percentage": percentage},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Related investment could not be found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

from rest_framework import serializers

from cashflow.cashcalls.models import CashCall


class CashCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashCall
        fields = "__all__"
        extra_kwargs = {"cc_emails": {"required": False}}

from core_utils.choices import EnumChoicesMixin


class CashCallStatus(EnumChoicesMixin):
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"

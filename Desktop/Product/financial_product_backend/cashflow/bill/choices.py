from core_utils.choices import ChoiceCharEnum


class BillTypeChoices(ChoiceCharEnum):
    upfront_fees = "Upfront fees"
    management_fees = "Management fees"
    membership_fees = "Membership fees"
    rhapsody_fees = "Rhapsody fees"
    credit_notes = "Credit notes"


class BillStatusChoices(ChoiceCharEnum):
    CREATED = "created"
    PAID = "paid"
    PAID_INCORRECTLY = "paid_incorrectly"
    PENDING = "pending"
    FAILED = "failed"


class BillNumberChoices(ChoiceCharEnum):
    upfront_fees = "UF"
    management_fees = "OF"
    membership_fees = "MF"
    rhapsody_fees = "RF"
    credit_notes = "CN"


BillYearChoices = [
    (2013, 2013),
    (2014, 2014),
    (2015, 2015),
    (2016, 2016),
    (2017, 2017),
    (2018, 2018),
    (2019, 2019),
    (2020, 2020),
    (2021, 2021),
    (2022, 2022),
    (2023, 2023),
    (2024, 2024),
    (2025, 2025),
]

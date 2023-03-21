from datetime import datetime
from decimal import Context
from decimal import Decimal
from decimal import getcontext

from django.db.models import Model

from core_utils.choices import ChoiceCharEnum


class DefaultConversionRateFromEUR(ChoiceCharEnum):
    USD = 1.03


class ConversionRatesFromUSD(ChoiceCharEnum):
    _2016 = 1.1454
    _2017 = 1.13
    _2018 = 1.18
    _2019 = 1.12
    _2020 = 1.14
    _2021 = 1.18
    _2022 = 1.18
    _2023 = 1.06


def get_conversion_rate_from_eur(requested_currency: str) -> Decimal:
    rate_euro_to_currency = DefaultConversionRateFromEUR.get_value(requested_currency)
    return Decimal(rate_euro_to_currency, Context(prec=2))


def convert_euro_to_dollar(amount_euro: Decimal) -> Decimal:
    conversion_rate = get_conversion_rate_from_eur("USD")
    return Decimal(amount_euro).quantize(Decimal(".01")) * conversion_rate


def convert_dollar_to_euro(amount_dollar: Decimal) -> Decimal:
    conversion_rate = 1 / get_conversion_rate_from_eur("USD")
    return Decimal(amount_dollar).quantize(Decimal(".01")) * conversion_rate

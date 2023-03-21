import decimal
from datetime import datetime
from datetime import timedelta

from django.utils import timezone
from docxtpl import DocxTemplate

from cashflow.bill.choices import BillNumberChoices
from cashflow.bill.fees.management_fees import calculate_management_fees
from cashflow.currency.conversion_rate import get_conversion_rate_from_eur


def generate_bill_number(bill, year=False):
    # Generation of the invoice number if not present

    if not bill.invoice_number and bill.type:
        year = year or timezone.now().year
        type = BillNumberChoices.get_value(bill.type)
        number_ = str(bill.get_next_number(bill.type, year)).zfill(7)

        bill.invoice_number = f"{year}_{type}_{number_}"
        bill.save(update_fields=["invoice_number"])


def generate_bill_template(bill, payin: dict):
    template = get_document_template(bill)
    context = get_document_context(bill, payin)
    template.render(context)
    current_path = "/tmp/generated_invoice.docx"
    template.save(current_path)
    return current_path, template


def get_document_template(bill):
    base_path = "core_management/templates/"
    investor_type = bill.investment.investor.kyc.type
    template_path = {
        "natural": "Annual_management_fees_invoice_template_natural.docx",
        "legal": "Annual_management_fees_invoice_template_legal.docx",
    }
    path = base_path + template_path[investor_type]
    document_template = DocxTemplate(path)
    return document_template


def get_document_context(bill: "Bill", payin: dict):
    investor = bill.get_investor()
    investment = bill.investment
    fees = investment.get_fees_amount_from_bill()
    acceleration_percentage = 0
    year = 2023 - investment.get_invest_date().year
    percentage = 0.02 if year <= 4 else 0.01
    acceleration_percentage = decimal.Decimal(percentage)
    invest_date = bill.investment.get_invest_date()
    if bill.type == "management_fees":
        payin["creation_datetime"] = "January 9th 2023"
        payin["due_date"] = "February 10th 2023"
    context = {
        "investor": investor,
        "current_year": str(datetime.today().year),
        "committed_amount": investment.get_formatted_committed_amount(),
        "conversion_rate": get_conversion_rate(investment),
        "acceleration_percentage": round(acceleration_percentage, 2),
        "company": investment.investor.name,
        "invoice": get_invoice_data(bill),
        "fees": get_investment_fees(bill, round(bill.amount_due, 2)),
        "date": get_investment_date(bill),
        "email": bill.get_owner_email(),
        "address": investor.kyc.get_full_address(),
        "fundraising": investment.fundraising.name,
        "payin": payin,
        "subscription": get_subscription(bill),
        "year": str(invest_date.year),
        "month": invest_date.strftime("%m"),
        "wallet": investment.wallet,
        "investment": investment,
    }
    return context


def get_subscription(bill):
    subscription = {}
    if bill.type == "management_fees":
        subscription["invoice_date"] = "January 9th 2023"
        subscription["due_date"] = "February 10th 2023"
    else:
        today_date = timezone.now()
        subscription["invoice_date"] = today_date.strftime("%d/%m/%Y")
        due_date = today_date + timedelta(days=20)
        subscription["due_date"] = due_date.strftime("%d/%m/%Y")
    return subscription


def get_conversion_rate(investment):
    currency = investment.fundraising.currency.name
    if currency == "USD":
        conversion_rate = 1 / get_conversion_rate_from_eur("USD")
        return round(decimal.Decimal(conversion_rate), 2)
    return 1


def get_invoice_data(bill):
    generate_bill_number(bill)
    invoice = {"tax": get_invoice_taxes(bill), "num": bill.invoice_number}
    return invoice


def get_invoice_taxes(bill):
    # investment = bill.investment
    # country = get_owner_country(investment)
    # if country == 'France' and bill.type != "management_fees":
    #     return 20
    # Financial team said that it has to be 0 in all cases on management_fees
    return 0


def get_owner_country(investment):
    kyc = investment.investor.kyc
    country = {
        "legal": kyc.business_address.country.name,
        "natural": kyc.representative_address.country.name,
    }
    return country[kyc.type] if kyc.type else None


def get_investment_fees(bill, fees):
    sub_total = round(fees, 2)
    invoice_tax = get_invoice_taxes(bill) / 100
    fees_taxes = round(decimal.Decimal(invoice_tax) * fees, 2)
    total = fees_taxes + sub_total
    investment_fees = {
        "stotal": sub_total,  # TODO change this property name here and in template
        "tax": fees_taxes,
        "total": total,
    }
    return investment_fees


def get_investment_date(bill):
    investment_date = bill.investment.get_invest_date()
    date = {
        "month": investment_date.month,
        "year": investment_date.year,
    }
    return date


def get_output_path(document_type, bill):
    folder = "/tmp/Fees_invoice/"
    investor = bill.investment.investor.name.replace(" ", "_")
    year = str(datetime.today().year)
    number = bill.invoice_number
    extension = ".pdf" if document_type == "pdf" else ".docx"
    file_path = f"{folder}{investor}_{year}_{number}{extension}"
    return file_path

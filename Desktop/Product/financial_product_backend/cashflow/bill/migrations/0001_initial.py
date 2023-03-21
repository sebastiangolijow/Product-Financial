# Generated by Django 2.2.28 on 2022-09-12 12:51

import cashflow.bill.models
from django.db import migrations, models
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bill",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "platform_id",
                    models.IntegerField(blank=True, null=True, unique=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, null=True, verbose_name="Updated at"
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("upfront_fees", "Upfront fees"),
                            ("management_fees", "Management fees"),
                            ("membership_fees", "Membership fees"),
                            ("rhapsody_fees", "Rhapsody fees"),
                        ],
                        default="upfront_fees",
                        max_length=140,
                        null=True,
                        verbose_name="Bill type",
                    ),
                ),
                (
                    "year",
                    models.IntegerField(
                        blank=True,
                        choices=[
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
                        ],
                        default=2022,
                        null=True,
                        verbose_name="Issuing year",
                    ),
                ),
                (
                    "invoice_number_deprecated",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Invoice number Deprecated",
                    ),
                ),
                (
                    "invoice_number",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Invoice number",
                    ),
                ),
                (
                    "last_sent",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Last sent"
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=cashflow.bill.models.bill_upload_to,
                        verbose_name="Issuing file",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=19,
                        null=True,
                        verbose_name="Fees Amount",
                    ),
                ),
                (
                    "acceleration_percentage",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=19,
                        null=True,
                        verbose_name="Acceleration Percentage",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bill",
                "verbose_name_plural": "Bills",
            },
        ),
        migrations.CreateModel(
            name="HistoricalBill",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "platform_id",
                    models.IntegerField(blank=True, db_index=True, null=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        blank=True, editable=False, null=True, verbose_name="Updated at"
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("upfront_fees", "Upfront fees"),
                            ("management_fees", "Management fees"),
                            ("membership_fees", "Membership fees"),
                            ("rhapsody_fees", "Rhapsody fees"),
                        ],
                        default="upfront_fees",
                        max_length=140,
                        null=True,
                        verbose_name="Bill type",
                    ),
                ),
                (
                    "year",
                    models.IntegerField(
                        blank=True,
                        choices=[
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
                        ],
                        default=2022,
                        null=True,
                        verbose_name="Issuing year",
                    ),
                ),
                (
                    "invoice_number_deprecated",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Invoice number Deprecated",
                    ),
                ),
                (
                    "invoice_number",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Invoice number",
                    ),
                ),
                (
                    "last_sent",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Last sent"
                    ),
                ),
                (
                    "file",
                    models.TextField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Issuing file",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=19,
                        null=True,
                        verbose_name="Fees Amount",
                    ),
                ),
                (
                    "acceleration_percentage",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=19,
                        null=True,
                        verbose_name="Acceleration Percentage",
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField()),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Bill",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]

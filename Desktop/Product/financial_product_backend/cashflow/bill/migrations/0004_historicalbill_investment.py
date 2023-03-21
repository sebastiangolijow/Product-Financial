# Generated by Django 2.2.28 on 2022-09-12 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bill", "0003_historicalbill_history_user"),
        ("core_management", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalbill",
            name="investment",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="core_management.Investment",
                verbose_name="Investment",
            ),
        ),
    ]
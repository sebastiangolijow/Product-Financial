# Generated by Django 2.2.28 on 2022-12-27 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bill', '0009_auto_20221010_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='type',
            field=models.CharField(blank=True, choices=[('upfront_fees', 'Upfront fees'), ('management_fees', 'Management fees'), ('membership_fees', 'Membership fees'), ('rhapsody_fees', 'Rhapsody fees'), ('credit_notes', 'Credit notes')], default='upfront_fees', max_length=140, null=True, verbose_name='Bill type'),
        ),
        migrations.AlterField(
            model_name='historicalbill',
            name='type',
            field=models.CharField(blank=True, choices=[('upfront_fees', 'Upfront fees'), ('management_fees', 'Management fees'), ('membership_fees', 'Membership fees'), ('rhapsody_fees', 'Rhapsody fees'), ('credit_notes', 'Credit notes')], default='upfront_fees', max_length=140, null=True, verbose_name='Bill type'),
        ),
    ]
# Generated by Django 2.2.28 on 2022-10-13 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cashcalls', '0006_manual_move_payin_to_cashcall'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cashcall',
            name='cc_emails',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='fees_percentage',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='investor',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='investor_name',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='payin',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='sendinblue_template_id',
        ),
        migrations.RemoveField(
            model_name='cashcall',
            name='total_committed_amount',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='cc_emails',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='fees_percentage',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='investor',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='investor_name',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='payin',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='sendinblue_template_id',
        ),
        migrations.RemoveField(
            model_name='historicalcashcall',
            name='total_committed_amount',
        ),
    ]

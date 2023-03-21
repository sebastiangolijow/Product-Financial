from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cashcalls", "0005_auto_20220923_1200")]

    operations = [
        # migrations.RunPython(
        #     code=move_payin_to_cashcall, reverse_code=reverse_move_payin_to_cashcall
        # ),
        # migrations.RunPython(
        #     code=migrate_data_from_cashcall_to_bill,
        #     reverse_code=reverse_migrate_data_from_cashcall_to_bill,
        # ),
    ]

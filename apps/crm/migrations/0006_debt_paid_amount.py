from django.db import migrations, models


def backfill_paid_amount(apps, schema_editor):
    Debt = apps.get_model("crm", "Debt")
    Debt.objects.filter(is_paid=True, paid_amount=0).update(paid_amount=models.F("amount"))


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0005_debt"),
    ]

    operations = [
        migrations.AddField(
            model_name="debt",
            name="paid_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="To'langan summa"),
        ),
        migrations.RunPython(backfill_paid_amount, migrations.RunPython.noop),
    ]

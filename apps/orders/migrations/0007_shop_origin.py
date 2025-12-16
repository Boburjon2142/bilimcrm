from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_deliverysettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverysettings",
            name="shop_lat",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Do‘kon lat (ixtiyoriy)"
            ),
        ),
        migrations.AddField(
            model_name="deliverysettings",
            name="shop_lng",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Do‘kon lng (ixtiyoriy)"
            ),
        ),
    ]

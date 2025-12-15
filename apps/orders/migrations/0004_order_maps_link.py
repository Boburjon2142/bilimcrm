from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_delivery_fields_and_zone"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="maps_link",
            field=models.URLField(blank=True, default="", verbose_name="Xarita havolasi"),
        ),
    ]

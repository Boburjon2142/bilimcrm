from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="address_text",
            field=models.CharField(blank=True, max_length=255, verbose_name="Qo‘shimcha manzil matni"),
        ),
        migrations.AddField(
            model_name="order",
            name="courier_maps_url",
            field=models.URLField(blank=True, default="", verbose_name="Kuryer xarita havolasi"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_distance_km",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7, verbose_name="Masofa (km)"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_fee",
            field=models.IntegerField(default=0, verbose_name="Yetkazib berish narxi (so‘m)"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_pricing_snapshot",
            field=models.JSONField(blank=True, default=dict, verbose_name="Yetkazib berish hisoboti"),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_zone_status",
            field=models.CharField(
                choices=[("OK", "OK"), ("BLOCKED", "BLOCKED")],
                default="OK",
                max_length=10,
                verbose_name="Zona holati",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="latitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Kenglik (lat)"),
        ),
        migrations.AddField(
            model_name="order",
            name="longitude",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Uzunlik (lng)"),
        ),
        migrations.CreateModel(
            name="DeliveryZone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("mode", models.CharField(choices=[("CIRCLE", "Doira"), ("BBOX", "To‘rtburchak")], default="CIRCLE", max_length=10)),
                ("center_lat", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("center_lng", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("radius_km", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("min_lat", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("min_lng", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("max_lat", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("max_lng", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("message", models.CharField(blank=True, max_length=255)),
            ],
            options={
                "verbose_name": "Yetkazib berish zonasi",
                "verbose_name_plural": "Yetkazib berish zonalari",
            },
        ),
    ]

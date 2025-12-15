from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_maps_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryNotice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Yetkazib berish ma'lumoti",
                "verbose_name_plural": "Yetkazib berish ma'lumotlari",
                "ordering": ["-updated_at"],
            },
        ),
    ]

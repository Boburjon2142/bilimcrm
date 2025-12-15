from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="location",
            field=models.CharField(blank=True, max_length=255, verbose_name="Lokatsiya"),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0004_expense"),
    ]

    operations = [
        migrations.CreateModel(
            name="Debt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=255, verbose_name="F.I.Sh")),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="Telefon")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Qarz summasi")),
                ("note", models.TextField(blank=True, verbose_name="Izoh")),
                ("is_paid", models.BooleanField(default=False, verbose_name="Yopildi")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Qarzdor",
                "verbose_name_plural": "Qarzdorlar",
                "ordering": ["-created_at"],
            },
        ),
    ]

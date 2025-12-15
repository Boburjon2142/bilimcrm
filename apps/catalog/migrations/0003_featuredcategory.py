from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_category_parent"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeaturedCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=255, verbose_name="Sarlavha")),
                ("limit", models.PositiveIntegerField(default=10, verbose_name="Nechta ko‘rsatilsin")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Tartib")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="featured_items",
                        to="catalog.category",
                        verbose_name="Kategoriya",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tanlangan kategoriya",
                "verbose_name_plural": "Tanlangan kategoriyalar",
                "ordering": ["order", "id"],
            },
        ),
    ]

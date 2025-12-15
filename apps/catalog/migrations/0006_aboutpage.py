from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_author_photo"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Biz haqimizda", max_length=255, verbose_name="Sarlavha")),
                ("body", models.TextField(blank=True, verbose_name="Matn")),
                ("link", models.URLField(blank=True, verbose_name="Havola")),
                ("image", models.ImageField(blank=True, null=True, upload_to="about/", verbose_name="Rasm")),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Biz haqimizda kontent",
                "verbose_name_plural": "Biz haqimizda kontenti",
                "ordering": ["-updated_at", "-id"],
            },
        ),
    ]

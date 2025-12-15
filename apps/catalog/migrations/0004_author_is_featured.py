from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_featuredcategory"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Asosiy sahifada ko‘rsatish"),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_author_is_featured"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="authors/", verbose_name="Rasm"),
        ),
    ]

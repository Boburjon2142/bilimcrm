from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("barcode", models.CharField(max_length=64, blank=True)),
                ("buy_price", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("sell_price", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("stock_qty", models.IntegerField(default=0)),
                ("version", models.PositiveIntegerField(default=1)),
                ("needs_review", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("full_name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=50, blank=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Sale",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("sale_datetime", models.DateTimeField()),
                ("total", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("payment_type", models.CharField(max_length=10, choices=[("cash", "cash"), ("card", "card")])),
                ("seller", models.CharField(max_length=120, blank=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to="sync.customer")),
            ],
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("expense_datetime", models.DateTimeField()),
                ("category", models.CharField(max_length=120, blank=True)),
                ("amount", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("note", models.TextField(blank=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="SyncEventLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("event_id", models.UUIDField(unique=True)),
                ("entity_type", models.CharField(max_length=50)),
                ("entity_id", models.UUIDField()),
                ("operation", models.CharField(max_length=10)),
                ("payload_json", models.JSONField(default=dict, blank=True)),
                ("device_id", models.CharField(max_length=120, blank=True)),
                ("status", models.CharField(max_length=20, default="applied")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="ConflictLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("event_id", models.UUIDField()),
                ("entity_type", models.CharField(max_length=50)),
                ("entity_id", models.UUIDField()),
                ("conflict_type", models.CharField(max_length=50)),
                ("server_payload", models.JSONField(default=dict, blank=True)),
                ("client_payload", models.JSONField(default=dict, blank=True)),
                ("resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="SaleItem",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("price", models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ("product", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to="sync.product")),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="sync.sale")),
            ],
        ),
    ]

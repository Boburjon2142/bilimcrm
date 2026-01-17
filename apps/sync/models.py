import uuid

from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=64, blank=True)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_qty = models.IntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    needs_review = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name


class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale_datetime = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=10, choices=[("cash", "cash"), ("card", "card")])
    seller = models.CharField(max_length=120, blank=True)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Sale {self.id}"


class SaleItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def line_total(self):
        return self.quantity * self.price


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense_datetime = models.DateTimeField()
    category = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.category} {self.amount}"


class SyncEventLog(models.Model):
    event_id = models.UUIDField(unique=True)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    operation = models.CharField(max_length=10)
    payload_json = models.JSONField(default=dict, blank=True)
    device_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, default="applied")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.entity_type} {self.operation} {self.event_id}"


class ConflictLog(models.Model):
    event_id = models.UUIDField()
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    conflict_type = models.CharField(max_length=50)
    server_payload = models.JSONField(default=dict, blank=True)
    client_payload = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.entity_type} {self.conflict_type}"

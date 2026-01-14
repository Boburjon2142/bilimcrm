from django.db import models
from django.utils import timezone


class Customer(models.Model):
    full_name = models.CharField("F.I.Sh", max_length=255)
    phone = models.CharField("Telefon", max_length=50, unique=True)
    email = models.EmailField("Email", blank=True)
    tags = models.CharField("Teglar", max_length=255, blank=True)
    notes = models.TextField("Izoh", blank=True)
    is_vip = models.BooleanField("VIP", default=False)
    is_problem = models.BooleanField("Muammo bo‘lgan", default=False)
    total_spent = models.DecimalField("Umumiy sarf", max_digits=12, decimal_places=2, default=0)
    orders_count = models.PositiveIntegerField("Buyurtmalar soni", default=0)
    last_order_at = models.DateTimeField("Oxirgi faollik", null=True, blank=True)
    discount_percent = models.PositiveIntegerField("Chegirma (%)", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_order_at", "full_name"]
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Courier(models.Model):
    name = models.CharField("F.I.Sh", max_length=255)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    telegram_username = models.CharField("Telegram", max_length=100, blank=True)
    telegram_id = models.CharField("Telegram ID", max_length=64, blank=True)
    is_active = models.BooleanField("Faol", default=True)
    last_active_at = models.DateTimeField("Oxirgi faollik", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "name"]
        verbose_name = "Kuryer"
        verbose_name_plural = "Kuryerlar"

    def __str__(self):
        return self.name


class InventoryLog(models.Model):
    REASON_CHOICES = [
        ("sale", "Sotuv"),
        ("restock", "To‘ldirish"),
        ("adjust", "Tuzatish"),
        ("cancel", "Bekor qilish"),
    ]

    book = models.ForeignKey("catalog.Book", on_delete=models.CASCADE, related_name="inventory_logs")
    delta = models.IntegerField("O‘zgarish")
    reason = models.CharField("Sabab", max_length=20, choices=REASON_CHOICES)
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_logs",
    )
    note = models.CharField("Izoh", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ombor yozuvi"
        verbose_name_plural = "Ombor yozuvlari"

    def __str__(self):
        return f"{self.book} ({self.delta})"


class Expense(models.Model):
    title = models.CharField("Sarlavha", max_length=255)
    amount = models.DecimalField("Chiqim", max_digits=12, decimal_places=2)
    spent_on = models.DateField("Sana", default=timezone.localdate)
    note = models.TextField("Izoh", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-spent_on", "-created_at"]
        verbose_name = "Chiqim"
        verbose_name_plural = "Chiqimlar"

    def __str__(self):
        return f"{self.title} ({self.amount})"


class Debt(models.Model):
    full_name = models.CharField("F.I.Sh", max_length=255)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    amount = models.DecimalField("Qarz summasi", max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField("To'langan summa", max_digits=12, decimal_places=2, default=0)
    note = models.TextField("Izoh", blank=True)
    is_paid = models.BooleanField("Yopildi", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Qarzdor"
        verbose_name_plural = "Qarzdorlar"

    def __str__(self):
        return f"{self.full_name} ({self.amount})"

    def remaining_amount(self):
        if self.is_paid:
            return 0
        paid = self.paid_amount or 0
        remaining = self.amount - paid
        return remaining if remaining > 0 else 0

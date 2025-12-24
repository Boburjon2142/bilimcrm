from django.contrib import admin

from .models import Courier, Customer, InventoryLog, Expense, Debt


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "discount_percent",
        "orders_count",
        "total_spent",
        "last_order_at",
        "is_vip",
        "is_problem",
    )
    list_filter = ("is_vip", "is_problem")
    search_fields = ("full_name", "phone")


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "telegram_username", "is_active", "last_active_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone", "telegram_username")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("book", "delta", "reason", "related_order", "created_at")
    list_filter = ("reason",)
    search_fields = ("book__title", "note")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "amount", "spent_on", "created_at")
    list_filter = ("spent_on",)
    search_fields = ("title", "note")


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "amount", "is_paid", "created_at")
    list_filter = ("is_paid",)
    search_fields = ("full_name", "phone", "note")

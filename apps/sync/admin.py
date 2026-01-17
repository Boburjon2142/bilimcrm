from django.contrib import admin

from .models import Product, Customer, Sale, SaleItem, Expense, SyncEventLog, ConflictLog


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "barcode", "sell_price", "stock_qty", "version", "needs_review", "updated_at")
    search_fields = ("name", "barcode")
    list_filter = ("needs_review",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "version", "updated_at")
    search_fields = ("full_name", "phone")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "sale_datetime", "total", "payment_type", "seller", "updated_at")
    list_filter = ("payment_type",)
    inlines = [SaleItemInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("expense_datetime", "category", "amount", "updated_at")
    search_fields = ("category", "note")


@admin.register(SyncEventLog)
class SyncEventLogAdmin(admin.ModelAdmin):
    list_display = ("event_id", "entity_type", "operation", "device_id", "status", "created_at")
    list_filter = ("entity_type", "operation", "status")
    search_fields = ("event_id", "device_id")


@admin.register(ConflictLog)
class ConflictLogAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_id", "conflict_type", "resolved", "created_at")
    list_filter = ("entity_type", "conflict_type", "resolved")
    search_fields = ("entity_id", "event_id")

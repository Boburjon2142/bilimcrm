from rest_framework import serializers

from .models import Product, Customer, Sale, SaleItem, Expense


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "barcode",
            "buy_price",
            "sell_price",
            "stock_qty",
            "version",
            "needs_review",
            "updated_at",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone", "version", "updated_at"]


class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ["id", "product", "quantity", "price"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "sale_datetime", "total", "payment_type", "seller", "customer", "version", "updated_at", "items"]


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "expense_datetime", "category", "amount", "note", "version", "updated_at"]

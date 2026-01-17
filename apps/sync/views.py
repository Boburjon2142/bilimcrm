from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Product, Sale, SaleItem, Expense, Customer, SyncEventLog, ConflictLog
from .serializers import ProductSerializer, SaleSerializer, ExpenseSerializer, CustomerSerializer


def _parse_uuid(value):
    try:
        return UUID(str(value))
    except Exception:
        return None


def _parse_decimal(value):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _now_iso():
    return timezone.now().isoformat()


def _register_conflict(event_id, entity_type, entity_id, conflict_type, server_payload, client_payload):
    ConflictLog.objects.create(
        event_id=event_id,
        entity_type=entity_type,
        entity_id=entity_id,
        conflict_type=conflict_type,
        server_payload=server_payload,
        client_payload=client_payload,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_push(request):
    device_id = (request.data.get("device_id") or "").strip()
    events = request.data.get("events") or []
    results = []

    for event in events:
        event_id = _parse_uuid(event.get("event_id"))
        entity_type = (event.get("entity_type") or "").lower()
        entity_id = _parse_uuid(event.get("entity_id"))
        operation = (event.get("operation") or "").upper()
        payload = event.get("payload_json") or {}

        if not event_id or not entity_id or not entity_type:
            results.append({"event_id": str(event.get("event_id")), "status": "invalid"})
            continue

        if SyncEventLog.objects.filter(event_id=event_id).exists():
            results.append({"event_id": str(event_id), "status": "duplicate"})
            continue

        status = "applied"

        if entity_type == "product":
            product = Product.objects.filter(id=entity_id).first()
            incoming_version = int(payload.get("version") or 1)
            incoming_stock = payload.get("stock_qty")
            if product:
                if incoming_version > product.version:
                    product.name = payload.get("name", product.name)
                    product.barcode = payload.get("barcode", product.barcode) or ""
                    product.buy_price = _parse_decimal(payload.get("buy_price", product.buy_price))
                    product.sell_price = _parse_decimal(payload.get("sell_price", product.sell_price))
                    if incoming_stock is not None:
                        product.stock_qty = int(incoming_stock)
                    product.version = incoming_version
                    product.save()
                else:
                    if incoming_stock is not None and int(incoming_stock) != product.stock_qty:
                        product.needs_review = True
                        product.save(update_fields=["needs_review"])
                        _register_conflict(
                            event_id,
                            "product",
                            product.id,
                            "stock_qty_conflict",
                            ProductSerializer(product).data,
                            payload,
                        )
                    else:
                        _register_conflict(
                            event_id,
                            "product",
                            product.id,
                            "version_conflict",
                            ProductSerializer(product).data,
                            payload,
                        )
                    status = "conflict"
            else:
                Product.objects.create(
                    id=entity_id,
                    name=payload.get("name", ""),
                    barcode=payload.get("barcode", "") or "",
                    buy_price=_parse_decimal(payload.get("buy_price", 0)),
                    sell_price=_parse_decimal(payload.get("sell_price", 0)),
                    stock_qty=int(payload.get("stock_qty") or 0),
                    version=incoming_version,
                )

        elif entity_type == "sale":
            if operation != "CREATE":
                _register_conflict(event_id, "sale", entity_id, "append_only", {}, payload)
                status = "ignored"
            else:
                sale_dt = payload.get("sale_datetime")
                sale_dt = parse_datetime(sale_dt) if sale_dt else timezone.now()
                sale = Sale.objects.create(
                    id=entity_id,
                    sale_datetime=sale_dt,
                    total=_parse_decimal(payload.get("total", 0)),
                    payment_type=payload.get("payment_type", "cash"),
                    seller=payload.get("seller", ""),
                )
                items = payload.get("items") or []
                for item in items:
                    SaleItem.objects.create(
                        sale=sale,
                        product_id=_parse_uuid(item.get("product")),
                        quantity=int(item.get("quantity") or 1),
                        price=_parse_decimal(item.get("price", 0)),
                    )

        elif entity_type == "expense":
            if operation != "CREATE":
                _register_conflict(event_id, "expense", entity_id, "append_only", {}, payload)
                status = "ignored"
            else:
                exp_dt = payload.get("expense_datetime")
                exp_dt = parse_datetime(exp_dt) if exp_dt else timezone.now()
                Expense.objects.create(
                    id=entity_id,
                    expense_datetime=exp_dt,
                    category=payload.get("category", ""),
                    amount=_parse_decimal(payload.get("amount", 0)),
                    note=payload.get("note", ""),
                )

        elif entity_type == "customer":
            customer = Customer.objects.filter(id=entity_id).first()
            incoming_version = int(payload.get("version") or 1)
            if customer:
                if incoming_version > customer.version:
                    customer.full_name = payload.get("full_name", customer.full_name)
                    customer.phone = payload.get("phone", customer.phone)
                    customer.version = incoming_version
                    customer.save()
                else:
                    _register_conflict(event_id, "customer", customer.id, "version_conflict", CustomerSerializer(customer).data, payload)
                    status = "conflict"
            else:
                Customer.objects.create(
                    id=entity_id,
                    full_name=payload.get("full_name", ""),
                    phone=payload.get("phone", ""),
                    version=incoming_version,
                )
        else:
            status = "invalid"

        SyncEventLog.objects.create(
            event_id=event_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            payload_json=payload,
            device_id=device_id,
            status=status,
        )
        results.append({"event_id": str(event_id), "status": status})

    return Response({"server_time": _now_iso(), "results": results})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sync_pull(request):
    since_raw = request.query_params.get("since")
    since = parse_datetime(since_raw) if since_raw else None
    if since is None:
        since = timezone.now() - timezone.timedelta(days=3650)

    products = Product.objects.filter(updated_at__gt=since)
    customers = Customer.objects.filter(updated_at__gt=since)
    sales = Sale.objects.filter(updated_at__gt=since)
    expenses = Expense.objects.filter(updated_at__gt=since)

    payload = {
        "server_time": _now_iso(),
        "products": ProductSerializer(products, many=True).data,
        "customers": CustomerSerializer(customers, many=True).data,
        "sales": SaleSerializer(sales, many=True).data,
        "expenses": ExpenseSerializer(expenses, many=True).data,
    }
    return Response(payload)

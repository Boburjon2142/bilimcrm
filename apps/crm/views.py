from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta


def _is_operator(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="Operator").exists()


def _operator_only_redirect(request):
    if _is_operator(request.user):
        return redirect("crm_pos")
    return None


def _operator_block(request):
    if _is_operator(request.user):
        return HttpResponseForbidden("Operator role has access only to POS.")
    return None

from apps.catalog.models import Book
from apps.orders.cart import Cart
from apps.orders.models import Order, OrderItem
from .models import Courier, Customer, InventoryLog
from .utils.pdf import build_pdf


def _set_status_timestamps(order: Order, status: str) -> None:
    now = timezone.now()
    if status == "paid" and not order.paid_at:
        order.paid_at = now
    if status == "assigned" and not order.assigned_at:
        order.assigned_at = now
    if status == "delivering" and not order.assigned_at:
        order.assigned_at = now
    if status == "closed" and not order.delivered_at:
        order.delivered_at = now
    if status == "canceled" and not order.canceled_at:
        order.canceled_at = now


@staff_member_required
def dashboard(request):
    operator_response = _operator_only_redirect(request)
    if operator_response:
        return operator_response
    today = timezone.localdate()
    orders_today = Order.objects.filter(created_at__date=today)
    revenue_today = orders_today.aggregate(total=Sum("total_price")).get("total") or Decimal("0")

    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum("total_price")).get("total") or Decimal("0")

    line_total_expr = ExpressionWrapper(
        F("quantity") * F("price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    top_books = (
        OrderItem.objects.annotate(line_total=line_total_expr)
        .values("book__title")
        .annotate(quantity=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-quantity")[:8]
    )
    top_customers = Customer.objects.order_by("-total_spent")[:8]

    courier_stats = (
        Order.objects.filter(courier__isnull=False)
        .values("courier__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    weekly_revenue = []
    max_total = Decimal("0")
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        total = (
            Order.objects.filter(created_at__date=day)
            .aggregate(total=Sum("total_price"))
            .get("total")
            or Decimal("0")
        )
        if total > max_total:
            max_total = total
        weekly_revenue.append({"label": day.strftime("%d.%m"), "total": total})
    for item in weekly_revenue:
        if max_total:
            item["percent"] = float((item["total"] / max_total) * Decimal("100"))
        else:
            item["percent"] = 0

    context = {
        "orders_today": orders_today.count(),
        "revenue_today": revenue_today,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_books": top_books,
        "top_customers": top_customers,
        "courier_stats": courier_stats,
        "weekly_revenue": weekly_revenue,
    }
    return render(request, "crm/dashboard.html", context)


def _format_money(value) -> str:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{v:,}".replace(",", " ")


@staff_member_required
def export_orders_pdf(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    orders = (
        Order.objects.select_related("customer", "courier")
        .order_by("-created_at")[:2000]
    )
    lines = [
        "BILIM UZ - Buyurtmalar tarixi",
        f"Yaratilgan: {timezone.localtime().strftime('%Y-%m-%d %H:%M')}",
        f"Jami: {orders.count()} ta",
        "",
        "ID | Sana | Mijoz | Telefon | Summa | Status | Kanal | Kuryer",
        "-" * 90,
    ]
    for order in orders:
        lines.append(
            f"#{order.id} | {order.created_at:%Y-%m-%d} | {order.full_name} | {order.phone} | "
            f"{_format_money(order.total_price)} | {order.get_status_display()} | "
            f"{order.get_order_source_display()} | {order.courier or '—'}"
        )
    pdf_bytes = build_pdf(lines)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="bilimuz_orders.pdf"'
    return response


@staff_member_required
def export_sales_pdf(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    items = (
        OrderItem.objects.select_related("book", "order")
        .order_by("-order__created_at")[:4000]
    )
    lines = [
        "BILIM UZ - Xaridlar tarixi",
        f"Yaratilgan: {timezone.localtime().strftime('%Y-%m-%d %H:%M')}",
        f"Jami: {items.count()} qator",
        "",
        "Order | Sana | Kitob | Soni | Narx | Jami",
        "-" * 90,
    ]
    for item in items:
        total = item.line_total()
        lines.append(
            f"#{item.order_id} | {item.order.created_at:%Y-%m-%d} | {item.book.title} | "
            f"{item.quantity} | {_format_money(item.price)} | {_format_money(total)}"
        )
    pdf_bytes = build_pdf(lines)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="bilimuz_sales.pdf"'
    return response


@staff_member_required
def export_report_pdf(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    orders = Order.objects.select_related("customer", "courier").order_by("-created_at")[:2000]
    items = OrderItem.objects.select_related("book", "order").order_by("-order__created_at")[:4000]

    def _cell(value: str, width: int) -> str:
        text = (value or "").strip()
        inner_width = max(width - 2, 1)
        if len(text) > inner_width:
            if inner_width <= 3:
                text = text[:inner_width]
            else:
                text = text[: inner_width - 3] + "..."
        return f" {text.ljust(inner_width)} "

    widths = [12, 8, 22, 40, 6, 16, 16, 18]
    headers = ["Turi", "ID", "Mijoz", "Kitob", "Soni", "Tel", "Summa", "Status"]

    def _border() -> str:
        return "-" * (sum(widths) + len(widths) + 1)

    def _row(cols) -> str:
        return "|" + "|".join([_cell(col, widths[i]) for i, col in enumerate(cols)]) + "|"

    lines = [
        "BILIM UZ - Hisobot (Buyurtmalar + Xaridlar)",
        f"Yaratilgan: {timezone.localtime().strftime('%Y-%m-%d %H:%M')}",
        "",
        _border(),
        _row(headers),
        _border(),
    ]

    for item in items:
        order = item.order
        total = item.line_total()
        lines.append(
            _row(
                [
                    "Online" if order.order_source == "online" else "Offline",
                    f"#{order.id}",
                    order.full_name,
                    item.book.title,
                    str(item.quantity),
                    order.phone,
                    _format_money(total),
                    order.get_status_display(),
                ]
            )
        )
    lines.append(_border())

    pdf_bytes = build_pdf(lines)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="bilimuz_report.pdf"'
    return response


@staff_member_required
def orders_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    status_filter = request.GET.get("status") or ""
    orders = Order.objects.select_related("customer", "courier").prefetch_related("items__book")
    if status_filter:
        orders = orders.filter(status=status_filter)

    if request.method == "POST":
        action = request.POST.get("action")
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id)

        if action == "status":
            new_status = request.POST.get("status")
            if new_status and order.order_source != "pos":
                order.status = new_status
                _set_status_timestamps(order, new_status)
                order.save(update_fields=["status", "paid_at", "assigned_at", "delivered_at", "canceled_at"])
        elif action == "assign":
            courier_id = request.POST.get("courier_id")
            if courier_id and order.order_source != "pos":
                order.courier_id = courier_id
                order.status = "assigned"
                _set_status_timestamps(order, "assigned")
                order.save(update_fields=["courier", "status", "assigned_at"])
        return redirect("crm_orders")

    context = {
        "orders": orders[:200],
        "status_filter": status_filter,
        "statuses": Order.STATUS_CHOICES,
        "couriers": Courier.objects.filter(is_active=True),
    }
    return render(request, "crm/orders.html", context)


@staff_member_required
def customers_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    customers = Customer.objects.all().order_by("-last_order_at")[:200]
    return render(request, "crm/customers.html", {"customers": customers})


@staff_member_required
def customer_detail(request, customer_id: int):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(customer=customer).order_by("-created_at")
    return render(request, "crm/customer_detail.html", {"customer": customer, "orders": orders})


@staff_member_required
def couriers_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    couriers = Courier.objects.all()
    courier_stats = (
        Order.objects.filter(courier__isnull=False)
        .values("courier__id", "courier__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return render(request, "crm/couriers.html", {"couriers": couriers, "courier_stats": courier_stats})


@staff_member_required
def inventory_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    if request.method == "POST":
        book_id = request.POST.get("book_id")
        delta_raw = request.POST.get("delta", "0")
        note = request.POST.get("note", "")
        try:
            delta = int(delta_raw)
        except (TypeError, ValueError):
            delta = 0
        if book_id and delta:
            book = get_object_or_404(Book, id=book_id)
            book.stock_quantity = (book.stock_quantity or 0) + delta
            book.save(update_fields=["stock_quantity"])
            InventoryLog.objects.create(book=book, delta=delta, reason="adjust", note=note)
        return redirect("crm_inventory")

    books = Book.objects.all().order_by("title")[:200]
    return render(request, "crm/inventory.html", {"books": books})


@staff_member_required
def pos_checkout(request):
    cart = Cart(request)
    if request.method == "POST":
        book_id = request.POST.get("book_id")
        barcode = (request.POST.get("barcode") or "").strip()
        quantity = request.POST.get("quantity", "1")
        action = request.POST.get("action")
        if action == "add" and book_id:
            cart.add(book_id, quantity)
            return redirect("crm_pos")
        if action == "add" and barcode and not book_id:
            book = Book.objects.filter(barcode=barcode).first()
            if not book:
                messages.warning(request, "Shtrix-kod topilmadi.")
                return redirect("crm_pos")
            cart.add(book.id, quantity)
            return redirect("crm_pos")

        if action == "remove" and book_id:
            cart.remove(book_id)
            return redirect("crm_pos")

        if action == "clear":
            cart.clear()
            return redirect("crm_pos")

        if action == "checkout":
            full_name = request.POST.get("full_name", "POS mijoz")
            phone = request.POST.get("phone", "")
            payment_type = request.POST.get("payment_type", "cash")
            cart_items = list(cart.items())
            if cart_items:
                subtotal = cart.total_price()
                customer = None
                discount_percent = 0
                if phone:
                    customer = Customer.objects.filter(phone=phone).first()
                    if customer:
                        discount_percent = min(int(customer.discount_percent or 0), 100)
                discount_amount = (subtotal * Decimal(discount_percent)) / Decimal("100") if discount_percent else 0
                total_price = subtotal - discount_amount
                order = Order.objects.create(
                    full_name=full_name,
                    phone=phone or "POS",
                    payment_type=payment_type,
                    subtotal_before_discount=subtotal,
                    discount_percent=discount_percent,
                    discount_amount=discount_amount,
                    total_price=total_price,
                    order_source="pos",
                    status="paid",
                    paid_at=timezone.now(),
                    customer=customer,
                )
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        book=item["book"],
                        quantity=item["quantity"],
                        price=item["price"],
                    )
                cart.clear()
            return redirect("crm_pos")

    books = Book.objects.all().order_by("title")[:200]
    return render(request, "crm/pos.html", {"books": books, "cart_items": list(cart.items()), "cart_total": cart.total_price()})


@staff_member_required
def cleanup_data(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    if request.method != "POST":
        return redirect("crm_dashboard")
    try:
        days = int(request.POST.get("days", "90"))
    except (TypeError, ValueError):
        days = 90
    days = max(0, min(days, 3650))
    cutoff = timezone.now() - timedelta(days=days)

    scope = (request.POST.get("scope") or "closed").strip()
    force_all = (request.POST.get("force_all") or "").strip() == "1"

    if force_all:
        orders_count = Order.objects.count()
        Order.objects.all().delete()

        logs_count = InventoryLog.objects.count()
        InventoryLog.objects.all().delete()

        customers_count = 0
    else:
        orders_qs = Order.objects.filter(created_at__lt=cutoff)
        if scope != "all":
            orders_qs = orders_qs.filter(status__in=["closed", "canceled", "finished", "accepted"])
        orders_count = orders_qs.count()
        orders_qs.delete()

        logs_qs = InventoryLog.objects.filter(created_at__lt=cutoff)
        logs_count = logs_qs.count()
        logs_qs.delete()

        customers_count = 0

    if orders_count or logs_count:
        messages.success(
            request,
            f"Tozalandi: {orders_count} ta buyurtma, {logs_count} ta ombor yozuvi (>{days} kun).",
        )
    else:
        messages.warning(
            request,
            f"O'chirish uchun mos yozuv topilmadi (>{days} kun).",
        )
    return redirect("crm_dashboard")

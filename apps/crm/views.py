from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta, date, time, datetime
import calendar


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
from .models import Courier, Customer, InventoryLog, Expense, Debt
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
    hour_start = 8
    hour_end = 20
    tz = timezone.get_current_timezone()
    hourly_income = []
    max_total = Decimal("0")

    for hour in range(hour_start, hour_end + 1):
        start_dt = timezone.make_aware(datetime.combine(today, time(hour, 0)), tz)
        end_dt = start_dt + timedelta(hours=1)
        total = (
            Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
            .aggregate(total=Sum("total_price"))
            .get("total")
            or Decimal("0")
        )
        if total > max_total:
            max_total = total
        hourly_income.append({"label": f"{hour:02d}:00", "total": total})

    hourly_data = []
    bar_max = 70
    bar_min = 4

    def _height(total: Decimal) -> int:
        if max_total <= 0:
            return bar_min
        ratio = float(total / max_total)
        return int(round(bar_min + (bar_max - bar_min) * ratio))

    for item in hourly_income:
        hourly_data.append(
            {
                "label": item["label"],
                "income": item["total"],
                "income_height": _height(item["total"]),
                "expense": Decimal("0"),
                "expense_height": 0,
            }
        )

    chart_width = 700
    chart_height = 200
    padding_left = 50
    padding_right = 20
    padding_top = 20
    padding_bottom = 30
    plot_width = chart_width - padding_left - padding_right
    plot_height = chart_height - padding_top - padding_bottom
    scale_max = max_total if max_total > 0 else Decimal("1")
    points = []
    dots = []
    count = len(hourly_income)
    for idx, item in enumerate(hourly_income):
        if count > 1:
            x = padding_left + (plot_width * idx / (count - 1))
        else:
            x = padding_left + (plot_width / 2)
        ratio = float(item["total"] / scale_max) if scale_max else 0.0
        y = padding_top + (plot_height * (1 - ratio))
        points.append(f"{x:.1f},{y:.1f}")
        dots.append({"x": round(x, 1), "y": round(y, 1), "value": item["total"]})

    chart_ticks = []
    for step in range(5):
        tick_ratio = step / 4
        value = (scale_max * Decimal(1 - tick_ratio)).quantize(Decimal("1"))
        y = padding_top + (plot_height * tick_ratio)
        chart_ticks.append({"value": value, "y": round(y, 1)})

    context = {
        "orders_today": orders_today.count(),
        "revenue_today": revenue_today,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_books": top_books,
        "top_customers": top_customers,
        "courier_stats": courier_stats,
        "hourly_data": hourly_data,
        "chart_points": " ".join(points),
        "chart_dots": dots,
        "chart_ticks": chart_ticks,
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
def monthly_report(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    today = timezone.localdate()
    month_start = today.replace(day=1)
    start_raw = (request.GET.get("start") or "").strip()
    end_raw = (request.GET.get("end") or "").strip()
    start_time_raw = (request.GET.get("start_time") or "").strip()
    end_time_raw = (request.GET.get("end_time") or "").strip()
    start_date = month_start
    end_date = today
    start_time = time(0, 0)
    end_time = time(23, 59)
    if start_raw:
        try:
            start_date = date.fromisoformat(start_raw)
        except ValueError:
            start_date = month_start
    if end_raw:
        try:
            end_date = date.fromisoformat(end_raw)
        except ValueError:
            end_date = today
    if start_time_raw:
        try:
            start_time = time.fromisoformat(start_time_raw)
        except ValueError:
            start_time = time(0, 0)
    if end_time_raw:
        try:
            end_time = time.fromisoformat(end_time_raw)
        except ValueError:
            end_time = time(23, 59)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(start_dt, tz)
    end_dt = timezone.make_aware(end_dt, tz)

    if request.method == "POST":
        form_type = (request.POST.get("form_type") or "").strip()
        title = (request.POST.get("title") or "").strip()
        amount_raw = (request.POST.get("amount") or "").strip()
        spent_on_raw = (request.POST.get("spent_on") or "").strip()
        note = (request.POST.get("note") or "").strip()
        if form_type == "expense" and title and amount_raw:
            try:
                amount = Decimal(amount_raw)
            except (TypeError, ValueError):
                amount = None
            if amount is not None:
                spent_on = today
                if spent_on_raw:
                    try:
                        spent_on = date.fromisoformat(spent_on_raw)
                    except ValueError:
                        spent_on = today
                Expense.objects.create(
                    title=title,
                    amount=amount,
                    spent_on=spent_on,
                    note=note,
                )
                return redirect("crm_report")
        if form_type == "debt" and title and amount_raw:
            try:
                amount = Decimal(amount_raw)
            except (TypeError, ValueError):
                amount = None
            phone = (request.POST.get("phone") or "").strip()
            if amount is not None:
                Debt.objects.create(
                    full_name=title,
                    phone=phone,
                    amount=amount,
                    note=note,
                )
                return redirect("crm_report")

    income_total = (
        Order.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        .aggregate(total=Sum("total_price"))
        .get("total")
        or Decimal("0")
    )
    expense_total = (
        Expense.objects.filter(spent_on__gte=start_date, spent_on__lte=end_date)
        .aggregate(total=Sum("amount"))
        .get("total")
        or Decimal("0")
    )
    net_total = income_total - expense_total

    expenses = Expense.objects.filter(spent_on__gte=start_date, spent_on__lte=end_date)[:200]
    debts = Debt.objects.filter(is_paid=False).order_by("-created_at")[:200]

    base_month = start_date
    last_day = calendar.monthrange(base_month.year, base_month.month)[1]
    range_start = date(base_month.year, base_month.month, 1)
    range_mid = date(base_month.year, base_month.month, 11)
    range_mid2 = date(base_month.year, base_month.month, 21)
    range_end = date(base_month.year, base_month.month, last_day)
    quick_ranges = [
        {"label": "1—10", "start": range_start, "end": date(base_month.year, base_month.month, 10)},
        {"label": "11—20", "start": range_mid, "end": date(base_month.year, base_month.month, 20)},
        {"label": f"21—{last_day}", "start": range_mid2, "end": range_end},
    ]
    for item in quick_ranges:
        item["is_active"] = start_date == item["start"] and end_date == item["end"]

    return render(
        request,
        "crm/report.html",
        {
            "month_start": start_date,
            "month_end": end_date,
            "income_total": income_total,
            "expense_total": expense_total,
            "net_total": net_total,
            "expenses": expenses,
            "debts": debts,
            "start_date": start_date,
            "end_date": end_date,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "quick_ranges": quick_ranges,
        },
    )


@staff_member_required
def expenses_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    expenses = Expense.objects.all().order_by("-spent_on", "-created_at")[:500]
    return render(request, "crm/expenses.html", {"expenses": expenses})


@staff_member_required
def debts_list(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    debts = Debt.objects.all().order_by("-created_at")[:500]
    return render(request, "crm/debts.html", {"debts": debts})


@staff_member_required
def export_monthly_report_pdf(request):
    operator_response = _operator_block(request)
    if operator_response:
        return operator_response
    today = timezone.localdate()
    month_start = today.replace(day=1)
    start_raw = (request.GET.get("start") or "").strip()
    end_raw = (request.GET.get("end") or "").strip()
    start_time_raw = (request.GET.get("start_time") or "").strip()
    end_time_raw = (request.GET.get("end_time") or "").strip()
    start_date = month_start
    end_date = today
    start_time = time(0, 0)
    end_time = time(23, 59)
    if start_raw:
        try:
            start_date = date.fromisoformat(start_raw)
        except ValueError:
            start_date = month_start
    if end_raw:
        try:
            end_date = date.fromisoformat(end_raw)
        except ValueError:
            end_date = today
    if start_time_raw:
        try:
            start_time = time.fromisoformat(start_time_raw)
        except ValueError:
            start_time = time(0, 0)
    if end_time_raw:
        try:
            end_time = time.fromisoformat(end_time_raw)
        except ValueError:
            end_time = time(23, 59)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(start_dt, tz)
    end_dt = timezone.make_aware(end_dt, tz)

    income_total = (
        Order.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        .aggregate(total=Sum("total_price"))
        .get("total")
        or Decimal("0")
    )
    expense_total = (
        Expense.objects.filter(spent_on__gte=start_date, spent_on__lte=end_date)
        .aggregate(total=Sum("amount"))
        .get("total")
        or Decimal("0")
    )
    net_total = income_total - expense_total

    lines = [
        "BILIM UZ - Oylik hisobot",
        f"Davr: {start_date:%Y-%m-%d} {start_time:%H:%M} - {end_date:%Y-%m-%d} {end_time:%H:%M}",
        "",
        f"Kirim (sotuv): {_format_money(income_total)}",
        f"Chiqim: {_format_money(expense_total)}",
        f"Qoldiq: {_format_money(net_total)}",
        "",
        "Chiqimlar ro'yxati:",
        "Sana | Sarlavha | Summa",
        "-" * 60,
    ]
    for expense in Expense.objects.filter(spent_on__gte=start_date, spent_on__lte=end_date).order_by("-spent_on"):
        lines.append(f"{expense.spent_on:%Y-%m-%d} | {expense.title} | {_format_money(expense.amount)}")

    pdf_bytes = build_pdf(lines)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="bilimuz_monthly_report.pdf"'
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

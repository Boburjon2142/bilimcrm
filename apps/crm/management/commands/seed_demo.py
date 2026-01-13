from io import BytesIO
from random import choice, randint

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image

from apps.catalog.models import AboutPage, Author, Banner, Book, Category, FeaturedCategory
from apps.crm.models import Courier, Customer, Debt, Expense, InventoryLog
from apps.orders.models import (
    DeliveryNotice,
    DeliverySettings,
    DeliveryZone,
    Order,
    OrderItem,
)


def _make_image_file(name: str, size=(1200, 600), color=None) -> ContentFile:
    if color is None:
        color = (randint(20, 200), randint(40, 200), randint(80, 220))
    image = Image.new("RGB", size, color)
    buff = BytesIO()
    image.save(buff, format="PNG")
    return ContentFile(buff.getvalue(), name=name)


def _ensure_count(model, target, factory):
    existing = model.objects.count()
    for idx in range(existing, target):
        factory(idx, existing)


class Command(BaseCommand):
    help = "Seed demo data for all models (4 per model) for local/dev usage."

    def handle(self, *args, **options):
        _ensure_count(
            Author,
            4,
            lambda idx, offset: Author.objects.create(
                name=f"Muallif {idx + 1}",
                bio="Demo muallif.",
                is_featured=(idx % 2 == 0),
            ),
        )

        _ensure_count(
            Category,
            4,
            lambda idx, offset: Category.objects.create(
                name=f"Kategoriya {idx + 1}",
                slug=f"kategoriya-{idx + 1}",
            ),
        )

        categories = list(Category.objects.all()[:4])
        authors = list(Author.objects.all()[:4])

        _ensure_count(
            Book,
            4,
            lambda idx, offset: Book.objects.create(
                title=f"Kitob {idx + 1}",
                slug=f"kitob-{idx + 1}",
                category=categories[idx % len(categories)],
                author=authors[idx % len(authors)],
                purchase_price=randint(20000, 60000),
                sale_price=randint(60000, 120000),
                description="Demo kitob tavsifi.",
                book_format=choice(["hard", "soft"]),
                pages=randint(120, 420),
                stock_quantity=randint(10, 120),
                is_recommended=(idx % 2 == 0),
            ),
        )

        books = list(Book.objects.all()[:4])

        _ensure_count(
            FeaturedCategory,
            4,
            lambda idx, offset: FeaturedCategory.objects.create(
                category=categories[idx % len(categories)],
                title=f"Featured {idx + 1}",
                limit=randint(6, 12),
                order=idx,
                is_active=True,
            ),
        )

        _ensure_count(
            Banner,
            4,
            lambda idx, offset: Banner.objects.create(
                title=f"Banner {idx + 1}",
                image=_make_image_file(f"banner-{idx + 1}.png"),
                link="https://bilim.uz",
                order=idx,
                is_active=True,
            ),
        )

        _ensure_count(
            AboutPage,
            4,
            lambda idx, offset: AboutPage.objects.create(
                title=f"Biz haqimizda {idx + 1}",
                body="Demo matn.",
                link="https://bilim.uz",
                is_active=(idx % 2 == 0),
            ),
        )

        _ensure_count(
            Customer,
            4,
            lambda idx, offset: Customer.objects.create(
                full_name=f"Mijoz {idx + 1}",
                phone=f"+99890{1000000 + idx:07d}",
                email=f"mijoz{idx + 1}@bilim.uz",
                tags="demo",
                notes="Demo mijoz.",
                is_vip=(idx % 2 == 0),
                total_spent=randint(100000, 500000),
                orders_count=randint(1, 12),
                last_order_at=timezone.now() - timezone.timedelta(days=idx),
                discount_percent=randint(0, 10),
            ),
        )

        _ensure_count(
            Courier,
            4,
            lambda idx, offset: Courier.objects.create(
                name=f"Kuryer {idx + 1}",
                phone=f"+99893{2000000 + idx:07d}",
                telegram_username=f"kuryer{idx + 1}",
                is_active=True,
                last_active_at=timezone.now() - timezone.timedelta(hours=idx * 3),
            ),
        )

        customers = list(Customer.objects.all()[:4])
        couriers = list(Courier.objects.all()[:4])

        _ensure_count(
            Order,
            4,
            lambda idx, offset: Order.objects.create(
                full_name=customers[idx % len(customers)].full_name,
                phone=customers[idx % len(customers)].phone,
                address=f"Toshkent sh., kocha {idx + 1}",
                payment_type=choice(["cash", "bank"]),
                status=choice(["new", "paid", "assigned", "delivering"]),
                order_source=choice(["online", "pos"]),
                customer=customers[idx % len(customers)],
                courier=couriers[idx % len(couriers)],
                subtotal_before_discount=0,
                discount_percent=0,
                discount_amount=0,
                total_price=0,
                delivery_distance_km=round(randint(1, 12) + 0.4, 2),
                delivery_fee=randint(5000, 20000),
            ),
        )

        orders = list(Order.objects.all()[:4])

        _ensure_count(
            OrderItem,
            4,
            lambda idx, offset: OrderItem.objects.create(
                order=orders[idx % len(orders)],
                book=books[idx % len(books)],
                quantity=randint(1, 3),
                price=books[idx % len(books)].sale_price,
            ),
        )

        for order in orders:
            items = list(order.items.all())
            if not items:
                continue
            subtotal = sum(item.price * item.quantity for item in items)
            order.subtotal_before_discount = subtotal
            order.discount_amount = 0
            order.total_price = subtotal + order.delivery_fee
            order.save(update_fields=["subtotal_before_discount", "discount_amount", "total_price"])

        _ensure_count(
            InventoryLog,
            4,
            lambda idx, offset: InventoryLog.objects.create(
                book=books[idx % len(books)],
                delta=randint(-3, 12),
                reason=choice(["sale", "restock", "adjust", "cancel"]),
                related_order=orders[idx % len(orders)],
                note="Demo ombor yozuvi.",
            ),
        )

        _ensure_count(
            Expense,
            4,
            lambda idx, offset: Expense.objects.create(
                title=f"Chiqim {idx + 1}",
                amount=randint(50000, 300000),
                spent_on=timezone.localdate() - timezone.timedelta(days=idx * 2),
                note="Demo chiqim.",
            ),
        )

        _ensure_count(
            Debt,
            4,
            lambda idx, offset: Debt.objects.create(
                full_name=f"Qarzdor {idx + 1}",
                phone=f"+99891{3000000 + idx:07d}",
                amount=randint(80000, 400000),
                note="Demo qarz.",
                is_paid=(idx % 2 == 1),
            ),
        )

        _ensure_count(
            DeliveryZone,
            4,
            lambda idx, offset: DeliveryZone.objects.create(
                name=f"Zona {idx + 1}",
                mode="CIRCLE",
                center_lat=41.2995 + (idx * 0.01),
                center_lng=69.2401 + (idx * 0.01),
                radius_km=randint(2, 8),
                message="Demo zona.",
            ),
        )

        _ensure_count(
            DeliveryNotice,
            4,
            lambda idx, offset: DeliveryNotice.objects.create(
                title=f"Yetkazib berish eslatma {idx + 1}",
                body="Demo yetkazib berish xabari.",
                is_active=True,
            ),
        )

        _ensure_count(
            DeliverySettings,
            4,
            lambda idx, offset: DeliverySettings.objects.create(
                base_fee_uzs=10000 + idx * 1000,
                per_km_fee_uzs=2000,
                min_fee_uzs=10000,
                max_fee_uzs=60000,
                free_over_uzs=100000 + idx * 5000,
            ),
        )

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar yaratildi."))

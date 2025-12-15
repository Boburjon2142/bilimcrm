from decimal import Decimal
from django.conf import settings
from apps.catalog.models import Book


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def _normalize_quantity(self, quantity):
        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            qty = 1
        return max(qty, 0)

    def add(self, book_id, quantity=1):
        key = str(book_id)
        quantity = self._normalize_quantity(quantity)
        self.cart[key] = self.cart.get(key, 0) + quantity
        if self.cart[key] <= 0:
            self.cart.pop(key, None)
        self.save()

    def update(self, book_id, quantity):
        key = str(book_id)
        quantity = self._normalize_quantity(quantity)
        if quantity <= 0:
            self.cart.pop(key, None)
        else:
            self.cart[key] = quantity
        self.save()

    def remove(self, book_id):
        key = str(book_id)
        if key in self.cart:
            self.cart.pop(key)
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def items(self):
        book_ids = self.cart.keys()
        books = Book.objects.filter(id__in=book_ids)
        book_map = {str(book.id): book for book in books}
        for key, quantity in self.cart.items():
            book = book_map.get(key)
            if book:
                price = book.sale_price
                yield {
                    "book": book,
                    "quantity": quantity,
                    "price": price,
                    "line_total": Decimal(price) * quantity,
                }

    def total_price(self):
        return sum(item["line_total"] for item in self.items())

    def __len__(self):
        return sum(self.cart.values())

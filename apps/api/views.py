from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.catalog.models import Book, Category, Author
from apps.orders.models import Order
from apps.crm.models import Customer, Courier
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    CategorySerializer,
    OrderSerializer,
    CustomerSerializer,
    CourierSerializer,
)


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminUser]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.select_related("author", "category").all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUser]


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.prefetch_related("items__book").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]


class CourierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    permission_classes = [IsAdminUser]


@api_view(["GET"])
@permission_classes([IsAdminUser])
def cache_demo(request):
    key = "redis-demo:ping"
    payload = {"ts": timezone.now().isoformat()}
    cache.set(key, payload, timeout=60)
    cached = cache.get(key)
    backend = settings.CACHES["default"]["BACKEND"]
    return Response({"backend": backend, "cached": cached})

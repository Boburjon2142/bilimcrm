from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BookViewSet, CategoryViewSet, OrderViewSet, CustomerViewSet, CourierViewSet, cache_demo

router = DefaultRouter()
router.register("authors", AuthorViewSet)
router.register("categories", CategoryViewSet)
router.register("books", BookViewSet)
router.register("orders", OrderViewSet)
router.register("customers", CustomerViewSet)
router.register("couriers", CourierViewSet)

urlpatterns = [
    path("cache-demo/", cache_demo),
    path("", include(router.urls)),
]

from django.urls import path

from . import offline_views

urlpatterns = [
    path("products/", offline_views.offline_products, name="offline_products"),
    path("sales/", offline_views.offline_sales, name="offline_sales"),
    path("expenses/", offline_views.offline_expenses, name="offline_expenses"),
    path("status/", offline_views.offline_status, name="offline_status"),
]

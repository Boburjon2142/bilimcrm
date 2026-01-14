from django.urls import path

from . import admin_views, views

urlpatterns = [
    path("", views.dashboard, name="crm_dashboard"),
    path("export/report.pdf", views.export_report_pdf, name="crm_export_report_pdf"),
    path("export/orders.pdf", views.export_orders_pdf, name="crm_export_orders_pdf"),
    path("export/sales.pdf", views.export_sales_pdf, name="crm_export_sales_pdf"),
    path("export/monthly.pdf", views.export_monthly_report_pdf, name="crm_export_monthly_report_pdf"),
    path("cleanup/", views.cleanup_data, name="crm_cleanup"),
    path("report/", views.monthly_report, name="crm_report"),
    path("entry/", views.entry_list, name="crm_entry"),
    path("prices/", views.prices_list, name="crm_prices"),
    path("expenses/", views.expenses_list, name="crm_expenses"),
    path("debts/", views.debts_list, name="crm_debts"),
    path("orders/", views.orders_list, name="crm_orders"),
    path("customers/", views.customers_list, name="crm_customers"),
    path("customers/<int:customer_id>/", views.customer_detail, name="crm_customer_detail"),
    path("couriers/", views.couriers_list, name="crm_couriers"),
    path("inventory/", views.inventory_list, name="crm_inventory"),
    path("pos/", views.pos_checkout, name="crm_pos"),
    path("search/", views.search, name="crm_search"),
    path("admin/", admin_views.admin_index, name="crm_admin_index"),
    path("admin/<str:app_label>/<str:model_name>/", admin_views.admin_list, name="crm_admin_list"),
    path("admin/<str:app_label>/<str:model_name>/add/", admin_views.admin_create, name="crm_admin_add"),
    path("admin/<str:app_label>/<str:model_name>/<int:pk>/edit/", admin_views.admin_update, name="crm_admin_edit"),
    path("admin/<str:app_label>/<str:model_name>/<int:pk>/delete/", admin_views.admin_delete, name="crm_admin_delete"),
]

from django.contrib import admin
from django.utils.html import format_html

from .models import DeliveryNotice, DeliveryZone, Order, OrderItem, DeliverySettings
from .services.delivery import build_courier_url, generate_google_maps_link, recalculate_delivery


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "delivery_fee",
        "delivery_distance_km",
        "delivery_zone_status",
        "maps_link_display",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_type", "created_at", "delivery_zone_status")
    inlines = [OrderItemInline]
    search_fields = ("full_name", "phone", "location", "address_text")
    readonly_fields = (
        "total_price",
        "delivery_distance_km",
        "delivery_fee",
        "delivery_zone_status",
        "maps_link",
        "courier_maps_url",
        "delivery_pricing_snapshot",
    )
    actions = ["recalculate_delivery_action"]

    @admin.display(description="Xarita")
    def maps_link_display(self, obj):
        if obj.latitude and obj.longitude:
            url = obj.maps_link or generate_google_maps_link(float(obj.latitude), float(obj.longitude))
            return format_html('<a href="{}" target="_blank" rel="noopener">Open in Maps</a>', url)
        return "—"

    @admin.action(description="Yetkazib berishni qayta hisoblash")
    def recalculate_delivery_action(self, request, queryset):
        for order in queryset:
            recalculate_delivery(order)
        self.message_user(request, f"{queryset.count()} ta buyurtma uchun qayta hisoblandi.")


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "mode", "is_active", "message")
    list_filter = ("mode", "is_active")
    search_fields = ("name", "message")


@admin.register(DeliveryNotice)
class DeliveryNoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "body")


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ("base_fee_uzs", "per_km_fee_uzs", "min_fee_uzs", "max_fee_uzs", "free_over_uzs", "updated_at")

    def has_add_permission(self, request):
        # Enforce singleton: allow add only if none exists.
        if DeliverySettings.objects.exists():
            return False
        return super().has_add_permission(request)

"""Delivery calculation helpers (distance, fee, zones, map links)."""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple

from django.conf import settings

from ..models import DeliveryZone, Order

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in km between two coordinates."""
    lat1_rad, lng1_rad, lat2_rad, lng2_rad = map(math.radians, [lat1, lng1, lat2, lng2])
    d_lat = lat2_rad - lat1_rad
    d_lng = lng2_rad - lng1_rad
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def _round_to_nearest(value: Decimal, base_unit: int = 1000) -> Decimal:
    """Round Decimal to nearest base_unit (e.g., 1000 UZS)."""
    if base_unit <= 0:
        return value
    scaled = (value / Decimal(base_unit)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return scaled * Decimal(base_unit)


def compute_delivery_fee(distance_km: Decimal, subtotal: Decimal) -> Tuple[int, Dict]:
    """Compute delivery fee based on settings and distance."""
    base_fee = Decimal(settings.DELIVERY_BASE_FEE_UZS)
    per_km_fee = Decimal(settings.DELIVERY_PER_KM_FEE_UZS)
    min_fee = Decimal(settings.DELIVERY_MIN_FEE_UZS)
    max_fee = Decimal(settings.DELIVERY_MAX_FEE_UZS)
    free_over = settings.DELIVERY_FREE_OVER_UZS

    raw_fee = base_fee + (per_km_fee * distance_km)

    if free_over is not None and subtotal >= Decimal(free_over):
        raw_fee = Decimal("0")

    if raw_fee > 0:
        clamped_fee = min(max(raw_fee, min_fee), max_fee)
    else:
        clamped_fee = raw_fee

    rounded_fee = _round_to_nearest(clamped_fee, 1000)
    fee_int = int(rounded_fee)

    snapshot = {
        "base_fee": int(base_fee),
        "per_km": float(per_km_fee),
        "distance_km": float(distance_km),
        "raw_fee": float(raw_fee),
        "rounded_fee": fee_int,
        "min_fee": int(min_fee),
        "max_fee": int(max_fee),
        "free_over": free_over,
        "subtotal": float(subtotal),
    }
    return fee_int, snapshot


def _matches_circle(zone: DeliveryZone, lat: float, lng: float) -> bool:
    if zone.center_lat is None or zone.center_lng is None or zone.radius_km is None:
        return False
    distance = haversine_distance_km(float(zone.center_lat), float(zone.center_lng), lat, lng)
    return distance <= float(zone.radius_km)


def _matches_bbox(zone: DeliveryZone, lat: float, lng: float) -> bool:
    return (
        zone.min_lat is not None
        and zone.min_lng is not None
        and zone.max_lat is not None
        and zone.max_lng is not None
        and float(zone.min_lat) <= lat <= float(zone.max_lat)
        and float(zone.min_lng) <= lng <= float(zone.max_lng)
    )


def check_zone_block(lat: float, lng: float) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Returns (is_blocked, message, zone_id).
    Rule: BLOCKED zones (is_active=False) take priority if multiple zones match.
    """
    blocked_match: Optional[DeliveryZone] = None
    allowed_match: Optional[DeliveryZone] = None

    for zone in DeliveryZone.objects.all():
        if zone.mode == "CIRCLE":
            matched = _matches_circle(zone, lat, lng)
        else:
            matched = _matches_bbox(zone, lat, lng)
        if not matched:
            continue
        if not zone.is_active:
            blocked_match = zone
        elif allowed_match is None:
            allowed_match = zone

    if blocked_match:
        return True, blocked_match.message or None, blocked_match.id
    if allowed_match:
        return False, allowed_match.message or None, allowed_match.id
    return False, None, None


def build_courier_url(lat: float, lng: float) -> str:
    origin = f"{settings.SHOP_LAT},{settings.SHOP_LNG}"
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origin}"
        f"&destination={lat},{lng}"
        "&travelmode=driving"
    )


def generate_google_maps_link(lat: float, lng: float) -> str:
    """Plain maps link (no directions)."""
    return f"https://www.google.com/maps?q={lat},{lng}"


def recalculate_delivery(order: Order, save: bool = True) -> Order:
    """
    Compute and persist delivery-related fields for an order.
    Caller should ensure order has latitude/longitude when delivery is needed.
    """
    has_coords = order.latitude is not None and order.longitude is not None
    distance_decimal = Decimal("0.00")
    courier_url = ""
    zone_message = None
    zone_id = None
    blocked = False

    if has_coords:
        distance_km = haversine_distance_km(
            float(settings.SHOP_LAT),
            float(settings.SHOP_LNG),
            float(order.latitude),
            float(order.longitude),
        )
        distance_decimal = Decimal(distance_km).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        blocked, zone_message, zone_id = check_zone_block(float(order.latitude), float(order.longitude))
        courier_url = build_courier_url(float(order.latitude), float(order.longitude))

    subtotal = order.total_price or Decimal("0")
    if blocked or not has_coords:
        fee_int = 0
        fee_snapshot = {
            "base_fee": int(settings.DELIVERY_BASE_FEE_UZS),
            "per_km": float(settings.DELIVERY_PER_KM_FEE_UZS),
            "distance_km": float(distance_decimal),
            "raw_fee": 0,
            "rounded_fee": 0,
            "min_fee": int(settings.DELIVERY_MIN_FEE_UZS),
            "max_fee": int(settings.DELIVERY_MAX_FEE_UZS),
            "free_over": settings.DELIVERY_FREE_OVER_UZS,
            "subtotal": float(subtotal),
        }
    else:
        fee_int, fee_snapshot = compute_delivery_fee(distance_decimal, subtotal)

    snapshot = {
        **fee_snapshot,
        "zone_status": "BLOCKED" if blocked else "OK",
        "zone_message": zone_message,
        "zone_id": zone_id,
        "has_coordinates": has_coords,
    }

    order.delivery_distance_km = distance_decimal
    order.delivery_fee = fee_int
    order.delivery_zone_status = "BLOCKED" if blocked else "OK"
    order.courier_maps_url = courier_url
    order.delivery_pricing_snapshot = snapshot

    if save:
        order.save(
            update_fields=[
                "delivery_distance_km",
                "delivery_fee",
                "delivery_zone_status",
                "courier_maps_url",
                "delivery_pricing_snapshot",
                "maps_link",
            ]
        )
    return order

import re

from django import template

register = template.Library()


@register.filter
def attr(obj, name):
    value = getattr(obj, name, "")
    if callable(value):
        return value()
    return value


@register.filter
def field_value(obj, field):
    if not field:
        return ""
    if getattr(field, "choices", None):
        display = getattr(obj, f"get_{field.name}_display", None)
        if callable(display):
            return display()
    value = getattr(obj, field.name, "")
    if callable(value):
        return value()
    return value


@register.filter
def phone(value):
    raw = "" if value is None else str(value).strip()
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 12 and digits.startswith("998"):
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:12]}"
    if len(digits) == 9:
        return f"+998 {digits[:2]} {digits[2:5]} {digits[5:7]} {digits[7:9]}"
    return raw

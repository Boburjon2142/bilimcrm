from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name",
            "phone",
            "extra_phone",
            "location",
            "address",
            "latitude",
            "longitude",
            "maps_link",
            "note",
            "payment_type",
        ]
        labels = {
            "address": "Mo'ljal",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "F.I.Sh"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+998 90 123 45 67"}),
            "extra_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Qo‘shimcha raqam (ixtiyoriy)"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Lokatsiya (shahar/tuman yoki GPS)"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Mo‘ljal (masalan: Atlas savdo markazi)"}),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
            "maps_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Google Maps havolasini kiriting (ixtiyoriy)",
                    "id": "id_maps_link",
                }
            ),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Izoh"}),
            "payment_type": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("latitude")
        lng = cleaned.get("longitude")
        if (lat and lng) or (lat is None and lng is None):
            pass
        else:
            raise forms.ValidationError("Kenglik va uzunlik birga yuborilishi kerak.")

        if lat is not None:
            if not (-90 <= float(lat) <= 90):
                self.add_error("latitude", "Kenglik noto‘g‘ri.")
        if lng is not None:
            if not (-180 <= float(lng) <= 180):
                self.add_error("longitude", "Uzunlik noto‘g‘ri.")
        return cleaned

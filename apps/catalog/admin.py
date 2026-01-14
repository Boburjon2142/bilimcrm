from django.contrib import admin
from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Author, Category, Book, Banner, FeaturedCategory, AboutPage


_EAN13_L_CODES = {
    "0": "0001101",
    "1": "0011001",
    "2": "0010011",
    "3": "0111101",
    "4": "0100011",
    "5": "0110001",
    "6": "0101111",
    "7": "0111011",
    "8": "0110111",
    "9": "0001011",
}
_EAN13_G_CODES = {
    "0": "0100111",
    "1": "0110011",
    "2": "0011011",
    "3": "0100001",
    "4": "0011101",
    "5": "0111001",
    "6": "0000101",
    "7": "0010001",
    "8": "0001001",
    "9": "0010111",
}
_EAN13_R_CODES = {
    "0": "1110010",
    "1": "1100110",
    "2": "1101100",
    "3": "1000010",
    "4": "1011100",
    "5": "1001110",
    "6": "1010000",
    "7": "1000100",
    "8": "1001000",
    "9": "1110100",
}
_EAN13_PARITY = {
    "0": "AAAAAA",
    "1": "AABABB",
    "2": "AABBAB",
    "3": "AABBBA",
    "4": "ABAABB",
    "5": "ABBAAB",
    "6": "ABBBAA",
    "7": "ABABAB",
    "8": "ABABBA",
    "9": "ABBABA",
}


def _ean13_bits(barcode: str) -> str:
    first = barcode[0]
    left = barcode[1:7]
    right = barcode[7:]
    parity = _EAN13_PARITY[first]
    bits = "101"
    for idx, digit in enumerate(left):
        if parity[idx] == "A":
            bits += _EAN13_L_CODES[digit]
        else:
            bits += _EAN13_G_CODES[digit]
    bits += "01010"
    for digit in right:
        bits += _EAN13_R_CODES[digit]
    bits += "101"
    return bits


def _build_ean13_pdf(barcode: str, width_mm: float = 54.2, height_mm: float = 32.0) -> bytes:
    points_per_mm = 72.0 / 25.4
    page_width = width_mm * points_per_mm
    page_height = height_mm * points_per_mm
    bits = _ean13_bits(barcode)
    quiet = 10
    total_modules = quiet * 2 + len(bits)
    module = page_width / total_modules
    top_margin = 2.0 * points_per_mm
    bottom_margin = 6.0 * points_per_mm
    guard_height = page_height - top_margin - bottom_margin
    bar_height = guard_height * 0.9
    start_x = quiet * module
    y = bottom_margin
    rects = []
    for idx, bit in enumerate(bits):
        if bit != "1":
            continue
        is_guard = idx < 3 or 45 <= idx < 50 or idx >= 92
        height = guard_height if is_guard else bar_height
        x = start_x + idx * module
        rects.append(f"{x:.2f} {y:.2f} {module:.2f} {height:.2f} re f")
    text_size = 9.0
    text_y = 2.0 * points_per_mm
    text_width = text_size * 0.6 * len(barcode)
    text_x = start_x + (len(bits) * module - text_width) / 2.0
    content = "\n".join(rects)
    text = (
        "BT\n"
        f"/F1 {text_size:.2f} Tf\n"
        f"1 0 0 1 {text_x:.2f} {text_y:.2f} Tm\n"
        f"({barcode}) Tj\n"
        "ET"
    )
    stream = f"0 0 0 rg\n{content}\n{text}\n"
    stream_bytes = stream.encode("ascii")
    objects = []
    objects.append(
        b"<< /Type /Catalog /Pages 2 0 R "
        b"/ViewerPreferences << /PrintScaling /None /PickTrayByPDFSize true >> >>"
    )
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width:.2f} {page_height:.2f}] "
        f"/Rotate 0 /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>".encode("ascii")
    )
    objects.append(
        f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
        + stream_bytes
        + b"endstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    xref = []
    pdf = [b"%PDF-1.4\n"]
    for i, obj in enumerate(objects, start=1):
        xref.append(sum(len(part) for part in pdf))
        pdf.append(f"{i} 0 obj\n".encode("ascii"))
        pdf.append(obj)
        pdf.append(b"\nendobj\n")
    xref_start = sum(len(part) for part in pdf)
    pdf.append(b"xref\n")
    pdf.append(f"0 {len(objects) + 1}\n".encode("ascii"))
    pdf.append(b"0000000000 65535 f \n")
    for offset in xref:
        pdf.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return b"".join(pdf)


class BookInline(admin.TabularInline):
    model = Book
    extra = 0
    fields = ("title", "category", "sale_price")
    readonly_fields = ("title", "category", "sale_price")


class BookAdminForm(forms.ModelForm):
    author_name = forms.CharField(label="Muallif", required=True)

    class Meta:
        model = Book
        fields = [
            "title",
            "slug",
            "category",
            "author_name",
            "purchase_price",
            "sale_price",
            "barcode",
            "stock_quantity",
            "description",
            "cover_image",
            "book_format",
            "pages",
            "is_recommended",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.author_id:
            self.fields["author_name"].initial = self.instance.author.name

    def save(self, commit=True):
        author_name = self.cleaned_data.get("author_name", "").strip()
        author_obj, _ = Author.objects.get_or_create(name=author_name)
        self.instance.author = author_obj
        return super().save(commit=commit)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured")
    search_fields = ("name",)
    list_editable = ("is_featured",)
    inlines = [BookInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "purchase_price",
        "sale_price",
        "barcode",
        "stock_quantity",
        "is_recommended",
        "views",
        "created_at",
    )
    list_editable = ("purchase_price", "sale_price", "barcode")
    list_filter = ("category", "author", "is_recommended", "book_format")
    search_fields = ("title", "author__name", "barcode")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category",)
    form = BookAdminForm
    readonly_fields = ("barcode_download",)

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if "barcode_download" not in fields:
            fields.append("barcode_download")
        return fields

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:book_id>/barcode/",
                self.admin_site.admin_view(self.barcode_svg_view),
                name="catalog_book_barcode",
            ),
        ]
        return custom_urls + urls

    def barcode_svg_view(self, request, book_id: int):
        book = get_object_or_404(Book, pk=book_id)
        if not book.barcode:
            book.barcode = Book.generate_barcode_from_id(book.id)
            book.save(update_fields=["barcode"])
        pdf_bytes = _build_ean13_pdf(book.barcode)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="barcode-{book.barcode}.pdf"'
        return response

    def barcode_download(self, obj):
        if not obj or not obj.pk:
            return "Saqlangandan keyin paydo bo'ladi."
        url = reverse("admin:catalog_book_barcode", args=[obj.pk])
        label = obj.barcode or "Barcode generatsiya"
        return format_html('<a href="{}">Yuklab olish ({})</a>', url, label)

    barcode_download.short_description = "Barcode (PDF)"


@admin.register(FeaturedCategory)
class FeaturedCategoryAdmin(admin.ModelAdmin):
    list_display = ("category", "title", "limit", "order", "is_active")
    list_editable = ("limit", "order", "is_active")
    search_fields = ("category__name", "title")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "created_at")
    list_editable = ("order", "is_active")


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "updated_at")
    list_editable = ("is_active",)
    search_fields = ("title", "body")

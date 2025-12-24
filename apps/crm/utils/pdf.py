from io import BytesIO
from textwrap import wrap


PAGE_WIDTH = 842
PAGE_HEIGHT = 595
MARGIN_X = 10
MARGIN_Y = 40
LINE_HEIGHT = 14
MAX_CHARS = 150


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _normalize(text: str) -> str:
    return (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("`", "'")
        .replace("ʼ", "'")
    )


def _split_lines(lines):
    for line in lines:
        line = _normalize(line)
        if not line:
            yield ""
            continue
        for part in wrap(line, MAX_CHARS):
            yield part


def _paginate(lines):
    max_lines = int((PAGE_HEIGHT - (2 * MARGIN_Y)) / LINE_HEIGHT)
    pages = []
    current = []
    for line in _split_lines(lines):
        if len(current) >= max_lines:
            pages.append(current)
            current = []
        current.append(line)
    if current:
        pages.append(current)
    return pages


def _build_page_stream(lines):
    y_start = PAGE_HEIGHT - MARGIN_Y
    x_start = MARGIN_X
    parts = [
        "BT",
        "/F1 9 Tf",
        f"{x_start} {y_start} Td",
    ]
    for line in lines:
        parts.append(f"({_escape(line)}) Tj")
        parts.append(f"0 -{LINE_HEIGHT} Td")
    parts.append("ET")
    return "\n".join(parts)


def build_pdf(lines):
    pages = _paginate(lines)
    page_count = len(pages) or 1
    pages_obj_num = (2 * page_count) + 2
    font_obj_num = 1

    objects = []

    # 1: font
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    # 2..: content + page pairs
    for idx, page_lines in enumerate(pages or [[""]], start=1):
        content_obj_num = 2 * idx
        page_obj_num = 2 * idx + 1
        stream = _build_page_stream(page_lines)
        stream_bytes = stream.encode("utf-8")
        objects.append(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream")
        objects.append(
            "<< /Type /Page "
            f"/Parent {pages_obj_num} 0 R "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {content_obj_num} 0 R >>"
        )

    # pages object
    kids = " ".join([f"{2 * i + 1} 0 R" for i in range(1, page_count + 1)])
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>")
    # catalog
    objects.append(f"<< /Type /Catalog /Pages {pages_obj_num} 0 R >>")

    # Build PDF
    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{i} 0 obj\n".encode("utf-8"))
        buffer.write(obj.encode("utf-8"))
        buffer.write(b"\nendobj\n")

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {len(offsets)}\n".encode("utf-8"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("utf-8"))
    buffer.write(b"trailer\n")
    buffer.write(f"<< /Size {len(offsets)} /Root {len(objects)} 0 R >>\n".encode("utf-8"))
    buffer.write(f"startxref\n{xref_start}\n%%EOF".encode("utf-8"))
    return buffer.getvalue()

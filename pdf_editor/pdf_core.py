"""Các thao tác xử lý PDF (không phụ thuộc giao diện).

Dùng thư viện PyMuPDF (pip install pymupdf).
"""
import os
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- phông chữ
# Phông chuẩn của PDF (Helvetica, Times...) KHÔNG có dấu tiếng Việt,
# nên luôn dùng một file .ttf có hỗ trợ tiếng Việt.
_FONT_CANDIDATES = {
    "Arial": ["C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"],
    "Arial Đậm": ["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    "Times New Roman": ["C:/Windows/Fonts/times.ttf",
                        "/System/Library/Fonts/Supplemental/Times New Roman.ttf"],
    "Times New Roman Đậm": ["C:/Windows/Fonts/timesbd.ttf",
                            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"],
    "Tahoma": ["C:/Windows/Fonts/tahoma.ttf", "/System/Library/Fonts/Supplemental/Tahoma.ttf"],
    "Calibri": ["C:/Windows/Fonts/calibri.ttf"],
    "Segoe UI": ["C:/Windows/Fonts/segoeui.ttf"],
    "DejaVu Sans": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "DejaVu Serif": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "Noto Serif (kèm theo)": [os.path.join(HERE, "fonts", "NotoSerif-Regular.ttf")],
}


def available_fonts():
    """Trả về {tên hiển thị: đường dẫn .ttf} của các phông có trên máy."""
    out = {}
    for name, paths in _FONT_CANDIDATES.items():
        for p in paths:
            if os.path.exists(p):
                out[name] = p
                break
    return out


def default_font():
    fonts = available_fonts()
    for pref in ("Arial", "Times New Roman", "DejaVu Sans", "Noto Serif (kèm theo)"):
        if pref in fonts:
            return pref, fonts[pref]
    name = next(iter(fonts))
    return name, fonts[name]


def _font_alias(path):
    """Tên nội bộ ngắn, ổn định cho mỗi file phông."""
    base = os.path.splitext(os.path.basename(path))[0]
    return "F" + "".join(ch for ch in base if ch.isalnum())[:20]


def hex_to_rgb(color):
    """'#ff0000' -> (1.0, 0.0, 0.0)"""
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------------------------------------------------------------- mở / lưu
def open_pdf(path, password=None):
    doc = pymupdf.open(path)
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise PermissionError("Sai mật khẩu hoặc tệp cần mật khẩu.")
    return doc


def save_pdf(doc, path, compress=True, user_pw=None, owner_pw=None):
    """Lưu PDF. Nếu path trùng file đang mở thì lưu ra file tạm rồi thay thế."""
    kw = dict(garbage=4 if compress else 1, deflate=compress, clean=compress)
    if user_pw or owner_pw:
        kw.update(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                  user_pw=user_pw or "", owner_pw=owner_pw or user_pw or "",
                  permissions=-1)
    same = doc.name and os.path.abspath(doc.name) == os.path.abspath(path)
    if same:
        tmp = path + ".tmp_save"
        doc.save(tmp, **kw)
        return tmp  # người gọi đóng doc rồi os.replace(tmp, path)
    doc.save(path, **kw)
    return None


# ---------------------------------------------------------------- trang
def rotate_pages(doc, pages, angle):
    for i in pages:
        p = doc[i]
        p.set_rotation((p.rotation + angle) % 360)


def delete_pages(doc, pages):
    if len(pages) >= len(doc):
        raise ValueError("Không thể xóa hết tất cả các trang.")
    doc.delete_pages(sorted(pages))


def move_page(doc, src, dst):
    """Chuyển trang src tới vị trí dst (đánh số từ 0)."""
    if src == dst:
        return
    doc.move_page(src, dst if dst < src else dst + 1)


def insert_blank_page(doc, after, like=None):
    ref = doc[like if like is not None else max(after, 0)] if len(doc) else None
    w, h = (ref.rect.width, ref.rect.height) if ref else pymupdf.paper_size("a4")
    doc.new_page(pno=after + 1, width=w, height=h)


def duplicate_page(doc, i):
    doc.fullcopy_page(i, i + 1)


def parse_ranges(text, n):
    """'1-3, 5, 8-' -> [0,1,2,4,7,...]. Đánh số từ 1 theo người dùng."""
    out = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a) if a.strip() else 1
            b = int(b) if b.strip() else n
        else:
            a = b = int(part)
        if a < 1 or b > n or a > b:
            raise ValueError(f"Khoảng trang không hợp lệ: '{part}' (tài liệu có {n} trang)")
        out.extend(range(a - 1, b))
    if not out:
        raise ValueError("Chưa nhập trang nào.")
    return out


def extract_pages(doc, pages, out_path):
    new = pymupdf.open()
    for i in pages:
        new.insert_pdf(doc, from_page=i, to_page=i)
    new.save(out_path, garbage=4, deflate=True)
    new.close()


def split_every(doc, n_each, out_dir, base="tach"):
    files = []
    for start in range(0, len(doc), n_each):
        end = min(start + n_each, len(doc)) - 1
        path = os.path.join(out_dir, f"{base}_trang_{start + 1}-{end + 1}.pdf")
        extract_pages(doc, range(start, end + 1), path)
        files.append(path)
    return files


def merge_pdfs(paths, out_path):
    out = pymupdf.open()
    for p in paths:
        if p.lower().endswith(".pdf"):
            with pymupdf.open(p) as src:
                out.insert_pdf(src)
        else:  # ảnh
            _append_image_page(out, p)
    out.save(out_path, garbage=4, deflate=True)
    out.close()


def _append_image_page(doc, img_path):
    with pymupdf.open(img_path) as img:
        rect = img[0].rect
        pdfbytes = img.convert_to_pdf()
    with pymupdf.open("pdf", pdfbytes) as ip:
        page = doc.new_page(width=rect.width, height=rect.height)
        page.show_pdf_page(rect, ip, 0)


def images_to_pdf(img_paths, out_path):
    doc = pymupdf.open()
    for p in img_paths:
        _append_image_page(doc, p)
    doc.save(out_path, garbage=4, deflate=True)
    doc.close()


def insert_pdf_file(doc, path, after):
    with pymupdf.open(path) as src:
        doc.insert_pdf(src, start_at=after + 1)


# ---------------------------------------------------------------- toạ độ
def view_to_pdf_point(page, x, y):
    """Toạ độ trên trang đang hiển thị (đã xoay, đơn vị điểm) -> toạ độ PDF gốc."""
    return pymupdf.Point(x, y) * page.derotation_matrix


def view_to_pdf_rect(page, rect):
    r = pymupdf.Rect(rect) * page.derotation_matrix
    r.normalize()
    return r


# ---------------------------------------------------------------- nội dung
def add_text(page, x, y, text, size=12, color="#000000", fontfile=None):
    """Thêm chữ; (x, y) là góc trên-trái theo toạ độ hiển thị."""
    if fontfile is None:
        fontfile = default_font()[1]
    alias = _font_alias(fontfile)
    pt = view_to_pdf_point(page, x, y + size)  # insert_text dùng đường chân chữ
    page.insert_text(pt, text, fontsize=size, fontname=alias, fontfile=fontfile,
                     color=hex_to_rgb(color), rotate=page.rotation)


def add_image(page, view_rect, img_path, keep_ratio=True):
    page.insert_image(view_to_pdf_rect(page, view_rect), filename=img_path,
                      keep_proportion=keep_ratio, rotate=0)


def whiteout(page, view_rect, color="#ffffff"):
    """Che (xoá hẳn) nội dung trong vùng: chữ bên dưới bị xoá thật, không chỉ bị phủ."""
    r = view_to_pdf_rect(page, view_rect)
    page.add_redact_annot(r, fill=hex_to_rgb(color))
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS)


def highlight(page, view_rect):
    r = view_to_pdf_rect(page, view_rect)
    words = [pymupdf.Rect(w[:4]) for w in page.get_text("words") if pymupdf.Rect(w[:4]).intersects(r)]
    annot = page.add_highlight_annot(words if words else r)
    annot.update()


def draw_rect(page, view_rect, color="#ff0000", width=1.5):
    annot = page.add_rect_annot(view_to_pdf_rect(page, view_rect))
    annot.set_border(width=width)
    annot.set_colors(stroke=hex_to_rgb(color))
    annot.update()


def add_note(page, x, y, text):
    annot = page.add_text_annot(view_to_pdf_point(page, x, y), text, icon="Note")
    annot.set_info(title="Ghi chú")
    annot.update()


def _span_at(page, rect):
    """Lấy cỡ chữ, màu, điểm chân chữ của đoạn chữ tại vị trí rect."""
    best = None
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                sr = pymupdf.Rect(sp["bbox"])
                if sr.intersects(rect):
                    area = (sr & rect).get_area()
                    if best is None or area > best[0]:
                        best = (area, sp)
    return best[1] if best else None


def _span_rgb(c):
    return ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255


def replace_text(doc, find, repl, pages=None, fontfile=None, match_case=True):
    """Tìm & thay chữ thật sự trong PDF. Trả về số chỗ đã thay.

    Cả dòng chứa chữ cần thay được viết lại (giữ cỡ chữ và màu), nên chữ phía
    sau tự dịch theo khi chữ mới dài/ngắn hơn chữ cũ.
    """
    if not find:
        return 0
    if fontfile is None:
        fontfile = default_font()[1]
    alias = _font_alias(fontfile)
    font = pymupdf.Font(fontfile=fontfile)
    total = 0

    def rep(t):
        if match_case:
            return t.replace(find, repl), t.count(find)
        import re
        pat = re.compile(re.escape(find), re.IGNORECASE)
        return pat.subn(lambda m: repl, t)

    for pno in (pages if pages is not None else range(len(doc))):
        page = doc[pno]
        jobs = []
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                spans = [sp for sp in ln["spans"] if sp["text"]]
                line_text = "".join(sp["text"] for sp in spans)
                _, n = rep(line_text)
                if not n or ln["dir"] != (1.0, 0.0):
                    continue
                # thay trong từng span; nếu chữ cần tìm nằm vắt qua 2 span thì gộp cả dòng
                new_spans, cnt = [], 0
                for sp in spans:
                    t, k = rep(sp["text"])
                    cnt += k
                    new_spans.append((t, sp["size"], _span_rgb(sp["color"]), sp["origin"]))
                if cnt < n:
                    sp0 = spans[0]
                    t, cnt = rep(line_text)
                    new_spans = [(t, sp0["size"], _span_rgb(sp0["color"]), sp0["origin"])]
                jobs.append((pymupdf.Rect(ln["bbox"]), new_spans))
                total += cnt
        if not jobs:
            continue
        for r, _ in jobs:
            page.add_redact_annot(r, fill=False)  # chỉ xoá chữ, giữ nền/khung/ảnh
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        for r, new_spans in jobs:
            x = new_spans[0][3][0]
            for t, size, color, origin in new_spans:
                page.insert_text(pymupdf.Point(x, origin[1]), t, fontsize=size,
                                 fontname=alias, fontfile=fontfile, color=color)
                x += font.text_length(t, fontsize=size)
    return total


def search_text(doc, find):
    """Trả về [(trang, Rect), ...]"""
    res = []
    for pno, page in enumerate(doc):
        for r in page.search_for(find):
            res.append((pno, r))
    return res


def highlight_all(doc, find):
    n = 0
    for pno, r in search_text(doc, find):
        doc[pno].add_highlight_annot(r).update()
        n += 1
    return n


def watermark(doc, text, size=60, color="#c0c0c0", opacity=0.35, fontfile=None):
    if fontfile is None:
        fontfile = default_font()[1]
    font = pymupdf.Font(fontfile=fontfile)
    rgb = hex_to_rgb(color)
    for page in doc:
        r = page.cropbox if page.rotation else page.rect
        r = pymupdf.Rect(0, 0, r.width, r.height)
        tw = pymupdf.TextWriter(r, opacity=opacity, color=rgb)
        width = font.text_length(text, fontsize=size)
        center = pymupdf.Point(r.width / 2, r.height / 2)
        tw.append(center - (width / 2, -size / 3), text, font=font, fontsize=size)
        view_w, view_h = page.rect.width, page.rect.height
        mat = pymupdf.Matrix((-45 if view_w < view_h else -30) + page.rotation)
        tw.write_text(page, morph=(center, mat), overlay=True)


def add_page_numbers(doc, fmt="Trang {n}/{total}", size=10, position="giữa dưới", fontfile=None):
    if fontfile is None:
        fontfile = default_font()[1]
    alias = _font_alias(fontfile)
    font = pymupdf.Font(fontfile=fontfile)
    total = len(doc)
    for i, page in enumerate(doc):
        s = fmt.format(n=i + 1, total=total)
        w = font.text_length(s, fontsize=size)
        r = page.rect
        x = {"trái dưới": 36, "phải dưới": r.width - 36 - w}.get(position, (r.width - w) / 2)
        pt = pymupdf.Point(x, r.height - 24)
        page.insert_text(pt * page.derotation_matrix, s, fontsize=size, fontname=alias,
                         fontfile=fontfile, rotate=page.rotation)


def extract_text(doc):
    return "\n\n".join(f"===== Trang {i + 1} =====\n{p.get_text()}" for i, p in enumerate(doc))


def export_images(doc, out_dir, dpi=150, pages=None, base="trang"):
    files = []
    for i in (pages if pages is not None else range(len(doc))):
        pix = doc[i].get_pixmap(dpi=dpi)
        path = os.path.join(out_dir, f"{base}_{i + 1:03d}.png")
        pix.save(path)
        files.append(path)
    return files


def compress(doc, out_path, image_dpi=110, quality=70):
    """Nén: giảm độ phân giải ảnh + dọn rác. Trả về (kích thước cũ, mới) theo byte."""
    old = len(doc.tobytes())
    tmp = pymupdf.open("pdf", doc.tobytes())
    try:
        tmp.rewrite_images(dpi_threshold=image_dpi + 10, dpi_target=image_dpi, quality=quality)
    except AttributeError:  # PyMuPDF quá cũ, bỏ qua bước nén ảnh
        pass
    tmp.save(out_path, garbage=4, deflate=True, clean=True)
    tmp.close()
    return old, os.path.getsize(out_path)


def set_metadata(doc, title=None, author=None, subject=None):
    md = doc.metadata or {}
    for k, v in (("title", title), ("author", author), ("subject", subject)):
        if v is not None:
            md[k] = v
    doc.set_metadata(md)


if __name__ == "__main__":
    print("Đây là thư viện. Chạy giao diện bằng: python pdf_editor.py")
    sys.exit(0)

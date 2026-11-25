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


# ================================================================ khớp phông gốc
_STYLE_WORDS = ("bolditalic", "boldoblique", "semibold", "demibold", "extrabold", "bold", "italic",
                "oblique", "regular", "roman", "normal", "medium", "light", "black", "heavy", "book",
                "condensed", "narrow", "semilight", "thin")
_font_index_cache = None


def _strip_subset(name):
    """'ABCDEF+Arial-BoldMT' -> 'Arial-BoldMT'"""
    if len(name) > 7 and name[6] == "+" and name[:6].isupper():
        return name[7:]
    return name


def _family_key(name):
    """Chuẩn hoá tên phông về họ phông: 'TimesNewRomanPS-BoldMT' -> 'timesnewroman'."""
    name = _strip_subset(name).split("-")[0].split(",")[0]
    k = "".join(ch for ch in name.lower() if ch.isalnum())
    for suf in ("psmt", "mt", "ps"):
        if k.endswith(suf) and len(k) > len(suf) + 2:
            k = k[: -len(suf)]
    for w in _STYLE_WORDS:
        if k.endswith(w) and len(k) > len(w) + 2:
            k = k[: -len(w)]
    return k


def _style_of(name, flags=0):
    n = _strip_subset(name).lower()
    bold = bool(flags & 16) or any(w in n for w in ("bold", "black", "heavy", "semibold", "demi"))
    italic = bool(flags & 2) or "italic" in n or "oblique" in n
    return bold, italic


def _font_dirs():
    home = os.path.expanduser("~")
    win = os.environ.get("WINDIR", "C:/Windows")
    return [os.path.join(win, "Fonts"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
            "/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
            os.path.join(home, "Library", "Fonts"), "/usr/share/fonts", "/usr/local/share/fonts",
            os.path.join(home, ".fonts"), os.path.join(home, ".local", "share", "fonts"),
            os.path.join(HERE, "fonts")]


def font_index():
    """Danh sách phông trên máy: [(họ_phông, đậm, nghiêng, đường_dẫn)] — quét 1 lần."""
    global _font_index_cache
    if _font_index_cache is not None:
        return _font_index_cache
    out, seen = [], set()
    for d in _font_dirs():
        if not d or not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if not fn.lower().endswith((".ttf", ".otf")):
                    continue
                path = os.path.join(root, fn)
                if path.lower() in seen:
                    continue
                seen.add(path.lower())
                try:
                    f = pymupdf.Font(fontfile=path)
                    out.append((_family_key(f.name), bool(f.is_bold), bool(f.is_italic), path))
                except Exception:  # noqa: BLE001
                    pass
    _font_index_cache = out
    return out


def _covers(font, text):
    return all(font.has_glyph(ord(ch)) for ch in text if not ch.isspace())


class FontPicker:
    """Chọn phông để viết lại một đoạn chữ, ưu tiên:
    1) chính phông đã nhúng trong PDF (giống y hệt bản gốc) nếu có đủ ký tự;
    2) phông cùng tên + cùng kiểu đậm/nghiêng cài trên máy;
    3) phông dự phòng người dùng chọn.
    """

    def __init__(self, doc, fallback_file, keep_font=True):
        self.doc, self.keep = doc, keep_font
        self.fallback = fallback_file
        self.fb_font = pymupdf.Font(fontfile=fallback_file)
        self._emb = {}       # xref -> Font | None
        self._sys = {}       # (fam,bold,italic) -> path | None
        self._pagefonts = {}  # (pno) -> {tên: xref}
        self.stats = {"goc": 0, "tuong_tu": 0, "du_phong": 0}

    def _embedded(self, page, span_font):
        if page.number not in self._pagefonts:
            m = {}
            for f in page.get_fonts(full=True):
                m[_strip_subset(f[3])] = f[0]
            self._pagefonts[page.number] = m
        xref = self._pagefonts[page.number].get(_strip_subset(span_font))
        if not xref:
            return None, None
        if xref not in self._emb:
            font = None
            try:
                _n, ext, _t, buf = self.doc.extract_font(xref)
                if buf and ext not in ("n/a", ""):
                    font = (pymupdf.Font(fontbuffer=buf), buf)
            except Exception:  # noqa: BLE001
                font = None
            self._emb[xref] = font
        return xref, self._emb[xref]

    def _system(self, span_font, flags):
        fam = _family_key(span_font)
        bold, italic = _style_of(span_font, flags)
        key = (fam, bold, italic)
        if key not in self._sys:
            cands = [x for x in font_index() if x[0] == fam]
            exact = [x for x in cands if x[1] == bold and x[2] == italic]
            pick = (exact or [x for x in cands if x[1] == bold] or cands or [None])[0]
            self._sys[key] = pick[3] if pick else None
        return self._sys[key]

    def pick(self, page, span, text):
        """-> (alias, Font, nguồn phông) — đăng ký vào trang SAU khi xoá chữ cũ."""
        if self.keep:
            xref, emb = self._embedded(page, span["font"])
            if emb and _covers(emb[0], text):
                self.stats["goc"] += 1
                return f"E{xref}", emb[0], dict(fontbuffer=emb[1])
            path = self._system(span["font"], span["flags"])
            if path:
                f = pymupdf.Font(fontfile=path)
                if _covers(f, text):
                    self.stats["tuong_tu"] += 1
                    return _font_alias(path), f, dict(fontfile=path)
        self.stats["du_phong"] += 1
        return _font_alias(self.fallback), self.fb_font, dict(fontfile=self.fallback)


def replace_text(doc, find, repl, pages=None, fontfile=None, match_case=True, keep_font=True):
    """Tìm & thay chữ thật sự trong PDF. Trả về (số chỗ đã thay, thống kê phông).

    - PDF thường: viết lại cả dòng chứa chữ (giữ cỡ, màu, phông gốc nếu được),
      chữ phía sau tự dịch theo khi chữ mới dài/ngắn hơn.
    - Trang scan đã OCR: che chữ cũ bằng màu giấy và viết chữ mới bằng màu mực.
    """
    if not find:
        return 0, {}
    if fontfile is None:
        fontfile = default_font()[1]
    picker = FontPicker(doc, fontfile, keep_font)
    total = 0
    import re
    pat = re.compile(re.escape(find), 0 if match_case else re.IGNORECASE)

    def rep(t):
        return pat.subn(lambda m: repl, t)

    for pno in (pages if pages is not None else range(len(doc))):
        page = doc[pno]
        if is_scanned_page(page):
            hits = []
            for r in _merge_hits(page.search_for(find)):
                found = page.get_textbox(r + (-1, -1, 1, 1))
                if pat.search(" ".join(found.split())):
                    hits.append((r, pat.search(" ".join(found.split())).group(0)))
            for r, old in hits:
                _scan_write(page, r, repl, fontfile, old_text=old)
                total += 1
            continue
        jobs = []
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                spans = [sp for sp in ln["spans"] if sp["text"]]
                line_text = "".join(sp["text"] for sp in spans)
                _, n = rep(line_text)
                if not n or ln["dir"] != (1.0, 0.0):
                    continue
                new_spans, cnt = [], 0
                for sp in spans:
                    t, k = rep(sp["text"])
                    cnt += k
                    new_spans.append((t, sp))
                if cnt < n:  # chữ cần tìm vắt qua nhiều đoạn định dạng -> gộp cả dòng
                    t, cnt = rep(line_text)
                    new_spans = [(t, spans[0])]
                jobs.append((pymupdf.Rect(ln["bbox"]), new_spans))
                total += cnt
        if not jobs:
            continue
        # chọn phông TRƯỚC khi xoá chữ cũ (cần đọc phông nhúng)
        plans = [[(t, sp, picker.pick(page, sp, t)) for t, sp in new_spans] for _, new_spans in jobs]
        for r, _ in jobs:
            page.add_redact_annot(r, fill=False)  # chỉ xoá chữ, giữ nền/khung/ảnh
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        done = set()
        for plan in plans:
            for _t, _sp, (alias, _f, src) in plan:
                if alias not in done:
                    page.insert_font(fontname=alias, **src)
                    done.add(alias)
        for plan in plans:
            x = plan[0][1]["origin"][0]
            for t, sp, (alias, font, _src) in plan:
                page.insert_text(pymupdf.Point(x, sp["origin"][1]), t, fontsize=sp["size"],
                                 fontname=alias, color=_span_rgb(sp["color"]))
                x += font.text_length(t, fontsize=sp["size"])
    return total, picker.stats


# ================================================================ bản scan
def is_scanned_page(page):
    """Trang chủ yếu là ảnh chụp (bản scan)?"""
    area = abs(page.rect)
    cov = 0
    for info in page.get_image_info():
        cov += abs(pymupdf.Rect(info["bbox"]) & page.rect)
    return cov > 0.6 * area


def sample_colors(page, pdf_rect):
    """Lấy màu giấy (nền) và màu mực trong vùng — để sửa bản scan cho tự nhiên."""
    pad = 3
    clip = (pymupdf.Rect(pdf_rect) + (-pad, -pad, pad, pad)) & page.cropbox
    pix = page.get_pixmap(dpi=150, clip=clip, alpha=False, annots=False)
    w, h, n, s = pix.width, pix.height, pix.n, pix.samples
    if w < 3 or h < 3:
        return (1, 1, 1), (0, 0, 0)

    def px(x, y):
        i = (y * w + x) * n
        return s[i], s[i + 1], s[i + 2]

    border = [px(x, y) for x in range(w) for y in (0, 1, h - 2, h - 1)]
    border += [px(x, y) for y in range(h) for x in (0, 1, w - 2, w - 1)]
    inner = [px(x, y) for y in range(0, h, 2) for x in range(0, w, 2)]

    def med(pixels):
        return tuple(sorted(c[k] for c in pixels)[len(pixels) // 2] / 255 for k in range(3))

    bg = med(border)
    inner.sort(key=sum)
    dark = inner[: max(1, len(inner) // 12)]
    ink = med(dark)
    if sum(bg) - sum(ink) < 0.6:  # vùng không có chữ rõ -> mực đen
        ink = (0.1, 0.1, 0.1)
    return bg, ink


def _ink_box(page, rect, bg, ink, dpi=200):
    """Khung bao nét mực thật trong vùng (toạ độ PDF) — None nếu không có mực."""
    clip = pymupdf.Rect(rect) & page.cropbox
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False, annots=False)
    w, h, n, sm = pix.width, pix.height, pix.n, pix.samples
    if w < 2 or h < 2:
        return None
    thr = (sum(bg) + sum(ink)) / 2 * 255
    xs, ys = [], []
    for y in range(h):
        row = y * w * n
        for x in range(w):
            i = row + x * n
            if sm[i] + sm[i + 1] + sm[i + 2] < thr:
                xs.append(x)
                ys.append(y)
    if len(xs) < 3:
        return None
    k = 72 / dpi
    return pymupdf.Rect(clip.x0 + min(xs) * k, clip.y0 + min(ys) * k,
                        clip.x0 + (max(xs) + 1) * k, clip.y0 + (max(ys) + 1) * k)


_metric_cache = {}


def _text_ink_metrics(text, fontfile):
    """Đo nét mực của chữ khi in cỡ 100: (trên đường chân, dưới đường chân, lề trái)."""
    key = (text, fontfile)
    if key not in _metric_cache:
        font = pymupdf.Font(fontfile=fontfile)
        width = font.text_length(text, fontsize=100) + 40
        d = pymupdf.open()
        pg = d.new_page(width=width, height=220)
        pg.insert_font(fontname="M", fontfile=fontfile)
        pg.insert_text((20, 150), text, fontsize=100, fontname="M")
        box = _ink_box(pg, pg.rect, (1, 1, 1), (0, 0, 0), dpi=72)
        d.close()
        _metric_cache[key] = ((150 - box.y0, box.y1 - 150, box.x0 - 20, box.width) if box
                              else (72, 0, 0, font.text_length(text, fontsize=100)))
    return _metric_cache[key]


def _scan_write(page, pdf_rect, text, fontfile, size=None, old_text=None):
    """Thay chữ trên ảnh scan: đo nét mực cũ -> che bằng màu giấy -> viết chữ mới cùng cỡ, cùng dòng."""
    r = pymupdf.Rect(pdf_rect)
    bg, ink = sample_colors(page, r)
    h = r.height
    region = r + (-h * 0.12, -h * 0.3, h * 0.12, h * 0.3)
    box = _ink_box(page, region, bg, ink) or r
    old_text = (old_text or "").strip()
    first = (old_text or text or "H").split("\n")[0]
    top, bot, left, iw = _text_ink_metrics(first if old_text else "Hx", fontfile)
    if size is None:
        if old_text:
            size_h = 100 * box.height / max(top + bot, 1)
            size = size_h
            if len(old_text) >= 4 and iw > 0:  # ảnh scan hay bị nghiêng -> chiều rộng đáng tin hơn
                size_w = 100 * box.width / iw
                size = min(max(size_w, size_h * 0.75), size_h * 1.1)
        else:
            size = box.height / 0.72
    baseline = box.y1 - bot * size / 100 if old_text else box.y1
    x = box.x0 - left * size / 100
    cover = (box | r) + (-1.2, -1.2, 1.2, 1.2)
    # xoá lớp chữ ẩn (OCR) trong vùng, rồi phủ màu giấy lên nét mực cũ
    page.add_redact_annot(cover, fill=False)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    page.draw_rect(cover, color=None, fill=bg, overlay=True)
    if not text:
        return
    font = pymupdf.Font(fontfile=fontfile)
    alias = _font_alias(fontfile)
    page.insert_font(fontname=alias, fontfile=fontfile)
    lines = text.split("\n")
    widest = max(font.text_length(ln, fontsize=size) for ln in lines)
    if x + widest > cover.x1:
        # chữ mới dài hơn: chỉ co lại nếu phía sau có chữ khác bị đè
        probe = pymupdf.Rect(cover.x1 + 0.5, box.y0, x + widest + 2, box.y1)
        nxt = _ink_box(page, probe, bg, ink)
        if nxt:
            room = nxt.x0 - x - size * 0.25
            if room > 0 and widest > room:
                size = max(size * 0.8, size * room / widest)
    for i, ln in enumerate(lines):
        page.insert_text(pymupdf.Point(x, baseline + i * size * 1.25), ln, fontsize=size,
                         fontname=alias, color=ink)


def scan_edit(page, view_rect, text, fontfile=None, size=None, old_text=None):
    """Sửa chữ trên bản scan: che vùng bằng đúng màu giấy, viết chữ mới bằng màu mực, cùng cỡ chữ cũ."""
    if fontfile is None:
        fontfile = default_font()[1]
    _scan_write(page, view_to_pdf_rect(page, view_rect), text, fontfile, size, old_text)


def text_in_rect(page, view_rect):
    """Chữ (thật hoặc từ OCR) nằm trong vùng chọn."""
    return page.get_textbox(view_to_pdf_rect(page, view_rect)).strip()


def _merge_hits(rects):
    """Gộp các mảnh của cùng một kết quả tìm kiếm trên cùng dòng."""
    out = []
    for r in rects:
        r = pymupdf.Rect(r)
        if out:
            p = out[-1]
            ov = min(p.y1, r.y1) - max(p.y0, r.y0)
            if ov > 0.5 * min(p.height, r.height) and -1 < r.x0 - p.x1 < 0.8 * max(p.height, r.height):
                out[-1] = p | r
                continue
        out.append(r)
    return out


def find_tessdata():
    """Tìm thư mục dữ liệu của Tesseract OCR."""
    cands = [os.environ.get("TESSDATA_PREFIX", "")]
    try:
        cands.append(pymupdf.get_tessdata())
    except Exception:  # noqa: BLE001
        pass
    pf = [os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
    cands += [os.path.join(p, "Tesseract-OCR", "tessdata") for p in pf if p]
    cands += [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tessdata"),
              "C:/Program Files/Tesseract-OCR/tessdata", "/opt/homebrew/share/tessdata",
              "/usr/local/share/tessdata", "/usr/share/tessdata"]
    import glob
    cands += glob.glob("/usr/share/tesseract-ocr/*/tessdata")
    for c in cands:
        if c and os.path.isdir(c) and any(f.endswith(".traineddata") for f in os.listdir(c)):
            return c
    return None


def ocr_languages(tessdata):
    return sorted(f[:-12] for f in os.listdir(tessdata) if f.endswith(".traineddata"))


def ocr_pages(doc, pages=None, lang="vie", dpi=300, fontfile=None, progress=None):
    """Nhận dạng chữ cho trang scan: thêm lớp chữ ẩn đúng vị trí, ảnh gốc giữ nguyên.
    Sau đó tìm kiếm, sao chép, tìm & thay đều dùng được. Trả về số trang đã OCR."""
    td = find_tessdata()
    if not td:
        raise RuntimeError("Chưa cài Tesseract OCR.")
    missing = [l for l in lang.split("+") if l not in ocr_languages(td)]
    if missing:
        raise RuntimeError(f"Tesseract thiếu gói ngôn ngữ: {', '.join(missing)} (trong {td}).")
    if fontfile is None:
        fontfile = default_font()[1]
    font = pymupdf.Font(fontfile=fontfile)
    alias = _font_alias(fontfile)
    done = 0
    todo = list(pages if pages is not None else range(len(doc)))
    for k, pno in enumerate(todo):
        page = doc[pno]
        if progress:
            progress(k, len(todo))
        if page.get_text().strip():  # đã có chữ thật -> bỏ qua
            continue
        tp = page.get_textpage_ocr(language=lang, dpi=dpi, full=True, tessdata=td)
        words = page.get_text("words", textpage=tp)
        if not words:
            continue
        page.insert_font(fontname=alias, fontfile=fontfile)
        lines = {}
        for w in words:
            lines.setdefault((w[5], w[6]), []).append(w)
        for ws in lines.values():
            hs = sorted(w[3] - w[1] for w in ws)
            size = max(hs[len(hs) // 2] * 0.82, 3)
            base = sorted(w[3] for w in ws)[len(ws) // 2] - size * 0.2
            for x0, y0, x1, y1, txt, *_ in ws:
                tl = font.text_length(txt, fontsize=size)
                fs = size * min(max((x1 - x0) / tl, 0.6), 1.4) if tl else size
                page.insert_text(pymupdf.Point(x0, base), txt + " ", fontsize=fs, fontname=alias,
                                 render_mode=3)
        done += 1
    if progress:
        progress(len(todo), len(todo))
    return done


def search_text(doc, find):
    """Trả về [(trang, Rect), ...]"""
    res = []
    for pno, page in enumerate(doc):
        for r in _merge_hits(page.search_for(find)):
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

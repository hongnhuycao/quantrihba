"""PHẦN MỀM CHỈNH SỬA PDF — giao diện tiếng Việt.

Chạy:  python pdf_editor.py  [tệp.pdf]
Cần:   pip install pymupdf      (Tkinter có sẵn trong Python cho Windows/macOS)
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdf_core as core  # noqa: E402

APP = "Trình sửa PDF"
PAD = 16
MAX_UNDO = 30

MODES = [
    ("chon", "🖐 Xem"),
    ("chu", "T Thêm chữ"),
    ("anh", "🖼 Ảnh / Chữ ký"),
    ("che", "▭ Che trắng"),
    ("tosang", "🖍 Tô sáng"),
    ("khung", "□ Khung"),
    ("ghichu", "🗨 Ghi chú"),
]
HINTS = {
    "chon": "Cuộn chuột để xem, Ctrl + cuộn để phóng to/thu nhỏ.",
    "chu": "Bấm vào trang tại chỗ muốn thêm chữ.",
    "anh": "Kéo chuột để vẽ khung, rồi chọn ảnh/chữ ký (PNG nền trong suốt đẹp nhất).",
    "che": "Kéo chuột quanh vùng cần xoá: nội dung bên dưới bị xoá hẳn và phủ trắng.",
    "tosang": "Kéo chuột quanh dòng chữ cần tô sáng.",
    "khung": "Kéo chuột để vẽ khung chữ nhật.",
    "ghichu": "Bấm vào trang để gắn ghi chú.",
}


class TextDialog(tk.Toplevel):
    """Hộp thoại nhập chữ: nội dung, phông, cỡ, màu."""

    def __init__(self, master, fonts, state):
        super().__init__(master)
        self.title("Thêm chữ")
        self.transient(master)
        self.resizable(False, False)
        self.result = None
        self.color = state["color"]
        f = ttk.Frame(self, padding=12)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Nội dung (có thể nhiều dòng):").grid(row=0, column=0, columnspan=4, sticky="w")
        self.txt = tk.Text(f, width=46, height=5, font=("Arial", 12))
        self.txt.grid(row=1, column=0, columnspan=4, pady=(4, 8))
        ttk.Label(f, text="Phông:").grid(row=2, column=0, sticky="w")
        self.font = ttk.Combobox(f, values=list(fonts), state="readonly", width=24)
        self.font.set(state["font"])
        self.font.grid(row=2, column=1, sticky="w")
        ttk.Label(f, text="Cỡ:").grid(row=2, column=2, sticky="e")
        self.size = ttk.Spinbox(f, from_=5, to=120, width=5)
        self.size.set(state["size"])
        self.size.grid(row=2, column=3, sticky="w")
        self.cbtn = tk.Button(f, text="  Màu chữ  ", bg=self.color, fg="white", command=self.pick)
        self.cbtn.grid(row=3, column=0, pady=10, sticky="w")
        b = ttk.Frame(f)
        b.grid(row=3, column=1, columnspan=3, sticky="e")
        ttk.Button(b, text="Huỷ", command=self.destroy).pack(side="right")
        ttk.Button(b, text="Thêm", command=self.ok).pack(side="right", padx=6)
        self.txt.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.wait_window()

    def pick(self):
        c = colorchooser.askcolor(self.color, parent=self)[1]
        if c:
            self.color = c
            self.cbtn.configure(bg=c)

    def ok(self):
        text = self.txt.get("1.0", "end").rstrip("\n")
        if not text.strip():
            self.destroy()
            return
        try:
            size = float(self.size.get())
        except ValueError:
            size = 12
        self.result = dict(text=text, font=self.font.get(), size=size, color=self.color)
        self.destroy()


class ReplaceDialog(tk.Toplevel):
    def __init__(self, master, on_replace):
        super().__init__(master)
        self.title("Tìm & thay chữ")
        self.transient(master)
        self.resizable(False, False)
        f = ttk.Frame(self, padding=12)
        f.pack()
        ttk.Label(f, text="Tìm chữ:").grid(row=0, column=0, sticky="w")
        self.find = ttk.Entry(f, width=40)
        self.find.grid(row=0, column=1, pady=3)
        ttk.Label(f, text="Thay bằng:").grid(row=1, column=0, sticky="w")
        self.repl = ttk.Entry(f, width=40)
        self.repl.grid(row=1, column=1, pady=3)
        self.case = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Phân biệt chữ hoa/thường", variable=self.case).grid(row=2, column=1, sticky="w")
        self.cur_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Chỉ trang đang xem", variable=self.cur_only).grid(row=3, column=1, sticky="w")
        ttk.Label(f, foreground="#666", wraplength=380, justify="left",
                  text="Lưu ý: dòng có chữ được thay sẽ viết lại bằng phông đang chọn trên thanh công cụ. "
                       "Với PDF scan (ảnh chụp) thì không thay được chữ.").grid(row=4, column=0, columnspan=2,
                                                                                 pady=6, sticky="w")
        b = ttk.Frame(f)
        b.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(b, text="Đóng", command=self.destroy).pack(side="right")
        ttk.Button(b, text="Thay tất cả",
                   command=lambda: on_replace(self.find.get(), self.repl.get(), self.case.get(),
                                              self.cur_only.get())).pack(side="right", padx=6)
        self.find.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())


class App:
    def __init__(self, root, path=None):
        self.root = root
        self.doc = None
        self.path = None
        self.cur = 0
        self.zoom = 1.3
        self.undo_stack, self.redo_stack = [], []
        self.dirty = False
        self.mode = tk.StringVar(value="chon")
        self.fonts = core.available_fonts()
        fname, _ = core.default_font()
        self.state = {"font": fname, "size": 12, "color": "#000000"}
        self.last_image = None
        self.drag_start = None
        self.drag_item = None
        self.search_hits, self.search_idx = [], -1
        self.photo = None

        root.title(APP)
        root.geometry("1200x820")
        root.minsize(800, 500)
        try:
            ttk.Style().theme_use("vista" if sys.platform == "win32" else "clam")
        except tk.TclError:
            pass
        self._menu()
        self._toolbar()
        self._body()
        self._keys()
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.update_ui()
        if path:
            root.after(100, lambda: self.open(path))

    # ================================================================ giao diện
    def _menu(self):
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="Mở PDF…", accelerator="Ctrl+O", command=self.open)
        f.add_command(label="Lưu", accelerator="Ctrl+S", command=self.save)
        f.add_command(label="Lưu thành…", accelerator="Ctrl+Shift+S", command=self.save_as)
        f.add_command(label="Lưu kèm mật khẩu…", command=self.save_with_password)
        f.add_command(label="Nén PDF (giảm dung lượng)…", command=self.compress)
        f.add_separator()
        f.add_command(label="Gộp nhiều PDF / ảnh thành 1 tệp…", command=self.merge)
        f.add_command(label="Chuyển ảnh sang PDF…", command=self.images_to_pdf)
        f.add_separator()
        f.add_command(label="Thông tin tài liệu…", command=self.metadata)
        f.add_command(label="Đóng tệp", command=self.close_doc)
        f.add_command(label="Thoát", command=self.quit)
        m.add_cascade(label="Tệp", menu=f)

        e = tk.Menu(m, tearoff=0)
        e.add_command(label="Hoàn tác", accelerator="Ctrl+Z", command=self.undo)
        e.add_command(label="Làm lại", accelerator="Ctrl+Y", command=self.redo)
        e.add_separator()
        e.add_command(label="Tìm & thay chữ…", accelerator="Ctrl+H", command=self.replace_dialog)
        e.add_command(label="Tô sáng mọi chỗ có chữ…", command=self.highlight_all)
        e.add_command(label="Đóng dấu chìm (watermark)…", command=self.watermark)
        e.add_command(label="Đánh số trang…", command=self.page_numbers)
        e.add_separator()
        e.add_command(label="Chọn màu chữ…", command=self.pick_color)
        m.add_cascade(label="Chỉnh sửa", menu=e)

        p = tk.Menu(m, tearoff=0)
        p.add_command(label="Xoay phải 90°", accelerator="Ctrl+R", command=lambda: self.rotate(90))
        p.add_command(label="Xoay trái 90°", accelerator="Ctrl+L", command=lambda: self.rotate(-90))
        p.add_command(label="Xoay 180°", command=lambda: self.rotate(180))
        p.add_separator()
        p.add_command(label="Chuyển trang lên", command=lambda: self.move(-1))
        p.add_command(label="Chuyển trang xuống", command=lambda: self.move(1))
        p.add_command(label="Nhân bản trang", command=self.duplicate)
        p.add_command(label="Chèn trang trắng phía sau", command=self.blank)
        p.add_command(label="Chèn trang từ PDF khác…", command=self.insert_file)
        p.add_command(label="Xoá trang đang chọn", accelerator="Delete", command=self.delete)
        p.add_separator()
        p.add_command(label="Trích trang ra tệp mới…", command=self.extract)
        p.add_command(label="Tách PDF (mỗi N trang)…", command=self.split)
        p.add_command(label="Xuất trang thành ảnh PNG…", command=self.export_png)
        p.add_command(label="Trích toàn bộ văn bản (.txt)…", command=self.export_text)
        m.add_cascade(label="Trang", menu=p)

        v = tk.Menu(m, tearoff=0)
        v.add_command(label="Phóng to", accelerator="Ctrl++", command=lambda: self.set_zoom(self.zoom * 1.2))
        v.add_command(label="Thu nhỏ", accelerator="Ctrl+-", command=lambda: self.set_zoom(self.zoom / 1.2))
        v.add_command(label="Vừa chiều rộng", command=self.fit_width)
        v.add_command(label="Vừa cả trang", command=self.fit_page)
        m.add_cascade(label="Xem", menu=v)

        h = tk.Menu(m, tearoff=0)
        h.add_command(label="Hướng dẫn nhanh", command=self.help)
        m.add_cascade(label="Trợ giúp", menu=h)
        self.root.config(menu=m)

    def _toolbar(self):
        tb = ttk.Frame(self.root, padding=(6, 4))
        tb.pack(side="top", fill="x")
        for txt, cmd in (("📂 Mở", self.open), ("💾 Lưu", self.save), ("↶", self.undo), ("↷", self.redo)):
            ttk.Button(tb, text=txt, command=cmd, width=len(txt) + 2).pack(side="left", padx=1)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        for key, label in MODES:
            ttk.Radiobutton(tb, text=label, value=key, variable=self.mode, style="Toolbutton",
                            command=self.mode_changed).pack(side="left", padx=1)
        tb = ttk.Frame(self.root, padding=(6, 0, 6, 4))  # hàng thứ 2
        tb.pack(side="top", fill="x")
        ttk.Label(tb, text="Phông chữ").pack(side="left")
        self.font_box = ttk.Combobox(tb, values=list(self.fonts), state="readonly", width=16)
        self.font_box.set(self.state["font"])
        self.font_box.bind("<<ComboboxSelected>>", lambda e: self.state.update(font=self.font_box.get()))
        self.font_box.pack(side="left", padx=2)
        self.color_btn = tk.Button(tb, text=" Màu ", bg=self.state["color"], fg="white", command=self.pick_color)
        self.color_btn.pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Label(tb, text="Tìm").pack(side="left")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(tb, textvariable=self.search_var, width=24)
        ent.pack(side="left")
        ent.bind("<Return>", lambda e: self.search_next())
        ttk.Button(tb, text="🔍 Tìm", command=self.search_next).pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Label(tb, text="Thu phóng").pack(side="left")
        ttk.Button(tb, text="−", width=2, command=lambda: self.set_zoom(self.zoom / 1.2)).pack(side="left")
        self.zoom_lbl = ttk.Label(tb, text="100%", width=5, anchor="center")
        self.zoom_lbl.pack(side="left")
        ttk.Button(tb, text="+", width=2, command=lambda: self.set_zoom(self.zoom * 1.2)).pack(side="left")
        ttk.Button(tb, text="Vừa trang", command=self.fit_page).pack(side="left", padx=4)
        ttk.Button(tb, text="🔁 Tìm & thay chữ", command=self.replace_dialog).pack(side="left", padx=4)

    def _body(self):
        pw = ttk.PanedWindow(self.root, orient="horizontal")
        pw.pack(fill="both", expand=True)
        left = ttk.Frame(pw, padding=4)
        ttk.Label(left, text="Các trang (Ctrl/Shift để chọn nhiều)").pack(anchor="w")
        lf = ttk.Frame(left)
        lf.pack(fill="both", expand=True)
        self.pages = tk.Listbox(lf, selectmode="extended", width=22, activestyle="none",
                                font=("Segoe UI", 10), exportselection=False)
        sb = ttk.Scrollbar(lf, command=self.pages.yview)
        self.pages.config(yscrollcommand=sb.set)
        self.pages.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.pages.bind("<<ListboxSelect>>", self.page_selected)
        bf = ttk.Frame(left)
        bf.pack(fill="x", pady=4)
        for txt, cmd in (("▲", lambda: self.move(-1)), ("▼", lambda: self.move(1)),
                         ("⟳", lambda: self.rotate(90)), ("＋", self.blank), ("🗑", self.delete)):
            ttk.Button(bf, text=txt, width=3, command=cmd).pack(side="left", padx=1)
        pw.add(left, weight=0)

        right = ttk.Frame(pw)
        self.canvas = tk.Canvas(right, bg="#8a8f98", highlightthickness=0, cursor="arrow")
        vs = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        hs = ttk.Scrollbar(right, orient="horizontal", command=self.canvas.xview)
        self.canvas.config(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        pw.add(right, weight=1)

        self.status = ttk.Label(self.root, relief="sunken", anchor="w", padding=(6, 2))
        self.status.pack(side="bottom", fill="x")

        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<MouseWheel>", self.on_wheel)
        c.bind("<Button-4>", lambda e: self.on_wheel(e, -1))
        c.bind("<Button-5>", lambda e: self.on_wheel(e, 1))
        c.bind("<Configure>", lambda e: self.center_page())

    def _keys(self):
        r = self.root
        r.bind("<Control-o>", lambda e: self.open())
        r.bind("<Control-s>", lambda e: self.save())
        r.bind("<Control-S>", lambda e: self.save_as())
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-h>", lambda e: self.replace_dialog())
        r.bind("<Control-r>", lambda e: self.rotate(90))
        r.bind("<Control-l>", lambda e: self.rotate(-90))
        r.bind("<Control-plus>", lambda e: self.set_zoom(self.zoom * 1.2))
        r.bind("<Control-equal>", lambda e: self.set_zoom(self.zoom * 1.2))
        r.bind("<Control-minus>", lambda e: self.set_zoom(self.zoom / 1.2))
        r.bind("<Next>", lambda e: self.goto(self.cur + 1))
        r.bind("<Prior>", lambda e: self.goto(self.cur - 1))
        self.pages.bind("<Delete>", lambda e: self.delete())

    # ================================================================ trạng thái
    def need_doc(self):
        if self.doc is None:
            messagebox.showinfo(APP, "Hãy mở một tệp PDF trước (Tệp → Mở PDF).")
            return False
        return True

    def snapshot(self):
        """Lưu trạng thái để hoàn tác — gọi TRƯỚC mỗi thay đổi."""
        self.undo_stack.append((self.doc.tobytes(), self.cur))
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def changed(self, msg=None):
        self.dirty = True
        self.update_ui()
        if msg:
            self.set_status(msg)

    def _restore(self, data):
        self.doc.close()
        self.doc = pymupdf.open("pdf", data[0])
        self.cur = min(data[1], len(self.doc) - 1)
        self.dirty = True
        self.update_ui()

    def undo(self):
        if self.doc and self.undo_stack:
            self.redo_stack.append((self.doc.tobytes(), self.cur))
            self._restore(self.undo_stack.pop())
            self.set_status("Đã hoàn tác.")

    def redo(self):
        if self.doc and self.redo_stack:
            self.undo_stack.append((self.doc.tobytes(), self.cur))
            self._restore(self.redo_stack.pop())
            self.set_status("Đã làm lại.")

    def set_status(self, msg):
        self.status.config(text=msg)

    def update_ui(self):
        name = os.path.basename(self.path) if self.path else "(chưa mở tệp)"
        self.root.title(f"{'● ' if self.dirty else ''}{name} — {APP}")
        self.pages.delete(0, "end")
        if self.doc:
            for i, p in enumerate(self.doc):
                rot = f"  ⟳{p.rotation}°" if p.rotation else ""
                self.pages.insert("end", f"  Trang {i + 1}{rot}")
            self.cur = max(0, min(self.cur, len(self.doc) - 1))
            self.pages.selection_set(self.cur)
            self.pages.see(self.cur)
        self.render()
        self.mode_changed(quiet=True)

    def mode_changed(self, quiet=False):
        cur = {"chu": "xterm", "ghichu": "hand2", "chon": "arrow"}.get(self.mode.get(), "crosshair")
        self.canvas.config(cursor=cur)
        if self.doc:
            info = f"Trang {self.cur + 1}/{len(self.doc)}   |   {HINTS[self.mode.get()]}"
            self.set_status(info)
        else:
            self.set_status("Mở một tệp PDF để bắt đầu (Ctrl+O).")

    # ================================================================ hiển thị
    def render(self):
        c = self.canvas
        c.delete("all")
        self.zoom_lbl.config(text=f"{round(self.zoom / 1.333 * 100)}%")
        if not self.doc:
            c.create_text(c.winfo_width() // 2 or 400, 200, fill="white", font=("Arial", 16),
                          text="Mở tệp PDF: Tệp → Mở PDF   (Ctrl+O)")
            return
        page = self.doc[self.cur]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(self.zoom, self.zoom), alpha=False, annots=True)
        self.photo = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.pw, self.ph = pix.width, pix.height
        c.create_rectangle(PAD + 3, PAD + 3, PAD + 3 + pix.width, PAD + 3 + pix.height, fill="#555", outline="")
        c.create_image(PAD, PAD, image=self.photo, anchor="nw", tags="page")
        c.config(scrollregion=(0, 0, pix.width + 2 * PAD, pix.height + 2 * PAD))
        # đánh dấu kết quả tìm kiếm trên trang này
        for i, (pno, r) in enumerate(self.search_hits):
            if pno == self.cur:
                vr = r * page.rotation_matrix
                vr.normalize()
                col = "#ff6600" if i == self.search_idx else "#ffcc00"
                c.create_rectangle(*self.v2c(vr.x0, vr.y0), *self.v2c(vr.x1, vr.y1), outline=col, width=2)
        self.center_page()

    def center_page(self):
        if not self.doc or not hasattr(self, "pw"):
            return
        cw = self.canvas.winfo_width()
        off = max(0, (cw - self.pw - 2 * PAD) // 2)
        self.canvas.config(scrollregion=(-off, 0, self.pw + 2 * PAD + off, self.ph + 2 * PAD))

    def v2c(self, x, y):
        """toạ độ trang (điểm) -> toạ độ canvas"""
        return PAD + x * self.zoom, PAD + y * self.zoom

    def c2v(self, cx, cy):
        x = (cx - PAD) / self.zoom
        y = (cy - PAD) / self.zoom
        r = self.doc[self.cur].rect
        return min(max(x, 0), r.width), min(max(y, 0), r.height)

    def set_zoom(self, z):
        self.zoom = min(max(z, 0.3), 6.0)
        self.render()

    def fit_width(self):
        if self.doc:
            self.set_zoom((self.canvas.winfo_width() - 2 * PAD - 10) / self.doc[self.cur].rect.width)

    def fit_page(self):
        if self.doc:
            r = self.doc[self.cur].rect
            self.set_zoom(min((self.canvas.winfo_width() - 2 * PAD) / r.width,
                              (self.canvas.winfo_height() - 2 * PAD) / r.height))

    def goto(self, i):
        if self.doc and 0 <= i < len(self.doc) and i != self.cur:
            self.cur = i
            self.pages.selection_clear(0, "end")
            self.pages.selection_set(i)
            self.pages.see(i)
            self.render()
            self.canvas.yview_moveto(0)
            self.mode_changed()

    def page_selected(self, _e=None):
        sel = self.pages.curselection()
        if sel and self.doc:
            i = sel[-1] if len(sel) == 1 else self.pages.index("active")
            i = i if i in sel else sel[0]
            if i != self.cur:
                self.cur = i
                self.render()
                self.canvas.yview_moveto(0)
                self.mode_changed()

    def selected_pages(self):
        sel = list(self.pages.curselection())
        return sel if sel else [self.cur]

    # ================================================================ chuột
    def on_wheel(self, e, direction=None):
        if direction is None:
            direction = -1 if e.delta > 0 else 1
        if e.state & 0x4:  # Ctrl
            self.set_zoom(self.zoom * (1.1 if direction < 0 else 1 / 1.1))
            return
        top, bottom = self.canvas.yview()
        if direction > 0 and bottom >= 0.999:
            self.goto(self.cur + 1)
        elif direction < 0 and top <= 0.001 and self.cur > 0:
            self.goto(self.cur - 1)
            self.canvas.yview_moveto(1)
        else:
            self.canvas.yview_scroll(direction * 3, "units")

    def on_press(self, e):
        if not self.doc:
            return
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        mode = self.mode.get()
        if mode == "chon":
            self.canvas.scan_mark(e.x, e.y)
            return
        if mode == "chu":
            self.add_text_at(*self.c2v(cx, cy))
            return
        if mode == "ghichu":
            self.add_note_at(*self.c2v(cx, cy))
            return
        self.drag_start = (cx, cy)
        col = {"che": "#d00", "tosang": "#e6b800", "anh": "#06c", "khung": self.state["color"]}[mode]
        self.drag_item = self.canvas.create_rectangle(cx, cy, cx, cy, outline=col, width=2, dash=(4, 2))

    def on_drag(self, e):
        if self.mode.get() == "chon":
            self.canvas.scan_dragto(e.x, e.y, gain=1)
            return
        if self.drag_item:
            cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
            self.canvas.coords(self.drag_item, *self.drag_start, cx, cy)

    def on_release(self, e):
        if not self.drag_item:
            return
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        x0, y0 = self.c2v(*self.drag_start)
        x1, y1 = self.c2v(cx, cy)
        self.canvas.delete(self.drag_item)
        self.drag_item = None
        rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        if rect[2] - rect[0] < 3 or rect[3] - rect[1] < 3:
            self.set_status("Hãy KÉO chuột để vẽ vùng (không chỉ bấm).")
            return
        mode = self.mode.get()
        page = lambda: self.doc[self.cur]  # noqa: E731
        try:
            if mode == "anh":
                path = filedialog.askopenfilename(
                    title="Chọn ảnh / chữ ký", initialdir=os.path.dirname(self.last_image or ""),
                    filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"), ("Tất cả", "*.*")])
                if not path:
                    return
                self.last_image = path
                self.snapshot()
                core.add_image(page(), rect, path)
                self.changed("Đã chèn ảnh.")
            elif mode == "che":
                self.snapshot()
                core.whiteout(page(), rect)
                self.changed("Đã xoá & che trắng vùng chọn.")
            elif mode == "tosang":
                self.snapshot()
                core.highlight(page(), rect)
                self.changed("Đã tô sáng.")
            elif mode == "khung":
                self.snapshot()
                core.draw_rect(page(), rect, self.state["color"])
                self.changed("Đã vẽ khung.")
        except Exception as ex:  # noqa: BLE001
            messagebox.showerror(APP, f"Không thực hiện được:\n{ex}")

    def add_text_at(self, x, y):
        d = TextDialog(self.root, self.fonts, self.state)
        if not d.result:
            return
        r = d.result
        self.state.update(font=r["font"], size=r["size"], color=r["color"])
        self.font_box.set(r["font"])
        self.color_btn.config(bg=r["color"])
        self.snapshot()
        try:
            core.add_text(self.doc[self.cur], x, y, r["text"], r["size"], r["color"], self.fonts[r["font"]])
            self.changed("Đã thêm chữ. (Ctrl+Z để hoàn tác)")
        except Exception as ex:  # noqa: BLE001
            self.undo_stack.pop()
            messagebox.showerror(APP, f"Không thêm được chữ:\n{ex}")

    def add_note_at(self, x, y):
        t = simpledialog.askstring("Ghi chú", "Nội dung ghi chú:", parent=self.root)
        if t:
            self.snapshot()
            core.add_note(self.doc[self.cur], x, y, t)
            self.changed("Đã gắn ghi chú.")

    def pick_color(self):
        c = colorchooser.askcolor(self.state["color"], parent=self.root)[1]
        if c:
            self.state["color"] = c
            self.color_btn.config(bg=c)

    # ================================================================ tệp
    def confirm_discard(self):
        if not self.dirty:
            return True
        a = messagebox.askyesnocancel(APP, "Tài liệu có thay đổi chưa lưu. Lưu trước khi tiếp tục?")
        if a is None:
            return False
        if a:
            return self.save()
        return True

    def open(self, path=None):
        if not self.confirm_discard():
            return
        path = path or filedialog.askopenfilename(title="Mở PDF", filetypes=[("PDF", "*.pdf"), ("Tất cả", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as fh:  # đọc vào bộ nhớ: không khoá tệp, lưu đè được
                data = fh.read()
            doc = pymupdf.open("pdf", data)
            if doc.needs_pass:
                pw = simpledialog.askstring(APP, "Tệp có mật khẩu. Nhập mật khẩu:", show="*", parent=self.root)
                if not pw or not doc.authenticate(pw):
                    messagebox.showerror(APP, "Sai mật khẩu.")
                    return
                doc = pymupdf.open("pdf", doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_NONE))
        except Exception as ex:  # noqa: BLE001
            messagebox.showerror(APP, f"Không mở được tệp:\n{ex}")
            return
        if self.doc:
            self.doc.close()
        self.doc, self.path, self.cur = doc, path, 0
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.search_hits = []
        self.dirty = False
        self.update_ui()
        self.root.after(50, self.fit_width)
        if not any(p.get_text().strip() for p in doc):
            self.set_status("Lưu ý: tệp này có vẻ là bản scan (ảnh), không sửa/tìm chữ được — "
                            "vẫn thêm chữ, ảnh, che trắng bình thường.")

    def _write(self, path, **kw):
        data = self.doc.tobytes(garbage=3, deflate=True, **kw)
        tmp = path + ".dang_luu"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)

    def save(self):
        if not self.need_doc():
            return False
        if not self.path:
            return self.save_as()
        try:
            self._write(self.path)
        except PermissionError:
            messagebox.showerror(APP, "Không ghi được tệp — có thể tệp đang mở trong chương trình khác.\n"
                                      "Hãy dùng 'Lưu thành…' với tên khác.")
            return False
        except Exception as ex:  # noqa: BLE001
            messagebox.showerror(APP, f"Lỗi khi lưu:\n{ex}")
            return False
        self.dirty = False
        self.update_ui()
        self.set_status(f"Đã lưu: {self.path}")
        return True

    def ask_save_path(self, title="Lưu thành", suffix=""):
        base = os.path.splitext(os.path.basename(self.path or "tai_lieu.pdf"))[0]
        return filedialog.asksaveasfilename(title=title, defaultextension=".pdf",
                                            initialdir=os.path.dirname(self.path or ""),
                                            initialfile=f"{base}{suffix}.pdf", filetypes=[("PDF", "*.pdf")])

    def save_as(self):
        if not self.need_doc():
            return False
        path = self.ask_save_path(suffix="_da_sua")
        if not path:
            return False
        self.path = path
        return self.save()

    def save_with_password(self):
        if not self.need_doc():
            return
        pw = simpledialog.askstring(APP, "Đặt mật khẩu mở tệp:", show="*", parent=self.root)
        if not pw:
            return
        if pw != simpledialog.askstring(APP, "Nhập lại mật khẩu:", show="*", parent=self.root):
            messagebox.showerror(APP, "Hai lần nhập không khớp.")
            return
        path = self.ask_save_path("Lưu bản có mật khẩu", "_mat_khau")
        if path:
            self._write(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=pw, owner_pw=pw)
            messagebox.showinfo(APP, f"Đã lưu bản có mật khẩu:\n{path}")

    def compress(self):
        if not self.need_doc():
            return
        path = self.ask_save_path("Lưu bản nén", "_nen")
        if not path:
            return
        self.root.config(cursor="watch")
        self.root.update()
        try:
            old, new = core.compress(self.doc, path)
        finally:
            self.root.config(cursor="")
        messagebox.showinfo(APP, f"Đã nén xong:\n{old / 1e6:.2f} MB → {new / 1e6:.2f} MB\n\n{path}")

    def close_doc(self):
        if self.doc and self.confirm_discard():
            self.doc.close()
            self.doc, self.path, self.dirty = None, None, False
            self.undo_stack.clear()
            self.update_ui()

    def quit(self):
        if self.confirm_discard():
            self.root.destroy()

    def merge(self):
        files = filedialog.askopenfilenames(
            title="Chọn các tệp cần gộp (theo thứ tự tên)",
            filetypes=[("PDF và ảnh", "*.pdf *.png *.jpg *.jpeg"), ("Tất cả", "*.*")])
        if not files:
            return
        files = sorted(files)
        order = "\n".join(f"{i + 1}. {os.path.basename(f)}" for i, f in enumerate(files))
        if not messagebox.askokcancel(APP, f"Gộp theo thứ tự:\n{order}"):
            return
        out = filedialog.asksaveasfilename(title="Lưu tệp đã gộp", defaultextension=".pdf",
                                           initialfile="da_gop.pdf", filetypes=[("PDF", "*.pdf")])
        if out:
            core.merge_pdfs(files, out)
            if messagebox.askyesno(APP, f"Đã gộp {len(files)} tệp.\nMở tệp vừa tạo?"):
                self.open(out)

    def images_to_pdf(self):
        files = filedialog.askopenfilenames(title="Chọn ảnh", filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp *.tif")])
        if not files:
            return
        out = filedialog.asksaveasfilename(title="Lưu PDF", defaultextension=".pdf",
                                           initialfile="anh.pdf", filetypes=[("PDF", "*.pdf")])
        if out:
            core.images_to_pdf(sorted(files), out)
            if messagebox.askyesno(APP, "Đã tạo PDF. Mở luôn?"):
                self.open(out)

    def metadata(self):
        if not self.need_doc():
            return
        md = self.doc.metadata or {}
        t = simpledialog.askstring(APP, "Tiêu đề tài liệu:", initialvalue=md.get("title", ""), parent=self.root)
        if t is None:
            return
        a = simpledialog.askstring(APP, "Tác giả:", initialvalue=md.get("author", ""), parent=self.root)
        if a is None:
            return
        self.snapshot()
        core.set_metadata(self.doc, title=t, author=a)
        self.changed("Đã cập nhật thông tin tài liệu.")

    # ================================================================ trang
    def rotate(self, angle):
        if self.need_doc():
            self.snapshot()
            core.rotate_pages(self.doc, self.selected_pages(), angle)
            self.changed("Đã xoay trang.")

    def delete(self):
        if not self.need_doc():
            return
        pages = self.selected_pages()
        if len(pages) >= len(self.doc):
            messagebox.showwarning(APP, "Không thể xoá hết tất cả các trang.")
            return
        names = ", ".join(str(p + 1) for p in pages)
        if messagebox.askyesno(APP, f"Xoá trang {names}?"):
            self.snapshot()
            core.delete_pages(self.doc, pages)
            self.cur = min(pages[0], len(self.doc) - 1)
            self.changed(f"Đã xoá trang {names}.")

    def move(self, step):
        if not self.need_doc():
            return
        dst = self.cur + step
        if 0 <= dst < len(self.doc):
            self.snapshot()
            core.move_page(self.doc, self.cur, dst)
            self.cur = dst
            self.changed(f"Đã chuyển trang tới vị trí {dst + 1}.")

    def duplicate(self):
        if self.need_doc():
            self.snapshot()
            core.duplicate_page(self.doc, self.cur)
            self.cur += 1
            self.changed("Đã nhân bản trang.")

    def blank(self):
        if self.need_doc():
            self.snapshot()
            core.insert_blank_page(self.doc, self.cur, like=self.cur)
            self.cur += 1
            self.changed("Đã chèn trang trắng.")

    def insert_file(self):
        if not self.need_doc():
            return
        path = filedialog.askopenfilename(title="Chọn PDF cần chèn", filetypes=[("PDF", "*.pdf")])
        if path:
            self.snapshot()
            core.insert_pdf_file(self.doc, path, self.cur)
            self.changed(f"Đã chèn {os.path.basename(path)} sau trang {self.cur + 1}.")

    def ask_pages(self, title):
        sel = self.selected_pages()
        init = ", ".join(str(p + 1) for p in sel) if len(sel) > 1 else f"1-{len(self.doc)}"
        s = simpledialog.askstring(title, f"Nhập trang (vd: 1-3, 5, 8-). Tài liệu có {len(self.doc)} trang:",
                                   initialvalue=init, parent=self.root)
        if not s:
            return None
        try:
            return core.parse_ranges(s, len(self.doc))
        except ValueError as ex:
            messagebox.showerror(APP, str(ex))
            return None

    def extract(self):
        if not self.need_doc():
            return
        pages = self.ask_pages("Trích trang")
        if pages:
            path = self.ask_save_path("Lưu trang trích", "_trich")
            if path:
                core.extract_pages(self.doc, pages, path)
                messagebox.showinfo(APP, f"Đã trích {len(pages)} trang:\n{path}")

    def split(self):
        if not self.need_doc():
            return
        n = simpledialog.askinteger(APP, "Tách thành các tệp, mỗi tệp bao nhiêu trang?", minvalue=1,
                                    maxvalue=len(self.doc), initialvalue=1, parent=self.root)
        if n:
            d = filedialog.askdirectory(title="Chọn thư mục lưu")
            if d:
                base = os.path.splitext(os.path.basename(self.path or "tai_lieu"))[0]
                files = core.split_every(self.doc, n, d, base)
                messagebox.showinfo(APP, f"Đã tách thành {len(files)} tệp trong:\n{d}")

    def export_png(self):
        if not self.need_doc():
            return
        pages = self.ask_pages("Xuất ảnh")
        if not pages:
            return
        dpi = simpledialog.askinteger(APP, "Độ phân giải (DPI): 150 = vừa, 300 = nét để in", initialvalue=150,
                                      minvalue=50, maxvalue=600, parent=self.root)
        d = filedialog.askdirectory(title="Chọn thư mục lưu ảnh") if dpi else None
        if d:
            base = os.path.splitext(os.path.basename(self.path or "trang"))[0]
            files = core.export_images(self.doc, d, dpi, pages, base)
            messagebox.showinfo(APP, f"Đã xuất {len(files)} ảnh vào:\n{d}")

    def export_text(self):
        if not self.need_doc():
            return
        path = filedialog.asksaveasfilename(title="Lưu văn bản", defaultextension=".txt",
                                            initialfile="van_ban.txt", filetypes=[("Văn bản", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(core.extract_text(self.doc))
            messagebox.showinfo(APP, f"Đã lưu văn bản:\n{path}")

    # ================================================================ chỉnh sửa
    def replace_dialog(self):
        if self.need_doc():
            ReplaceDialog(self.root, self.do_replace)

    def do_replace(self, find, repl, case, cur_only):
        if not find:
            return
        self.snapshot()
        try:
            n = core.replace_text(self.doc, find, repl, pages=[self.cur] if cur_only else None,
                                  fontfile=self.fonts[self.state["font"]], match_case=case)
        except Exception as ex:  # noqa: BLE001
            self.undo_stack.pop()
            messagebox.showerror(APP, f"Lỗi khi thay chữ:\n{ex}")
            return
        if n:
            self.changed(f"Đã thay {n} chỗ “{find}” → “{repl}”.")
            messagebox.showinfo(APP, f"Đã thay {n} chỗ.")
        else:
            self.undo_stack.pop()
            messagebox.showinfo(APP, f"Không tìm thấy “{find}”.")

    def search_next(self):
        if not self.need_doc():
            return
        q = self.search_var.get().strip()
        if not q:
            self.search_hits = []
            self.render()
            return
        if not self.search_hits or getattr(self, "_last_q", None) != q:
            self._last_q = q
            self.search_hits = core.search_text(self.doc, q)
            self.search_idx = -1
            if not self.search_hits:
                self.set_status(f"Không tìm thấy “{q}”.")
                self.render()
                return
        self.search_idx = (self.search_idx + 1) % len(self.search_hits)
        pno, _ = self.search_hits[self.search_idx]
        if pno != self.cur:
            self.goto(pno)
        self.render()
        self.set_status(f"Kết quả {self.search_idx + 1}/{len(self.search_hits)} — trang {pno + 1}. "
                        f"Nhấn Enter để tới kết quả tiếp.")

    def highlight_all(self):
        if not self.need_doc():
            return
        q = simpledialog.askstring(APP, "Tô sáng mọi chỗ có chữ:", initialvalue=self.search_var.get(),
                                   parent=self.root)
        if q:
            self.snapshot()
            n = core.highlight_all(self.doc, q)
            if n:
                self.changed(f"Đã tô sáng {n} chỗ.")
            else:
                self.undo_stack.pop()
                messagebox.showinfo(APP, "Không tìm thấy.")

    def watermark(self):
        if not self.need_doc():
            return
        t = simpledialog.askstring(APP, "Chữ đóng dấu chìm trên mọi trang:", initialvalue="BẢN NHÁP",
                                   parent=self.root)
        if t:
            self.snapshot()
            core.watermark(self.doc, t, fontfile=self.fonts[self.state["font"]])
            self.changed("Đã đóng dấu chìm.")

    def page_numbers(self):
        if not self.need_doc():
            return
        fmt = simpledialog.askstring(APP, "Mẫu số trang ({n} = số trang, {total} = tổng số trang):",
                                     initialvalue="Trang {n}/{total}", parent=self.root)
        if not fmt:
            return
        pos = simpledialog.askstring(APP, "Vị trí: giữa dưới / trái dưới / phải dưới",
                                     initialvalue="giữa dưới", parent=self.root) or "giữa dưới"
        self.snapshot()
        try:
            core.add_page_numbers(self.doc, fmt, position=pos.strip().lower(),
                                  fontfile=self.fonts[self.state["font"]])
        except (KeyError, IndexError, ValueError):
            self.undo_stack.pop()
            messagebox.showerror(APP, "Mẫu không hợp lệ. Chỉ dùng {n} và {total}.")
            return
        self.changed("Đã đánh số trang.")

    def help(self):
        messagebox.showinfo(APP, (
            "HƯỚNG DẪN NHANH\n\n"
            "• Mở PDF: Ctrl+O. Lưu: Ctrl+S. Hoàn tác: Ctrl+Z.\n"
            "• Chọn công cụ trên thanh trên cùng rồi thao tác trên trang:\n"
            "   – Thêm chữ: bấm vào chỗ cần viết.\n"
            "   – Ảnh/Chữ ký: kéo khung rồi chọn ảnh.\n"
            "   – Che trắng: kéo quanh vùng cần xoá.\n"
            "   – Tô sáng / Khung: kéo chuột.\n"
            "• Sửa chữ có sẵn: Chỉnh sửa → Tìm & thay chữ (Ctrl+H).\n"
            "• Trang: chọn trang ở cột trái (Ctrl/Shift chọn nhiều) → xoay, xoá, di chuyển.\n"
            "• Gộp / tách / nén / đặt mật khẩu: menu Tệp và Trang.\n\n"
            "Chữ tiếng Việt dùng phông có dấu (Arial, Times New Roman…)."))


def main():
    try:  # nét chữ trên màn hình độ phân giải cao (Windows)
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001
        pass
    root = tk.Tk()
    App(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()


if __name__ == "__main__":
    main()

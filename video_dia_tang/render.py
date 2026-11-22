import sys, os, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

UP = "/root/.claude/uploads/2c4af208-e19c-52b2-975f-31083f7f436c/"
SP = os.path.dirname(os.path.abspath(__file__))
AUDIO = [UP + f for f in os.listdir(UP) if f.endswith(".mp3")][0]
W, H, FPS = 1080, 1920, 30
DUR = 262.75
NF = int(DUR * FPS)
FONT_T = SP + "/fonts/expo-google-fonts-noto-serif-0.4.2/600SemiBold/NotoSerif_600SemiBold.ttf"
FONT_B = SP + "/fonts/expo-google-fonts-noto-serif-0.4.2/400Regular/NotoSerif_400Regular.ttf"
FONT_I = SP + "/fonts/expo-google-fonts-noto-serif-0.4.2/400Regular_Italic/NotoSerif_400Regular_Italic.ttf"
if not os.path.exists(FONT_I):
    FONT_I = FONT_B

IMG = {
    "lotus": "c0580fc8", "temple": "3ac057ee", "cry": "849ea7a6", "sea": "6b6a0069",
    "king": "08c04331", "heaven": "e058ceec", "dz": "14995c80", "dzc": "c048b46d",
    "monk": "61128297", "baby": "4fe6dbf1", "buddha": "4ec63eae", "kings": "5b0798ef",
}

# ---------- scenes: (key, t0, t1, (cx,cy,zoom) start, end, fx, look) ; coords in source px (~941x1670)
S = [
    ("lotus", 0, 14, (470, 900, 1.00), (475, 930, 1.22), "gold", "open"),
    ("temple", 14, 34, (470, 1000, 1.05), (420, 1150, 1.40), "gold", ""),
    ("cry", 34, 54, (470, 900, 1.05), (440, 1010, 1.55), "dust", ""),
    ("sea", 54, 70, (300, 950, 1.30), (580, 1000, 1.10), "ember", ""),
    ("king", 70, 81, (300, 900, 1.25), (470, 950, 1.02), "ember", ""),
    ("dz", 81, 99, (470, 600, 1.90), (470, 900, 1.00), "gold", "chorus"),
    ("dzc", 99, 109, (500, 900, 1.05), (560, 820, 1.25), "gold", "chorus"),
    ("heaven", 109, 119.5, (520, 900, 1.25), (470, 880, 1.02), "petal", "glow"),
    ("monk", 119.5, 127, (470, 1000, 1.05), (420, 1060, 1.30), "dust", ""),
    ("baby", 127, 138, (500, 1100, 1.10), (660, 1150, 1.50), "dust", ""),
    ("buddha", 138, 158.5, (470, 900, 1.02), (560, 900, 1.30), "petal", "glow"),
    ("cry", 158.5, 168, (450, 980, 1.35), (440, 1030, 1.70), "dust", "memory"),
    ("kings", 168, 179, (470, 1000, 1.25), (470, 960, 1.03), "gold", ""),
    ("dz", 179, 197, (470, 950, 1.00), (470, 640, 1.60), "gold", "climax"),
    ("dzc", 197, 206, (560, 820, 1.30), (520, 900, 1.05), "gold", "chorus"),
    ("cry", 206, 210, (450, 1000, 1.45), (440, 1020, 1.60), "dust", "memory"),
    ("monk", 210, 214, (470, 1050, 1.25), (480, 1080, 1.40), "dust", "memory"),
    ("heaven", 214, 220.5, (450, 950, 1.20), (420, 980, 1.40), "petal", "memory"),
    ("dzc", 220.5, 240, (520, 950, 1.00), (590, 780, 1.45), "gold", "glow"),
    ("dz", 240, 254, (470, 900, 1.00), (470, 760, 1.25), "gold", "climax"),
    ("lotus", 254, DUR, (475, 930, 1.22), (475, 900, 1.05), "gold", "end"),
]
XF = 0.8  # half crossfade

L = [  # lyrics (start, text) ; each shows until next start
    (30, "Bà-la-môn nữ thương mẹ vô vàn"),
    (34, "Trước đài Đức Phật\nlệ tràn chứa chan"),
    (41, "Mẹ qua đời, lòng con đau xót"),
    (45, "Dâng hết gia tài\ncúng Phật thành tâm"),
    (50, "Nguyện cho mẹ thoát chốn tối tăm"),
    (54, "Nương nhờ công đức\nlìa vòng khổ đau"),
    (61, "Nhìn chúng sinh trong miền tăm tối"),
    (66, "Nghe tiếng than vang khắp ngục sâu"),
    (70, "Nàng phát đại nguyện nhiệm mầu"),
    (74, "Cứu muôn loài thoát\nbể sầu trầm luân"),
    (81, "!Địa Tạng Vương ơi!\nĐịa Tạng Vương ơi!"),
    (85, "!Ngàn đời đại nguyện sáng ngời!"),
    (89, "!“Địa ngục vị không,\nthệ bất thành Phật”"),
    (95, "!“Chúng sinh độ tận,\nphương chứng Bồ Đề”"),
    (99, "!Địa Tạng Vương ơi!\nĐịa Tạng Vương ơi!"),
    (104, "!Tích trượng trong tay,\nminh châu sáng ngời"),
    (109, "!Dẫu qua muôn kiếp luân hồi"),
    (113, "!Ngài còn cứu khổ\nchẳng rời chúng sinh"),
    (120, "Một đời khác, nàng tên Quang Mục"),
    (124, "Thương mẹ hiền\nchịu cảnh đọa đày"),
    (129, "Trước Phật thành kính đêm ngày"),
    (133, "Phát tâm cứu độ\nmuôn loài khổ đau"),
    (138, "Từ lòng hiếu hóa thành đại nguyện"),
    (142, "Từ tình thương soi sáng hằng sa"),
    (147, "Dẫu qua vô lượng thời gian"),
    (151, "Tâm Ngài vẫn vẹn\nmuôn ngàn từ bi"),
    (159, "~Ai còn cha mẹ trên đời…"),
    (162, "~Xin thương, xin hiếu,\nđừng lời muộn màng"),
    (168, "Nguyện cho muôn loài bình an"),
    (172, "Bước theo ánh đạo"),
    (174, "Vượt ngàn khổ đau"),
    (179, "!Địa Tạng Vương ơi!\nĐịa Tạng Vương ơi!"),
    (183, "!Ngàn đời đại nguyện\nsáng ngời từ bi"),
    (187, "!“Địa ngục vị không,\nthệ bất thành Phật”"),
    (192, "!“Chúng sinh độ tận,\nphương chứng Bồ Đề”"),
    (197, "!Địa Tạng Vương ơi!\nĐịa Tạng Vương ơi!"),
    (201, "!Tích trượng trong tay,\nminh châu sáng ngời"),
    (206, "!Dẫu qua muôn kiếp luân hồi"),
    (210, "!Ngài còn cứu khổ"),
    (214, "!Chẳng rời chúng sinh"),
    (221, "!Nam mô Đại Nguyện\nĐịa Tạng Vương Bồ Tát"),
    (231, "Xin đem lòng sáng\ngửi khắp muôn phương"),
    (235, "Nguyện cho người gặp\nnẻo lành an vui"),
    (240, "!Nam mô Đại Nguyện\nĐịa Tạng Vương Bồ Tát"),
    (251, None),
]
C = [
    (2.5, 12.8, "ĐỊA TẠNG VƯƠNG\nĐẠI NGUYỆN", "title"),
    (5.5, 12.8, "— Lời Nguyện Cuối —", "sub"),
    (16.5, 28.8, "Thuở xưa, có một người con gái\nhiếu hạnh…", "narr"),
    (254.5, DUR - 0.3, "Nam mô Đại Nguyện\nĐịa Tạng Vương Bồ Tát", "title2"),
]
for i in range(len(L) - 1):
    t0, tx = L[i]
    t1 = L[i + 1][0]
    if tx is None:
        continue
    st = "lyric"
    if tx.startswith("!"):
        st, tx = "chorus", tx[1:]
        if "Địa Tạng Vương ơi" in tx:
            st = "cry_out"
    elif tx.startswith("~"):
        st, tx = "bridge", tx[1:]
    C.append((t0 - 0.25, min(t1 - 0.35, t0 + 9.5), tx, st))

INK = (74, 42, 24)
GOLD = (150, 92, 20)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------- assets
_img = {}


def get_img(key):
    if key not in _img:
        im = Image.open(UP + IMG[key] + "-image.png").convert("RGB")
        big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        big = big.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        _img[key] = (big, im.width, im.height)
    return _img[key]


def ken(key, cx, cy, z):
    big, w0, h0 = get_img(key)
    cover = max(W / w0, H / h0)
    s = cover * z  # output px per source px
    cw, ch = W / s, H / s
    cx = min(max(cx, cw / 2), w0 - cw / 2)
    cy = min(max(cy, ch / 2), h0 - ch / 2)
    x0, y0 = (cx - cw / 2) * 2, (cy - ch / 2) * 2
    k = 2 / s
    out = big.transform((W, H), Image.AFFINE, (k, 0, x0, 0, k, y0), resample=Image.BICUBIC)
    return np.asarray(out, dtype=np.float32) / 255.0


def sprite(r, color, hard=0.35):
    n = r * 2 + 1
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2.2
    a = np.maximum(a, (d < hard * 0.5) * 1.0) if hard else a
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def petal_sprites():
    out = []
    base = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.ellipse((14, 4, 46, 56), fill=(244, 150, 160, 220))
    d.ellipse((20, 10, 40, 46), fill=(252, 196, 200, 200))
    base = base.filter(ImageFilter.GaussianBlur(1.2))
    for ang in range(0, 360, 15):
        out.append(base.rotate(ang, resample=Image.BICUBIC))
    return out


GOLD_SP = [sprite(r, (255, 214, 120)) for r in (6, 9, 13, 18)]
EMBER_SP = [sprite(r, (255, 120, 40)) for r in (4, 6, 9, 12)]
DUST_SP = [sprite(r, (255, 240, 215)) for r in (4, 6, 8)]
PETALS = petal_sprites()

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_vd = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.55) / (H * 0.70)) ** 2)
VIGN = np.clip(1 - 0.55 * np.clip(_vd - 0.45, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)


def radial(cx, cy, rad):
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad
    return np.clip(1 - d, 0, 1) ** 2


GLOW_CACHE = {}


def glow_map(key):
    if key not in GLOW_CACHE:
        GLOW_CACHE[key] = (radial(W * 0.55, H * 0.45, H * 0.6)[..., None] * np.array([1.0, 0.82, 0.5], np.float32))
    return GLOW_CACHE[key]


# ---------- audio envelope
def load_env():
    p = SP + "/env.npy"
    if os.path.exists(p):
        return np.load(p)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", "12000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 12000 // FPS
    n = len(a) // hop
    e = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    # fast (beat) and slow components
    k = np.ones(15) / 15
    slow = np.convolve(e, k, "same")
    fast = np.clip(e - slow, 0, None)
    fast = fast / (fast.max() + 1e-6)
    slow = slow / slow.max()
    env = np.stack([slow, fast], 1)
    np.save(p, env)
    return env


ENV = load_env()


def env_at(f):
    f = min(f, len(ENV) - 1)
    return ENV[f]


# ---------- particles (stateless functions of t)
def particles(layer, kind, t, seed, alpha):
    if alpha <= 0.01:
        return
    rng = random.Random(seed)
    if kind == "gold":
        n, sps = 46, GOLD_SP
    elif kind == "ember":
        n, sps = 70, EMBER_SP
    elif kind == "dust":
        n, sps = 34, DUST_SP
    else:
        n, sps = 26, PETALS
    for i in range(n):
        x0, y0 = rng.random() * W, rng.random() * H
        sp = rng.uniform(0.4, 1.0)
        ph = rng.random() * 6.28
        si = rng.randrange(len(sps) if kind != "petal" else 1)
        if kind == "gold":
            y = (y0 - t * 38 * sp) % (H + 80) - 40
            x = x0 + 30 * math.sin(t * 0.5 * sp + ph)
            a = (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.2 * sp + ph))) * 0.55
        elif kind == "ember":
            y = (y0 - t * 110 * sp) % (H + 80) - 40
            x = x0 + 45 * math.sin(t * 1.3 * sp + ph)
            a = (0.4 + 0.6 * abs(math.sin(t * 5 * sp + ph))) * (0.4 + 0.6 * y / H) * 0.85
        elif kind == "dust":
            y = (y0 - t * 18 * sp) % (H + 80) - 40
            x = x0 + 20 * math.sin(t * 0.4 + ph)
            a = (0.5 + 0.5 * math.sin(t * 1.5 * sp + ph)) * 0.45
        else:
            y = (y0 + t * 90 * sp) % (H + 120) - 60
            x = (x0 - t * 35 * sp + 60 * math.sin(t * 0.9 * sp + ph)) % (W + 120) - 60
            a = 0.9
            si = int((t * 40 * sp + ph * 20) / 15) % len(PETALS)
        spr = sps[si]
        a *= alpha
        if a < 0.03:
            continue
        if a < 0.99:
            s2 = spr.copy()
            s2.putalpha(s2.getchannel("A").point(lambda v, a=a: int(v * a)))
        else:
            s2 = spr
        layer.alpha_composite(s2, (int(x - spr.width / 2), int(y - spr.height / 2)))


# ---------- text
_txt = {}


def render_text(text, style):
    key = (text, style)
    if key in _txt:
        return _txt[key]
    if style == "title":
        font, col, sp = ImageFont.truetype(FONT_T, 92), (128, 60, 18), 22
    elif style == "title2":
        font, col, sp = ImageFont.truetype(FONT_T, 74), (128, 60, 18), 20
    elif style == "sub":
        font, col, sp = ImageFont.truetype(FONT_I, 50), (120, 70, 40), 10
    elif style == "big":
        font, col, sp = ImageFont.truetype(FONT_T, 78), (128, 60, 18), 20
    elif style == "vow":
        font, col, sp = ImageFont.truetype(FONT_T, 70), (120, 40, 12), 22
    elif style == "cry_out":
        font, col, sp = ImageFont.truetype(FONT_T, 84), (140, 58, 8), 24
    elif style == "chorus":
        font, col, sp = ImageFont.truetype(FONT_T, 64), (124, 50, 14), 22
    elif style == "bridge":
        font, col, sp = ImageFont.truetype(FONT_I, 64), (92, 40, 22), 22
    elif style == "narr":
        font, col, sp = ImageFont.truetype(FONT_I, 52), (100, 60, 36), 18
    elif style == "quote":
        font, col, sp = ImageFont.truetype(FONT_I, 56), (96, 44, 22), 18
    else:
        font, col, sp = ImageFont.truetype(FONT_B, 54), INK, 18
    lines = text.split("\n")
    # wrap long single lines
    wrapped = []
    for ln in lines:
        words = ln.split(" ")
        cur = ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            if font.getlength(test) > W - 150 and cur:
                wrapped.append(cur)
                cur = w_
            else:
                cur = test
        wrapped.append(cur)
    asc, desc = font.getmetrics()
    lh = asc + desc + sp
    th = lh * len(wrapped)
    pad = 70
    img = Image.new("RGBA", (W, th + pad * 2), (0, 0, 0, 0))
    # soft paper halo behind text
    halo = Image.new("L", img.size, 0)
    hd = ImageDraw.Draw(halo)
    for i, ln in enumerate(wrapped):
        tw = font.getlength(ln)
        y = pad + i * lh
        hd.rounded_rectangle((W / 2 - tw / 2 - 30, y - 6, W / 2 + tw / 2 + 30, y + asc + desc + 10), 30, fill=150)
    halo = halo.filter(ImageFilter.GaussianBlur(28))
    hl = Image.new("RGBA", img.size, (246, 238, 226, 0))
    hl.putalpha(halo)
    img.alpha_composite(hl)
    d = ImageDraw.Draw(img)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, ln in enumerate(wrapped):
        tw = font.getlength(ln)
        x, y = W / 2 - tw / 2, pad + i * lh
        gd.text((x, y), ln, font=font, fill=(255, 250, 240, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(glow)
    for i, ln in enumerate(wrapped):
        tw = font.getlength(ln)
        x, y = W / 2 - tw / 2, pad + i * lh
        d.text((x, y), ln, font=font, fill=col + (255,))
    if style in ("title", "title2", "vow", "big", "cry_out"):
        # gold underline ornament
        y = pad + th + 4
        d.line((W / 2 - 120, y, W / 2 + 120, y), fill=(190, 130, 40, 220), width=3)
        d.ellipse((W / 2 - 7, y - 7, W / 2 + 7, y + 7), fill=(200, 140, 40, 230))
    _txt[key] = img
    return img


def text_y(style, t):
    act = [x for x in S if x[1] <= t < x[2]]
    if act and act[0][0] in ("cry", "kings") and style not in ("title", "sub", "title2"):
        return 1430
    if style == "title":
        return 260
    if style == "sub":
        return 600
    if style == "title2":
        return 300
    return 230


# ---------- compose one frame
def scene_alpha(i, t):
    k, t0, t1 = S[i][0], S[i][1], S[i][2]
    a_in = 1.0 if i == 0 else ease((t - (t0 - XF)) / (2 * XF))
    a_out = 1.0 if i == len(S) - 1 else 1 - ease((t - (t1 - XF)) / (2 * XF))
    return min(a_in, a_out)


def scene_frame(i, t, f):
    key, t0, t1, a, b, fx, look = S[i]
    p = ease((t - (t0 - XF)) / ((t1 + XF) - (t0 - XF)))
    cx = a[0] + (b[0] - a[0]) * p
    cy = a[1] + (b[1] - a[1]) * p
    z = a[2] * (b[2] / a[2]) ** p
    fr = ken(key, cx, cy, z)
    slow, fast = env_at(f)
    if look == "memory":
        g = fr.mean(2, keepdims=True)
        sep = np.concatenate([g * 1.05, g * 0.93, g * 0.78], 2)
        fr = fr * 0.35 + sep * 0.65
        fr = fr * 0.92 + 0.06
    if look in ("glow", "climax", "open", "end", "chorus"):
        amt = {"glow": 0.18, "climax": 0.24, "open": 0.10, "end": 0.12, "chorus": 0.20}[look]
        amt = amt * (0.6 + 0.6 * slow) + (0.25 if look == "climax" else 0.1) * fast
        gm = glow_map(key) * amt
        fr = 1 - (1 - fr) * (1 - gm)
    return fr


def frame(f):
    t = f / FPS
    acc = None
    act = [i for i in range(len(S)) if S[i][1] - XF <= t < S[i][2] + XF]
    tot = 0
    parts = []
    for i in act:
        al = scene_alpha(i, t)
        if al <= 0:
            continue
        parts.append((i, al))
    # blend
    for i, al in parts:
        fr = scene_frame(i, t, f)
        acc = fr * al if acc is None else acc * (1 - al) + fr * al
        tot = 1
    fr = acc
    fr = fr * VIGN
    # transition light leak (warm bloom at cuts)
    for i in range(1, len(S)):
        dt = abs(t - S[i][1])
        if dt < 1.2:
            k = (1 - dt / 1.2) ** 2 * (0.10 if S[i][6] == "memory" else 0.16)
            leak = radial(W * (0.85 if i % 2 else 0.15), H * 0.3, H * 0.8)[..., None] * np.array([1, .7, .4], np.float32)
            fr = 1 - (1 - fr) * (1 - leak * k)
    for (c0, c1, txt, st) in C:
        if st == "cry_out" and c0 <= t <= c0 + 3.5:
            k = math.exp(-(t - c0) * 1.3) * 0.32 * ease((t - c0) / 0.25)
            fr = 1 - (1 - fr) * (1 - glow_map("burst") * k)
    img = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")
    # particles
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, al in parts:
        particles(layer, S[i][5], t, 1000 + i, al)
    img.alpha_composite(layer)
    # captions
    for (c0, c1, txt, st) in C:
        if c0 - 0.1 <= t <= c1 + 0.1:
            fi = 1.0 if st == "title" and False else 1.0
            fin = 1.0 if st in ("title", "sub", "title2", "narr") else 0.45
            a = min(ease((t - c0) / fin), ease((c1 - t) / 0.5))
            if a <= 0:
                continue
            ti = render_text(txt, st)
            y = text_y(st, t) + int(18 * (1 - a))
            if a < 0.999:
                ti = ti.copy()
                ti.putalpha(ti.getchannel("A").point(lambda v, a=a: int(v * a)))
            img.alpha_composite(ti, (0, y))
    out = np.asarray(img.convert("RGB"), dtype=np.float32)
    # fade from / to black
    if t < 1.5:
        out *= ease(t / 1.5)
    if t > DUR - 2.5:
        out *= ease((DUR - t) / 2.5)
    return out.astype(np.uint8)


def render_chunk(a, b, path):
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame(f).tobytes())
        if (f - a) % 300 == 0:
            print(path, f - a, "/", b - a, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for tt in sys.argv[2:]:
            Image.fromarray(frame(int(float(tt) * FPS))).save(SP + f"/still_{tt}.jpg", quality=88)
    elif mode == "chunk":
        k, n = int(sys.argv[2]), int(sys.argv[3])
        a, b = NF * k // n, NF * (k + 1) // n
        render_chunk(a, b, SP + f"/chunk_{k}.mp4")

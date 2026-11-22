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
    ("lotus", 0, 15, (470, 900, 1.00), (475, 930, 1.22), "gold", "open"),
    ("temple", 15, 33, (470, 1000, 1.05), (520, 1150, 1.35), "gold", ""),
    ("cry", 33, 51, (470, 900, 1.05), (440, 1010, 1.55), "dust", ""),
    ("sea", 51, 70, (300, 950, 1.30), (560, 1000, 1.10), "ember", ""),
    ("king", 70, 88, (470, 950, 1.05), (600, 980, 1.30), "ember", ""),
    ("heaven", 88, 107, (520, 900, 1.25), (470, 880, 1.02), "petal", "glow"),
    ("monk", 107, 124, (470, 1000, 1.05), (480, 1080, 1.30), "dust", ""),
    ("baby", 124, 141, (500, 1100, 1.10), (640, 1150, 1.45), "dust", ""),
    ("buddha", 141, 158, (470, 900, 1.02), (560, 950, 1.25), "petal", "glow"),
    ("kings", 158, 175, (470, 1000, 1.25), (470, 960, 1.03), "gold", ""),
    ("dz", 175, 196, (470, 600, 1.90), (470, 900, 1.00), "gold", "glow"),
    ("dzc", 196, 214, (520, 900, 1.05), (560, 800, 1.30), "gold", "glow"),
    ("cry", 214, 220, (450, 1000, 1.45), (440, 1020, 1.60), "dust", "memory"),
    ("sea", 220, 226, (300, 900, 1.40), (330, 900, 1.55), "ember", "memory"),
    ("heaven", 226, 232, (450, 950, 1.20), (420, 980, 1.40), "petal", "memory"),
    ("baby", 232, 238, (620, 1150, 1.40), (680, 1180, 1.65), "dust", "memory"),
    ("dz", 238, 256.5, (470, 950, 1.00), (470, 640, 1.70), "gold", "climax"),
    ("lotus", 256.5, DUR, (475, 930, 1.22), (475, 900, 1.05), "gold", "end"),
]
XF = 0.8  # half crossfade

# ---------- captions: (t0, t1, text, style)
C = [
    (2.5, 13.5, "ĐỊA TẠNG VƯƠNG\nĐẠI NGUYỆN", "title"),
    (6.0, 13.5, "— Lời Nguyện Cuối —", "sub"),
    (16.5, 24.0, "Thuở xưa, có một người con gái\nhiếu hạnh…", "cap"),
    (24.5, 32.0, "ngày đêm quỳ trước Phật,\ncầu cho mẹ hiền.", "cap"),
    (34.5, 42.0, "Mẹ nàng một đời gieo nghiệp,\nlìa trần về nơi tăm tối.", "cap"),
    (42.5, 50.0, "Giọt lệ con rơi,\nthấm vào từng nén hương khuya.", "cap"),
    (52.5, 60.5, "Nương tâm niệm Phật,\nnàng đến bên bờ biển nghiệp…", "cap"),
    (61.0, 69.0, "nơi muôn người chìm trong\nsóng lửa khổ đau.", "cap"),
    (71.5, 79.0, "Quỷ vương Vô Độc chắp tay thưa:", "cap"),
    (79.5, 87.0, "“Thánh nữ chớ sầu,\nthân mẫu người\nđã sinh về cõi trời.”", "quote"),
    (89.5, 97.5, "Mẹ đã an lành…", "cap"),
    (98.0, 106.0, "nước mắt con giờ hoá thành hoa.", "cap"),
    (108.5, 116.0, "Một kiếp khác, nàng là Quang Mục,", "cap"),
    (116.5, 123.0, "dâng cơm cúng dường,\nnguyện cứu mẹ thoát khổ.", "cap"),
    (125.5, 133.0, "Đứa trẻ vừa chào đời đã cất tiếng:", "cap"),
    (133.5, 140.0, "“Con ơi… mẹ đây.”", "quote"),
    (142.5, 150.0, "Nàng quỳ trước Phật, phát lời đại nguyện:", "cap"),
    (150.5, 157.0, "“Trăm nghìn muôn kiếp,\ncon nguyện cứu khổ chúng sinh.”", "quote"),
    (159.5, 166.5, "Có vị vua nguyện thành Phật\nđể độ người,", "cap"),
    (167.0, 174.0, "có vị nguyện độ hết chúng sinh\nrồi mới thành Phật.", "cap"),
    (177.0, 185.5, "Bao kiếp luân hồi,\nmột tấm lòng không đổi…", "cap"),
    (186.0, 195.0, "Ngài là\nĐịa Tạng Vương Bồ Tát.", "big"),
    (197.5, 205.0, "Tích trượng mở cửa địa ngục,", "cap"),
    (205.5, 213.0, "minh châu soi sáng mọi nẻo tối tăm.", "cap"),
    (215.0, 225.0, "Từ giọt lệ của một người con…", "cap"),
    (226.0, 237.0, "đã thành đại nguyện\ncứu khổ muôn loài.", "cap"),
    (239.5, 247.5, "“Địa ngục chưa trống,\nthề không thành Phật.”", "vow"),
    (248.0, 256.0, "“Chúng sinh độ tận,\nphương chứng Bồ Đề.”", "vow"),
    (257.5, DUR - 0.3, "Nam mô Đại Nguyện\nĐịa Tạng Vương Bồ Tát", "title2"),
]

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
    if style in ("title", "title2", "vow", "big"):
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
    if look in ("glow", "climax", "open", "end"):
        amt = {"glow": 0.18, "climax": 0.22, "open": 0.10, "end": 0.12}[look]
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
            a = min(ease((t - c0) / 1.0), ease((c1 - t) / 0.9))
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

# -*- coding: utf-8 -*-
"""تصميم صورة الخبر (نسخة بايثون من ZFImage.java): خلفية حمراء متدرجة + دائرة خفيفة،
عنوان «فوری» بخط Black، والنص تحته بخط Semibold مضبوط بالكشيدة على 3 الى 5 اسطر.
يحتاج Pillow مع raqm (تشكيل الحروف العربية)."""
import importlib
import io
import os
import re
import subprocess
import sys
from functools import lru_cache

W, H, S = 1080, 1350, 2          # احداثيات التصميم، والدقة الفعلية 2160 x 2700
HEAD_FA = "فوری"
HEAD_SIZE, HEAD_BASE = 173.5, 566.0
RIGHT, TEXT_W, TEXT_TOP = 898.0, 708.0, 763.0
SIZE_MIN, SIZE_CAP = 38.0, 100.0
LINE_MULT, LAST_MAX = 1.5, 0.88
DUAL = "بتثجحخسشصضطظعغفقكلمنهيئىپچڤگکی"
FIRST_DOT = re.compile(r"\.(\s|$)")
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BLACK = os.path.join(HERE, "sf_arabic_black.ttf")
FONT_SEMI = os.path.join(HERE, "sf_arabic_semibold.ttf")

_PIL = {}


def install_deps():
    """يثبّت Pillow + libraqm لو ناقصين (على سيرفر GitHub). ما يستورد Pillow بنفس العملية.
    يرمي استثناء لو فشل. السيرفر يعيد تشغيل نفسه بعدها (execv) عشان يشوف المكتبة الجديدة."""
    chk = [sys.executable, "-c", "import sys\nfrom PIL import features\nsys.exit(0 if features.check('raqm') else 1)"]
    errs = []

    def ok():
        return subprocess.run(chk, capture_output=True).returncode == 0

    def run(cmd):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                errs.append(" ".join(((p.stderr or "") + (p.stdout or "")).split())[-160:])
        except OSError as e:
            errs.append(str(e))

    if ok():
        return
    if subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True).returncode != 0:
        run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "pillow"])
        if subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True).returncode != 0:
            run([sys.executable, "-m", "pip", "install", "-q", "--user", "pillow"])
    if not ok():
        run(["sudo", "-n", "apt-get", "install", "-y", "-qq", "libraqm0"])
    if not ok():
        raise Exception("Pillow مع raqm غير متوفر (لازم لتشكيل الحروف العربية)" + (": " + errs[-1] if errs else ""))


def ensure_deps():
    """يستورد Pillow (لازم يكون مثبّت: السيرفر يستدعي install_deps اول ما يبدأ). يرمي استثناء لو ناقص."""
    importlib.invalidate_caches()
    try:
        import site
        site.addsitedir(site.getusersitepackages())
    except Exception:
        pass
    global Image, ImageDraw, ImageFont
    try:
        from PIL import Image, ImageDraw, ImageFont, features  # noqa: F401
    except ImportError as e:
        raise Exception("Pillow غير متوفر: %s" % e)
    if not features.check("raqm"):
        raise Exception("Pillow بدون raqm (تشكيل الحروف العربية)")


@lru_cache(maxsize=None)
def _font(path, px):
    return ImageFont.truetype(path, px)


@lru_cache(maxsize=200000)
def _measure(text, size, path):
    """عرض النص بوحدات التصميم (مثل measureText)."""
    return _font(path, size * S).getlength(text, direction="rtl", language="ar") / S


# ------------------------------------------------------------ اختيار النص
def clean_text(t):
    s = re.sub(r"\s+", " ", t).strip()
    for _ in range(3):
        s = re.sub(r"^[\W_]+", "", s)
        s = re.sub(r"^(عاجل|فوری|خبر فوری)(?![^\W_])", "", s)
    s = re.sub(r"^[\W_]+", "", s)
    s = re.sub(r"[\s.,،؛:;!?؟…\-]+$", "", s).strip()
    return s


def pick_post_text(raw):
    s = (raw or "").replace("\r", "").strip()
    no_links = re.sub(r"[ \t]+", " ", re.sub(r"(https?://|www\.|t\.me/)\S+", "", s)).strip()
    if no_links:
        s = no_links
    t = s
    m = FIRST_DOT.search(s)
    if m:
        t = s[:m.start() + 1]
    else:
        p = s.find("\n\n")
        if p > 0:
            t = s[:p]
    return clean_text(t)


# ------------------------------------------------------------ تقسيم الاسطر
def _wrap(words, size, path, w):
    out, cur = [], ""
    for wd in words:
        if _measure(wd, size, path) > w:
            return None
        t = wd if not cur else cur + " " + wd
        if cur and _measure(t, size, path) > w:
            out.append(cur)
            cur = wd
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def _last_short(ls, size, path):
    if len(ls) < 2:
        return True
    return _measure(ls[-1], size, path) <= TEXT_W * LAST_MAX


def _choose_size(words, path):
    big = _wrap(words, SIZE_CAP, path, TEXT_W)
    if big is not None and len(big) < 3:
        return SIZE_CAP, big
    for pas in range(2):
        for n in range(3, 6):
            sz = SIZE_CAP
            while sz >= SIZE_MIN:
                ls = _wrap(words, sz, path, TEXT_W)
                if ls is not None and len(ls) == n and (pas == 1 or _last_short(ls, sz, path)):
                    return sz, ls
                sz -= 1.0
    return -1.0, None


# ------------------------------------------------------------ الكشيدة
def _is_letter(c):
    o = ord(c)
    return o != 0x0640 and ((0x0621 <= o <= 0x064A) or (0x0671 <= o <= 0x06D3))


def _candidates(w):
    c = []
    for i in range(len(w) - 1):
        a, b = w[i], w[i + 1]
        if a not in DUAL or not _is_letter(b):
            continue
        if a == "ل" and b in "اأإآ":
            continue
        c.append(i)
    mid = (len(w) - 1) * 0.45
    c.sort(key=lambda x: abs(x - mid))
    return c


def _build(w, cand, cnt):
    if not cand:
        return w
    sb = []
    for i, ch in enumerate(w):
        sb.append(ch)
        for k, ci in enumerate(cand):
            if ci == i:
                sb.append("\u0640" * cnt[k])
    return "".join(sb)


def _draw_text(d, right, base, text, font):
    d.text((right * S, base * S), text, font=font, fill=(255, 255, 255), anchor="rs",
           direction="rtl", language="ar")


def _draw_justified(d, line, size, base):
    font = _font(FONT_SEMI, size * S)
    ws = line.split(" ")
    nw = len(ws)
    sp = _measure(" ", size, FONT_SEMI)
    cands = [_candidates(w) for w in ws]
    total = sum(len(c) for c in cands)
    natural = sum(_measure(w, size, FONT_SEMI) for w in ws) + sp * (nw - 1)
    k = _measure("\u0640", size, FONT_SEMI)
    m = 0 if total == 0 else max(0, int((TEXT_W - natural) / k))
    m = min(m, total * 4)
    while True:
        cnt = [[0] * len(c) for c in cands]
        left, rnd = m, 0
        while left > 0:
            any_ = False
            for i in range(nw):
                if left <= 0:
                    break
                cs = len(cands[i])
                if cs == 0:
                    continue
                cnt[i][rnd % cs] += 1
                left -= 1
                any_ = True
            if not any_:
                break
            rnd += 1
        width = sp * (nw - 1)
        out = []
        for i in range(nw):
            out.append(_build(ws[i], cands[i], cnt[i]))
            width += _measure(out[i], size, FONT_SEMI)
        if width <= TEXT_W or m == 0:
            break
        m -= 1
    gap = sp
    if nw > 1 and width < TEXT_W:
        gap = sp + (TEXT_W - width) / (nw - 1)
    x = RIGHT
    for i in range(nw):
        ww = _measure(out[i], size, FONT_SEMI)
        _draw_text(d, x, base, out[i], font)
        x -= ww + gap


# ------------------------------------------------------------ الخلفية
_STOPS = [(0.0, (129, 11, 11)), (.1, (136, 14, 13)), (.2, (143, 15, 14)), (.3, (152, 16, 16)), (.4, (163, 17, 17)),
          (.5, (174, 18, 19)), (.6, (188, 20, 19)), (.7, (199, 21, 21)), (.8, (209, 21, 20)), (.9, (214, 20, 22)),
          (1.0, (219, 19, 23))]


def _grad(t):
    for (a, ca), (b, cb) in zip(_STOPS, _STOPS[1:]):
        if t <= b:
            f = 0.0 if b == a else (t - a) / (b - a)
            return tuple(int(round(ca[i] + (cb[i] - ca[i]) * f)) for i in range(3))
    return _STOPS[-1][1]


def default_bg():
    """تدرج احمر عمودي + دائرة بيضاء شفافة (مثل defaultBg بالتطبيق)."""
    hh = H * S
    col = Image.new("RGB", (1, hh))
    col.putdata([_grad(min(1.0, max(0.0, (y + 0.5) / hh))) for y in range(hh)])
    bg = col.resize((W * S, hh), Image.NEAREST).convert("RGBA")
    circle = Image.new("RGBA", (W * S, hh), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse([(1019 - 430) * S, (500 - 430) * S, (1019 + 430) * S, (500 + 430) * S],
                                   fill=(255, 255, 255, 10))
    return Image.alpha_composite(bg, circle).convert("RGB")


def render(text):
    """الصورة الكاملة (2160x2700) بالفارسية: العنوان «فوری» + النص (لين اول نقطة)."""
    img = default_bg()
    d = ImageDraw.Draw(img)
    _draw_text(d, RIGHT, HEAD_BASE, HEAD_FA, _font(FONT_BLACK, HEAD_SIZE * S))
    s = pick_post_text(text) or "متن خود را اینجا بنویسید"
    words = s.split(" ")
    size, lines = _choose_size(words, FONT_SEMI)
    while size < 0 and len(words) > 1:
        words = words[:-1]
        words[-1] = re.sub(r"[\s.,،؛:;!?؟…\-]+$", "", words[-1]) + "…"
        size, lines = _choose_size(words, FONT_SEMI)
    if size < 0:
        size, lines = SIZE_MIN, [words[0]]
    font = _font(FONT_SEMI, size * S)
    base = TEXT_TOP + 0.8 * size
    pitch = LINE_MULT * size
    for i, ln in enumerate(lines):
        if i < len(lines) - 1:
            _draw_justified(d, ln, size, base + i * pitch)
        else:
            _draw_text(d, RIGHT, base + i * pitch, ln, font)
    return img


def to_jpeg(img, pct=100, quality=98):
    if pct < 100:
        img = img.resize((img.width * pct // 100, img.height * pct // 100), Image.LANCZOS)
    b = io.BytesIO()
    img.save(b, "JPEG", quality=quality, subsampling=0)
    return b.getvalue(), img.width, img.height

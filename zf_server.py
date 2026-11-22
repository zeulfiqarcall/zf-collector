#!/usr/bin/env python3
"""ZF Collector - نسخة السيرفر (GitHub Actions).
يقرأ القنوات العامة t.me/s/... ويفلتر ويرسل الجديد لتلغرام (وروبيكا اختياريا).
الاعدادات: config.json (تتغير من التطبيق). التوكنات: GitHub Secrets (TG_TOKEN, RB_TOKEN).
الحالة: state.json / status.json (يحفظها الـ workflow)."""
import os, re, sys, json, time, html, hashlib, datetime
import urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(HERE, "config.json")
STATE_FILE = os.path.join(HERE, "state.json")
STATUS_FILE = os.path.join(HERE, "status.json")
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
MAX_PER_CHANNEL = 10
KEEP_HASHES = 300
TG_GAP = 3.0

L = r"[^\W\d_]"  # حرف (يعوض \p{L})
DIAC = r"[\u064B-\u065F\u0670\u0640]*"

POST_ID = re.compile(r'data-post="[^"/]+/(\d+)"')
TEXT_OPEN = re.compile(r'<div class="tgme_widget_message_text js-message_text(?: [^"]*)?"[^>]*>')
T0 = time.time()
BUDGET = 330          # ثواني: بعدها نوقف ونحفظ (الباقي بالفحص الجاي)


def extract_text(block):
    m = TEXT_OPEN.search(block)
    if not m:
        return ""
    i, depth = m.end(), 1
    for t in re.finditer(r"<div\b|</div>", block[i:]):
        depth += -1 if t.group() == "</div>" else 1
        if depth == 0:
            return block[i:i + t.start()]
    return block[i:]
LINKS = re.compile(r"https?://\S+|t\.me/\S+|www\.\S+|@\w+")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2300-\u23FF\u2B00-\u2BFF\u2934\u2935\u25AA\u25AB\u25B6\u25C0"
                   "\u25FB-\u25FE\u2139\u24C2\u203C\u2049\u3030\u303D\u3297\u3299\uFE0E\uFE0F\u20E3\U000E0020-\U000E007F]")

# ------------------------------------------------------------ فلتر الشرك (نفس منطق التطبيق)
SHIRK = re.compile(
    rf"(?<!{L})يا\s*(علي|حسين|زهراء|فاطمه|زينب|عباس|ابا الفضل|ابا عبدالله|ابا عبد الله|مهدي|صاحب الزمان|امام زمان|امام الزمان|حجه|ام البنين|سيده زينب|سيده فاطمه)(?!{L})"
    rf"|(?<!{L})مدد\s*يا(?!{L})"
    rf"|(?<!{L})يا\s*مدد(?!{L})"
    rf"|(?<!{L})(ادركني|اغثني|اغثنا|ادركنا|انصرني|انصرنا|اشفع لي|اشفع لنا|اشفني|اقض حاجتي|اقضي حاجتي)\s*يا(?!{L})"
    rf"(?!\s*(?:الله|رب|ربي|ربنا|الهي|اله|رحمن|رحيم|حي|قيوم|كريم|غفور|غفار|عزيز|جبار|لطيف|سميع|بصير|مجيب|رزاق|قدير|عظيم|حليم|ودود|وهاب|فتاح|تواب|منان|مولاي|ذا)(?!{L}))")


def loose(w):
    out = []
    for ch in w:
        if ch == " ":
            out.append(r"\s+")
            continue
        cl = {"ا": "[اأإآٱ]", "ي": "[يىیئ]", "ه": "[هة]", "ك": "[كک]", "و": "[وؤ]"}.get(ch, re.escape(ch))
        out.append(cl + DIAC)
    return "".join(out)


def build_names():
    base = ["سيده زينب", "سيده فاطمه", "سيده الكونين", "سيده نساء العالمين", "ام البنين", "ام كلثوم", "ام ابيها",
            "ابا الفضل العباس", "ابا الفضل", "قمر بني هاشم", "ابا عبدالله الحسين", "ابا عبد الله الحسين",
            "ابا عبدالله", "ابا عبد الله", "ابا صالح المهدي", "ابا صالح", "ابا الحسن", "ابا الحسين",
            "ابا القاسم", "ابا جعفر", "صاحب الزمان", "صاحب العصر", "ولي العصر", "بقيه الله", "حجه الله",
            "حجه بن الحسن", "قائم ال محمد", "مولانا المهدي", "مولاي المهدي", "امير المومنين", "سيد الشهداء",
            "سيد الاوصياء", "زين العابدين", "سيد الساجدين", "باب الحوائج", "كاشف الكرب", "قاضي الحاجات",
            "كاشف الغمه", "غياث المستغيثين", "علي الاكبر", "علي الاصغر", "علي بن ابي طالب", "علي بن الحسين",
            "علي بن موسي الرضا", "موسي بن جعفر", "حسين بن علي", "رقيه", "سكينه", "رباب", "عبد الله الرضيع",
            "علي", "حسين", "زهراء", "فاطمه الزهراء", "فاطمه", "زينب", "عباس", "مهدي", "حجه"]
    imams = ["علي", "حسين", "حسن", "رضا", "كاظم", "جواد", "هادي", "عسكري", "باقر", "صادق", "سجاد",
             "الحسين", "الحسن", "الرضا", "الكاظم", "الجواد", "الهادي", "العسكري", "الباقر", "الصادق", "السجاد",
             "العصر", "الزمان", "زمان", "المهدي", "علي بن ابي طالب"]
    names = base + ["امام " + m for m in imams]
    return sorted(names, key=lambda s: -len(s))


NAMES = "|".join(loose(n) for n in build_names())
MD = loose("مدد")
YA = loose("يا")
VERBS = "|".join(loose(v) for v in ["ادركني", "ادركنا", "اغثني", "اغثنا", "انصرني", "انصرنا", "اشفع لي",
                                     "اشفع لنا", "اشفني", "اقض حاجتي", "اقضي حاجتي"])
VOC = re.compile(rf"(?<!{L})(?:{MD}\s*)?{YA}\s*({NAMES})(?!{L})(?:\s*{MD}(?!{L}))?")
SHIRK2 = re.compile(rf"(?<!{L})(?:{NAMES})\s*(?:{VERBS})(?!{L})")
_core = rf"{YA}\s*(?:{NAMES})(?!{L})"
_hon = r"(?:\s*[()\[\]]*\s*(?:ع|س|ص|عج|ع\.س)\s*[()\[\]]*)?"
RM_MADAD = re.compile(rf"(?<!{L})(?:{MD}\s*{_core}{_hon}|{_core}{_hon}\s*{MD}(?!{L})|{YA}\s*{MD}(?!{L}))")
RM_PLEA = re.compile(rf"(?<!{L})(?:(?:{VERBS})\s*{YA}\s*(?:{NAMES})|{YA}\s*(?:{loose('غوث')}|{loose('غياث')})\s*(?:{NAMES}))(?!{L})")


def norm_ar(t):
    x = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", t)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"), ("ى", "ي"), ("ی", "ي"), ("ة", "ه"),
                 ("ک", "ك"), ("ؤ", "و"), ("ئ", "ي")):
        x = x.replace(a, b)
    return re.sub(r"\s+", " ", x)


def tidy(t):
    t = re.sub(r"\(\s*\)|\[\s*\]", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    t = re.sub(r"^[\s.,،؛:;!?؟\-–—]+", "", t)
    t = re.sub(r"[\s،؛:\-–—]+$", "", t)
    return t.strip()


def lines(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [l.strip() for l in str(v or "").split("\n") if l.strip()]


def rep(t, a, b):
    if not a:
        return t
    return re.sub(re.escape(a), lambda m: b, t, flags=re.I)


def filter_text(cfg, raw):
    """يرجع النص النهائي او None (تخطي)."""
    if not raw:
        return None
    t = raw.replace("\u00a0", " ").strip()
    if not t:
        return None
    low = norm_ar(t).lower()
    for w in lines(cfg.get("block")):
        if norm_ar(w).lower() in low:
            return None
    if cfg.get("shirk", True):
        t = RM_MADAD.sub(" ", t)
        t = RM_PLEA.sub(" ", t)
        t = VOC.sub(r"\1", t)
        t = tidy(t)
        if not re.search(r"[^\W_]", t):
            return None
        if SHIRK.search(norm_ar(t)) or SHIRK2.search(t):
            return None
    if cfg.get("links", True):
        t = LINKS.sub("", t)
    if cfg.get("noEmoji", False):
        t = EMOJI.sub("", t)
    for w in lines(cfg.get("remove")):
        t = rep(t, w, "")
    for r in lines(cfg.get("replace")):
        i = r.find("=>")
        if i > 0:
            t = rep(t, r[:i].strip(), r[i + 2:].strip())
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t or None


# ------------------------------------------------------------ شبكة
def http(url, body=None, ctype="application/x-www-form-urlencoded", timeout=30):
    headers = {"User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read(3_000_000).decode("utf-8", "replace")


class ParseFail(Exception):
    pass


def html_to_text(h):
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def is_long(s):
    return len(s) > 500 or s.count("\n") >= 8


def tg_send(token, chat, text, use_html):
    data = {"chat_id": chat, "text": text, "disable_web_page_preview": "true"}
    if use_html:
        data["parse_mode"] = "HTML"
    r = http("https://api.telegram.org/bot" + token + "/sendMessage", urllib.parse.urlencode(data).encode())
    j = json.loads(r)
    if not j.get("ok"):
        d = str(j.get("description", r))
        if use_html and "parse" in d.lower():
            raise ParseFail(d)
        raise Exception("تلغرام: " + d)


def tr_chunk(t):
    if not t.strip():
        return t
    body = "client=gtx&sl=ar&tl=fa&dt=t&q=" + urllib.parse.quote(t)
    r = http("https://translate.googleapis.com/translate_a/single", body.encode())
    arr = json.loads(r)[0]
    out = "".join(seg[0] for seg in arr if seg and seg[0])
    if not out:
        raise Exception("فشلت الترجمة")
    return out


def translate_fa(text):
    res, chunk = [], ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > 1500 and chunk:
            res.append(tr_chunk(chunk))
            chunk = ""
        chunk = chunk + "\n" + line if chunk else line
    if chunk:
        res.append(tr_chunk(chunk))
    return "\n".join(res).strip()


def rb_post(token, chat, text, qf, ql):
    b = {"chat_id": chat, "text": text}
    if qf >= 0 and ql > 0:
        b["metadata"] = {"meta_data_parts": [{"type": "Quote", "from_index": qf, "length": ql}]}
    body = json.dumps(b).encode()
    last = None
    for base in ("https://botapi.rubika.ir/v3/", "https://messengerg2b1.iranlms.ir/v3/"):
        try:
            j = json.loads(http(base + token + "/sendMessage", body, "application/json"))
            if str(j.get("status", "")).upper() == "OK":
                return
            last = Exception(j.get("status_det") or j.get("message") or str(j))
            if "status" in j:
                break
        except Exception as e:
            last = e
    raise last or Exception("فشل الإرسال")


def rb_send(token, chat, text, qf, ql):
    if qf >= 0 and ql > 0:
        try:
            rb_post(token, chat, text, qf, ql)
            return
        except Exception:
            pass
    rb_post(token, chat, text, -1, 0)


# ------------------------------------------------------------ منع التكرار
def norm_hash(s):
    return hashlib.sha1(re.sub(r"[^\w]+|_", "", s.lower()).encode()).hexdigest()[:12]


# ------------------------------------------------------------ الفحص
class Ctx:
    def __init__(self, cfg, state, tg_token, rb_token):
        self.cfg, self.state = cfg, state
        self.tg, self.rb = tg_token, rb_token
        self.last_tg = 0.0
        self.rb_err = None
        self.notext = 0
        self.cut = False


def rb_deliver(cx, out):
    cfg = cx.cfg
    rb_chat = str(cfg.get("rbChat", "")).strip()
    if not cx.rb or not rb_chat:
        raise Exception("عبّي توكن وقناة روبيكا")
    rb_out = translate_fa(out) if cfg.get("rbTranslate", True) else out
    if len(rb_out) > 3800:
        rb_out = rb_out[:3800] + "…"
    rb_foot = str(cfg.get("rbFooter", "")).strip()
    qf, ql = -1, 0
    if is_long(rb_out):
        msg = rb_out + "\n\n" + rb_foot if rb_foot else rb_out
        qf, ql = 0, len(rb_out)
    elif rb_foot:
        msg = rb_out + "\n\n" + rb_foot
        qf, ql = len(rb_out) + 2, len(rb_foot)
    else:
        msg = rb_out
    rb_send(cx.rb, rb_chat, msg, qf, ql)


def rb_try(cx, out):
    try:
        rb_deliver(cx, out)
        return True
    except Exception as e:
        m = str(e).replace(cx.rb or "\0", "***")
        if "INVALID_ACCESS" in m:
            m = "INVALID_ACCESS (تأكد من RB_TOKEN ومعرّف القناة وان البوت ادمن)"
        cx.rb_err = "روبيكا: " + m
        return False


def retry_rb(cx):
    """يعيد ارسال رسائل روبيكا الفاشلة (اقصى 12 محاولة للرسالة)."""
    q = cx.state.setdefault("rb_pending", [])
    if not cx.cfg.get("rubika", False):
        del q[:]
        return 0
    done = 0
    for item in list(q):
        if rb_try(cx, item["t"]):
            q.remove(item)
            done += 1
        else:
            item["n"] = item.get("n", 0) + 1
            if item["n"] >= 12:
                q.remove(item)
            break           # غالبا مشكلة عامة: نجرب بالفحص الجاي
    return done


def post_one(cx, out):
    cfg = cx.cfg
    foot = str(cfg.get("footer", "")).strip()
    body = out[:3800] + "…" if len(out) > 3800 else out
    if is_long(body):
        tg_html = "<blockquote expandable>" + esc(body) + "</blockquote>" + ("\n\n" + esc(foot) if foot else "")
    else:
        tg_html = esc(body) + ("\n<blockquote>" + esc(foot) + "</blockquote>" if foot else "")
    plain = body + "\n\n" + foot if foot else body
    gap = TG_GAP - (time.time() - cx.last_tg)
    if gap > 0:
        time.sleep(gap)
    chat = str(cfg.get("tgChat", "")).strip()
    try:
        tg_send(cx.tg, chat, tg_html, True)
    except ParseFail:
        tg_send(cx.tg, chat, plain, False)
    cx.last_tg = time.time()
    if cfg.get("rubika", False) and not rb_try(cx, out):
        q = cx.state.setdefault("rb_pending", [])
        q.append({"t": out, "n": 0})
        del q[:-30]


def parse_posts(page):
    starts, ids = [], []
    for m in POST_ID.finditer(page):
        i = int(m.group(1))
        if ids and ids[-1] == i:
            continue
        starts.append(m.start())
        ids.append(i)
    return starts, ids


def poll_channel(cx, ch, paused):
    page = http("https://t.me/s/" + ch)
    starts, ids = parse_posts(page)
    if not ids:
        raise Exception("القناة غير عامة او غير موجودة")
    key = ch.lower()
    last_map = cx.state.setdefault("last", {})
    max_id = max(ids)
    last = last_map.get(key)
    if last is None or paused:          # اول مرة او ايقاف مؤقت: نبدأ من الجديد فقط
        last_map[key] = max_id
        return 0, 0
    sent = skipped = handled = 0
    sent_hashes = cx.state.setdefault("sent", [])
    new = [i for i in ids if i > last]
    for n, pid in enumerate(ids):
        if pid <= last:
            continue
        if handled >= MAX_PER_CHANNEL:
            break
        if time.time() - T0 > BUDGET:
            cx.cut = True
            break
        end = starts[n + 1] if n + 1 < len(starts) else len(page)
        text = html_to_text(extract_text(page[starts[n]:end])).strip()
        if not text:
            cx.notext += 1
        out = filter_text(cx.cfg, text)
        if out is not None and norm_hash(out) not in sent_hashes:
            post_one(cx, out)
            sent_hashes.append(norm_hash(out))
            del sent_hashes[:-KEEP_HASHES]
            sent += 1
        else:
            skipped += 1
        last_map[key] = pid
        handled += 1
    print("@%s: منشورات=%d آخر_محفوظ=%s جديد=%d أُرسل=%d تخطّى=%d" % (ch, len(ids), last, len(new), sent, skipped))
    return sent, skipped


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def main():
    cfg = load_json(CFG_FILE, {})
    state = load_json(STATE_FILE, {"last": {}, "sent": []})
    tg = os.environ.get("TG_TOKEN", "").strip()
    rb = os.environ.get("RB_TOKEN", "").strip()
    paused = bool(cfg.get("paused", False))
    channels = []
    for c in cfg.get("channels", []):
        c = re.sub(r"(?i)^https?://", "", str(c).strip())
        c = re.sub(r"(?i)^(www\.)?t\.me/(s/)?", "", c).replace("@", "")
        c = re.sub(r"[/?#].*$", "", c).strip()
        if re.fullmatch(r"[A-Za-z0-9_]{4,}", c) and c.lower() not in [x.lower() for x in channels]:
            channels.append(c)
    # قناة انحذفت من الاعدادات: ننسى حالتها (لو رجعت تبدأ من الجديد)
    keep = {c.lower() for c in channels}
    for k in list(state.get("last", {})):
        if k not in keep:
            del state["last"][k]

    tz = datetime.timezone(datetime.timedelta(hours=float(cfg.get("tzOffset", 3))))
    now = datetime.datetime.now(tz)
    if not tg or not str(cfg.get("tgChat", "")).strip():
        status = "عبّي TG_TOKEN في Secrets وقناتك في الاعدادات"
        sent = skipped = 0
    elif not channels:
        status = "ما فيه قنوات مضافة"
        sent = skipped = 0
    else:
        cx = Ctx(cfg, state, tg, rb)
        sent = skipped = 0
        err = ""
        retried = retry_rb(cx)
        for ch in channels:
            if time.time() - T0 > BUDGET:
                cx.cut = True
                break
            try:
                s, k = poll_channel(cx, ch, paused)
                sent += s
                skipped += k
            except Exception as e:
                msg = "@%s: %s" % (ch, str(e).replace(tg, "***"))
                print("خطأ " + msg)
                if not err:
                    err = msg
            save_json(STATE_FILE, state)
        status = ("متوقف مؤقتا • " if paused else "") + "أُرسل %d • تخطّى %d" % (sent, skipped)
        if cx.notext:
            status += " (منها %d بلا نص)" % cx.notext
        if cx.cut:
            status += " • انتهى الوقت وكمّل بالفحص الجاي"
        if retried:
            status += " • روبيكا أُعيد %d" % retried
        if err:
            status += " • خطأ " + err
        if cx.rb_err:
            status += " • " + cx.rb_err
    status = now.strftime("%H:%M") + " — " + status
    print(status)

    save_json(STATE_FILE, state)
    # status.json: نكتبه فقط اذا صار شي، او مرّت ساعة (عشان ما نملأ الريبو بكوميتات)
    old = load_json(STATUS_FILE, {})
    changed = sent or skipped or "خطأ" in status or "روبيكا" in status
    if changed or time.time() - float(old.get("ts", 0)) > 3600:
        save_json(STATUS_FILE, {"text": status, "ts": int(time.time())})


if __name__ == "__main__":
    main()

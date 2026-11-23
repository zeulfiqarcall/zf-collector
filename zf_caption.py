# -*- coding: utf-8 -*-
"""محرر الكابشن + الهاشتاغات (نسخة بايثون من ZFCaption.java و ZFTags.java).
اوفلاين: قواعد ثابتة فقط. الترجمة للفارسية (to_fa) هي الوحيدة اللي تحتاج انترنت."""
import re

L = r"[^\W\d_]"          # حرف
LD = r"[^\W_]"           # حرف او رقم
SRC = "مصادر إعلامية"

INVISIBLE = re.compile("[\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF]")
MARKS = re.compile("[\u064B-\u0652\u0670\u0640]")
URL = re.compile(r"(?i)(https?://|www\.|t\.me/|wa\.me/|chat\.whatsapp\.com/|instagram\.com/|twitter\.com/|x\.com/|youtu\.be/|youtube\.com/|facebook\.com/)\S+")
DOMAIN = re.compile(rf"(?i)(?<!{LD})[a-z0-9-]+\.(com|net|org|ir|me|co|info|tv|news)(?!{LD})\S*")
MENTION = re.compile(r"@[A-Za-z0-9_.]+")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u25A0-\u25FF\u2900-\u29FF\uFE0F\u200D\U0001F1E6-\U0001F1FF]")
HASHTAG = re.compile(r"#(\w+)")

FOLLOW = re.compile(
    "(اشترك|اشتركوا|تابعنا|تابعونا|تابعوا|للمتابعه|انضم|انضموا|رابط القناه|قناتنا|صفحتنا"
    "|لمزيد من الاخبار|لمزيد من التفاصيل|لمزيد من المعلومات|شاركونا|شارك الخبر|لا تنسوا|فعل الجرس"
    "|ترقبوا|ترقبونا|سنوافيكم|نوافيكم|تفاصيل لاحقه|تفاصيل لاحقا|التفاصيل لاحقا|المزيد من التفاصيل|المزيد لاحقا)")
META = re.compile(
    rf"(?:(?:جاء|ورد)\s+في\s+(?:ال)?نص|(?:حسب|بحسب|وفقا ل|طبقا ل)\s*(?:ال)?نص(?!{L})|(?:ال)?نص\s+المنقول|تبين\s+ان\s+(?:ال)?نص|النص\s+المترجم)\s*[،,:]?")
FILL_START = re.compile(
    r"^\s*[وف]?\s*(?:(?:في|ومن)\s+سياق\s+متصل|في\s+التفاصيل|ويذكر\s+ان|يذكر\s+ان|من\s+الجدير\s+بالذكر\s+ان|وللتذكير|للتذكير"
    r"|تجدر\s+الاشاره\s+الي\s+ان|هذا\s+ويذكر\s+ان|هذا\s+وقد|في\s+هذا\s+السياق|في\s+هذا\s+الاطار)"
    rf"\s*[،,:]?\s*(?:(?:انه|انها|ان)(?!{L})\s*)?")
URGENT_START = re.compile(rf"^\s*(?:خبر\s+)?(?:عاجل|فوري)(?!{L})\s*[:|\-–—⧽>»]*\s*")
URGENT_CUE = re.compile(
    rf"(?<!{L})(?:للتو|قبل قليل|قبل لحظات|قبل دقائق|قبل دقايق|في هذه اللحظات|يحدث الان|يجري الان|تجري الان|جاري الان)(?!{L})")
SRC_LABEL = re.compile(r"^\s*(?:المصدر|مصدر الخبر|المصدر الاصلي|source|via)\s*[:：\-–]")
SRC_FROM_SHORT = re.compile(r"^\s*نقلا عن\s+.{0,40}$")
SIGNATURE = re.compile(r"^\s*(?:[|•\-–—]\s*)?(?:قناه|صحيفه|موقع|وكاله|شبكه|مجموعه|منصه|حساب)\s+.{1,35}$")
SEPARATOR = re.compile(r"^[\s\-–—_=*~•·.|]+$")
DANGLING = re.compile(r"(?:نقلا عن|عبر|بحسب|حسب|وفقا ل)\s*$")

OUTLETS = [
    "رويترز", "اسوشيتد برس", "الاسوشيتد برس", "فرانس برس", "وكاله فرانس برس", "وكاله الانباء الفرنسيه",
    "الجزيره نت", "الجزيره", "العربيه نت", "العربيه", "سكاي نيوز عربيه", "سكاي نيوز", "بي بي سي", "سي ان ان", "فوكس نيوز",
    "نيويورك تايمز", "واشنطن بوست", "وول ستريت جورنال", "الغارديان", "الاندبندنت", "اكسيوس", "بلومبيرغ", "بلومبرغ",
    "تايمز اوف اسرائيل", "هارتس", "يديعوت احرونوت", "معاريف", "القناه 12", "القناه 13", "القناه 14",
    "الميادين", "روسيا اليوم", "سبوتنيك", "ريا نوفوستي", "انترفاكس", "الاناضول", "تسنيم", "ايرنا", "ارنا", "سانا", "وفا", "كونا",
    "وكاله الانباء الكويتيه", "وكاله الانباء السعوديه", "وكاله الانباء الاماراتيه", "وكاله الانباء الايرانيه", "وكاله الانباء العراقيه",
    "العربي الجديد", "القدس العربي", "راي اليوم", "الشرق الاوسط", "اندبندنت عربيه", "فرانس 24", "فرانس24",
    "دويتشه فيله", "يورونيوز", "ان بي سي", "سي بي اس", "ايه بي سي", "بوليتيكو", "ميدل ايست اي", "المنار",
]
OUTLET_CUES = "(?:قناه|موقع|صحيفه|جريده|وكاله|شبكه|مجله|اذاعه|تلفزيون|هيئه البث)"
OUTLET_PAT = re.compile(
    rf"(?<!{LD})([وفبكل]{{0,2}})(?:{OUTLET_CUES}\s+)?(?:" + "|".join(o.replace(" ", r"\s+") for o in OUTLETS) + rf")(?!{LD})")
OUTLET_LATIN = re.compile(
    r"(?<![A-Za-z])(?:Reuters|AFP|AP|BBC|CNN|Axios|Bloomberg|Al\s?Jazeera|Al\s?Arabiya|RT|Sputnik|TASS|Tasnim|Fars|Mehr|IRNA|Press\s?TV|Politico|Haaretz|Ynet|i24)(?![A-Za-z])")
VERB_OUTLET = re.compile(
    rf"(?<!{L})([وف]?(?:نقلا عن|بحسب|حسب|وفقا ل|وفق|عبر|ذكرت|ذكر|افادت|افاد|نقلت|نقل|قالت|كشفت|كشف|اعلنت|اكدت|نشرت|بثت)\s+)"
    r"(?:قناه|صحيفه|جريده|موقع|مجله|شبكه|اذاعه|حساب|صفحه)\s+"
    r"(?:«[^»]{1,40}»|\"[^\"]{1,40}\"|\w+(?:\s+(?:الاخباريه|الفضائيه|الالكتروني|الاخباري))?)")
DUP_SRC = re.compile("(" + SRC + ")(?:\\s*(?:،|و)?\\s*" + SRC + ")+")
TERROR = re.compile(
    rf"(?<!{L})(?:[وفبكل]?(?:امريكا|اميركا|اسرائيل)|(?:[وفبك]?ال|[وف]?لل)ولايات\s+المتحده(?:\s+الامريكيه)?)(?!{L})(?!\s+الارهابيه)")

_NORM = {ord("أ"): "ا", ord("إ"): "ا", ord("آ"): "ا", ord("ٱ"): "ا", ord("ة"): "ه", ord("ى"): "ي",
         ord("ی"): "ي", ord("ئ"): "ي", ord("ؤ"): "و", ord("ک"): "ك"}


def norm(s):
    return s.translate(_NORM)


def is_outlet(n):
    return n in OUTLETS


def is_follow(n):
    return FOLLOW.search(n) is not None


def collapse(s):
    return re.sub(r"[ \t\u00A0]+", " ", s).strip()


class Result:
    def __init__(self):
        self.urgent = False
        self.title = ""
        self.body = ""
        self.tags = []
        self.ar = ""
        self.warn = ""


def build(raw):
    try:
        r = _make(raw, False)
        if r.warn:
            safe = _make(raw, True)
            if safe.title:
                return safe
        return r
    except Exception as e:
        r = Result()
        s = (raw or "").strip()
        r.title = s[:140]
        r.ar = s
        r.warn = "تعذر التحرير: %s" % e
        return r


def _make(raw, safe):
    r = Result()
    s = (raw or "").replace("\r", "\n")
    for p in (INVISIBLE, MARKS):
        s = p.sub("", s)
    for p in (URL, DOMAIN, MENTION, EMOJI):
        s = p.sub(" ", s)

    own, lines = [], []
    for ln in s.split("\n"):
        t = ln.strip()
        if not t:
            continue
        found = HASHTAG.findall(t)
        if found:
            own.extend(found)
            t2 = re.sub(r"^(?:#\w+\s*)+", "", t)
            t2 = re.sub(r"(?:\s*#\w+)+\s*$", "", t2)
            t = collapse(HASHTAG.sub(lambda m: m.group(1).replace("_", " "), t2))
            if not t:
                continue
        lines.append(t)

    kept = []
    for i, ln in enumerate(lines):
        t = collapse(ln)
        if not t:
            continue
        n = norm(t)
        if SEPARATOR.fullmatch(t):
            continue
        if SRC_LABEL.search(n):
            continue
        if SRC_FROM_SHORT.fullmatch(n):
            continue
        if i == len(lines) - 1 and len(t) <= 45 and SIGNATURE.fullmatch(n):
            continue
        kept.append(t)

    sents = []
    urgent = False
    for ln in kept:
        for sent_raw in _split_sentences(ln):
            sen = _strip_edges(sent_raw)
            for _ in range(3):
                um = URGENT_START.search(norm(sen))
                if um and um.end() > 0:
                    urgent = True
                    sen = _strip_edges(sen[um.end():])
                else:
                    break
            if not sen:
                continue
            if FOLLOW.search(norm(sen)):
                continue
            sen = _remove_meta(sen)
            if not safe:
                sen = _strip_fill_start(sen)
            sen = _scrub_sources(sen)
            sen = collapse(DANGLING.sub("", sen))
            sen = _strip_edges(sen)
            if not _has_letter(sen) or len(sen) < 3:
                continue
            if sen == SRC:
                continue
            sents.append(sen)
    if not sents:
        return r

    for o in own:
        no = norm(o).replace("_", " ").strip()
        if no in ("عاجل", "خبر عاجل", "فوري"):
            urgent = True
    if not urgent and URGENT_CUE.search(norm(" ".join(sents))):
        urgent = True
    r.urgent = urgent

    src_nums = _numbers(" ".join(sents))

    uniq = []
    if safe:
        uniq.extend(sents)
    else:
        keys = []
        for x in sents:
            k = _key(x)
            dup = False
            for i, o in enumerate(keys):
                if o == k or (len(k) >= 15 and k in o):
                    dup = True
                    break
                if len(o) >= 15 and o in k:
                    uniq[i] = x
                    keys[i] = k
                    dup = True
                    break
            if not dup:
                uniq.append(x)
                keys.append(k)

    title = uniq[0]
    rest = list(uniq[1:])
    if len(title) > 130:
        cut = -1
        for i in range(min(len(title), 130)):
            if title[i] in "،," and i >= 40:
                cut = i
        if cut > 0:
            head = _strip_edges(title[:cut])
            tail = _strip_edges(title[cut + 1:])
            if len(tail) >= 15 and len(head) >= 25:
                title = head
                rest.insert(0, tail)
    title = _fix_sentence(title)
    title = _terror(title)
    r.title = title

    body = []
    for i, sen in enumerate(rest):
        if i > 0:
            body.append("\n\n" if i % 2 == 0 else " ")
        body.append(_fix_sentence(sen) + ".")
    r.body = "".join(body).strip()

    r.tags = pick_tags(norm(" ".join(sents)), own, urgent)

    out = []
    if urgent:
        out.append("عاجل ⧽ ")
    out.append(title + ".")
    if r.body:
        out.append("\n\n" + r.body)
    if r.tags:
        out.append("\n\n" + " ".join("#" + t.replace(" ", "_") for t in r.tags))
    r.ar = "".join(out)

    if not safe:
        out_nums = _numbers(r.title + " " + r.body)
        for n in sorted(src_nums, key=lambda x: x):
            if n not in out_nums:
                r.warn = "رقم ناقص: " + n
                break
    low = r.ar.lower()
    if "http" in low or "t.me" in low or "@" in r.ar:
        r.warn = "رابط او حساب بالكابشن"
    del r.tags[5:]
    return r


# ------------------------------------------------------------ ادوات
def _has_letter(s):
    return any(c.isalpha() for c in s)


def _key(s):
    return re.sub(r"[\W_]+", "", norm(s))


def _strip_edges(s):
    t = re.sub(r"^[\s\-–—•·*:|/\\>]+", "", s)
    t = re.sub(r"[\s.,،؛:;!?؟…\-–—|]+$", "", t)
    return collapse(t)


def _remove_meta(s):
    n = norm(s)
    out, last = [], 0
    for m in META.finditer(n):
        out.append(s[last:m.start()])
        last = m.end()
    out.append(s[last:])
    return collapse("".join(out))


def _strip_fill_start(s):
    for _ in range(2):
        m = FILL_START.search(norm(s))
        if m and 0 < m.end() < len(s):
            s = collapse(s[m.end():])
        else:
            break
    return s


def _scrub_sources(s):
    t = s
    o, last = [], 0
    for m in VERB_OUTLET.finditer(norm(t)):
        o.append(t[last:m.start()] + t[m.start(1):m.end(1)] + SRC)
        last = m.end()
    o.append(t[last:])
    t = "".join(o)
    o, last = [], 0
    for m in OUTLET_PAT.finditer(norm(t)):
        o.append(t[last:m.start()] + t[m.start(1):m.end(1)] + SRC)
        last = m.end()
    o.append(t[last:])
    t = OUTLET_LATIN.sub(SRC, "".join(o))
    t = DUP_SRC.sub(r"\1", t)
    return collapse(t)


def _terror(title):
    o, last = [], 0
    for m in TERROR.finditer(norm(title)):
        o.append(title[last:m.end()] + " الإرهابية")
        last = m.end()
    o.append(title[last:])
    return "".join(o)


def _fix_sentence(t):
    s = _strip_edges(t)
    s = re.sub(rf"(?<!{L})({L})\.\s", r"\1 ", s)
    s = re.sub(r"\.(\s)", r"،\1", s)
    s = re.sub(r"\.+$", "", s)
    return collapse(s)


def _split_sentences(line):
    out, cur = [], []
    n = len(line)
    for i, ch in enumerate(line):
        cur.append(ch)
        end = False
        next_ws = i + 1 >= n or line[i + 1].isspace()
        if ch in "!؟?…":
            end = next_ws
        elif ch == "." and next_ws:
            ln = len(cur)
            single = ln >= 2 and cur[ln - 2].isalpha() and (ln == 2 or not cur[ln - 3].isalpha())
            end = not single
        if end:
            out.append("".join(cur).strip())
            cur = []
    rest = "".join(cur).strip()
    if rest:
        out.append(rest)
    return out


def _numbers(s):
    b = []
    for c in s:
        if "٠" <= c <= "٩":
            c = chr(ord("0") + ord(c) - ord("٠"))
        elif "۰" <= c <= "۹":
            c = chr(ord("0") + ord(c) - ord("۰"))
        b.append(c)
    return {m.group().replace(",", ".").replace("٫", ".") for m in re.finditer(r"[0-9]+(?:[.,٫][0-9]+)?", "".join(b))}


# ------------------------------------------------------------ هاشتاغات (ZFTags)
class _Ent:
    def __init__(self, tag, cat):
        self.tag, self.cat, self.pats = tag, cat, []


def _pat(alias):
    a = alias.strip().replace(" ", r"\s+")
    if alias.startswith("ال"):
        return re.compile(rf"(?<!{L})[وف]?(?:[بك]?ال|لل)" + a[2:] + rf"(?!{L})")
    return re.compile(rf"(?<!{L})(?:[وف]?(?:[بك]?ال|لل)|[وفبكل]{{0,2}})" + a + rf"(?!{L})")


_ENTS = []


def _add(cat, spec):
    p = spec.split("|")
    e = _Ent(p[0], cat)
    seen = set()
    for x in p:
        n = norm(x).strip()
        if not n or n in seen:
            continue
        seen.add(n)
        e.pats.append(_pat(n))
    _ENTS.append(e)


for _s in [
    "إيران", "العراق", "سوريا|سورية", "لبنان", "فلسطين", "إسرائيل", "الأردن", "مصر", "السعودية|المملكة العربية السعودية",
    "الإمارات|الإمارات العربية المتحدة", "قطر", "الكويت", "البحرين", "سلطنة عمان", "اليمن", "تركيا", "روسيا", "أوكرانيا",
    "أمريكا|أميركا|الولايات المتحدة|الولايات المتحدة الأمريكية", "بريطانيا|المملكة المتحدة", "فرنسا", "ألمانيا", "إيطاليا",
    "إسبانيا", "الصين", "اليابان", "الهند", "باكستان", "أفغانستان", "كوريا الشمالية", "كوريا الجنوبية", "تايوان", "ليبيا",
    "تونس", "الجزائر", "المغرب", "السودان", "جنوب السودان", "الصومال", "إثيوبيا", "أذربيجان", "أرمينيا", "بيلاروسيا",
    "بولندا", "اليونان", "قبرص", "هولندا", "السويد", "النرويج", "كندا", "المكسيك", "البرازيل", "فنزويلا", "كوبا", "أستراليا",
    "إندونيسيا", "ماليزيا", "بنغلاديش", "نيجيريا", "غزة", "الضفة الغربية", "القدس", "كشمير",
    "تل أبيب", "حيفا", "رفح", "خان يونس", "جباليا", "جنين", "نابلس", "رام الله", "الخليل", "طولكرم", "بيروت", "دمشق", "حلب",
    "إدلب", "بغداد", "الموصل", "البصرة", "أربيل", "كركوك", "طهران", "أصفهان", "تبريز", "شيراز", "القاهرة", "الإسكندرية",
    "الرياض", "أبوظبي", "دبي", "الدوحة", "المنامة", "مسقط", "صنعاء", "عدن", "الحديدة", "أنقرة", "إسطنبول", "موسكو", "كييف",
    "واشنطن", "نيويورك", "لندن", "باريس", "برلين", "بروكسل", "بكين", "طوكيو", "كابول", "طرابلس", "بنغازي", "الخرطوم",
    "الفاشر", "مقديشو",
    "حزب الله", "حماس|حركة حماس", "الجهاد الإسلامي|حركة الجهاد الإسلامي", "الحوثيون|الحوثيين|الحوثي|أنصار الله",
    "الحرس الثوري", "جيش الاحتلال|الجيش الإسرائيلي", "كتائب القسام|القسام|سرايا القدس", "هيئة تحرير الشام", "طالبان",
    "داعش", "الحشد الشعبي", "قسد", "الناتو|حلف الناتو|حلف شمال الأطلسي", "الأمم المتحدة", "مجلس الأمن",
    "الاتحاد الأوروبي", "الجامعة العربية", "أوبك", "الأونروا", "الصليب الأحمر", "البنتاغون|البنتاجون", "البيت الأبيض",
    "الكرملين", "الكنيست", "الموساد", "الشاباك", "سنتكوم|القيادة المركزية الأمريكية", "فاغنر",
    "ترامب|دونالد ترامب", "بايدن|جو بايدن", "هاريس|كامالا هاريس", "أوباما", "نتنياهو", "غالانت", "بن غفير", "سموتريتش",
    "بوتين|فلاديمير بوتين", "زيلينسكي", "ماكرون", "ستارمر", "شولتس", "ميرتس", "ميلوني", "شي جين بينغ", "أردوغان",
    "خامنئي", "بزشكيان", "عراقجي", "جواد ظريف", "السيسي", "محمد بن سلمان", "محمد بن زايد", "تميم بن حمد", "بشار الأسد",
    "الجولاني|أحمد الشرع", "نعيم قاسم", "حسن نصر الله|نصر الله", "السنوار", "هنية|إسماعيل هنية", "محمود عباس|أبو مازن",
    "غوتيريش", "كيم جونغ أون", "مودي", "روبيو", "هيغسيث", "ويتكوف", "جي دي فانس", "إيلون ماسك", "لافروف", "شويغو", "كاتس",
    "هرتسوغ",
]:
    _add(0, _s)
for _s in [
    "قصف|قصفت", "غارات|غارة|غارتين", "هجوم|هجمات|هجوما", "انفجار|انفجارات|تفجير|تفجيرات", "اشتباكات|اشتباك",
    "اغتيال|اغتالت|اغتيل", "اعتقال|اعتقالات|اعتقلت", "مسيرات|طائرة مسيرة|طائرات مسيرة", "صواريخ|صاروخ", "استهداف|استهدفت",
    "حرب", "هدنة", "وقف إطلاق النار", "مفاوضات|محادثات", "عقوبات", "زلزال|هزة أرضية", "حريق|حرائق", "فيضانات|فيضان|سيول",
    "انتخابات", "اتفاق|اتفاقية", "احتجاجات|مظاهرات|تظاهرات", "إعدام|إعدامات", "إضراب", "اقتحام|اقتحمت", "اختطاف|خطف",
    "تبادل الأسرى|صفقة التبادل", "حصار", "نزوح|نازحين", "مجاعة", "تحطم طائرة|سقوط طائرة", "تصعيد", "تهديدات|تهديد",
]:
    _add(1, _s)


def _add_unique(lst, tag):
    k = norm(tag).replace("_", " ").strip()
    for x in lst:
        if norm(x).replace("_", " ").strip() == k:
            return False
    lst.append(tag)
    return True


def pick_tags(nt, own, urgent=False):
    ents = []
    for o in own:
        n = norm(o).replace("_", " ").strip()
        if len(n) < 2 or len(n) > 25:
            continue
        if re.fullmatch(r"[0-9]+", n):
            continue
        if n in ("عاجل", "خبر عاجل", "فوري"):
            continue
        if is_outlet(n) or is_follow(n):
            continue
        _add_unique(ents, o.replace("_", " ").strip())

    hits = []
    for e in _ENTS:
        best = None
        for p in e.pats:
            m = p.search(nt)
            if m and (best is None or m.start() < best[1]):
                best = (e, m.start(), m.end())
        if best:
            hits.append(best)
    keep = []
    for h in hits:
        inside = False
        for o in hits:
            if o is h:
                continue
            if o[1] <= h[1] and o[2] >= h[2] and (o[2] - o[1]) > (h[2] - h[1]):
                inside = True
                break
        if not inside:
            keep.append(h)
    keep.sort(key=lambda h: h[1])

    topics = []
    for h in keep:
        if h[0].cat == 0:
            if len(ents) < 4:
                _add_unique(ents, h[0].tag)
        else:
            _add_unique(topics, h[0].tag)
    del ents[4:]
    room = min(2, 5 - len(ents))
    out = list(ents)
    for i in range(min(len(topics), room)):
        out.append(topics[i])
    del out[5:]
    return out


# ------------------------------------------------------------ الترجمة للفارسية
def to_fa(r, translate):
    """translate = دالة ترجمة (نص عربي -> فارسي). ترمي استثناء اذا فشلت."""
    t = translate(r.title).strip()
    t = re.sub(r"^[\s\W]+", "", t, flags=re.U)
    t = re.sub(r"[\s.,،؛:;!?؟…]+$", "", t)
    t = re.sub(r"\.(\s)", r"،\1", t)
    if not t:
        raise Exception("ترجمة العنوان فاضية")
    sb = []
    if r.urgent:
        sb.append("فوری ⧽ ")
    sb.append(t + ".")
    if r.body:
        b = translate(r.body).strip()
        if not b:
            raise Exception("ترجمة النص فاضية")
        sb.append("\n\n" + b)
    if r.tags:
        parts = [p.strip() for p in translate("\n".join(x.replace("_", " ") for x in r.tags)).split("\n") if p.strip()]
        if len(parts) == len(r.tags):
            tg = []
            for p in parts:
                p = re.sub(r"[\s\-]+", "_", p)
                p = re.sub(r"[^\w]", "", p)
                tg.append("#" + p)
            sb.append("\n\n" + " ".join(tg))
    return "".join(sb)

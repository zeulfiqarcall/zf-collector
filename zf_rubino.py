# -*- coding: utf-8 -*-
"""النشر في روبينو (انستغرام روبيكا) بحساب المستخدم - نسخة بايثون من ZFRubino.java.
روبينو ما له API رسمي: هذا بروتوكول التطبيق نفسه (غير رسمي)، وممكن يتغير بأي وقت.
كل ما ممكن يتغير مجمّع في الثوابت تحت. التوكن (auth) ما يتطبع في اللوق."""
import io
import json
import random
import time
import urllib.error
import urllib.request

API_URL = "https://rubino1.iranlms.ir/"
API_VERSION, APP_NAME, APP_VERSION = "0", "Main", "3.0.8"
APP_PACKAGE, PLATFORM, LANG = "app.rbmain.a", "Android", "fa"


class Rubino:
    def __init__(self, auth, store):
        """store = dict يحفظ فيه معرّف الملف (profile) بين التشغيلات."""
        self.auth = "".join(c for c in (auth or "") if not c.isspace() and c not in "\"'")
        self.store = store
        self.last_http = 0

    # ------------------------------------------------------------ شبكة
    def _http(self, url, body, ctype, headers=None):
        h = {"Content-Type": ctype, "User-Agent": "okhttp/3.12.1"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=body, headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                self.last_http = r.status
                return r.read(2_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            self.last_http = e.code
            res = e.read(2_000_000).decode("utf-8", "replace")
            if not res.strip():
                raise Exception("HTTP %d" % e.code)
            return res

    def _call(self, method, data):
        req = {"api_version": API_VERSION, "auth": self.auth,
               "client": {"app_name": APP_NAME, "app_version": APP_VERSION, "lang_code": LANG,
                          "package": APP_PACKAGE, "platform": PLATFORM},
               "data": data, "method": method}
        body = json.dumps(req, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        res = ""
        for i in range(3):
            res = self._http(API_URL, body, "application/json")
            if not res.strip().startswith("<"):
                break
            if i < 2:
                time.sleep(1.5)
        if res.strip().startswith("<"):
            raise Exception("روبينو رجّع صفحة خطأ (HTTP %d) في %s — جرّب بعد شوي" % (self.last_http, method))
        try:
            r = json.loads(res)
        except ValueError:
            raise Exception("رد غير مفهوم من روبينو (%s): %s" % (method, _cut(res)))
        if "status" not in r and "data_enc" in r:
            raise Exception("روبينو رد بتشفير (data_enc) — البروتوكول تغيّر ويحتاج تحديث")
        st = _str(r, "status")
        if st.upper() != "OK":
            raise Exception(_describe(method, st, _str(r, "status_det")))
        d = r.get("data")
        return d if isinstance(d, dict) else {}

    # ------------------------------------------------------------ ملف الحساب
    def _profile_id(self):
        pid = str(self.store.get("rbn_profile", "")).strip()
        if pid:
            return pid
        first = None
        try:
            arr = self._call("getProfileList", {"equal": False, "limit": 10, "sort": "FromMax"}).get("profiles")
            if arr:
                pid = _str(arr[0], "id")
        except Exception as e:
            first = e
        if not pid:
            try:
                p = self._call("getMyProfileInfo", {}).get("profile")
                if isinstance(p, dict):
                    pid = _str(p, "id")
            except Exception as e:
                first = first or e
        if not pid:
            if first:
                raise first
            raise Exception("ما لقيت ملف روبينو لهذا الحساب — افتح روبينو مرة وأنشئ الملف")
        self.store["rbn_profile"] = pid
        return pid

    # ------------------------------------------------------------ رفع + نشر
    def _upload(self, profile, data, name):
        up = self._call("requestUploadFile", {"file_name": name, "file_size": len(data),
                                              "file_type": "Picture", "profile_id": profile})
        file_id = _str(up, "id") or _str(up, "file_id")
        server = _first(up, "server_url", "upload_url", "url")
        hash_req = _first(up, "hash_file_request", "access_hash_send")
        if not file_id or not server:
            raise Exception("رد غير متوقع من روبينو عند طلب الرفع: " + _cut(json.dumps(up, ensure_ascii=False)))
        hd = {"auth": self.auth, "file-id": file_id, "total-part": "1", "part-number": "1",
              "chunk-size": str(len(data))}
        if hash_req:
            hd["hash-file-request"] = hash_req
            hd["access-hash-send"] = hash_req
        up_res = self._http(server, data, "application/octet-stream", hd)
        try:
            r = json.loads(up_res)
        except ValueError:
            raise Exception("رد غير مفهوم عند رفع الصورة: " + _cut(up_res))
        st = _str(r, "status")
        if st and st.upper() != "OK":
            raise Exception(_describe("uploadFile", st, _str(r, "status_det")))
        d = r.get("data") if isinstance(r.get("data"), dict) else r
        hash_rec = _first(d, "hash_file_receive", "access_hash_rec")
        if not hash_rec:
            raise Exception("رفع الصورة ما رجّع رمز الاستلام: " + _cut(up_res))
        return file_id, hash_rec

    def publish(self, img, w, h, caption, thumb):
        """ينشر صورة JPEG مع كابشن. يرجّع رسالة النجاح او يرمي استثناء برسالة واضحة."""
        if not self.auth:
            raise Exception("ما فيه توكن روبينو")
        profile = self._profile_id()
        last = None
        for v in range(5):
            sep_thumb = v <= 1
            same_thumb = v in (3, 4)
            multi_flag = v in (1, 3)
            strs = v == 4
            main = self._upload(profile, img, "zf_post.jpg")
            th = self._upload(profile, thumb, "zf_thumb.jpg") if sep_thumb else None
            rnd = 100000 + random.randrange(900000000)
            add = {"caption": caption, "file_id": main[0], "hash_file_receive": main[1],
                   "height": str(h) if strs else h, "width": str(w) if strs else w,
                   "post_type": "Picture", "rnd": str(rnd) if strs else rnd, "profile_id": profile}
            if multi_flag:
                add["is_multi_file"] = False
            if th:
                add["thumbnail_file_id"], add["thumbnail_hash_file_receive"] = th
            elif same_thumb:
                add["thumbnail_file_id"], add["thumbnail_hash_file_receive"] = main
            try:
                res = self._call("addPost", add)
                post = res.get("post")
                pid = _str(post, "id") if isinstance(post, dict) else ""
                return "تم النشر في روبينو ✓" if pid else \
                    "روبينو قبل الطلب لكن ما رجّع المنشور — تأكد في صفحتك: " + _cut(json.dumps(res, ensure_ascii=False))
            except Exception as ex:
                last = ex
                if "INVALID_INPUT" not in str(ex):
                    raise
        raise last


def _str(o, k):
    if not isinstance(o, dict) or o.get(k) is None:
        return ""
    return str(o[k])


def _first(o, *ks):
    for k in ks:
        v = _str(o, k)
        if v:
            return v
    return ""


def _cut(s):
    s = " ".join((s or "").split())
    return s[:220] + "…" if len(s) > 220 else s


def _describe(method, status, det):
    s = (status + " " + det).upper()
    if "INVALID_AUTH" in s or "NOT_REGISTERED" in s:
        return "توكن الدخول غير صالح — حدّث السر RBN_AUTH في GitHub (%s)" % (det or status)
    return "روبينو رفض (%s): %s%s" % (method, status or "؟", " / " + det if det else "")


def make_thumb(img_bytes, Image):
    """نسخة مصغرة JPEG (عرض 320)."""
    try:
        b = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        th = max(1, round(b.height * (320 / b.width)))
        o = io.BytesIO()
        b.resize((320, th), Image.LANCZOS).save(o, "JPEG", quality=80)
        return o.getvalue()
    except Exception:
        return img_bytes

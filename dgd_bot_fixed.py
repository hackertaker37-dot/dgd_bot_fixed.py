# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════════════╗
 ║     TAKER OTP BOT - ULTIMATE FINAL EDITION          ║
 ║     Developer: @hackerTaker                         ║
 ║     API: xwdsms.org (Full Integration)               ║
 ║     Version: 3.0 Final                               ║
 ╚══════════════════════════════════════════════════════╝
"""
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات الأساسية ════════════════
BOT_TOKEN = "8686995713:AAEt_gy-p6CHv64UEz9zitP8hLkDPoVG8Hk"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_ultimate.db"
DELETE_AFTER = 180  # حذف رسائل الجروب بعد 3 دقائق

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ الخدمات الافتراضية ════════════════
DEFAULT_SERVICES = {
    "whatsapp": {"en": "WhatsApp", "icon": "💬", "ar": "واتساب"},
    "facebook": {"en": "Facebook", "icon": "📘", "ar": "فيسبوك"},
    "instagram": {"en": "Instagram", "icon": "📷", "ar": "انستغرام"},
    "tiktok": {"en": "TikTok", "icon": "🎵", "ar": "تيك توك"},
    "telegram": {"en": "Telegram", "icon": "✈️", "ar": "تيليجرام"},
    "imo": {"en": "IMO", "icon": "📞", "ar": "ايمو"},
    "snapchat": {"en": "Snapchat", "icon": "👻", "ar": "سناب شات"},
    "google": {"en": "Google", "icon": "🔍", "ar": "جوجل"},
    "twitter": {"en": "Twitter/X", "icon": "🐦", "ar": "تويتر"},
    "discord": {"en": "Discord", "icon": "🎮", "ar": "ديسكورد"},
    "amazon": {"en": "Amazon", "icon": "📦", "ar": "امازون"},
    "apple": {"en": "Apple", "icon": "🍎", "ar": "ابل"},
    "microsoft": {"en": "Microsoft", "icon": "🪟", "ar": "مايكروسوفت"},
    "uber": {"en": "Uber", "icon": "🚗", "ar": "اوبر"},
    "netflix": {"en": "Netflix", "icon": "🎬", "ar": "نتفلكس"},
    "youtube": {"en": "YouTube", "icon": "▶️", "ar": "يوتيوب"},
    "all": {"en": "All Services", "icon": "🌐", "ar": "كل الخدمات"},
}

# ════════════════ الدول الافتراضية ════════════════
DEFAULT_COUNTRIES = {
    "22501": "ساحل العاج", "23276": "سيراليون", "26134": "مدغشقر",
    "44740": "المملكة المتحدة", "23490": "نيجيريا", "25471": "كينيا",
    "24910": "السودان", "49155": "ألمانيا", "23762": "الكاميرون",
    "22178": "السنغال", "22901": "بنين", "22898": "توجو",
}

COUNTRY_FLAGS = {
    "225": "🇨🇮", "232": "🇸🇱", "261": "🇲🇬", "44": "🇬🇧", "234": "🇳🇬",
    "254": "🇰🇪", "249": "🇸🇩", "49": "🇩🇪", "237": "🇨🇲", "221": "🇸🇳",
    "229": "🇧🇯", "228": "🇹🇬",
}

def get_flag(prefix):
    for code, flag in COUNTRY_FLAGS.items():
        if prefix.startswith(code):
            return flag
    return "🌍"

# ════════════════ API Functions ════════════════
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        return data["id"], data["number"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception("هذه الدولة غير متوفرة حالياً")
        raise Exception(f"خطأ في الاتصال")
    except Exception as e:
        raise Exception(f"خطأ: {e}")

def api_check_otp(number):
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=6)
        data = resp.json()
        if data.get("success"):
            return data.get("status"), data.get("otp"), data.get("message", "")
        return None, None, ""
    except:
        return None, None, ""

def api_delete_number(alloc_id):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=4)
        return True
    except:
        return False

def api_get_balance():
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=6)
        return resp.json().get("balance", "0")
    except:
        return "0"

# ════════════════ قاعدة البيانات ════════════════
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        # المستخدمين
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            last_name TEXT, lang TEXT DEFAULT NULL, balance REAL DEFAULT 0,
            is_banned INTEGER DEFAULT 0, total_requests INTEGER DEFAULT 0,
            total_otps INTEGER DEFAULT 0, first_seen TEXT, last_seen TEXT)''')
        # الأرقام النشطة
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
            service TEXT, assigned_to INTEGER, created_at TEXT,
            status TEXT DEFAULT 'waiting', otp TEXT, full_msg TEXT)''')
        # سجل الأكواد
        c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
            otp TEXT, service TEXT, full_message TEXT,
            timestamp TEXT, assigned_to INTEGER)''')
        # الإحالات
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE,
            ref_count INTEGER DEFAULT 0)''')
        # قنوات الاشتراك
        c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE, description TEXT,
            enabled INTEGER DEFAULT 1)''')
        # الإعدادات
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
        # الدول المخصصة
        c.execute('''CREATE TABLE IF NOT EXISTS custom_countries (
            prefix TEXT PRIMARY KEY, name TEXT)''')
        # الخدمات المخصصة
        c.execute('''CREATE TABLE IF NOT EXISTS custom_services (
            service_key TEXT PRIMARY KEY, en_name TEXT,
            icon TEXT, ar_name TEXT)''')
        # إعدادات افتراضية
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        # إدراج الدول
        for p, n in DEFAULT_COUNTRIES.items():
            c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (p, n))
        # إدراج الخدمات
        for k, d in DEFAULT_SERVICES.items():
            c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)",
                      (k, d['en'], d['icon'], d['ar']))
        self.conn.commit()

    def setting(self, key, val=None):
        c = self.conn.cursor()
        if val is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, val))
            self.conn.commit()
            return val
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        r = c.fetchone()
        return r[0] if r else None

    def get_countries(self):
        c = self.conn.cursor()
        c.execute("SELECT prefix, name FROM custom_countries ORDER BY name")
        return {r[0]: r[1] for r in c.fetchall()}

    def add_country(self, p, n):
        self.conn.cursor().execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (p, n))
        self.conn.commit()

    def del_country(self, p):
        self.conn.cursor().execute("DELETE FROM custom_countries WHERE prefix=?", (p,))
        self.conn.commit()

    def get_services(self):
        c = self.conn.cursor()
        c.execute("SELECT service_key, en_name, icon, ar_name FROM custom_services ORDER BY ar_name")
        return {r[0]: {"en": r[1], "icon": r[2], "ar": r[3]} for r in c.fetchall()}

    def add_service(self, k, en, icon, ar):
        self.conn.cursor().execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (k, en, icon, ar))
        self.conn.commit()

    def del_service(self, k):
        if k == "all": return
        self.conn.cursor().execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (k,))
        self.conn.commit()

    def get_user(self, uid):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        return c.fetchone()

    def save_user(self, msg):
        uid = msg.from_user.id
        now = datetime.now().isoformat()
        c = self.conn.cursor()
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            c.execute("INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                      (uid, msg.from_user.username, msg.from_user.first_name, msg.from_user.last_name, now, now))
        else:
            c.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now, uid))
        self.conn.commit()

    def set_lang(self, uid, lang):
        self.conn.cursor().execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
        self.conn.commit()

    def all_users(self):
        c = self.conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0")
        return [r[0] for r in c.fetchall()]

db = Database(DB_PATH)

# ════════════════ نصوص ثنائية اللغة ════════════════
TEXTS = {
    "lang_select": {"ar": "🌐 *اختر لغتك*\n\nاختر اللغة التي تريد استخدام البوت بها:", "en": "🌐 *Select Your Language*\n\nChoose the language you want to use:"},
    "lang_set": {"ar": "✅ تم تعيين اللغة العربية", "en": "✅ English language set"},
    "lang_changed": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to English"},
    "welcome": {"ar": "🔰 *أهلاً بك في Taker OTP*\n\n• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n\n*اختر الخدمة:*", "en": "🔰 *Welcome to Taker OTP*\n\n• Select the service you want\n• Then select the country\n• Receive the code instantly\n\n*Select service:*"},
    "choose_country": {"ar": "*اختر الدولة:*", "en": "*Select country:*"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n🕒 {time}\n⏳ بانتظار الكود...", "en": "✅ *Number Assigned*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n🕒 {time}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n🕒 {time}\n⏳ بانتظار الكود...", "en": "🔄 *Number Changed*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n🕒 {time}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً", "en": "⚠️ *Bot under maintenance*\nPlease try again later"},
    "subscribe": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "banned": {"ar": "🚫 *أنت محظور من استخدام البوت*", "en": "🚫 *You are banned from using the bot*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 إجمالي الطلبات: `{r}`\n🔷 الأكواد المستلمة: `{o}`", "en": "📊 *Your Statistics*\n\n🔷 Total Requests: `{r}`\n🔷 OTPs Received: `{o}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 رصيدك: `{b:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 رصيد الموقع: `{site}`\n🏦 الحد الأدنى للسحب: `18.0 USDT`\n\n💡 اربح `0.05 USDT` عن كل صديق", "en": "💰 *Your Balance*\n\n💎 Balance: `{b:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site Balance: `{site}`\n🏦 Min Withdrawal: `18.0 USDT`\n\n💡 Earn `0.05 USDT` per friend"},
    "invite": {"ar": "🤝 *دعوة الأصدقاء*\n\n🔗 رابط الدعوة الخاص بك:\n`{link}`\n\n💰 تربح `0.05 USDT` عن كل صديق\n📤 شارك الرابط مع أصدقائك", "en": "🤝 *Invite Friends*\n\n🔗 Your referral link:\n`{link}`\n\n💰 Earn `0.05 USDT` per friend\n📤 Share the link with your friends"},
    "traffic_title": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "⚠️ لا توجد أرقام نشطة حالياً", "en": "⚠️ No active numbers at the moment"},
    "prefix_added": {"ar": "✅ *تمت إضافة الدولة*\n\n🌍 {flag} {name}\n🔢 `{prefix}`", "en": "✅ *Country Added*\n\n🌍 {flag} {name}\n🔢 `{prefix}`"},
    "prefix_exists": {"ar": "⚠️ *الدولة موجودة مسبقاً*\n\n🌍 {flag} {name}\n🔢 `{prefix}`", "en": "⚠️ *Country Already Exists*\n\n🌍 {flag} {name}\n🔢 `{prefix}`"},
    "prefix_removed": {"ar": "✅ *تم حذف الدولة*", "en": "✅ *Country Removed*"},
    "service_added": {"ar": "✅ *تمت إضافة الخدمة*\n\n{icon} {ar_name}", "en": "✅ *Service Added*\n\n{icon} {en_name}"},
    "service_removed": {"ar": "✅ *تم حذف الخدمة*", "en": "✅ *Service Removed*"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*\n\nمرحباً بك في لوحة إدارة البوت", "en": "*⚙️ Admin Panel*\n\nWelcome to the bot control panel"},
    "admin_add_country": {"ar": "*➕ إضافة دولة*\n\nأرسل Prefix الدولة (مثال: `24910`):", "en": "*➕ Add Country*\n\nSend country prefix (e.g.: `24910`):"},
    "admin_del_country": {"ar": "*➖ حذف دولة*\n\nاختر الدولة:", "en": "*➖ Delete Country*\n\nSelect country:"},
    "admin_add_service": {"ar": "*➕ إضافة خدمة*\n\nأرسل مفتاح الخدمة (مثال: `snapchat`):", "en": "*➕ Add Service*\n\nSend service key (e.g.: `snapchat`):"},
    "admin_del_service": {"ar": "*➖ حذف خدمة*\n\nاختر الخدمة:", "en": "*➖ Delete Service*\n\nSelect service:"},
    "admin_broadcast": {"ar": "*📢 إذاعة*\n\nأرسل الرسالة للإرسال لجميع المستخدمين:", "en": "*📢 Broadcast*\n\nSend message to all users:"},
    "admin_broadcast_done": {"ar": "✅ *تم الإرسال*\n\nعدد المستلمين: `{cnt}`", "en": "✅ *Sent*\n\nRecipients: `{cnt}`"},
    "admin_ban": {"ar": "*🚫 حظر*\n\nأرسل ID المستخدم:", "en": "*🚫 Ban*\n\nSend user ID:"},
    "admin_unban": {"ar": "*✅ فك حظر*\n\nأرسل ID المستخدم:", "en": "*✅ Unban*\n\nSend user ID:"},
    "admin_done": {"ar": "✅ *تم بنجاح*", "en": "✅ *Done Successfully*"},
    "otp_user": {"ar": "*🔐 تم استقبال رمز التفعيل*\n\n📞 الرقم: `+{num}`\n🌍 الدولة: {flag} {country}\n{icon} التطبيق: {svc}\n🔢 الكود: `{code}`\n\nانسخ الكود واستخدمه فوراً", "en": "*🔐 Activation Code Received*\n\n📞 Number: `+{num}`\n🌍 Country: {flag} {country}\n{icon} Service: {svc}\n🔢 Code: `{code}`\n\nCopy the code and use it immediately"},
    "otp_group": {"ar": "*🔐 كود جديد*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`", "en": "*🔐 New OTP*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`"},
    "countries_list": {"ar": "🌍 *الدول المتاحة:*\n\n", "en": "🌍 *Available Countries:*\n\n"},
    "back": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "btn_new": {"ar": "📱 رقم جديد", "en": "📱 New Number"},
    "btn_countries": {"ar": "🌍 الدول", "en": "🌍 Countries"},
    "btn_stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "btn_balance": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "btn_invite": {"ar": "🤝 دعوة", "en": "🤝 Invite"},
    "btn_traffic": {"ar": "🟢 المرور", "en": "🟢 Traffic"},
    "btn_admin": {"ar": "⚙️ الإدارة", "en": "⚙️ Admin"},
    "btn_lang": {"ar": "🌐 اللغة", "en": "🌐 Language"},
}

def t(key, uid=None, **kw):
    lang = "ar"
    if uid:
        u = db.get_user(uid)
        if u and u[4]:
            lang = u[4]
    txt = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ar", key))
    return txt.format(**kw) if kw else txt

def btn_text(key, uid):
    u = db.get_user(uid)
    lang = u[4] if u and u[4] else "ar"
    return TEXTS[f"btn_{key}"][lang]

# ════════════════ دوال مساعدة ════════════════
def clean(n):
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    t = str(text).lower()
    if not t: return "OTP"
    services_check = [
        ("WhatsApp", ["whatsapp", "واتساب", "واتس"]),
        ("Telegram", ["telegram", "تيليجرام", "تليجرام"]),
        ("Facebook", ["facebook", "فيسبوك", "fb"]),
        ("Instagram", ["instagram", "انستغرام", "انستقرام", "انستا"]),
        ("TikTok", ["tiktok", "تيك توك"]),
        ("IMO", ["imo"]),
        ("Snapchat", ["snapchat", "سناب شات", "سناب"]),
        ("Google", ["google", "gmail", "جوجل"]),
        ("Twitter/X", ["twitter", "تويتر", "x.com"]),
        ("Discord", ["discord", "ديسكورد"]),
        ("Amazon", ["amazon", "امازون"]),
        ("Apple", ["apple", "ابل", "icloud"]),
        ("Microsoft", ["microsoft", "مايكروسوفت"]),
        ("Uber", ["uber", "اوبر"]),
        ("Netflix", ["netflix", "نتفلكس"]),
        ("YouTube", ["youtube", "يوتيوب"]),
    ]
    for svc, keywords in services_check:
        if any(kw in t for kw in keywords):
            return svc
    return "OTP"

ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "TikTok": "🎵", "IMO": "📞", "Snapchat": "👻", "Google": "🔍",
    "Twitter/X": "🐦", "Discord": "🎮", "Amazon": "📦", "Apple": "🍎",
    "Microsoft": "🪟", "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️", "OTP": "🔐"
}

def mask_number(num):
    n = str(num)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

def release_user_number(uid):
    c = db.conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    for (aid,) in c.fetchall():
        try: api_delete_number(aid)
        except: pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    db.conn.commit()

def assign_number(uid, aid, num, prefix, svc):
    release_user_number(uid)
    c = db.conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at, status) VALUES (?,?,?,?,?,?,?)",
              (aid, num, prefix, svc, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    db.conn.commit()

def get_active_numbers():
    c = db.conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, service, assigned_to, full_msg FROM active_numbers WHERE status='waiting'")
    return c.fetchall()

def check_subscription(uid):
    c = db.conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    if not channels: return True
    for (url,) in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch, uid).status not in ["member", "administrator", "creator"]:
                return False
        except: return False
    return True

def sub_markup(uid):
    c = db.conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    if not channels: return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 Subscribe", url=url))
    mk.add(types.InlineKeyboardButton("✅ " + t("back", uid).split()[-1] if False else "✅ Check", callback_data="check_sub"))
    return mk

def lang_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return mk

def process_referral(ref_code, new_uid):
    c = db.conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
        c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (row[0],))
    db.conn.commit()

def get_ref_link(uid):
    ref = f"ref{uid}"
    db.conn.cursor().execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
    db.conn.commit()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton(btn_text("new", uid)),
        types.KeyboardButton(btn_text("countries", uid)),
        types.KeyboardButton(btn_text("stats", uid))
    )
    kb.add(
        types.KeyboardButton(btn_text("balance", uid)),
        types.KeyboardButton(btn_text("invite", uid)),
        types.KeyboardButton(btn_text("traffic", uid))
    )
    kb.add(types.KeyboardButton(btn_text("lang", uid)))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(btn_text("admin", uid)))
    return kb

def services_menu():
    services = db.get_services()
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for k, d in services.items():
        if k != "all":
            btns.append(types.InlineKeyboardButton(f"{d['icon']} {d['ar']}", callback_data=f"svc_{k}"))
    if "all" in services:
        btns.append(types.InlineKeyboardButton(f"{services['all']['icon']} {services['all']['ar']}", callback_data="svc_all"))
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    return mk

def countries_for_service(uid, svc):
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for p, n in sorted(countries.items()):
        flag = get_flag(p)
        btns.append(types.InlineKeyboardButton(f"{flag} {n}", callback_data=f"get_{p}_{svc}"))
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    mk.row(types.InlineKeyboardButton(t("back", uid), callback_data="menu_services"))
    return mk

def number_actions(uid, prefix, svc, aid):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("🔄 " + t("btn_new", uid), callback_data=f"ch_{prefix}_{svc}_{aid}"),
        types.InlineKeyboardButton("🌍 " + t("btn_countries", uid), callback_data=f"svc_{svc}")
    )
    mk.row(
        types.InlineKeyboardButton("📞 Channel", url="https://t.me/numhj"),
        types.InlineKeyboardButton(t("back", uid), callback_data="main_menu")
    )
    return mk

# ════════════════ أوامر البوت ════════════════
@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    # حفظ المستخدم
    db.save_user(message)
    
    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    
    # فحص اللغة
    u = db.get_user(uid)
    if not u or not u[4]:
        # اختيار اللغة إجباري
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
        return
    
    # فحص الصيانة
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown")
        return
    
    # فحص الحظر
    if u[6] == 1:
        bot.send_message(cid, t("banned", uid), parse_mode="Markdown")
        return
    
    # فحص الاشتراك
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return
    
    # عرض القائمة الرئيسية
    photo = db.setting("welcome_photo")
    txt = t("welcome", uid)
    mk = services_menu()
    
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    bot.send_message(cid, "• • •", reply_markup=main_keyboard(uid))

# اختيار اللغة
@bot.callback_query_handler(func=lambda c: c.data in ["lang_ar", "lang_en"])
def set_language(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = "ar" if call.data == "lang_ar" else "en"
    db.set_lang(uid, lang)
    bot.answer_callback_query(call.id, t("lang_set", uid))
    
    # حذف رسالة اختيار اللغة
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    
    # إعادة تشغيل البوت باللغة الجديدة
    start_command(call.message)

# تغيير اللغة من الكيبورد
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, "✅")
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "❌", show_alert=True)

# اختيار خدمة
@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    uid = call.from_user.id
    svc = call.data.split("_")[1]
    services = db.get_services()
    svc_name = services.get(svc, {}).get("ar", svc)
    
    bot.edit_message_text(
        f"*{t('choose_country', uid)}*\n\n🛠 {svc_name}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=countries_for_service(uid, svc)
    )

# جلب رقم
@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]
    svc = parts[2] if len(parts) > 2 else "all"
    
    release_user_number(uid)
    
    try:
        aid, num = api_get_number(prefix)
        num = clean(num)
        assign_number(uid, aid, num, prefix, svc)
        
        countries = db.get_countries()
        services = db.get_services()
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        svc_name = services.get(svc, {}).get("ar", svc)
        now = datetime.now().strftime("%H:%M")
        
        msg = t("number_assigned", uid, number=num, flag=flag, country=name, service=svc_name, time=now)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(uid, prefix, svc, aid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

# تغيير رقم
@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]
    svc = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    if old_alloc:
        api_delete_number(old_alloc)
        db.conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (old_alloc,))
        db.conn.commit()
    
    release_user_number(uid)
    
    try:
        aid, num = api_get_number(prefix)
        num = clean(num)
        assign_number(uid, aid, num, prefix, svc)
        
        countries = db.get_countries()
        services = db.get_services()
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        svc_name = services.get(svc, {}).get("ar", svc)
        now = datetime.now().strftime("%H:%M")
        
        msg = t("number_changed", uid, number=num, flag=flag, country=name, service=svc_name, time=now)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(uid, prefix, svc, aid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

# رجوع للقائمة الرئيسية أو الخدمات
@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_to_menu(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    
    if call.data == "menu_services":
        bot.edit_message_text(
            t("welcome", uid),
            cid,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=services_menu()
        )
    else:
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        start_command(call.message)

# ════════════════ المعالج العام للرسائل ════════════════
@bot.message_handler(func=lambda m: True)
def universal_handler(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text
    
    # معالجة حالات الإدارة
    state = admin_states.get(uid)
    
    # إضافة دولة - Prefix
    if state == "add_country_prefix":
        admin_states[uid] = ("add_country_name", txt.strip())
        bot.send_message(cid, "أرسل اسم الدولة:")
        return
    
    # إضافة دولة - اسم
    if isinstance(state, tuple) and state[0] == "add_country_name":
        prefix = state[1]
        name = txt.strip()
        db.add_country(prefix, name)
        flag = get_flag(prefix)
        bot.send_message(cid, t("prefix_added", uid, flag=flag, name=name, prefix=prefix), parse_mode="Markdown")
        del admin_states[uid]
        return
    
    # إضافة خدمة - مفتاح
    if state == "add_service_key":
        admin_states[uid] = ("add_service_en", txt.strip().lower())
        bot.send_message(cid, "أرسل اسم الخدمة بالإنجليزية:")
        return
    
    # إضافة خدمة - اسم إنجليزي
    if isinstance(state, tuple) and state[0] == "add_service_en":
        admin_states[uid] = ("add_service_icon", state[1], txt.strip())
        bot.send_message(cid, "أرسل أيقونة الخدمة (إيموجي واحد):")
        return
    
    # إضافة خدمة - أيقونة
    if isinstance(state, tuple) and state[0] == "add_service_icon":
        admin_states[uid] = ("add_service_ar", state[1], state[2], txt.strip())
        bot.send_message(cid, "أرسل اسم الخدمة بالعربية:")
        return
    
    # إضافة خدمة - اسم عربي
    if isinstance(state, tuple) and state[0] == "add_service_ar":
        key = state[1]
        en_name = state[2]
        icon = state[3]
        ar_name = txt.strip()
        db.add_service(key, en_name, icon, ar_name)
        bot.send_message(cid, t("service_added", uid, icon=icon, ar_name=ar_name, en_name=en_name), parse_mode="Markdown")
        del admin_states[uid]
        return
    
    # إذاعة
    if state == "broadcast":
        users = db.all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.03)
            except: pass
        bot.send_message(cid, t("admin_broadcast_done", uid, cnt=cnt), parse_mode="Markdown")
        del admin_states[uid]
        return
    
    # حظر / فك حظر
    if state in ["ban", "unban"]:
        try:
            target = int(txt)
            db.conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?", (target,))
            db.conn.commit()
            bot.send_message(cid, t("admin_done", uid), parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
        del admin_states[uid]
        return
    
    # إضافة قناة اشتراك - رابط
    if state == "addch_url":
        admin_states[uid] = ("addch_desc", txt.strip())
        bot.send_message(cid, "أرسل وصفاً للقناة:")
        return
    
    # إضافة قناة اشتراك - وصف
    if isinstance(state, tuple) and state[0] == "addch_desc":
        url = state[1]
        desc = txt.strip()
        db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        db.conn.commit()
        bot.send_message(cid, "✅ تمت الإضافة")
        del admin_states[uid]
        return
    
    # زر تغيير اللغة
    if txt == btn_text("lang", uid):
        u = db.get_user(uid)
        current_lang = u[4] if u and u[4] else "ar"
        new_lang = "en" if current_lang == "ar" else "ar"
        db.set_lang(uid, new_lang)
        bot.send_message(cid, t("lang_changed", uid), parse_mode="Markdown")
        bot.send_message(cid, "• • •", reply_markup=main_keyboard(uid))
        return
    
    # زر رقم جديد
    if txt == btn_text("new", uid):
        bot.send_message(cid, t("welcome", uid), parse_mode="Markdown", reply_markup=services_menu())
        return
    
    # زر الدول
    if txt == btn_text("countries", uid):
        countries = db.get_countries()
        msg = t("countries_list", uid) + "\n".join(f"{get_flag(p)} {n}" for p, n in sorted(countries.items()))
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # زر الإحصائيات
    if txt == btn_text("stats", uid):
        u = db.get_user(uid)
        bot.send_message(cid, t("stats", uid, r=u[6] if u else 0, o=u[7] if u else 0), parse_mode="Markdown")
        return
    
    # زر الرصيد
    if txt == btn_text("balance", uid):
        u = db.get_user(uid)
        c = db.conn.cursor()
        c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
        refs = c.fetchone()
        bot.send_message(cid, t("balance", uid, b=u[5] if u else 0, ref=refs[0] if refs else 0, site=api_get_balance()), parse_mode="Markdown")
        return
    
    # زر الدعوة
    if txt == btn_text("invite", uid):
        link = get_ref_link(uid)
        bot.send_message(cid, t("invite", uid, link=link), parse_mode="Markdown")
        return
    
    # زر المرور
    if txt == btn_text("traffic", uid):
        c = db.conn.cursor()
        c.execute("SELECT prefix, service, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix, service ORDER BY COUNT(*) DESC LIMIT 10")
        rows = c.fetchall()
        if not rows:
            bot.send_message(cid, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic_title", uid), ""]
            for p, svc, cnt in rows:
                name = db.get_countries().get(p, p)
                flag = get_flag(p)
                icon = db.get_services().get(svc, {}).get("icon", "🔐")
                lines.append(f"{flag} {name} {icon}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
        return
    
    # زر الإدارة
    if txt == btn_text("admin", uid) and uid in ADMIN_IDS:
        show_admin_panel(cid, uid)
        return

# ════════════════ لوحة الإدارة ════════════════
def show_admin_panel(cid, uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 Active" if db.setting("maintenance") != "1" else "🔴 Maintenance"
    mk.add(types.InlineKeyboardButton(f"Status: {st}", callback_data="tog"))
    mk.add(
        types.InlineKeyboardButton("➕ Add Country", callback_data="add_country_btn"),
        types.InlineKeyboardButton("➖ Del Country", callback_data="del_country_btn")
    )
    mk.add(
        types.InlineKeyboardButton("➕ Add Service", callback_data="add_service_btn"),
        types.InlineKeyboardButton("➖ Del Service", callback_data="del_service_btn")
    )
    mk.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_btn"),
        types.InlineKeyboardButton("👥 Users", callback_data="users_list_btn")
    )
    mk.add(
        types.InlineKeyboardButton("🚫 Ban", callback_data="ban_btn"),
        types.InlineKeyboardButton("✅ Unban", callback_data="unban_btn")
    )
    mk.add(
        types.InlineKeyboardButton("🔗 Force Sub", callback_data="force_sub_btn"),
        types.InlineKeyboardButton("🖼️ Photo", callback_data="set_photo_btn")
    )
    mk.add(
        types.InlineKeyboardButton("🗑️ Clear Data", callback_data="clear_data_btn"),
        types.InlineKeyboardButton("↩️ Exit", callback_data="main_menu")
    )
    bot.send_message(cid, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

admin_states = {}

# Callbacks لوحة الإدارة
@bot.callback_query_handler(func=lambda c: c.data == "tog")
def tog_callback(call):
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅")
    show_admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "add_country_btn")
def add_country_callback(call):
    admin_states[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text(t("admin_add_country", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "del_country_btn")
def del_country_callback(call):
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup()
    for p, n in countries.items():
        flag = get_flag(p)
        mk.add(types.InlineKeyboardButton(f"{flag} {n}", callback_data=f"delc_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text(t("admin_del_country", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc_callback(call):
    db.del_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅")
    show_admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "add_service_btn")
def add_service_callback(call):
    admin_states[call.from_user.id] = "add_service_key"
    bot.edit_message_text(t("admin_add_service", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "del_service_btn")
def del_service_callback(call):
    services = db.get_services()
    mk = types.InlineKeyboardMarkup()
    for k, d in services.items():
        if k != "all":
            mk.add(types.InlineKeyboardButton(f"{d['icon']} {d['ar']}", callback_data=f"dels_{k}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text(t("admin_del_service", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dels_"))
def dels_callback(call):
    db.del_service(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅")
    show_admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_btn")
def broadcast_callback(call):
    admin_states[call.from_user.id] = "broadcast"
    bot.edit_message_text(t("admin_broadcast", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["ban_btn", "unban_btn"])
def ban_unban_callback(call):
    admin_states[call.from_user.id] = "ban" if call.data == "ban_btn" else "unban"
    txt = t("admin_ban", call.from_user.id) if call.data == "ban_btn" else t("admin_unban", call.from_user.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "users_list_btn")
def users_list_callback(call):
    c = db.conn.cursor()
    c.execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15")
    rows = c.fetchall()
    txt = "*👥 Users:*\n\n" + "\n".join(f"• `{u}` @{un or '—'}" for u, un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "force_sub_btn")
def force_sub_callback(call):
    c = db.conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    chs = c.fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ Add", callback_data="addch"), types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*🔗 Force Subscribe*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch_callback(call):
    admin_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*Send channel URL:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch_callback(call):
    ch_id = int(call.data.split("_")[1])
    db.conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
    db.conn.commit()
    force_sub_callback(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo_btn")
def set_photo_callback(call):
    admin_states[call.from_user.id] = "photo"
    bot.edit_message_text("*Send photo:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: admin_states.get(m.from_user.id) == "photo")
def save_photo_handler(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ Saved")
    del admin_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data_btn")
def clear_data_callback(call):
    c = db.conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ Cleared")
    show_admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back_callback(call):
    show_admin_panel(call.message.chat.id, call.from_user.id)

# ════════════════ حلقة فحص OTP ════════════════
def otp_checker_loop():
    """حلقة فحص الأكواد تلقائياً كل 3 ثوان"""
    while True:
        try:
            for alloc_id, number, prefix, service_key, uid, full_msg in get_active_numbers():
                try:
                    status, otp, raw_msg = api_check_otp(number)
                    
                    if status == "success" and otp:
                        # اكتشاف التطبيق
                        detected_service = detect_service(raw_msg) if raw_msg else "OTP"
                        if detected_service == "OTP":
                            services = db.get_services()
                            detected_service = services.get(service_key, {}).get("en", "OTP")
                        
                        icon = ICONS.get(detected_service, "🔐")
                        country = db.get_countries().get(prefix, prefix)
                        flag = get_flag(prefix)
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
                        
                        # إرسال للمستخدم
                        if uid:
                            try:
                                user_msg = t("otp_user", uid, num=number, flag=flag, country=country, icon=icon, svc=detected_service, code=code)
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                            except: pass
                        
                        # إرسال للجروب مع حذف تلقائي
                        for cid in CHAT_IDS:
                            try:
                                masked = mask_number(number)
                                group_msg = t("otp_group", None, flag=flag, country=country, icon=icon, svc=detected_service, masked=masked, code=code)
                                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                                # حذف تلقائي بعد 3 دقائق
                                threading.Thread(
                                    target=lambda cid=cid, mid=sent.message_id: (
                                        time.sleep(DELETE_AFTER),
                                        bot.delete_message(cid, mid)
                                    ),
                                    daemon=True
                                ).start()
                            except: pass
                        
                        # تحديث قاعدة البيانات
                        c = db.conn.cursor()
                        c.execute("UPDATE active_numbers SET status='success', otp=?, full_msg=? WHERE alloc_id=?", (otp, raw_msg, alloc_id))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                        c.execute("INSERT INTO otp_logs (number, otp, service, full_message, timestamp, assigned_to) VALUES (?,?,?,?,?,?)",
                                  (number, otp, detected_service, raw_msg, datetime.now().isoformat(), uid))
                        db.conn.commit()
                        
                        # حذف الرقم من API وقاعدة البيانات
                        api_delete_number(alloc_id)
                        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                        db.conn.commit()
                    
                    elif status == "expired":
                        api_delete_number(alloc_id)
                        c = db.conn.cursor()
                        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                        db.conn.commit()
                
                except Exception as e:
                    logger.error(f"OTP check error for {number}: {e}")
        
        except Exception as e:
            logger.error(f"OTP loop error: {e}")
        
        time.sleep(3)

# ════════════════ Flask ════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return "Taker OTP Bot - Ultimate Edition"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot": "Taker OTP", "timestamp": datetime.now().isoformat()}), 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)

# ════════════════ تشغيل البوت ════════════════
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Taker OTP Bot - Ultimate Final Edition")
    logger.info("=" * 60)
    
    # تشغيل خادم الويب
    threading.Thread(target=run_web_server, daemon=True).start()
    logger.info("✅ Web server started on port 8080")
    
    # تشغيل حلقة فحص OTP
    threading.Thread(target=otp_checker_loop, daemon=True).start()
    logger.info("✅ OTP checker loop started")
    
    # تشغيل البوت
    logger.info("✅ Bot polling started")
    bot.infinity_polling()

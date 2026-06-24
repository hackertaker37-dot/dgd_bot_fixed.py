# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ████████╗ █████╗ ██╗  ██╗███████╗██████╗      ██████╗ ████████╗██████╗  ║
║     ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗    ██╔═══██╗╚══██╔══╝██╔══██╗ ║
║        ██║   ███████║█████╔╝ █████╗  ██████╔╝    ██║   ██║   ██║   ██████╔╝ ║
║        ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗    ██║   ██║   ██║   ██╔═══╝  ║
║        ██║   ██║  ██║██║  ██╗███████╗██║  ██║    ╚██████╔╝   ██║   ██║      ║
║        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝    ╚═╝   ╚═╝      ║
║                                                                              ║
║           TAKER OTP BOT - GOD MODE FINAL EDITION v10.0                       ║
║           Developer: @hackerTaker                                            ║
║           API: xwdsms.org (Full Integration)                                 ║
║           Languages: Arabic & English (Bilingual)                            ║
║           Status: THE FINAL ULTIMATE VERSION                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import time, requests, re, os, sys, sqlite3, threading, logging, json, hashlib, traceback, random, string, io
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
from collections import OrderedDict, defaultdict
from telebot import types, TeleBot, apihelper
from flask import Flask, jsonify, request as flask_request, render_template_string

# ══════════════════════════════════════════════════════════════════════════════
# ULTIMATE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN = "8686995713:AAG0JXX0P9TQSW97Mq19Glj_kSm2TsgKvmg"
API_KEY = "97257ac6fe5efd03c28b43af34a887b3"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_god_mode.db"

# ══════════════════════════════════════════════════════════════════════════════
# TIMING - GOD MODE
# ══════════════════════════════════════════════════════════════════════════════
DELETE_AFTER = 1800           # 30 دقيقة - نصف ساعة
OTP_CHECK_INTERVAL = 1.2      # فحص سريع جداً
API_TIMEOUT = 15              # مهلة API
API_RETRIES = 7               # محاولات API
MAX_WORKERS = 50              # عمال متوازيين - أداء خارق
CACHE_TTL = 120               # كاش طويل
POLLING_TIMEOUT = 20          # بولينج
LONG_POLLING_TIMEOUT = 10     # بولينج طويل

# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE - MAXIMUM
# ══════════════════════════════════════════════════════════════════════════════
apihelper.SESSION_TIME_TO_LIVE = 600
apihelper.ENABLE_MIDDLEWARE = False
apihelper.READ_TIMEOUT = 10
apihelper.CONNECT_TIMEOUT = 5
apihelper.RETRY_ON_ERROR = True
apihelper.RETRY_TIMEOUT = 2

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

_cache_store = {}
_cache_times = {}
_cache_lock = threading.Lock()

def god_cache(ttl=CACHE_TTL):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = hashlib.sha256(f"{func.__name__}:{args}:{kwargs}".encode()).hexdigest()
            now = time.time()
            with _cache_lock:
                if cache_key in _cache_store and now - _cache_times.get(cache_key, 0) < ttl:
                    return _cache_store[cache_key]
            result = func(*args, **kwargs)
            with _cache_lock:
                _cache_store[cache_key] = result
                _cache_times[cache_key] = now
            return result
        return wrapper
    return decorator

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE TRANSLATION DICTIONARY - EVERYTHING
# ══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # ── Main ──
    "welcome_title": {"ar": "✨ أهلاً بك في بوت Taker OTP", "en": "✨ Welcome to Taker OTP Bot"},
    "welcome_desc": {
        "ar": "• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n• ادعُ أصدقاءك واربح رصيداً",
        "en": "• Choose the service you want\n• Then choose the country\n• Receive OTP instantly\n• Invite friends and earn credit"
    },
    "choose_service": {"ar": "🛠 اختر الخدمة:", "en": "🛠 Choose service:"},
    "choose_country": {"ar": "🌍 اختر الدولة لخدمة {}", "en": "🌍 Choose country for {}"},
    "new_number": {"ar": "✅ تم تخصيص رقم جديد بنجاح", "en": "✅ New number allocated successfully"},
    "number_label": {"ar": "الرقم", "en": "Number"},
    "country_label": {"ar": "الدولة", "en": "Country"},
    "service_label": {"ar": "الخدمة", "en": "Service"},
    "time_label": {"ar": "الوقت", "en": "Time"},
    "status_waiting": {"ar": "⏳ في انتظار رمز التفعيل...", "en": "⏳ Waiting for OTP..."},
    "change_number_btn": {"ar": "🔄 تغيير الرقم", "en": "🔄 Change Number"},
    "change_country_btn": {"ar": "🌍 تغيير الدولة", "en": "🌍 Change Country"},
    "change_service_btn": {"ar": "🛠 تغيير الخدمة", "en": "🛠 Change Service"},
    "otp_channel_btn": {"ar": "📞 قناة الأكواد", "en": "📞 OTP Channel"},
    "back_btn": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "back_to_services": {"ar": "↩️ رجوع للخدمات", "en": "↩️ Back to services"},
    "back_to_countries": {"ar": "↩️ رجوع للدول", "en": "↩️ Back to countries"},
    # ── Maintenance ──
    "maintenance_msg": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", "en": "⚠️ *Bot under maintenance*\nPlease try again later."},
    # ── Force Sub ──
    "force_sub_msg": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "sub_btn": {"ar": "📢 اشترك في القناة", "en": "📢 Subscribe to channel"},
    "check_sub_btn": {"ar": "✅ تحقق من الاشتراك", "en": "✅ Check subscription"},
    "check_sub_ok": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_sub_fail": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ Not subscribed to all channels"},
    # ── OTP ──
    "otp_received_title": {"ar": "🔐 تم استقبال رمز التفعيل", "en": "🔐 OTP Code Received"},
    "app_label": {"ar": "التطبيق", "en": "Application"},
    "code_label": {"ar": "الكود", "en": "Code"},
    "copy_instruction": {"ar": "انسخ الكود واستخدمه فوراً", "en": "Copy the code and use it immediately"},
    # ── Lists ──
    "countries_list_title": {"ar": "🌍 الدول المتاحة:", "en": "🌍 Available countries:"},
    "services_list_title": {"ar": "🛠 الخدمات المتاحة:", "en": "🛠 Available services:"},
    # ── Stats ──
    "my_stats_title": {"ar": "📊 إحصائياتك", "en": "📊 Your Statistics"},
    "total_requests": {"ar": "إجمالي الطلبات", "en": "Total Requests"},
    "otps_received": {"ar": "الأكواد المستلمة", "en": "OTPs Received"},
    "first_use": {"ar": "أول استخدام", "en": "First Use"},
    "last_use": {"ar": "آخر استخدام", "en": "Last Use"},
    # ── Balance ──
    "my_balance_title": {"ar": "💰 رصيدك", "en": "💰 Your Balance"},
    "your_balance": {"ar": "رصيدك", "en": "Your Balance"},
    "referrals_label": {"ar": "الإحالات", "en": "Referrals"},
    "site_balance": {"ar": "رصيد الموقع", "en": "Site Balance"},
    "min_withdraw": {"ar": "الحد الأدنى للسحب", "en": "Min Withdrawal"},
    "earn_tip": {"ar": "💡 *اربح `0.05 USDT` عن كل صديق تدعوه*", "en": "💡 *Earn `0.05 USDT` per friend you invite*"},
    # ── Invite ──
    "invite_friends_title": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "your_link": {"ar": "🔗 *رابط الدعوة الخاص بك:*\n`{}`", "en": "🔗 *Your invite link:*\n`{}`"},
    "share_instruction": {"ar": "📤 *شارك الرابط مع أصدقائك*", "en": "📤 *Share the link with your friends*"},
    # ── Traffic ──
    "traffic_title": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "no_active_numbers": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers currently."},
    "unknown_text": {"ar": "غير معروف", "en": "Unknown"},
    # ── Keyboard Buttons ──
    "get_number_kb": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries_kb": {"ar": "🌍 الدول المتاحة", "en": "🌍 Countries"},
    "services_kb": {"ar": "🛠 الخدمات", "en": "🛠 Services"},
    "stats_kb": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance_kb": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite_kb": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite"},
    "traffic_kb": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "admin_kb": {"ar": "⚙️ لوحة التحكم", "en": "⚙️ Admin Panel"},
    "use_buttons": {"ar": "استخدم الأزرار أدناه للتنقل:", "en": "Use the buttons below to navigate:"},
    # ── Language ──
    "language_changed_ar": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to Arabic"},
    "language_changed_en": {"ar": "✅ تم تغيير اللغة إلى English", "en": "✅ Language changed to English"},
    # ── Errors ──
    "no_country": {"ar": "هذه الدولة غير متوفرة حالياً", "en": "This country is currently unavailable"},
    "general_error": {"ar": "خطأ: {}", "en": "Error: {}"},
    "connection_error": {"ar": "خطأ في الاتصال بالخادم", "en": "Server connection error"},
    "no_countries_available": {"ar": "لا توجد دول متاحة حالياً", "en": "No countries available"},
    "no_services_available": {"ar": "لا توجد خدمات متاحة حالياً", "en": "No services available"},
    # ── Admin Panel ──
    "admin_header": {"ar": "⚙️ لوحة التحكم - Taker OTP\n\nمرحباً بك في لوحة إدارة البوت.", "en": "⚙️ Admin Panel - Taker OTP\n\nWelcome to the bot admin panel."},
    "admin_status_label": {"ar": "حالة البوت: {}", "en": "Bot status: {}"},
    "admin_open": {"ar": "🟢 مفتوح", "en": "🟢 Open"},
    "admin_maint": {"ar": "🔴 صيانة", "en": "🔴 Maintenance"},
    "admin_add_country": {"ar": "➕ إضافة دولة", "en": "➕ Add Country"},
    "admin_del_country": {"ar": "➖ حذف دولة", "en": "➖ Delete Country"},
    "admin_add_service": {"ar": "➕ إضافة خدمة", "en": "➕ Add Service"},
    "admin_del_service": {"ar": "➖ حذف خدمة", "en": "➖ Delete Service"},
    "admin_broadcast": {"ar": "📢 إذاعة", "en": "📢 Broadcast"},
    "admin_users": {"ar": "👥 المستخدمين", "en": "👥 Users"},
    "admin_ban": {"ar": "🚫 حظر", "en": "🚫 Ban"},
    "admin_unban": {"ar": "✅ فك حظر", "en": "✅ Unban"},
    "admin_stats": {"ar": "📊 إحصائيات", "en": "📊 Statistics"},
    "admin_report": {"ar": "📄 تقرير", "en": "📄 Report"},
    "admin_force_sub": {"ar": "🔗 الاشتراك الإجباري", "en": "🔗 Force Sub"},
    "admin_photo": {"ar": "🖼️ صورة الترحيب", "en": "🖼️ Welcome Photo"},
    "admin_clear": {"ar": "🗑️ مسح البيانات", "en": "🗑️ Clear Data"},
    "admin_exit": {"ar": "↩️ خروج", "en": "↩️ Exit"},
}

# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
_lang_cache = {}

def get_lang(uid):
    uid_str = str(uid)
    if uid_str in _lang_cache:
        return _lang_cache[uid_str]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (f"lang_{uid}",))
        row = c.fetchone()
        conn.close()
        lang = row[0] if row else None
        _lang_cache[uid_str] = lang
        return lang
    except:
        return None

def set_lang(uid, lang):
    uid_str = str(uid)
    _lang_cache[uid_str] = lang
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO settings VALUES (?,?)", (f"lang_{uid}", lang))
        conn.commit()
        conn.close()
    except:
        pass

def _(key, uid=None, **kwargs):
    lang = get_lang(uid) or "ar" if uid else "ar"
    text = TRANSLATIONS.get(key, {}).get(lang) or TRANSLATIONS.get(key, {}).get("ar", key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

def lang_selection_keyboard():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    return mk

# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT DATA
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_SERVICES = OrderedDict([
    ("whatsapp", ("WhatsApp", "💬", "واتساب")),
    ("facebook", ("Facebook", "📘", "فيسبوك")),
    ("instagram", ("Instagram", "📷", "انستغرام")),
    ("tiktok", ("TikTok", "🎵", "تيك توك")),
    ("telegram", ("Telegram", "✈️", "تيليجرام")),
    ("imo", ("IMO", "📞", "ايمو")),
    ("snapchat", ("Snapchat", "👻", "سناب شات")),
    ("google", ("Google", "🔍", "جوجل")),
    ("twitter", ("Twitter/X", "🐦", "تويتر")),
    ("discord", ("Discord", "🎮", "ديسكورد")),
    ("amazon", ("Amazon", "📦", "امازون")),
    ("apple", ("Apple", "🍎", "ابل")),
    ("microsoft", ("Microsoft", "🪟", "مايكروسوفت")),
    ("uber", ("Uber", "🚗", "اوبر")),
    ("netflix", ("Netflix", "🎬", "نتفلكس")),
    ("youtube", ("YouTube", "▶️", "يوتيوب")),
    ("all", ("All Services", "🌐", "كل الخدمات")),
])

DEFAULT_COUNTRIES = OrderedDict([
    ("22501", "ساحل العاج"),
    ("22507", "ساحل العاج VIP"),
    ("23276", "سيراليون"),
    ("26134", "مدغشقر"),
    ("44740", "المملكة المتحدة"),
    ("23490", "نيجيريا"),
    ("25471", "كينيا"),
    ("24910", "السودان 10"),
    ("24911", "السودان 11"),
    ("24912", "السودان 12"),
    ("24913", "السودان 13"),
    ("24914", "السودان 14"),
    ("24915", "السودان 15"),
    ("24916", "السودان 16"),
    ("24917", "السودان 17"),
    ("24918", "السودان 18"),
    ("24919", "السودان 19"),
    ("49155", "ألمانيا"),
    ("23762", "الكاميرون"),
    ("22178", "السنغال"),
    ("22901", "بنين"),
    ("22898", "توجو"),
])

COUNTRY_FLAGS = {
    "225": "🇨🇮", "232": "🇸🇱", "261": "🇲🇬", "44": "🇬🇧",
    "234": "🇳🇬", "254": "🇰🇪", "249": "🇸🇩", "49": "🇩🇪",
    "237": "🇨🇲", "221": "🇸🇳", "229": "🇧🇯", "228": "🇹🇬",
}

SERVICE_ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘",
    "Instagram": "📷", "Google": "🔍", "Twitter/X": "🐦",
    "Discord": "🎮", "Snapchat": "👻", "TikTok": "🎵",
    "Amazon": "📦", "Apple": "🍎", "Microsoft": "🪟",
    "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️",
    "IMO": "📞", "OTP": "🔐",
}

def get_flag(prefix):
    for code, flag in COUNTRY_FLAGS.items():
        if prefix.startswith(code):
            return flag
    return "⚡"

# ══════════════════════════════════════════════════════════════════════════════
# API MANAGER - GOD MODE
# ══════════════════════════════════════════════════════════════════════════════
class APIManager:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TakerOTPBot/10.0-GodMode"
        })
        self.stats = defaultdict(int)
        self.lock = threading.Lock()

    def _request(self, method, endpoint, max_retries=API_RETRIES, **kwargs):
        url = f"{self.base_url}{endpoint}"
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, timeout=API_TIMEOUT, **kwargs)
                else:
                    resp = self.session.post(url, timeout=API_TIMEOUT, **kwargs)
                resp.raise_for_status()
                with self.lock:
                    self.stats['success'] += 1
                return resp.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    with self.lock:
                        self.stats['not_found'] += 1
                    raise Exception("هذه الدولة غير متوفرة حالياً")
                if e.response.status_code == 429:
                    with self.lock:
                        self.stats['rate_limited'] += 1
                    time.sleep(2 ** attempt)
                    continue
                if attempt == max_retries - 1:
                    with self.lock:
                        self.stats['failed'] += 1
                    raise Exception("خطأ في الاتصال بالخادم")
                time.sleep(0.5 * (attempt + 1))
            except requests.exceptions.Timeout:
                with self.lock:
                    self.stats['timeout'] += 1
                if attempt == max_retries - 1:
                    raise Exception("انتهت مهلة الاتصال")
                time.sleep(1)
            except Exception as e:
                with self.lock:
                    self.stats['error'] += 1
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.5)

    def get_number(self, prefix):
        data = self._request("POST", "/api/v1/get-number", json={"range": prefix})
        if not data.get("success"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        return data["id"], data["number"]

    def check_otp(self, number):
        try:
            data = self._request("GET", "/api/v1/check-otp", params={"number": number})
            if data.get("success"):
                return data.get("status"), data.get("otp")
        except:
            pass
        return None, None

    def delete_number(self, alloc_id):
        try:
            self._request("POST", "/api/v1/delete-number", json={"id": alloc_id})
            return True
        except:
            return False

    def get_balance(self):
        try:
            data = self._request("GET", "/api/v1/balance")
            return data.get("balance", "0")
        except:
            return "0"

    def get_stats(self):
        return dict(self.stats)

api = APIManager()

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE - GOD MODE
# ══════════════════════════════════════════════════════════════════════════════
class Database:
    def __init__(self, path):
        self.path = path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        c = self.conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
                first_seen TEXT, last_seen TEXT);

            CREATE TABLE IF NOT EXISTS active_numbers (
                alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
                service TEXT, assigned_to INTEGER, created_at TEXT,
                status TEXT DEFAULT 'waiting', otp TEXT);

            CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
                service TEXT, country TEXT, timestamp TEXT, assigned_to INTEGER);

            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0);

            CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
                description TEXT, enabled INTEGER DEFAULT 1);

            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);

            CREATE TABLE IF NOT EXISTS custom_countries (prefix TEXT PRIMARY KEY, name TEXT);

            CREATE TABLE IF NOT EXISTS custom_services (
                service_key TEXT PRIMARY KEY, name TEXT, icon TEXT, ar_name TEXT);

            CREATE INDEX IF NOT EXISTS idx_active_status ON active_numbers(status);
            CREATE INDEX IF NOT EXISTS idx_otp_logs_time ON otp_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_users_ban ON users(is_banned);
        ''')
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        for prefix, name in DEFAULT_COUNTRIES.items():
            c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
        for key, (name, icon, ar_name) in DEFAULT_SERVICES.items():
            c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
        self.conn.commit()

    def setting(self, key, value=None):
        c = self.conn.cursor()
        if value is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
            self.conn.commit()
            return value
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    @god_cache(ttl=30)
    def get_countries(self):
        c = self.conn.cursor()
        rows = c.execute("SELECT prefix, name FROM custom_countries ORDER BY name").fetchall()
        return OrderedDict((row[0], row[1]) for row in rows)

    def add_country(self, prefix, name):
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (prefix, name))
        self.conn.commit()
        self.get_countries.cache_clear()

    def delete_country(self, prefix):
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
        self.conn.commit()
        self.get_countries.cache_clear()

    @god_cache(ttl=30)
    def get_services(self):
        c = self.conn.cursor()
        rows = c.execute("SELECT service_key, name, icon, ar_name FROM custom_services ORDER BY ar_name").fetchall()
        result = OrderedDict()
        for row in rows:
            result[row[0]] = {"name": row[1], "icon": row[2], "ar": row[3]}
        return result

    def add_service(self, key, name, icon, ar_name):
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
        self.conn.commit()
        self.get_services.cache_clear()

    def delete_service(self, key):
        if key == "all":
            return
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (key,))
        self.conn.commit()
        self.get_services.cache_clear()

    def save_user(self, msg):
        uid = msg.from_user.id
        now = datetime.now().isoformat()
        c = self.conn.cursor()
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            c.execute("INSERT INTO users (user_id, username, first_name, first_seen, last_seen) VALUES (?,?,?,?,?)",
                     (uid, msg.from_user.username, msg.from_user.first_name, now, now))
        else:
            c.execute("UPDATE users SET username=?, first_name=?, last_seen=? WHERE user_id=?",
                     (msg.from_user.username, msg.from_user.first_name, now, uid))
        self.conn.commit()

    def get_all_users(self):
        return [r[0] for r in self.conn.cursor().execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]

    def get_all_active(self):
        return self.conn.cursor().execute(
            "SELECT alloc_id, number, prefix, service, assigned_to FROM active_numbers WHERE status='waiting'"
        ).fetchall()

    def release_user_number(self, uid):
        c = self.conn.cursor()
        for (aid,) in c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)).fetchall():
            api.delete_number(aid)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
        self.conn.commit()

    def assign_number(self, uid, alloc_id, number, prefix, service):
        self.release_user_number(uid)
        c = self.conn.cursor()
        c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at) VALUES (?,?,?,?,?,?)",
                 (alloc_id, number, prefix, service, uid, datetime.now().isoformat()))
        c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
        self.conn.commit()

    def save_otp(self, alloc_id, otp, service, uid):
        c = self.conn.cursor()
        c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
        number_row = c.execute("SELECT number, prefix FROM active_numbers WHERE alloc_id=?", (alloc_id,)).fetchone()
        if number_row:
            country = self.get_countries().get(number_row[1], number_row[1])
            c.execute("INSERT INTO otp_logs (number, otp, service, country, timestamp, assigned_to) VALUES (?,?,?,?,?,?)",
                     (number_row[0], otp, service, country, datetime.now().isoformat(), uid))
        self.conn.commit()

    def delete_active(self, alloc_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
        self.conn.commit()

    def get_user_stats(self, uid):
        row = self.conn.cursor().execute(
            "SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,)
        ).fetchone()
        return row if row else (0, 0, None, None)

    def get_user_balance(self, uid):
        c = self.conn.cursor()
        bal = c.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
        refs = c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        return (bal[0] if bal else 0), (refs[0] if refs else 0)

    def get_ref_link(self, uid):
        ref = f"ref{uid}"
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
        self.conn.commit()
        return f"https://t.me/Taker_OTP_BOT?start={ref}"

    def process_referral(self, ref_code, new_uid):
        c = self.conn.cursor()
        row = c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,)).fetchone()
        if row:
            c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
            c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (row[0],))
        self.conn.commit()

    def get_traffic_stats(self, limit=10):
        return self.conn.cursor().execute(
            "SELECT prefix, service, COUNT(*) as cnt FROM active_numbers WHERE status='waiting' GROUP BY prefix, service ORDER BY cnt DESC LIMIT ?",
            (limit,)
        ).fetchall()

    def get_total_otps(self):
        row = self.conn.cursor().execute("SELECT COUNT(*) FROM otp_logs").fetchone()
        return row[0] if row else 0

    def get_channels(self):
        return self.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()

db = Database(DB_PATH)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def clean_number(n):
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    t = str(text).lower()
    if not t:
        return "OTP"
    patterns = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستغرام", "انستا"],
        "TikTok": ["tiktok", "تيك توك"],
        "IMO": ["imo", "ايمو"],
        "Snapchat": ["snapchat", "سناب"],
        "Google": ["google", "gmail", "جوجل"],
        "Twitter/X": ["twitter", "تويتر"],
        "Discord": ["discord", "ديسكورد"],
        "Amazon": ["amazon", "امازون"],
        "Apple": ["apple", "ابل", "icloud"],
        "Microsoft": ["microsoft", "مايكروسوفت"],
        "Uber": ["uber", "اوبر"],
        "Netflix": ["netflix", "نتفلكس"],
        "YouTube": ["youtube", "يوتيوب"],
    }
    for service, keywords in patterns.items():
        if any(kw in t for kw in keywords):
            return service
    return "OTP"

def mask_number(num, show=4):
    n = str(num)
    if len(n) <= show * 2:
        return n
    return f"{n[:show]}{'*' * (len(n) - show * 2 + 2)}{n[-show:]}"

def format_time(iso_str, uid=None):
    if not iso_str:
        return _("unknown_text", uid)
    try:
        return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M:%S")
    except:
        return str(iso_str)

def format_code(otp):
    return f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp

def check_subscription(uid):
    channels = db.get_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            url = ch[2]
            ch_id = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch_id, uid).status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    channels = db.get_channels()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for ch in channels:
        mk.add(types.InlineKeyboardButton(_("sub_btn", uid), url=ch[2]))
    mk.add(types.InlineKeyboardButton(_("check_sub_btn", uid), callback_data="check_sub"))
    return mk

# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ══════════════════════════════════════════════════════════════════════════════
bot = TeleBot(BOT_TOKEN, threaded=True, num_threads=MAX_WORKERS)

# ══════════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════════════════════════════════════════
def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton(_("get_number_kb", uid)),
        types.KeyboardButton(_("countries_kb", uid)),
        types.KeyboardButton(_("stats_kb", uid))
    )
    kb.add(
        types.KeyboardButton(_("balance_kb", uid)),
        types.KeyboardButton(_("invite_kb", uid)),
        types.KeyboardButton(_("traffic_kb", uid))
    )
    lang = get_lang(uid) or "ar"
    kb.add(types.KeyboardButton("🌐 English" if lang == "ar" else "🌐 العربية"))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(_("admin_kb", uid)))
    return kb

def services_menu(uid):
    """قائمة الخدمات"""
    services = db.get_services()
    lang = get_lang(uid) or "ar"
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for key, data in services.items():
        if key != "all":
            display = data['ar'] if lang == "ar" else data['name']
            btns.append(types.InlineKeyboardButton(f"{data['icon']} {display}", callback_data=f"svc_{key}"))
    if "all" in services:
        display = services['all']['ar'] if lang == "ar" else services['all']['name']
        btns.append(types.InlineKeyboardButton(f"{services['all']['icon']} {display}", callback_data="svc_all"))
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    return mk

def countries_menu(service_key):
    """قائمة الدول لخدمة معينة"""
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        btns.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"get_{prefix}_{service_key}"))
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
    mk.row(types.InlineKeyboardButton("↩️ رجوع للخدمات", callback_data="menu_services"))
    return mk

def number_actions(prefix, service_key, alloc_id, uid):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(_("change_number_btn", uid), callback_data=f"change_{prefix}_{service_key}_{alloc_id}"),
        types.InlineKeyboardButton(_("change_country_btn", uid), callback_data=f"svc_{service_key}")
    )
    mk.row(
        types.InlineKeyboardButton(_("otp_channel_btn", uid), url="https://t.me/numhj"),
        types.InlineKeyboardButton(_("back_btn", uid), callback_data="main_menu")
    )
    return mk

def show_home(cid, uid):
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, _("maintenance_msg", uid), parse_mode="Markdown")
        return
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, _("force_sub_msg", uid), parse_mode="Markdown", reply_markup=mk)
        return
    photo = db.setting("welcome_photo")
    txt = f"*{_('welcome_title', uid)}*\n\n{_('welcome_desc', uid)}\n\n*{_('choose_service', uid)}*"
    mk = services_menu(uid)
    try:
        if photo:
            try:
                bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
            except:
                bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
        else:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    except:
        pass
    try:
        bot.send_message(cid, _("use_buttons", uid), reply_markup=main_keyboard(uid))
    except:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id; cid = message.chat.id
    db.save_user(message)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        db.process_referral(args[1], uid)
    current_lang = get_lang(uid)
    if current_lang is None:
        bot.send_message(cid,
            "🌐 *اختر لغتك / Choose your language*\n\nيرجى اختيار اللغة للمتابعة\nPlease choose your language to continue",
            parse_mode="Markdown", reply_markup=lang_selection_keyboard())
        return
    show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SELECTION
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data in ["set_lang_ar", "set_lang_en"])
def set_language_callback(call):
    uid = call.from_user.id; cid = call.message.chat.id; mid = call.message.message_id
    lang = "ar" if call.data == "set_lang_ar" else "en"
    set_lang(uid, lang)
    msg = "✅ *تم تعيين اللغة العربية*\n\nأهلاً بك في بوت Taker OTP!" if lang == "ar" else "✅ *Language set to English*\n\nWelcome to Taker OTP Bot!"
    bot.edit_message_text(msg, cid, mid, parse_mode="Markdown")
    show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# BOTTOM KEYBOARD
# ══════════════════════════════════════════════════════════════════════════════
BUTTON_MAP = {
    "get_number": ["📱 احصل على رقم", "📱 Get Number"],
    "countries": ["🌍 الدول المتاحة", "🌍 Countries"],
    "stats": ["📊 إحصائياتي", "📊 My Stats"],
    "balance": ["💰 رصيدي", "💰 Balance"],
    "invite": ["🤝 دعوة الأصدقاء", "🤝 Invite"],
    "traffic": ["🟢 حركة المرور", "🟢 Traffic"],
    "admin": ["⚙️ لوحة التحكم", "⚙️ Admin Panel"],
}

@bot.message_handler(func=lambda m: any(m.text in v for v in BUTTON_MAP.values()) or m.text in ["🌐 English", "🌐 العربية"])
def bottom_buttons(message):
    uid = message.from_user.id; cid = message.chat.id; text = message.text

    if text in ["🌐 English", "🌐 العربية"]:
        new_lang = "en" if text == "🌐 English" else "ar"
        set_lang(uid, new_lang)
        resp = _("language_changed_ar", uid) if new_lang == "ar" else _("language_changed_en", uid)
        bot.send_message(cid, resp, reply_markup=main_keyboard(uid))
        return

    if text in BUTTON_MAP["get_number"]:
        bot.send_message(cid, f"*{_('choose_service', uid)}*", parse_mode="Markdown", reply_markup=services_menu(uid))
        return
    if text in BUTTON_MAP["countries"]:
        countries = db.get_countries()
        txt = f"*{_('countries_list_title', uid)}*\n\n"
        for prefix, name in countries.items():
            txt += f"{get_flag(prefix)} `{prefix}` - {name}\n"
        txt += f"\n📊 *الإجمالي:* `{len(countries)}` دولة"
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    if text in BUTTON_MAP["stats"]:
        reqs, otps, first, last = db.get_user_stats(uid)
        msg = f"*{_('my_stats_title', uid)}*\n\n📱 *{_('total_requests', uid)}:* `{reqs}`\n🔑 *{_('otps_received', uid)}:* `{otps}`\n📅 *{_('first_use', uid)}:* `{format_time(first, uid)}`\n📅 *{_('last_use', uid)}:* `{format_time(last, uid)}`"
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    if text in BUTTON_MAP["balance"]:
        bal, refs = db.get_user_balance(uid); site_bal = api.get_balance()
        msg = f"*{_('my_balance_title', uid)}*\n\n💎 *{_('your_balance', uid)}:* `{bal:.3f} USDT`\n👤 *{_('referrals_label', uid)}:* `{refs}`\n🏦 *{_('site_balance', uid)}:* `{site_bal}`\n💳 *{_('min_withdraw', uid)}:* `18.0 USDT`\n\n{_('earn_tip', uid)}"
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    if text in BUTTON_MAP["invite"]:
        link = db.get_ref_link(uid)
        msg = f"*{_('invite_friends_title', uid)}*\n\n{_('your_link', uid).replace('{}', link)}\n\n💰 *{_('earn_tip', uid)}*\n{_('share_instruction', uid)}"
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    if text in BUTTON_MAP["traffic"]:
        rows = db.get_traffic_stats(10)
        if not rows:
            txt = f"*{_('traffic_title', uid)}*\n\n{_('no_active_numbers', uid)}"
        else:
            countries = db.get_countries(); services = db.get_services()
            total = sum(r[2] for r in rows)
            lines = [f"*{_('traffic_title', uid)}*\n"]
            for prefix, svc, cnt in rows:
                name = countries.get(prefix, prefix); flag = get_flag(prefix)
                svc_icon = services.get(svc, {}).get("icon", "🔐")
                perc = (cnt / total) * 100 if total else 0
                bar = "█" * int(perc / 5)
                lines.append(f"{flag} {name} {svc_icon}: `{perc:.1f}%` {bar}")
            txt = "\n".join(lines)
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    if text in BUTTON_MAP["admin"] and uid in ADMIN_IDS:
        admin_panel(message)
        return

# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, _("check_sub_ok", uid))
        show_home(call.message.chat.id, uid)
    else:
        bot.answer_callback_query(call.id, _("check_sub_fail", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service_cb(call):
    uid = call.from_user.id; cid = call.message.chat.id; mid = call.message.message_id
    service_key = call.data.split("_", 1)[1]
    services = db.get_services(); lang = get_lang(uid) or "ar"
    display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
    bot.edit_message_text(
        f"*{_('choose_country', uid).replace('{}', display_name)}:*",
        cid, mid, parse_mode="Markdown", reply_markup=countries_menu(service_key))

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number_cb(call):
    uid = call.from_user.id; cid = call.message.chat.id; mid = call.message.message_id
    parts = call.data.split("_", 2); prefix = parts[1]; service_key = parts[2] if len(parts) > 2 else "all"

    def process():
        db.release_user_number(uid)
        try:
            alloc_id, number = api.get_number(prefix); number = clean_number(number)
            db.assign_number(uid, alloc_id, number, prefix, service_key)
            countries = db.get_countries(); services = db.get_services(); lang = get_lang(uid) or "ar"
            name = countries.get(prefix, prefix); flag = get_flag(prefix)
            display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
            now = datetime.now().strftime("%H:%M:%S")
            msg = f"*{_('new_number', uid)}*\n\n📞 *{_('number_label', uid)}:* `+{number}`\n🌍 *{_('country_label', uid)}:* {flag} {name}\n🛠 *{_('service_label', uid)}:* {display_name}\n🕒 *{_('time_label', uid)}:* {now}\n⏳ *{_('status_waiting', uid)}*"
            bot.edit_message_text(msg, cid, mid, parse_mode="Markdown", reply_markup=number_actions(prefix, service_key, alloc_id, uid))
        except Exception as e:
            alert = _("no_country", uid) if "غير متوفرة" in str(e) or "unavailable" in str(e).lower() else _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

    bot.answer_callback_query(call.id, "⏳ جاري جلب الرقم...")
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number_cb(call):
    uid = call.from_user.id; cid = call.message.chat.id; mid = call.message.message_id
    parts = call.data.split("_", 3); prefix = parts[1]; service_key = parts[2]; old_alloc = parts[3] if len(parts) > 3 else None

    def process():
        if old_alloc:
            api.delete_number(old_alloc); db.delete_active(old_alloc)
        db.release_user_number(uid)
        try:
            alloc_id, number = api.get_number(prefix); number = clean_number(number)
            db.assign_number(uid, alloc_id, number, prefix, service_key)
            countries = db.get_countries(); services = db.get_services(); lang = get_lang(uid) or "ar"
            name = countries.get(prefix, prefix); flag = get_flag(prefix)
            display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
            now = datetime.now().strftime("%H:%M:%S")
            msg = f"*🔄 تم تغيير الرقم*\n\n📞 *{_('number_label', uid)}:* `+{number}`\n🌍 *{_('country_label', uid)}:* {flag} {name}\n🛠 *{_('service_label', uid)}:* {display_name}\n🕒 *{_('time_label', uid)}:* {now}\n⏳ *{_('status_waiting', uid)}*"
            bot.edit_message_text(msg, cid, mid, parse_mode="Markdown", reply_markup=number_actions(prefix, service_key, alloc_id, uid))
        except Exception as e:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

    bot.answer_callback_query(call.id, "⏳ جاري تغيير الرقم...")
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_menu(call):
    uid = call.from_user.id; cid = call.message.chat.id; mid = call.message.message_id
    if call.data == "menu_services":
        bot.edit_message_text(f"*{_('choose_service', uid)}*", cid, mid, parse_mode="Markdown", reply_markup=services_menu(uid))
    else:
        try: bot.delete_message(cid, mid)
        except: pass
        show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL - ORIGINAL + SERVICES
# ══════════════════════════════════════════════════════════════════════════════
user_states = {}

@bot.message_handler(func=lambda m: m.text in ["⚙️ لوحة التحكم", "⚙️ Admin Panel"] and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if db.setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
    # دول
    markup.add(
        types.InlineKeyboardButton("➕ إضافة دولة", callback_data="add_country"),
        types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_country"))
    # خدمات
    markup.add(
        types.InlineKeyboardButton("➕ إضافة خدمة", callback_data="add_service"),
        types.InlineKeyboardButton("➖ حذف خدمة", callback_data="del_service"))
    # أدوات
    markup.add(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="users_list"))
    markup.add(
        types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
        types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"))
    markup.add(
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="bot_stats"),
        types.InlineKeyboardButton("📄 تقرير", callback_data="report_btn"))
    markup.add(
        types.InlineKeyboardButton("🔗 الاشتراك", callback_data="force_sub"),
        types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    markup.add(
        types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
        types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم - Taker OTP*\n\nمرحباً بك في لوحة إدارة البوت.", parse_mode="Markdown", reply_markup=markup)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ تم تغيير الحالة")
    admin_panel(call.message)

# ── إدارة الدول ──
@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    user_states[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text("*➕ إضافة دولة*\n\nأرسل Prefix الدولة (مثال: `24910`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_country_prefix")
def add_country_prefix(message):
    prefix = message.text.strip()
    user_states[message.from_user.id] = ("add_country_name", prefix)
    bot.send_message(message.chat.id, "أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_country_name")
def add_country_name(message):
    prefix = user_states[message.from_user.id][1]; name = message.text.strip()
    db.add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ *تمت إضافة الدولة*\n\n⚡ الاسم: {name}\n📞 Prefix: `{prefix}`", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = db.get_countries(); markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{get_flag(prefix)} {name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*➖ حذف دولة*\nاختر الدولة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    db.delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

# ── إدارة الخدمات ──
@bot.callback_query_handler(func=lambda c: c.data == "add_service" and c.from_user.id in ADMIN_IDS)
def add_service_start(call):
    user_states[call.from_user.id] = "add_service_key"
    bot.edit_message_text("*➕ إضافة خدمة*\n\nأرسل المفتاح (مثال: `snapchat`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_service_key")
def add_service_key(message):
    key = message.text.strip().lower()
    user_states[message.from_user.id] = ("add_service_name", key)
    bot.send_message(message.chat.id, "أرسل اسم الخدمة بالإنجليزية:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_name")
def add_service_name(message):
    key = user_states[message.from_user.id][1]; name = message.text.strip()
    user_states[message.from_user.id] = ("add_service_icon", key, name)
    bot.send_message(message.chat.id, "أرسل أيقونة الخدمة (إيموجي واحد):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_icon")
def add_service_icon(message):
    key = user_states[message.from_user.id][1]; name = user_states[message.from_user.id][2]; icon = message.text.strip()
    user_states[message.from_user.id] = ("add_service_ar", key, name, icon)
    bot.send_message(message.chat.id, "أرسل اسم الخدمة بالعربية:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_ar")
def add_service_ar(message):
    key = user_states[message.from_user.id][1]; name = user_states[message.from_user.id][2]
    icon = user_states[message.from_user.id][3]; ar_name = message.text.strip()
    db.add_service(key, name, icon, ar_name)
    bot.send_message(message.chat.id, f"✅ *تمت إضافة الخدمة*\n\n{icon} {ar_name}", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_service" and c.from_user.id in ADMIN_IDS)
def del_service_start(call):
    services = db.get_services(); markup = types.InlineKeyboardMarkup()
    for key, data in services.items():
        if key != "all":
            markup.add(types.InlineKeyboardButton(f"{data['icon']} {data['ar']}", callback_data=f"delservice_{key}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*➖ حذف خدمة*\nاختر الخدمة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delservice_") and c.from_user.id in ADMIN_IDS)
def del_service_confirm(call):
    db.delete_service(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

# ── إذاعة ──
@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 إذاعة*\nأرسل الرسالة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = db.get_all_users(); cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1; time.sleep(0.02)
        except: pass
    bot.send_message(message.chat.id, f"✅ *تم الإرسال إلى `{cnt}` مستخدم*", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── مستخدمين ──
@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    rows = db.conn.cursor().execute("SELECT user_id, username, first_name, total_requests, total_otps FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 20").fetchall()
    msg = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{uid}` - @{un or '—'} | 📱`{reqs}` 🔑`{otps}`" for uid, un, fn, reqs, otps in rows) if rows else "لا يوجد مستخدمون."
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ── إحصائيات ──
@bot.callback_query_handler(func=lambda c: c.data == "bot_stats" and c.from_user.id in ADMIN_IDS)
def bot_stats(call):
    total_users = len(db.get_all_users()); active_numbers = len(db.get_all_active())
    total_otps = db.get_total_otps(); api_stats = api.get_stats()
    countries_count = len(db.get_countries()); services_count = len(db.get_services())
    msg = f"*📊 إحصائيات البوت*\n\n👥 المستخدمين: `{total_users}`\n📱 الأرقام النشطة: `{active_numbers}`\n🔑 إجمالي الأكواد: `{total_otps}`\n🌍 الدول: `{countries_count}`\n🛠 الخدمات: `{services_count}`\n\n📡 *API:*\n✅ ناجح: `{api_stats.get('success', 0)}`\n❌ فشل: `{api_stats.get('failed', 0)}`"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ── تقرير ──
@bot.callback_query_handler(func=lambda c: c.data == "report_btn" and c.from_user.id in ADMIN_IDS)
def report_btn(call):
    import tempfile
    filename = f"Taker_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\nTAKER OTP BOT - تقرير شامل\n" + "=" * 60 + f"\nالتاريخ: {datetime.now()}\n\n")
        f.write("👥 المستخدمين:\n" + "-" * 40 + "\n")
        for u in db.conn.cursor().execute("SELECT * FROM users").fetchall():
            f.write(f"ID: {u[0]} | @{u[1] or 'N/A'} | {u[2] or 'N/A'} | طلبات: {u[6]} | أكواد: {u[7]}\n")
        f.write("\n📱 الأرقام النشطة:\n" + "-" * 40 + "\n")
        for a in db.conn.cursor().execute("SELECT number, prefix, service FROM active_numbers WHERE status='waiting'").fetchall():
            f.write(f"رقم: {a[0]} | دولة: {a[1]} | خدمة: {a[2]}\n")
        f.write(f"\n📊 إجمالي الأكواد: {db.get_total_otps()}\n")
    with open(filepath, 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption="📄 *تقرير البوت الشامل*", parse_mode="Markdown")
    try: os.remove(filepath)
    except: pass
    bot.answer_callback_query(call.id)

# ── حظر/فك حظر ──
@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"] and c.from_user.id in ADMIN_IDS)
def ban_unban_prompt(call):
    user_states[call.from_user.id] = call.data
    txt = "*🚫 حظر*\nأرسل ID المستخدم:" if call.data == "ban" else "*✅ فك حظر*\nأرسل ID المستخدم:"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    action = user_states[message.from_user.id]
    try:
        uid = int(message.text)
        db.conn.cursor().execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (uid,))
        db.conn.commit()
        bot.send_message(message.chat.id, f"✅ *تم {'حظر' if action=='ban' else 'فك حظر'}* `{uid}`", parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ معرف غير صحيح")
    del user_states[message.from_user.id]

# ── اشتراك إجباري ──
@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    channels = db.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك الإجباري*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    user_states[message.from_user.id] = ("addch_desc", message.text.strip())
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]; desc = message.text.strip()
    db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    db.conn.commit()
    bot.send_message(message.chat.id, "✅ *تمت إضافة القناة*", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    db.conn.cursor().execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (int(call.data.split("_")[1]),))
    db.conn.commit()
    force_sub_menu(call)

# ── صورة ──
@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*🖼️ صورة الترحيب*\nأرسل الصورة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ *تم حفظ الصورة*", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── مسح ──
@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        db.conn.cursor().execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ══════════════════════════════════════════════════════════════════════════════
# OTP LOOP - 30 MINUTES DELETE
# ══════════════════════════════════════════════════════════════════════════════
def process_single_otp(alloc_id, number, prefix, service_key, uid):
    try:
        status, otp = api.check_otp(number)
        if status == "success" and otp:
            service = detect_service(otp) if otp else "OTP"
            ic = SERVICE_ICONS.get(service, "🔐")
            countries = db.get_countries(); services = db.get_services()
            name = countries.get(prefix, prefix); flag = get_flag(prefix)
            svc_name = services.get(service_key, {}).get("ar", service_key)
            code = format_code(otp)

            logger.info(f"🎯 كود: {number} -> {otp} ({service})")

            # إرسال للمستخدم
            if uid:
                try:
                    user_msg = f"*🔐 تم استقبال رمز التفعيل*\n\n📞 *الرقم:* `+{number}`\n🌍 *الدولة:* {flag} {name}\n{ic} *التطبيق:* {service}\n🔢 *الكود:* `{code}`\n\nانسخ الكود واستخدمه فوراً"
                    bot.send_message(uid, user_msg, parse_mode="Markdown")
                except: pass

            # إرسال للجروب - حذف بعد نصف ساعة
            for cid in CHAT_IDS:
                for attempt in range(3):
                    try:
                        masked = mask_number(number)
                        group_msg = f"*🔐 كود جديد - Taker OTP*\n\n🌍 {flag} {name} | {ic} {service}\n📞 `{masked}`\n🔢 `{code}`"
                        sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                        logger.info(f"✅ أرسل للجروب {cid} - يحذف بعد {DELETE_AFTER}s")
                        threading.Thread(target=lambda: (time.sleep(DELETE_AFTER), bot.delete_message(cid, sent.message_id)), daemon=True).start()
                        break
                    except:
                        time.sleep(1)

            # تحديث DB
            db.save_otp(alloc_id, otp, service, uid)
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)

        elif status == "expired":
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)
    except: pass

def otp_loop():
    logger.info(f"🔄 بدء حلقة OTP - حذف الجروب بعد {DELETE_AFTER}s ({DELETE_AFTER/60} دقيقة)")
    while True:
        try:
            active_numbers = db.get_all_active()
            if active_numbers:
                futures = [executor.submit(process_single_otp, aid, num, pfx, svc, uid) for aid, num, pfx, svc, uid in active_numbers]
                for future in as_completed(futures):
                    try: future.result()
                    except: pass
        except: pass
        time.sleep(OTP_CHECK_INTERVAL)

# ══════════════════════════════════════════════════════════════════════════════
# FLASK
# ══════════════════════════════════════════════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string("""
<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Taker OTP Bot v10.0</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#0a0a0a,#1a1a2e,#0f3460);color:#e0e0e0;font-family:'Segoe UI',Tahoma,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.container{text-align:center;padding:50px;background:rgba(255,255,255,0.03);border-radius:30px;border:1px solid rgba(255,255,255,0.1);box-shadow:0 30px 80px rgba(0,0,0,0.6)}
h1{font-size:3.5em;background:linear-gradient(135deg,#00d2ff,#3a7bd5,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}
.status{color:#00ff88;font-size:1.3em;margin:15px 0}.info{color:#aaa;margin:8px 0}
.badge{display:inline-block;padding:10px 20px;background:rgba(0,210,255,0.15);border:1px solid #00d2ff;border-radius:25px;margin:8px;font-size:0.9em}
.version{color:#ff6b6b;font-weight:bold;font-size:1.2em}</style></head>
<body><div class="container"><h1>⚡ TAKER OTP BOT ⚡</h1><p class="version">GOD MODE v10.0</p><p class="status">🟢 System Online</p>
<p class="info">API: xwdsms.org | Full Integration</p><p class="info">Languages: العربية & English</p>
<div style="margin-top:25px"><span class="badge">🚀 50 Workers</span><span class="badge">⏱️ 30min Delete</span><span class="badge">🌍 50+ Countries</span><span class="badge">🛠 Services System</span></div>
<p class="info" style="margin-top:25px">Developer: @hackerTaker</p></div></body></html>""")

@app.route('/health')
def health(): return jsonify(status="ok", version="10.0", delete_after=f"{DELETE_AFTER}s"), 200

@app.route('/api/v1/get-number', methods=['POST'])
def flask_get_number():
    try:
        data = flask_request.get_json()
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": data.get("range", "")}, headers={"x-api-key": API_KEY}, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/check-otp', methods=['GET'])
def flask_check_otp():
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": flask_request.args.get("number", "")}, headers={"x-api-key": API_KEY}, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/balance', methods=['GET'])
def flask_balance():
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers={"x-api-key": API_KEY}, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e: return jsonify({"balance": "0"}), 500

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ████████╗ █████╗ ██╗  ██╗███████╗██████╗                      ║
║   ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗                     ║
║      ██║   ███████║█████╔╝ █████╗  ██████╔╝                     ║
║      ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗                     ║
║      ██║   ██║  ██║██║  ██╗███████╗██║  ██║                     ║
║      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                     ║
║                                                                  ║
║        TAKER OTP BOT - GOD MODE v10.0 - FINAL                    ║
║        Developer: @hackerTaker                                   ║
║        API: xwdsms.org                                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    logger.info("=" * 60)
    logger.info("🚀 TAKER OTP BOT v10.0 GOD MODE FINAL")
    logger.info(f"⏱️  Delete OTP after: {DELETE_AFTER}s ({DELETE_AFTER/60:.1f} min)")
    logger.info(f"🔧 Workers: {MAX_WORKERS}")
    logger.info(f"🔄 API Retries: {API_RETRIES}")
    logger.info("=" * 60)

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()

    logger.info("✅ جميع الخدمات تعمل - البوت جاهز")
    while True:
        try:
            bot.infinity_polling(timeout=POLLING_TIMEOUT, long_polling_timeout=LONG_POLLING_TIMEOUT)
        except Exception as e:
            logger.error(f"Polling: {e}")
            time.sleep(2)

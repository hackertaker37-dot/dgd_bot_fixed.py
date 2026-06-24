# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     ████████╗ █████╗ ██╗  ██╗███████╗██████╗      ██████╗ ████████╗██████╗      ║
║     ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗    ██╔═══██╗╚══██╔══╝██╔══██╗     ║
║        ██║   ███████║█████╔╝ █████╗  ██████╔╝    ██║   ██║   ██║   ██████╔╝     ║
║        ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗    ██║   ██║   ██║   ██╔═══╝      ║
║        ██║   ██║  ██║██║  ██╗███████╗██║  ██║    ╚██████╔╝   ██║   ██║          ║
║        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝    ╚═╝   ╚═╝          ║
║                                                                      ║
║              TAKER OTP BOT - MEGA ULTIMATE EDITION v7.0              ║
║              Developer: @hackerTaker                                 ║
║              API: xwdsms.org (Full Integration)                      ║
║              Languages: Arabic & English (Bilingual)                 ║
║              Status: PRODUCTION READY - MAXIMUM PERFORMANCE          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
import time
import requests
import re
import os
import sys
import sqlite3
import threading
import logging
import json
import random
import string
import hashlib
import traceback
import platform
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
from collections import OrderedDict, defaultdict
from telebot import types, TeleBot, apihelper
from flask import Flask, jsonify, request as flask_request, render_template_string

# ═══════════════════════════════════════════════════════════════════
# SYSTEM INFORMATION
# ═══════════════════════════════════════════════════════════════════
SYSTEM_INFO = {
    "os": platform.system(),
    "python": platform.python_version(),
    "machine": platform.machine(),
    "processor": platform.processor(),
}

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION - ULTRA SETTINGS
# ═══════════════════════════════════════════════════════════════════
BOT_TOKEN = "8686995713:AAEvUVf_SLRx5ZKbTUCGvlFQhgg3HO5tKJ0"
API_KEY = "97257ac6fe5efd03c28b43af34a887b3"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_mega.db"

# ═══════════════════════════════════════════════════════════════════
# TIMING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
DELETE_AFTER = 1800          # نصف ساعة = 1800 ثانية
OTP_CHECK_INTERVAL = 1.5     # فحص OTP كل 1.5 ثانية
API_TIMEOUT = 12             # مهلة API
API_RETRIES = 5              # عدد محاولات API
MAX_WORKERS = 24             # عدد العمال المتوازيين
CACHE_TTL = 60               # مدة الكاش
SESSION_TTL = 600            # مدة الجلسة
POLLING_TIMEOUT = 15         # مهلة البولينج
LONG_POLLING_TIMEOUT = 8     # مهلة البولينج الطويل

# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE TUNING
# ═══════════════════════════════════════════════════════════════════
apihelper.SESSION_TIME_TO_LIVE = SESSION_TTL
apihelper.ENABLE_MIDDLEWARE = False
apihelper.READ_TIMEOUT = 8
apihelper.CONNECT_TIMEOUT = 5
apihelper.RETRY_ON_ERROR = True
apihelper.RETRY_TIMEOUT = 3

# Thread Pool Executor
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Cache System
_cache_store = {}
_cache_times = {}
_cache_lock = threading.Lock()

def mega_cache(ttl=CACHE_TTL):
    """نظام كاش متقدم"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = hashlib.md5(f"{func.__name__}:{args}:{kwargs}".encode()).hexdigest()
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

# ═══════════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ═══════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# COMPLETE TRANSLATION DICTIONARY
# ═══════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # ── الترحيب ──
    "welcome_title": {
        "ar": "✨ أهلاً بك في بوت Taker OTP",
        "en": "✨ Welcome to Taker OTP Bot"
    },
    "welcome_desc": {
        "ar": "• احصل على أرقام وهمية لتفعيل حساباتك\n• استقبل رموز التفعيل بشكل فوري\n• ادعُ أصدقاءك واربح رصيداً\n• أكثر من 50 دولة متاحة",
        "en": "• Get virtual numbers for activation\n• Receive OTP codes instantly\n• Invite friends and earn credit\n• Over 50 countries available"
    },
    "choose_country": {
        "ar": "🌍 اختر الدولة المناسبة:",
        "en": "🌍 Choose your country:"
    },
    # ── الأرقام ──
    "new_number": {
        "ar": "✅ تم تخصيص رقم جديد بنجاح",
        "en": "✅ New number allocated successfully"
    },
    "number_label": {"ar": "الرقم", "en": "Number"},
    "country_label": {"ar": "الدولة", "en": "Country"},
    "time_label": {"ar": "الوقت", "en": "Time"},
    "status_waiting": {
        "ar": "⏳ في انتظار استقبال رمز التفعيل...",
        "en": "⏳ Waiting for verification code..."
    },
    # ── الأزرار ──
    "change_number_btn": {"ar": "🔄 تغيير الرقم", "en": "🔄 Change Number"},
    "change_country_btn": {"ar": "🌍 تغيير الدولة", "en": "🌍 Change Country"},
    "otp_channel_btn": {"ar": "📞 قناة الأكواد", "en": "📞 OTP Channel"},
    "back_btn": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    # ── الصيانة ──
    "maintenance_msg": {
        "ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.",
        "en": "⚠️ *Bot under maintenance*\nPlease try again later."
    },
    # ── الاشتراك الإجباري ──
    "force_sub_msg": {
        "ar": "🔒 *يجب الاشتراك في القنوات أولاً*",
        "en": "🔒 *You must subscribe to the channels first*"
    },
    "sub_btn": {"ar": "📢 اشترك في القناة", "en": "📢 Subscribe to channel"},
    "check_sub_btn": {"ar": "✅ تحقق من الاشتراك", "en": "✅ Check subscription"},
    "check_sub_ok": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_sub_fail": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ Not subscribed to all channels"},
    # ── الأكواد ──
    "otp_received_title": {
        "ar": "🔐 تم استقبال رمز التفعيل",
        "en": "🔐 OTP Code Received"
    },
    "app_label": {"ar": "التطبيق", "en": "Application"},
    "code_label": {"ar": "الكود", "en": "Code"},
    "copy_instruction": {
        "ar": "انسخ الكود واستخدمه فوراً قبل انتهاء الصلاحية",
        "en": "Copy the code and use it immediately before expiry"
    },
    # ── القوائم ──
    "countries_list_title": {
        "ar": "🌍 الدول والخدمات المتاحة:",
        "en": "🌍 Available countries & services:"
    },
    "services_count": {"ar": "الخدمات", "en": "Services"},
    # ── الإحصائيات ──
    "my_stats_title": {"ar": "📊 إحصائياتك", "en": "📊 Your Statistics"},
    "total_requests": {"ar": "إجمالي الطلبات", "en": "Total Requests"},
    "otps_received": {"ar": "الأكواد المستلمة", "en": "OTPs Received"},
    "first_use": {"ar": "أول استخدام", "en": "First Use"},
    "last_use": {"ar": "آخر استخدام", "en": "Last Use"},
    # ── الرصيد ──
    "my_balance_title": {"ar": "💰 رصيدك", "en": "💰 Your Balance"},
    "your_balance": {"ar": "رصيدك", "en": "Your Balance"},
    "referrals_label": {"ar": "الإحالات", "en": "Referrals"},
    "site_balance": {"ar": "رصيد الموقع", "en": "Site Balance"},
    "min_withdraw": {"ar": "الحد الأدنى للسحب", "en": "Min Withdrawal"},
    "earn_tip": {
        "ar": "💡 *اربح `0.05 USDT` عن كل صديق تدعوه*",
        "en": "💡 *Earn `0.05 USDT` per friend you invite*"
    },
    # ── الدعوة ──
    "invite_friends_title": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "your_link": {"ar": "🔗 *رابط الدعوة الخاص بك:*\n`{}`", "en": "🔗 *Your invite link:*\n`{}`"},
    "share_instruction": {"ar": "📤 *شارك الرابط مع أصدقائك*", "en": "📤 *Share the link with your friends*"},
    # ── حركة المرور ──
    "traffic_title": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "no_active_numbers": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers currently."},
    "unknown_text": {"ar": "غير معروف", "en": "Unknown"},
    # ── أزرار الكيبورد ──
    "get_number_kb": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries_kb": {"ar": "🌍 الدول المتاحة", "en": "🌍 Countries"},
    "stats_kb": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance_kb": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite_kb": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite"},
    "traffic_kb": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "admin_kb": {"ar": "⚙️ لوحة التحكم", "en": "⚙️ Admin Panel"},
    "use_buttons": {"ar": "استخدم الأزرار أدناه للتنقل:", "en": "Use the buttons below to navigate:"},
    # ── تغيير اللغة ──
    "language_changed_ar": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to Arabic"},
    "language_changed_en": {"ar": "✅ تم تغيير اللغة إلى English", "en": "✅ Language changed to English"},
    # ── الأخطاء ──
    "no_country": {"ar": "هذه الدولة غير متوفرة حالياً", "en": "This country is currently unavailable"},
    "general_error": {"ar": "خطأ: {}", "en": "Error: {}"},
    "connection_error": {"ar": "خطأ في الاتصال بالخادم", "en": "Server connection error"},
}

# ═══════════════════════════════════════════════════════════════════
# LANGUAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════
_lang_cache = {}
_lang_lock = threading.Lock()

def get_lang(uid):
    uid_str = str(uid)
    with _lang_lock:
        if uid_str in _lang_cache:
            return _lang_cache[uid_str]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (f"lang_{uid}",))
        row = c.fetchone()
        conn.close()
        lang = row[0] if row else None
        with _lang_lock:
            _lang_cache[uid_str] = lang
        return lang
    except:
        return None

def set_lang(uid, lang):
    uid_str = str(uid)
    with _lang_lock:
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
    if uid is None:
        lang = "ar"
    else:
        lang = get_lang(uid) or "ar"
    text = TRANSLATIONS.get(key, {}).get(lang)
    if text is None:
        text = TRANSLATIONS.get(key, {}).get("ar", key)
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

# ═══════════════════════════════════════════════════════════════════
# DEFAULT DATA
# ═══════════════════════════════════════════════════════════════════
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
    return "🏳"

# ═══════════════════════════════════════════════════════════════════
# API FUNCTIONS WITH RETRY SYSTEM
# ═══════════════════════════════════════════════════════════════════
class APIManager:
    """مدير API متقدم مع إعادة محاولة وتتبع الأخطاء"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TakerOTPBot/7.0"
        })
        self.stats = defaultdict(int)
    
    def _request(self, method, endpoint, max_retries=API_RETRIES, **kwargs):
        url = f"{self.base_url}{endpoint}"
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, timeout=API_TIMEOUT, **kwargs)
                else:
                    resp = self.session.post(url, timeout=API_TIMEOUT, **kwargs)
                resp.raise_for_status()
                self.stats['success'] += 1
                return resp.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.stats['not_found'] += 1
                    raise Exception("هذه الدولة غير متوفرة حالياً")
                if e.response.status_code == 429:
                    self.stats['rate_limited'] += 1
                    time.sleep(2 ** attempt)
                    continue
                if attempt == max_retries - 1:
                    self.stats['failed'] += 1
                    raise Exception("خطأ في الاتصال بالخادم")
                time.sleep(0.5 * (attempt + 1))
            except requests.exceptions.Timeout:
                self.stats['timeout'] += 1
                if attempt == max_retries - 1:
                    raise Exception("انتهت مهلة الاتصال")
                time.sleep(1)
            except Exception as e:
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

# ═══════════════════════════════════════════════════════════════════
# DATABASE SYSTEM
# ═══════════════════════════════════════════════════════════════════
class Database:
    """نظام قاعدة بيانات متقدم"""
    
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
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                total_otps INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT
            );
            
            CREATE TABLE IF NOT EXISTS active_numbers (
                alloc_id TEXT PRIMARY KEY,
                number TEXT,
                prefix TEXT,
                assigned_to INTEGER,
                created_at TEXT,
                status TEXT DEFAULT 'waiting',
                otp TEXT,
                service TEXT
            );
            
            CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                otp TEXT,
                service TEXT,
                country TEXT,
                timestamp TEXT,
                assigned_to INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY,
                ref_code TEXT UNIQUE,
                ref_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT UNIQUE,
                description TEXT,
                enabled INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            
            CREATE TABLE IF NOT EXISTS custom_countries (
                prefix TEXT PRIMARY KEY,
                name TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_active_status ON active_numbers(status);
            CREATE INDEX IF NOT EXISTS idx_otp_logs_time ON otp_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_users_ban ON users(is_banned);
        ''')
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        for prefix, name in DEFAULT_COUNTRIES.items():
            c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
        self.conn.commit()
    
    def setting(self, key, value=None):
        c = self.conn.cursor()
        if value is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
            self.conn.commit()
            return value
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None
    
    @mega_cache(ttl=30)
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
            "SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'"
        ).fetchall()
    
    def release_user_number(self, uid):
        c = self.conn.cursor()
        for (aid,) in c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)).fetchall():
            api.delete_number(aid)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
        self.conn.commit()
    
    def assign_number(self, uid, alloc_id, number, prefix):
        self.release_user_number(uid)
        c = self.conn.cursor()
        c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, assigned_to, created_at) VALUES (?,?,?,?,?)",
                 (alloc_id, number, prefix, uid, datetime.now().isoformat()))
        c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
        self.conn.commit()
    
    def save_otp(self, alloc_id, otp, service, uid):
        c = self.conn.cursor()
        c.execute("UPDATE active_numbers SET status='success', otp=?, service=? WHERE alloc_id=?", (otp, service, alloc_id))
        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
        countries = self.get_countries()
        number_row = c.execute("SELECT number, prefix FROM active_numbers WHERE alloc_id=?", (alloc_id,)).fetchone()
        if number_row:
            country = countries.get(number_row[1], number_row[1])
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
            "SELECT prefix, COUNT(*) as cnt FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY cnt DESC LIMIT ?",
            (limit,)
        ).fetchall()
    
    def get_total_otps(self):
        row = self.conn.cursor().execute("SELECT COUNT(*) FROM otp_logs").fetchone()
        return row[0] if row else 0
    
    def get_channels(self):
        return self.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()

db = Database(DB_PATH)

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def clean_number(n):
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    t = str(text).lower()
    patterns = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستغرام", "انستا"],
        "TikTok": ["tiktok", "تيك توك"],
        "IMO": ["imo", "ايمو"],
        "Snapchat": ["snapchat", "سناب"],
        "Google": ["google", "gmail", "جوجل"],
        "Twitter/X": ["twitter", "تويتر", "x.com"],
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
    if len(otp) > 3:
        return f"{otp[:3]}-{otp[3:]}"
    return otp

def check_subscription(uid):
    channels = db.get_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            url = ch[2]  # channel_url
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

# ═══════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════
bot = TeleBot(BOT_TOKEN, threaded=True, num_threads=MAX_WORKERS)

# ═══════════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════════
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

def countries_menu():
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        btns.append(types.InlineKeyboardButton(
            f"{flag} {name}", callback_data=f"getnum_{prefix}"
        ))
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
    return mk

def number_actions(prefix, alloc_id, uid):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(_("change_number_btn", uid), callback_data=f"change_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton(_("change_country_btn", uid), callback_data="country_menu")
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
    txt = f"*{_('welcome_title', uid)}*\n\n{_('welcome_desc', uid)}\n\n*{_('choose_country', uid)}*"
    mk = countries_menu()
    
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

# ═══════════════════════════════════════════════════════════════════
# /start COMMAND
# ═══════════════════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    db.save_user(message)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        db.process_referral(args[1], uid)
    
    current_lang = get_lang(uid)
    
    if current_lang is None:
        bot.send_message(
            cid,
            "🌐 *اختر لغتك / Choose your language*\n\n"
            "يرجى اختيار اللغة للمتابعة\n"
            "Please choose your language to continue",
            parse_mode="Markdown",
            reply_markup=lang_selection_keyboard()
        )
        return
    
    show_home(cid, uid)

# ═══════════════════════════════════════════════════════════════════
# LANGUAGE SELECTION
# ═══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data in ["set_lang_ar", "set_lang_en"])
def set_language_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    lang = "ar" if call.data == "set_lang_ar" else "en"
    
    set_lang(uid, lang)
    
    if lang == "ar":
        msg = "✅ *تم تعيين اللغة العربية*\n\nأهلاً بك في بوت Taker OTP!"
    else:
        msg = "✅ *Language set to English*\n\nWelcome to Taker OTP Bot!"
    
    bot.edit_message_text(msg, cid, mid, parse_mode="Markdown")
    show_home(cid, uid)

# ═══════════════════════════════════════════════════════════════════
# BOTTOM KEYBOARD HANDLERS
# ═══════════════════════════════════════════════════════════════════
BUTTON_MAP = {
    "get_number": ["📱 احصل على رقم", "📱 Get Number"],
    "countries": ["🌍 الدول المتاحة", "🌍 Countries"],
    "stats": ["📊 إحصائياتي", "📊 My Stats"],
    "balance": ["💰 رصيدي", "💰 Balance"],
    "invite": ["🤝 دعوة الأصدقاء", "🤝 Invite"],
    "traffic": ["🟢 حركة المرور", "🟢 Traffic"],
    "admin": ["⚙️ لوحة التحكم", "⚙️ Admin Panel"],
}

@bot.message_handler(func=lambda m: any(
    m.text in v for v in BUTTON_MAP.values()
) or m.text in ["🌐 English", "🌐 العربية"])
def bottom_buttons(message):
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text
    
    # تغيير اللغة
    if text in ["🌐 English", "🌐 العربية"]:
        new_lang = "en" if text == "🌐 English" else "ar"
        set_lang(uid, new_lang)
        resp = _("language_changed_ar", uid) if new_lang == "ar" else _("language_changed_en", uid)
        bot.send_message(cid, resp, reply_markup=main_keyboard(uid))
        return
    
    # احصل على رقم
    if text in BUTTON_MAP["get_number"]:
        bot.send_message(cid, f"*{_('choose_country', uid)}*", parse_mode="Markdown", reply_markup=countries_menu())
        return
    
    # الدول المتاحة
    if text in BUTTON_MAP["countries"]:
        countries = db.get_countries()
        txt = f"*{_('countries_list_title', uid)}*\n\n"
        for prefix, name in countries.items():
            txt += f"{get_flag(prefix)} `{prefix}` - {name}\n"
        txt += f"\n📊 *الإجمالي:* `{len(countries)}` دولة"
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # إحصائياتي
    if text in BUTTON_MAP["stats"]:
        reqs, otps, first, last = db.get_user_stats(uid)
        msg = (
            f"*{_('my_stats_title', uid)}*\n\n"
            f"📱 *{_('total_requests', uid)}:* `{reqs}`\n"
            f"🔑 *{_('otps_received', uid)}:* `{otps}`\n"
            f"📅 *{_('first_use', uid)}:* `{format_time(first, uid)}`\n"
            f"📅 *{_('last_use', uid)}:* `{format_time(last, uid)}`"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # رصيدي
    if text in BUTTON_MAP["balance"]:
        bal, refs = db.get_user_balance(uid)
        site_bal = api.get_balance()
        msg = (
            f"*{_('my_balance_title', uid)}*\n\n"
            f"💎 *{_('your_balance', uid)}:* `{bal:.3f} USDT`\n"
            f"👤 *{_('referrals_label', uid)}:* `{refs}`\n"
            f"🏦 *{_('site_balance', uid)}:* `{site_bal}`\n"
            f"💳 *{_('min_withdraw', uid)}:* `18.0 USDT`\n\n"
            f"{_('earn_tip', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # دعوة الأصدقاء
    if text in BUTTON_MAP["invite"]:
        link = db.get_ref_link(uid)
        msg = (
            f"*{_('invite_friends_title', uid)}*\n\n"
            f"{_('your_link', uid).replace('{}', link)}\n\n"
            f"💰 *{_('earn_tip', uid)}*\n"
            f"{_('share_instruction', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # حركة المرور
    if text in BUTTON_MAP["traffic"]:
        rows = db.get_traffic_stats(10)
        if not rows:
            txt = f"*{_('traffic_title', uid)}*\n\n{_('no_active_numbers', uid)}"
        else:
            countries = db.get_countries()
            total = sum(r[1] for r in rows)
            lines = [f"*{_('traffic_title', uid)}*\n"]
            for i, (prefix, cnt) in enumerate(rows, 1):
                name = countries.get(prefix, prefix)
                flag = get_flag(prefix)
                perc = (cnt / total) * 100 if total else 0
                bar = "█" * int(perc / 5)
                lines.append(f"{flag} `{name}` → `{perc:.1f}%` {bar}")
            txt = "\n".join(lines)
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # لوحة التحكم
    if text in BUTTON_MAP["admin"] and uid in ADMIN_IDS:
        admin_panel(message)
        return

# ═══════════════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, _("check_sub_ok", uid))
        show_home(call.message.chat.id, uid)
    else:
        bot.answer_callback_query(call.id, _("check_sub_fail", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def get_number(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    prefix = call.data.split("_")[1]
    
    # تنفيذ في الخلفية لسرعة الاستجابة
    def process():
        db.release_user_number(uid)
        try:
            alloc_id, number = api.get_number(prefix)
            number = clean_number(number)
            db.assign_number(uid, alloc_id, number, prefix)
            
            countries = db.get_countries()
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            now = datetime.now().strftime("%H:%M:%S")
            
            msg = (
                f"*{_('new_number', uid)}*\n\n"
                f"📞 *{_('number_label', uid)}:* `+{number}`\n"
                f"🌍 *{_('country_label', uid)}:* {flag} {name}\n"
                f"🕒 *{_('time_label', uid)}:* {now}\n"
                f"⏳ *{_('status_waiting', uid)}*"
            )
            
            bot.edit_message_text(
                msg, cid, mid,
                parse_mode="Markdown",
                reply_markup=number_actions(prefix, alloc_id, uid)
            )
        except Exception as e:
            alert = _("no_country", uid) if "غير متوفرة" in str(e) or "unavailable" in str(e).lower() else _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)
    
    bot.answer_callback_query(call.id, "⏳ جاري جلب الرقم...")
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    parts = call.data.split("_", 2)
    prefix = parts[1]
    old_alloc = parts[2] if len(parts) > 2 else None
    
    def process():
        if old_alloc:
            api.delete_number(old_alloc)
            db.delete_active(old_alloc)
        
        db.release_user_number(uid)
        
        try:
            alloc_id, number = api.get_number(prefix)
            number = clean_number(number)
            db.assign_number(uid, alloc_id, number, prefix)
            
            countries = db.get_countries()
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            now = datetime.now().strftime("%H:%M:%S")
            
            msg = (
                f"*🔄 تم تغيير الرقم*\n\n"
                f"📞 *{_('number_label', uid)}:* `+{number}`\n"
                f"🌍 *{_('country_label', uid)}:* {flag} {name}\n"
                f"🕒 *{_('time_label', uid)}:* {now}\n"
                f"⏳ *{_('status_waiting', uid)}*"
            )
            
            bot.edit_message_text(
                msg, cid, mid,
                parse_mode="Markdown",
                reply_markup=number_actions(prefix, alloc_id, uid)
            )
        except Exception as e:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)
    
    bot.answer_callback_query(call.id, "⏳ جاري تغيير الرقم...")
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    if call.data == "country_menu":
        bot.edit_message_text(
            f"*{_('choose_country', uid)}*",
            cid, mid, parse_mode="Markdown",
            reply_markup=countries_menu()
        )
    else:
        try:
            bot.delete_message(cid, mid)
        except:
            pass
        show_home(cid, uid)

# ═══════════════════════════════════════════════════════════════════
# ADMIN PANEL - ORIGINAL STYLE
# ═══════════════════════════════════════════════════════════════════
user_states = {}

@bot.message_handler(func=lambda m: m.text in ["⚙️ لوحة التحكم", "⚙️ Admin Panel"] and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    maintenance_status = db.setting("maintenance")
    status_text = "🟢 مفتوح" if maintenance_status != "1" else "🔴 صيانة"
    
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status_text}", callback_data="toggle_maint"))
    
    markup.add(
        types.InlineKeyboardButton("➕ إضافة دولة", callback_data="add_country"),
        types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_country")
    )
    
    markup.add(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="users_list")
    )
    
    markup.add(
        types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
        types.InlineKeyboardButton("✅ فك حظر", callback_data="unban")
    )
    
    markup.add(
        types.InlineKeyboardButton("📊 إحصائيات البوت", callback_data="bot_stats"),
        types.InlineKeyboardButton("📄 تقرير PDF", callback_data="report_btn")
    )
    
    markup.add(
        types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="force_sub"),
        types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="set_photo")
    )
    
    markup.add(
        types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="clear_data"),
        types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu")
    )
    
    msg = (
        "*⚙️ لوحة التحكم - Taker OTP*\n\n"
        f"🕒 *الوقت:* `{datetime.now().strftime('%H:%M:%S')}`\n"
        f"📅 *التاريخ:* `{datetime.now().strftime('%Y-%m-%d')}`\n\n"
        "مرحباً بك في لوحة إدارة البوت."
    )
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

# ═══════════════════════════════════════════════════════════════════
# ADMIN CALLBACKS
# ═══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ تم تغيير حالة البوت")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    user_states[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text(
        "*➕ إضافة دولة جديدة*\n\nأرسل Prefix الدولة (مثال: `24910`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_country_prefix")
def add_country_prefix(message):
    prefix = message.text.strip()
    user_states[message.from_user.id] = ("add_country_name", prefix)
    bot.send_message(message.chat.id, "✏️ أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_country_name")
def add_country_name(message):
    prefix = user_states[message.from_user.id][1]
    name = message.text.strip()
    db.add_country(prefix, name)
    flag = get_flag(prefix)
    bot.send_message(
        message.chat.id,
        f"✅ *تمت إضافة الدولة بنجاح*\n\n📞 *Prefix:* `{prefix}`\n{flag} *الاسم:* {name}",
        parse_mode="Markdown"
    )
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = db.get_countries()
    markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        markup.add(types.InlineKeyboardButton(f"{flag} {name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text(
        "*➖ حذف دولة*\nاختر الدولة التي تريد حذفها:",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    prefix = call.data.split("_")[1]
    db.delete_country(prefix)
    bot.answer_callback_query(call.id, "✅ تم حذف الدولة بنجاح")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text(
        "*📢 إذاعة*\n\nأرسل الرسالة التي تريد إرسالها لجميع المستخدمين:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = db.get_all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.02)
        except:
            pass
    bot.send_message(
        message.chat.id,
        f"✅ *تم الإرسال بنجاح*\n\n👥 عدد المستخدمين: `{cnt}`\n📊 النسبة: `{(cnt/len(users)*100):.1f}%`" if users else "لا يوجد مستخدمين",
        parse_mode="Markdown"
    )
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    rows = db.conn.cursor().execute(
        "SELECT user_id, username, first_name, total_requests, total_otps FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 20"
    ).fetchall()
    
    if not rows:
        msg = "👤 لا يوجد مستخدمون بعد."
    else:
        msg = "*👥 آخر 20 مستخدم:*\n\n"
        for uid, uname, fname, reqs, otps in rows:
            name = f"@{uname}" if uname else fname or str(uid)
            msg += f"• `{uid}` - {name} | 📱`{reqs}` 🔑`{otps}`\n"
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "bot_stats" and c.from_user.id in ADMIN_IDS)
def bot_stats(call):
    total_users = len(db.get_all_users())
    active_numbers = len(db.get_all_active())
    total_otps = db.get_total_otps()
    api_stats = api.get_stats()
    countries_count = len(db.get_countries())
    
    msg = (
        "*📊 إحصائيات البوت*\n\n"
        f"👥 *المستخدمين:* `{total_users}`\n"
        f"📱 *الأرقام النشطة:* `{active_numbers}`\n"
        f"🔑 *إجمالي الأكواد:* `{total_otps}`\n"
        f"🌍 *الدول:* `{countries_count}`\n\n"
        f"*📡 حالة API:*\n"
        f"✅ ناجح: `{api_stats.get('success', 0)}`\n"
        f"❌ فشل: `{api_stats.get('failed', 0)}`\n"
        f"⏰ timeout: `{api_stats.get('timeout', 0)}`\n"
    )
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "report_btn" and c.from_user.id in ADMIN_IDS)
def report_btn(call):
    import tempfile
    filename = f"Taker_OTP_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("TAKER OTP BOT - تقرير شامل\n")
        f.write(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("👥 المستخدمين:\n")
        f.write("-" * 40 + "\n")
        users = db.conn.cursor().execute("SELECT user_id, username, first_name, total_requests, total_otps FROM users").fetchall()
        for u in users:
            f.write(f"ID: {u[0]} | @{u[1] or 'N/A'} | {u[2] or 'N/A'} | طلبات: {u[3]} | أكواد: {u[4]}\n")
        
        f.write("\n📱 الأرقام النشطة:\n")
        f.write("-" * 40 + "\n")
        active = db.conn.cursor().execute("SELECT number, prefix, assigned_to FROM active_numbers WHERE status='waiting'").fetchall()
        for a in active:
            f.write(f"رقم: {a[0]} | دولة: {a[1]} | مستخدم: {a[2]}\n")
        
        f.write(f"\n📊 إجمالي الأكواد: {db.get_total_otps()}\n")
    
    with open(filepath, 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption="📄 *تقرير البوت الشامل*", parse_mode="Markdown")
    
    try:
        os.remove(filepath)
    except:
        pass
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"] and c.from_user.id in ADMIN_IDS)
def ban_unban_prompt(call):
    action = "ban" if call.data == "ban" else "unban"
    user_states[call.from_user.id] = action
    txt = "*🚫 حظر*\nأرسل ID المستخدم:" if action == "ban" else "*✅ فك حظر*\nأرسل ID المستخدم:"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    action = user_states[message.from_user.id]
    try:
        uid = int(message.text)
        is_ban = 1 if action == "ban" else 0
        db.conn.cursor().execute("UPDATE users SET is_banned=? WHERE user_id=?", (is_ban, uid))
        db.conn.commit()
        action_name = "حظر" if action == "ban" else "فك حظر"
        bot.send_message(message.chat.id, f"✅ *تم {action_name}* `{uid}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ معرف غير صحيح")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    channels = db.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(
        types.InlineKeyboardButton("➕ إضافة قناة", callback_data="addch"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    )
    bot.edit_message_text(
        "*🔗 قنوات الاشتراك الإجباري*",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text(
        "*➕ إضافة قناة*\nأرسل رابط القناة:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    url = message.text.strip()
    user_states[message.from_user.id] = ("addch_desc", url)
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    db.conn.commit()
    bot.send_message(message.chat.id, "✅ *تمت إضافة القناة بنجاح*", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    db.conn.cursor().execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    db.conn.commit()
    force_sub_menu(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text(
        "*🖼️ صورة الترحيب*\nأرسل الصورة التي تريد تعيينها:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ *تم حفظ صورة الترحيب بنجاح*", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    c = db.conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات بنجاح")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ═══════════════════════════════════════════════════════════════════
# OTP LOOP - ULTRA FAST
# ═══════════════════════════════════════════════════════════════════
def process_single_otp(alloc_id, number, prefix, uid):
    """معالجة رقم OTP واحد"""
    try:
        status, otp = api.check_otp(number)
        
        if status == "success" and otp:
            service = detect_service(otp)
            ic = SERVICE_ICONS.get(service, "🔐")
            countries = db.get_countries()
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            code = format_code(otp)
            
            logger.info(f"🎯 كود جديد: {number} -> {otp} ({service})")
            
            # إرسال للمستخدم
            if uid:
                try:
                    user_msg = (
                        f"*{_('otp_received_title', uid)}*\n\n"
                        f"📞 *{_('number_label', uid)}:* `+{number}`\n"
                        f"🌍 *{_('country_label', uid)}:* {flag} {name}\n"
                        f"{ic} *{_('app_label', uid)}:* {service}\n"
                        f"🔢 *{_('code_label', uid)}:* `{code}`\n\n"
                        f"{_('copy_instruction', uid)}"
                    )
                    bot.send_message(uid, user_msg, parse_mode="Markdown")
                    logger.info(f"✅ أرسل للمستخدم {uid}")
                except Exception as e:
                    logger.error(f"❌ فشل إرسال للمستخدم {uid}: {e}")
            
            # إرسال للجروب
            for cid in CHAT_IDS:
                for attempt in range(3):
                    try:
                        masked = mask_number(number)
                        group_msg = (
                            f"*🔐 كود جديد - Taker OTP*\n\n"
                            f"🌍 {flag} {name} | {ic} {service}\n"
                            f"📞 `{masked}`\n"
                            f"🔢 `{code}`"
                        )
                        sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                        logger.info(f"✅ أرسل للجروب {cid}")
                        
                        # ════════════════ حذف بعد نصف ساعة ════════════════
                        threading.Thread(
                            target=lambda: (
                                time.sleep(DELETE_AFTER),
                                bot.delete_message(cid, sent.message_id)
                            ),
                            daemon=True
                        ).start()
                        break
                    except Exception as e:
                        logger.error(f"❌ محاولة {attempt+1} فشلت للجروب {cid}: {e}")
                        time.sleep(1)
            
            # تحديث قاعدة البيانات
            db.save_otp(alloc_id, otp, service, uid)
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)
        
        elif status == "expired":
            logger.info(f"⏰ انتهت صلاحية الرقم {number}")
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)
    
    except Exception as e:
        logger.error(f"خطأ في معالجة {number}: {e}")

def otp_loop():
    """حلقة فحص OTP الرئيسية"""
    logger.info("🔄 بدء حلقة فحص OTP...")
    logger.info(f"⏱️ مدة حذف رسائل الجروب: {DELETE_AFTER} ثانية ({DELETE_AFTER/60} دقيقة)")
    
    while True:
        try:
            active_numbers = db.get_all_active()
            
            if active_numbers:
                logger.info(f"🔍 جاري فحص {len(active_numbers)} رقم نشط...")
                
                # معالجة متوازية
                futures = []
                for alloc_id, number, prefix, uid in active_numbers:
                    futures.append(executor.submit(process_single_otp, alloc_id, number, prefix, uid))
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"خطأ في حلقة OTP: {e}")
        
        time.sleep(OTP_CHECK_INTERVAL)

# ═══════════════════════════════════════════════════════════════════
# FLASK WEB SERVER
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taker OTP Bot - Mega v7.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        h1 {
            font-size: 3em;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        .status { color: #00ff88; font-size: 1.2em; margin: 10px 0; }
        .info { color: #888; margin: 5px 0; }
        .version { color: #ff6b6b; font-weight: bold; }
        .badge {
            display: inline-block;
            padding: 8px 16px;
            background: rgba(0,210,255,0.2);
            border: 1px solid #00d2ff;
            border-radius: 20px;
            margin: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ TAKER OTP BOT ⚡</h1>
        <p class="version">MEGA ULTIMATE v7.0</p>
        <p class="status">🟢 System Online</p>
        <p class="info">API: xwdsms.org | Full Integration</p>
        <p class="info">Languages: العربية & English</p>
        <p class="info">Python: {{ python_ver }} | OS: {{ os_name }}</p>
        <div style="margin-top: 20px;">
            <span class="badge">🚀 High Performance</span>
            <span class="badge">🔐 Secure</span>
            <span class="badge">🌍 50+ Countries</span>
            <span class="badge">⚡ Fast</span>
        </div>
        <p class="info" style="margin-top: 20px;">Developer: @hackerTaker</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(
        HTML_TEMPLATE,
        python_ver=SYSTEM_INFO['python'],
        os_name=SYSTEM_INFO['os']
    )

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "version": "7.0",
        "uptime": str(datetime.now()),
        "system": SYSTEM_INFO
    }), 200

@app.route('/api/v1/get-number', methods=['POST'])
def flask_get_number():
    try:
        data = flask_request.get_json()
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        resp = requests.post(f"{BASE_URL}/api/v1/get-number",
                           json={"range": data.get("range", "")},
                           headers=headers, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/check-otp', methods=['GET'])
def flask_check_otp():
    try:
        number = flask_request.args.get("number", "")
        headers = {"x-api-key": API_KEY}
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp",
                          params={"number": number}, headers=headers, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/balance', methods=['GET'])
def flask_balance():
    try:
        headers = {"x-api-key": API_KEY}
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"balance": "0"}), 500

def run_web():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Flask Web Server running on port {port}")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)

# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ████████╗ █████╗ ██╗  ██╗███████╗██████╗                    ║
║     ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗                   ║
║        ██║   ███████║█████╔╝ █████╗  ██████╔╝                   ║
║        ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗                   ║
║        ██║   ██║  ██║██║  ██╗███████╗██║  ██║                   ║
║        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                   ║
║                                                                  ║
║              TAKER OTP BOT - MEGA ULTIMATE v7.0                  ║
║              Developer: @hackerTaker                             ║
║              API: xwdsms.org                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("=" * 60)
    logger.info("🚀 TAKER OTP BOT v7.0 MEGA ULTIMATE")
    logger.info(f"📱 Bot Token: {BOT_TOKEN[:15]}...")
    logger.info(f"🔑 API Key: {API_KEY[:15]}...")
    logger.info(f"📢 Groups: {CHAT_IDS}")
    logger.info(f"👑 Admins: {ADMIN_IDS}")
    logger.info(f"⏱️  Delete OTP messages after: {DELETE_AFTER}s ({DELETE_AFTER/60:.1f} minutes)")
    logger.info(f"🔧 Workers: {MAX_WORKERS}")
    logger.info(f"⏰ OTP Check Interval: {OTP_CHECK_INTERVAL}s")
    logger.info(f"💾 Database: {DB_PATH}")
    logger.info(f"🐍 Python: {SYSTEM_INFO['python']}")
    logger.info(f"💻 OS: {SYSTEM_INFO['os']}")
    logger.info("=" * 60)
    
    # تشغيل Flask
    threading.Thread(target=run_web, daemon=True, name="Flask-Web").start()
    
    # تشغيل OTP Loop
    threading.Thread(target=otp_loop, daemon=True, name="OTP-Loop").start()
    
    logger.info("✅ جميع الخدمات تعمل...")
    logger.info("🚀 البوت جاهز للاستقبال...")
    
    # تشغيل البوت
    while True:
        try:
            bot.infinity_polling(
                timeout=POLLING_TIMEOUT,
                long_polling_timeout=LONG_POLLING_TIMEOUT,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(2)

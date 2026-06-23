# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════╗
 ║       TAKER OTP BOT - Ultimate Edition      ║
 ║       Developer: @hackerTaker               ║
 ║       API: xwdsms.org (Full Integration)     ║
 ║       Bilingual: AR/EN Support Added        ║
 ╚══════════════════════════════════════════════╝
"""
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات الأساسية ════════════════
BOT_TOKEN = "8686995713:AAGVKoSpcbn6d2OwzvMfqOzI5LDUeO5eHqs"
API_KEY = "97257ac6fe5efd03c28b43af34a887b3"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_final.db"
DELETE_AFTER = 180  # حذف رسائل الجروب بعد 3 دقائق

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ قاموس الترجمة ثنائي اللغة ════════════════
TRANSLATIONS = {
    "welcome_title": {"ar": "✨ أهلاً بك في بوت Taker OTP", "en": "✨ Welcome to Taker OTP Bot"},
    "welcome_desc": {
        "ar": "• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n• ادعُ أصدقاءك واربح رصيداً",
        "en": "• Choose the service you want\n• Then choose the country\n• Receive OTP instantly\n• Invite friends and earn credit"
    },
    "choose_service": {"ar": "اختر الخدمة:", "en": "Choose service:"},
    "choose_country": {"ar": "اختر الدولة لخدمة {}", "en": "Choose country for {}"},
    "new_number": {"ar": "✅ تم تخصيص رقم جديد", "en": "✅ New number allocated"},
    "number": {"ar": "الرقم", "en": "Number"},
    "country": {"ar": "الدولة", "en": "Country"},
    "service": {"ar": "الخدمة", "en": "Service"},
    "time": {"ar": "الوقت", "en": "Time"},
    "status_waiting": {"ar": "في انتظار رمز التفعيل", "en": "Waiting for OTP"},
    "change_number": {"ar": "🔄 تغيير الرقم", "en": "🔄 Change number"},
    "change_country": {"ar": "🌍 تغيير الدولة", "en": "🌍 Change country"},
    "otp_channel": {"ar": "📞 قناة الأكواد", "en": "📞 OTP Channel"},
    "back": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "maintenance": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", "en": "⚠️ *Bot under maintenance*\nPlease try again later."},
    "force_sub": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "sub_btn": {"ar": "📢 اشترك في القناة", "en": "📢 Subscribe to channel"},
    "check_sub_btn": {"ar": "✅ تحقق من الاشتراك", "en": "✅ Check subscription"},
    "check_sub_ok": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_sub_fail": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ Not subscribed to all channels"},
    "otp_received": {"ar": "🔐 تم استقبال رمز التفعيل", "en": "🔐 OTP Received"},
    "app": {"ar": "التطبيق", "en": "Application"},
    "code": {"ar": "الكود", "en": "Code"},
    "copy_code": {"ar": "انسخ الكود واستخدمه فوراً", "en": "Copy the code and use it immediately"},
    "new_code_group": {"ar": "🔐 كود جديد", "en": "🔐 New Code"},
    "countries_services": {"ar": "🌍 الدول والخدمات المتاحة:", "en": "🌍 Available countries & services:"},
    "services_count": {"ar": "الخدمات", "en": "Services"},
    "my_stats": {"ar": "📊 إحصائياتك", "en": "📊 Your Statistics"},
    "total_requests": {"ar": "إجمالي الطلبات", "en": "Total Requests"},
    "otps_received": {"ar": "الأكواد المستلمة", "en": "OTPs Received"},
    "first_use": {"ar": "أول استخدام", "en": "First Use"},
    "last_use": {"ar": "آخر استخدام", "en": "Last Use"},
    "my_balance": {"ar": "💰 رصيدك", "en": "💰 Your Balance"},
    "your_balance": {"ar": "رصيدك", "en": "Your Balance"},
    "referrals": {"ar": "الإحالات", "en": "Referrals"},
    "site_balance": {"ar": "رصيد الموقع", "en": "Site Balance"},
    "min_withdraw": {"ar": "الحد الأدنى للسحب", "en": "Min Withdrawal"},
    "earn_tip": {"ar": "💡 *اربح `0.05 USDT` عن كل صديق تدعوه*", "en": "💡 *Earn `0.05 USDT` per friend you invite*"},
    "invite_friends": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "your_link": {"ar": "🔗 *رابط الدعوة الخاص بك:*\n`{}`", "en": "🔗 *Your invite link:*\n`{}`"},
    "share_link": {"ar": "📤 *شارك الرابط مع أصدقائك*", "en": "📤 *Share the link with your friends*"},
    "traffic": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "no_active_numbers": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers currently."},
    "active_numbers": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "unknown": {"ar": "غير معروف", "en": "Unknown"},
    "get_number_btn": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries_btn": {"ar": "🌍 الدول المتاحة", "en": "🌍 Countries"},
    "stats_btn": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance_btn": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite_btn": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite"},
    "traffic_btn": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "admin_btn": {"ar": "⚙️ لوحة التحكم", "en": "⚙️ Admin Panel"},
    "use_buttons": {"ar": "استخدم الأزرار أدناه للتنقل:", "en": "Use the buttons below to navigate:"},
    "change_number_title": {"ar": "🔄 تم تغيير الرقم", "en": "🔄 Number Changed"},
    "new_number_msg": {"ar": "الرقم الجديد", "en": "New Number"},
    "language_changed": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to English"},
    "lang_btn_ar": {"ar": "🌐 English", "en": "🌐 English"},
    "lang_btn_en": {"ar": "🌐 العربية", "en": "🌐 العربية"},
    "back_to_services": {"ar": "↩️ رجوع للخدمات", "en": "↩️ Back to services"},
    "no_country": {"ar": "هذه الدولة غير متوفرة حالياً", "en": "This country is currently unavailable"},
    "api_error": {"ar": "خطأ في الاتصال", "en": "Connection error"},
    "general_error": {"ar": "خطأ: {}", "en": "Error: {}"},
    "admin_header": {"ar": "⚙️ لوحة التحكم\n\nمرحباً بك في لوحة إدارة البوت.", "en": "⚙️ Admin Panel\n\nWelcome to the bot admin panel."},
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
    "admin_force_sub": {"ar": "🔗 الاشتراك", "en": "🔗 Force Sub"},
    "admin_photo": {"ar": "🖼️ صورة الترحيب", "en": "🖼️ Welcome Photo"},
    "admin_clear": {"ar": "🗑️ مسح البيانات", "en": "🗑️ Clear Data"},
    "admin_exit": {"ar": "↩️ خروج", "en": "↩️ Exit"},
    "bot_status": {"ar": "حالة البوت: {}", "en": "Bot status: {}"},
    "lang_select_title": {
        "ar": "🌐 *اختر لغتك / Choose your language*",
        "en": "🌐 *اختر لغتك / Choose your language*"
    },
    "lang_selected_ar": {"ar": "✅ *تم تعيين اللغة العربية بنجاح*\n\nأهلاً بك في بوت Taker OTP!", "en": "✅ *Language set to Arabic successfully*\n\nWelcome to Taker OTP Bot!"},
    "lang_selected_en": {"ar": "✅ *Language set to English successfully*\n\nWelcome to Taker OTP Bot!", "en": "✅ *Language set to English successfully*\n\nWelcome to Taker OTP Bot!"},
}


def get_lang(uid):
    """جلب لغة المستخدم من قاعدة البيانات - ترجع None إذا لم يختر بعد"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (f"lang_{uid}",))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None


def set_lang(uid, lang):
    """حفظ لغة المستخدم في قاعدة البيانات"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO settings VALUES (?,?)", (f"lang_{uid}", lang))
        conn.commit()
        conn.close()
    except:
        pass


def _(key, uid=None, **kwargs):
    """دالة الترجمة - ترجع النص المناسب حسب لغة المستخدم"""
    if uid:
        lang = get_lang(uid)
    else:
        lang = "ar"
    # إذا لم يختر لغة بعد، نعرض العربية افتراضياً
    if lang is None:
        lang = "ar"
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
    """كيبورد اختيار اللغة الإجباري"""
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    return mk


# ════════════════ الخدمات الافتراضية ════════════════
DEFAULT_SERVICES = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "ar": "واتساب"},
    "facebook": {"name": "Facebook", "icon": "📘", "ar": "فيسبوك"},
    "instagram": {"name": "Instagram", "icon": "📷", "ar": "انستغرام"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "ar": "تيك توك"},
    "telegram": {"name": "Telegram", "icon": "✈️", "ar": "تيليجرام"},
    "imo": {"name": "IMO", "icon": "📞", "ar": "ايمو"},
    "snapchat": {"name": "Snapchat", "icon": "👻", "ar": "سناب شات"},
    "google": {"name": "Google", "icon": "🔍", "ar": "جوجل"},
    "twitter": {"name": "Twitter/X", "icon": "🐦", "ar": "تويتر"},
    "discord": {"name": "Discord", "icon": "🎮", "ar": "ديسكورد"},
    "amazon": {"name": "Amazon", "icon": "📦", "ar": "امازون"},
    "apple": {"name": "Apple", "icon": "🍎", "ar": "ابل"},
    "microsoft": {"name": "Microsoft", "icon": "🪟", "ar": "مايكروسوفت"},
    "uber": {"name": "Uber", "icon": "🚗", "ar": "اوبر"},
    "netflix": {"name": "Netflix", "icon": "🎬", "ar": "نتفلكس"},
    "youtube": {"name": "YouTube", "icon": "▶️", "ar": "يوتيوب"},
    "all": {"name": "All Services", "icon": "🌐", "ar": "كل الخدمات"},
}

# ════════════════ الدول الافتراضية ════════════════
DEFAULT_COUNTRIES = {
    "22501": "ساحل العاج",
    "23276": "سيراليون",
    "26134": "مدغشقر",
    "44740": "المملكة المتحدة",
    "23490": "نيجيريا",
    "25471": "كينيا",
    "24910": "السودان",
    "49155": "ألمانيا",
    "23762": "الكاميرون",
    "22178": "السنغال",
    "22901": "بنين",
    "22898": "توجو",
}

COUNTRY_FLAGS = {
    "225": "🇨🇮", "232": "🇸🇱", "261": "🇲🇬", "44": "🇬🇧", "234": "🇳🇬",
    "254": "🇰🇪", "249": "🇸🇩", "49": "🇩🇪", "237": "🇨🇲", "221": "🇸🇳",
    "229": "🇧🇯", "228": "🇹🇬",
}

def get_flag(prefix):
    for code, flag in COUNTRY_FLAGS.items():
        if prefix.startswith(code): return flag
    return "🌍"

# ════════════════ API Functions ════════════════
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=10)
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
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=8)
        data = resp.json()
        if data.get("success"):
            return data.get("status"), data.get("otp"), data.get("message", "")
        return None, None, ""
    except:
        return None, None, ""

def api_delete_number(alloc_id):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=5)
        return True
    except:
        return False

def api_get_balance():
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return resp.json().get("balance", "0")
    except:
        return "0"

# ════════════════ قاعدة البيانات ════════════════
def get_db():
    """الحصول على اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
        service TEXT, assigned_to INTEGER, created_at TEXT,
        status TEXT DEFAULT 'waiting', otp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
        otp TEXT, service TEXT, full_message TEXT,
        timestamp TEXT, assigned_to INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE,
        ref_count INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_url TEXT UNIQUE, description TEXT,
        enabled INTEGER DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS custom_countries (
        prefix TEXT PRIMARY KEY, name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS custom_services (
        service_key TEXT PRIMARY KEY, name TEXT, icon TEXT, ar_name TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
    
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
    
    for key, data in DEFAULT_SERVICES.items():
        c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)",
                  (key, data['name'], data['icon'], data['ar']))
    
    conn.commit()
    conn.close()

init_db()

# ════════════════ دوال قاعدة البيانات ════════════════
def get_setting(key):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_all_countries():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT prefix, name FROM custom_countries ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (prefix, name))
    conn.commit()
    conn.close()

def delete_country(prefix):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()

def get_all_services():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT service_key, name, icon, ar_name FROM custom_services ORDER BY ar_name")
    rows = c.fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row[0]] = {"name": row[1], "icon": row[2], "ar": row[3]}
    return result

def add_service(key, name, icon, ar_name):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
    conn.commit()
    conn.close()

def delete_service(key):
    if key == "all": return
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (key,))
    conn.commit()
    conn.close()

# ════════════════ دوال مساعدة ════════════════
def save_user(message):
    uid = message.from_user.id
    now = datetime.now().isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                  (uid, message.from_user.username, message.from_user.first_name, message.from_user.last_name, now, now))
    else:
        c.execute("UPDATE users SET username=?, first_name=?, last_name=?, last_seen=? WHERE user_id=?",
                  (message.from_user.username, message.from_user.first_name, message.from_user.last_name, now, uid))
    conn.commit()
    conn.close()

def is_banned(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def get_all_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def release_user_number(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    for (aid,) in c.fetchall():
        try: api_delete_number(aid)
        except: pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    conn.commit()
    conn.close()

def assign_number(uid, alloc_id, number, prefix, service):
    release_user_number(uid)
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at, status) VALUES (?,?,?,?,?,?,?)",
              (alloc_id, number, prefix, service, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_all_active():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, service, assigned_to FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0, None, None)

def get_user_balance(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()
    c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
    refs = c.fetchone()
    conn.close()
    return (bal[0] if bal else 0), (refs[0] if refs else 0)

def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
    conn.commit()
    conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

def process_referral(ref_code, new_uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
        c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (row[0],))
    conn.commit()
    conn.close()

def clean(n): return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    t = str(text).lower()
    if not t: return "OTP"
    if "whatsapp" in t or "واتساب" in t or "واتس" in t: return "WhatsApp"
    if "telegram" in t or "تيليجرام" in t or "تليجرام" in t: return "Telegram"
    if "facebook" in t or "فيسبوك" in t or "fb" in t: return "Facebook"
    if "instagram" in t or "انستقرام" in t or "انستغرام" in t or "انستا" in t: return "Instagram"
    if "tiktok" in t or "تيك توك" in t: return "TikTok"
    if "imo" in t: return "IMO"
    if "snapchat" in t or "سناب" in t: return "Snapchat"
    if "google" in t or "gmail" in t or "جوجل" in t: return "Google"
    if "twitter" in t or "تويتر" in t or "x.com" in t: return "Twitter/X"
    if "discord" in t or "ديسكورد" in t: return "Discord"
    if "amazon" in t or "امازون" in t: return "Amazon"
    if "apple" in t or "ابل" in t or "icloud" in t: return "Apple"
    if "microsoft" in t or "مايكروسوفت" in t: return "Microsoft"
    if "uber" in t or "اوبر" in t: return "Uber"
    if "netflix" in t or "نتفلكس" in t: return "Netflix"
    if "youtube" in t or "يوتيوب" in t: return "YouTube"
    return "OTP"

ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "TikTok": "🎵", "IMO": "📞", "Snapchat": "👻", "Google": "🔍",
    "Twitter/X": "🐦", "Discord": "🎮", "Amazon": "📦", "Apple": "🍎",
    "Microsoft": "🪟", "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️", "OTP": "🔐"
}

def format_time(iso_str, uid=None):
    if not iso_str: return _("unknown", uid)
    try: return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M")
    except: return iso_str

def check_subscription(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels: return True
    for (url,) in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch, uid).status not in ["member", "administrator", "creator"]:
                return False
        except: return False
    return True

def sub_markup(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels: return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(
            _("sub_btn", uid), url=url
        ))
    mk.add(types.InlineKeyboardButton(
        _("check_sub_btn", uid), callback_data="check_sub"
    ))
    return mk

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton(_("get_number_btn", uid)),
        types.KeyboardButton(_("countries_btn", uid)),
        types.KeyboardButton(_("stats_btn", uid))
    )
    kb.add(
        types.KeyboardButton(_("balance_btn", uid)),
        types.KeyboardButton(_("invite_btn", uid)),
        types.KeyboardButton(_("traffic_btn", uid))
    )
    # زر تغيير اللغة
    lang = get_lang(uid)
    if lang == "ar":
        lang_btn_text = "🌐 English"
    else:
        lang_btn_text = "🌐 العربية"
    kb.add(types.KeyboardButton(lang_btn_text))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(_("admin_btn", uid)))
    return kb

def services_menu(uid):
    """قائمة الخدمات مع أيقونات"""
    services = get_all_services()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    lang = get_lang(uid)
    for key, data in services.items():
        if key != "all":
            display_name = data['ar'] if lang == "ar" else data['name']
            buttons.append(types.InlineKeyboardButton(
                f"{data['icon']} {display_name}", callback_data=f"svc_{key}"))
    if "all" in services:
        display_name = services['all']['ar'] if lang == "ar" else services['all']['name']
        buttons.append(types.InlineKeyboardButton(
            f"{services['all']['icon']} {display_name}", callback_data="svc_all"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup

def countries_for_service(service_key, uid):
    """عرض الدول المتاحة لخدمة معينة"""
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for prefix, name in sorted(countries.items()):
        flag = get_flag(prefix)
        buttons.append(types.InlineKeyboardButton(
            f"{flag} {name}", callback_data=f"get_{prefix}_{service_key}"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    markup.row(types.InlineKeyboardButton(
        _("back_to_services", uid), callback_data="menu_services"))
    return markup

def number_actions(prefix, service_key, alloc_id, uid):
    """أزرار التحكم بعد الحصول على رقم"""
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(_("change_number", uid), callback_data=f"change_{prefix}_{service_key}_{alloc_id}"),
        types.InlineKeyboardButton(_("change_country", uid), callback_data=f"svc_{service_key}")
    )
    mk.row(
        types.InlineKeyboardButton(_("otp_channel", uid), url="https://t.me/numhj"),
        types.InlineKeyboardButton(_("back", uid), callback_data="main_menu")
    )
    return mk

def show_home(cid, uid):
    """عرض الصفحة الرئيسية"""
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, _("maintenance", uid), parse_mode="Markdown")
        return
    
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, _("force_sub", uid), parse_mode="Markdown", reply_markup=mk)
        return
    
    photo = get_setting("welcome_photo")
    welcome_title = _("welcome_title", uid)
    welcome_desc = _("welcome_desc", uid)
    txt = f"*{welcome_title}*\n\n{welcome_desc}\n\n*{_('choose_service', uid)}*"
    
    mk = services_menu(uid)
    
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    bot.send_message(cid, _("use_buttons", uid), reply_markup=main_keyboard(uid))

# ════════════════ أوامر البوت ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    save_user(message)
    
    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    
    # ═════ التحقق من اللغة أولاً ═════
    current_lang = get_lang(uid)
    
    if current_lang is None:
        # المستخدم جديد - إجباره على اختيار اللغة
        bot.send_message(
            cid,
            "🌐 *اختر لغتك / Choose your language*\n\n"
            "يرجى اختيار اللغة للمتابعة\n"
            "Please choose your language to continue",
            parse_mode="Markdown",
            reply_markup=lang_selection_keyboard()
        )
        return
    
    # المستخدم لديه لغة - انتقل للرئيسية
    show_home(cid, uid)


# ════════════════ كول باك اختيار اللغة ════════════════
@bot.callback_query_handler(func=lambda c: c.data in ["set_lang_ar", "set_lang_en"])
def set_language_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = "ar" if call.data == "set_lang_ar" else "en"
    
    set_lang(uid, lang)
    
    if lang == "ar":
        msg = "✅ *تم تعيين اللغة العربية بنجاح*\n\nأهلاً بك في بوت Taker OTP!"
    else:
        msg = "✅ *Language set to English successfully*\n\nWelcome to Taker OTP Bot!"
    
    bot.edit_message_text(msg, cid, call.message.message_id, parse_mode="Markdown")
    
    # الآن نعرض الواجهة الرئيسية
    show_home(cid, uid)


@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, _("check_sub_ok", uid))
        show_home(call.message.chat.id, uid)
    else:
        bot.answer_callback_query(call.id, _("check_sub_fail", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    """اختيار خدمة وعرض الدول"""
    uid = call.from_user.id
    service_key = call.data.split("_", 1)[1]
    services = get_all_services()
    lang = get_lang(uid)
    display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
    
    choose_text = _("choose_country", uid)
    bot.edit_message_text(
        f"*{choose_text.replace('{}', display_name)}:*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=countries_for_service(service_key, uid)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    """جلب رقم واحد فقط للمستخدم"""
    uid = call.from_user.id
    parts = call.data.split("_", 2)
    prefix = parts[1]
    service_key = parts[2] if len(parts) > 2 else "all"
    
    release_user_number(uid)
    
    try:
        alloc_id, number = api_get_number(prefix)
        number = clean(number)
        assign_number(uid, alloc_id, number, prefix, service_key)
        
        countries = get_all_countries()
        services = get_all_services()
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        lang = get_lang(uid)
        display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
        now = datetime.now().strftime("%H:%M")
        
        msg = (
            f"*{_('new_number', uid)}*\n\n"
            f"📞 *{_('number', uid)}:* `+{number}`\n"
            f"🌍 *{_('country', uid)}:* {flag} {name}\n"
            f"🛠 *{_('service', uid)}:* {display_name}\n"
            f"🕒 *{_('time', uid)}:* {now}\n"
            f"⏳ *{_('status_waiting', uid)}*"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        error_msg = str(e)
        if "غير متوفرة" in error_msg or "unavailable" in error_msg.lower():
            alert = _("no_country", uid)
        else:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
        bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    """تغيير الرقم الحالي"""
    uid = call.from_user.id
    parts = call.data.split("_", 3)
    prefix = parts[1]
    service_key = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    if old_alloc:
        api_delete_number(old_alloc)
        conn = get_db()
        conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (old_alloc,))
        conn.commit()
        conn.close()
    
    release_user_number(uid)
    
    try:
        alloc_id, number = api_get_number(prefix)
        number = clean(number)
        assign_number(uid, alloc_id, number, prefix, service_key)
        
        countries = get_all_countries()
        services = get_all_services()
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        lang = get_lang(uid)
        display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
        now = datetime.now().strftime("%H:%M")
        
        msg = (
            f"*{_('change_number_title', uid)}*\n\n"
            f"📞 *{_('new_number_msg', uid)}:* `+{number}`\n"
            f"🌍 *{_('country', uid)}:* {flag} {name}\n"
            f"🛠 *{_('service', uid)}:* {display_name}\n"
            f"🕒 *{_('time', uid)}:* {now}\n"
            f"⏳ *{_('status_waiting', uid)}*"
        )
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        alert = _("general_error", uid).replace("{}", str(e)[:100])
        bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    if call.data == "menu_services":
        bot.edit_message_text(
            f"*{_('choose_service', uid)}*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=services_menu(uid)
        )
    else:
        show_home(call.message.chat.id, uid)

# ════════════════ الكيبورد السفلي - Handler واحد بدون تعارض ════════════════
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_all_text(message):
    """
    Handler رئيسي واحد لكل النصوص - يمنع التكرار والتعارض
    """
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text.strip() if message.text else ""
    
    # تجاهل الرسائل الفارغة
    if not text:
        return
    
    # ══════ أزرار القائمة السفلية ══════
    # نبني قاموس الأزرار حسب لغة المستخدم الحالية
    lang = get_lang(uid) or "ar"
    
    # أزرار القائمة الرئيسية
    btn_get = TRANSLATIONS["get_number_btn"][lang]
    btn_countries = TRANSLATIONS["countries_btn"][lang]
    btn_stats = TRANSLATIONS["stats_btn"][lang]
    btn_balance = TRANSLATIONS["balance_btn"][lang]
    btn_invite = TRANSLATIONS["invite_btn"][lang]
    btn_traffic = TRANSLATIONS["traffic_btn"][lang]
    btn_admin = TRANSLATIONS["admin_btn"][lang]
    btn_lang_ar = "🌐 English"  # الزر المعروض للمستخدم العربي
    btn_lang_en = "🌐 العربية"   # الزر المعروض للمستخدم الإنجليزي
    
    # ══════ 1. زر الحصول على رقم ══════
    if text in [TRANSLATIONS["get_number_btn"]["ar"], TRANSLATIONS["get_number_btn"]["en"]]:
        bot.send_message(cid, f"*{_('choose_service', uid)}*", parse_mode="Markdown", reply_markup=services_menu(uid))
        return
    
    # ══════ 2. زر الدول ══════
    if text in [TRANSLATIONS["countries_btn"]["ar"], TRANSLATIONS["countries_btn"]["en"]]:
        countries = get_all_countries()
        services = get_all_services()
        txt = f"*{_('countries_services', uid)}*\n\n"
        for prefix, name in sorted(countries.items()):
            flag = get_flag(prefix)
            txt += f"• {flag} `{prefix}` - {name}\n"
        txt += f"\n*{_('services_count', uid)}:* {len(services)}"
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # ══════ 3. زر الإحصائيات ══════
    if text in [TRANSLATIONS["stats_btn"]["ar"], TRANSLATIONS["stats_btn"]["en"]]:
        requests, otps, first, last = get_user_stats(uid)
        msg = (
            f"*{_('my_stats', uid)}*\n\n"
            f"🔷 *{_('total_requests', uid)}:* `{requests}`\n"
            f"🔷 *{_('otps_received', uid)}:* `{otps}`\n"
            f"🔷 *{_('first_use', uid)}:* `{format_time(first, uid)}`\n"
            f"🔷 *{_('last_use', uid)}:* `{format_time(last, uid)}`"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # ══════ 4. زر الرصيد ══════
    if text in [TRANSLATIONS["balance_btn"]["ar"], TRANSLATIONS["balance_btn"]["en"]]:
        bal, refs = get_user_balance(uid)
        site_bal = api_get_balance()
        msg = (
            f"*{_('my_balance', uid)}*\n\n"
            f"💎 *{_('your_balance', uid)}:* `{bal:.3f} USDT`\n"
            f"👤 *{_('referrals', uid)}:* `{refs}`\n"
            f"🏦 *{_('site_balance', uid)}:* `{site_bal}`\n"
            f"🏦 *{_('min_withdraw', uid)}:* `18.0 USDT`\n\n"
            f"{_('earn_tip', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # ══════ 5. زر الدعوة ══════
    if text in [TRANSLATIONS["invite_btn"]["ar"], TRANSLATIONS["invite_btn"]["en"]]:
        link = get_ref_link(uid)
        msg = (
            f"*{_('invite_friends', uid)}*\n\n"
            f"{_('your_link', uid).replace('{}', link)}\n\n"
            f"💰 *{_('earn_tip', uid)}*\n"
            f"{_('share_link', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # ══════ 6. زر حركة المرور ══════
    if text in [TRANSLATIONS["traffic_btn"]["ar"], TRANSLATIONS["traffic_btn"]["en"]]:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT prefix, service, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix, service ORDER BY COUNT(*) DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            txt = f"*{_('active_numbers', uid)}*\n\n{_('no_active_numbers', uid)}"
        else:
            lines = [f"*{_('active_numbers', uid)}*\n"]
            for prefix, svc, cnt in rows:
                flag = get_flag(prefix)
                name = get_all_countries().get(prefix, prefix)
                svc_icon = get_all_services().get(svc, {}).get("icon", "🔐")
                lines.append(f"{flag} {name} {svc_icon}: `{cnt}`")
            txt = "\n".join(lines)
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # ══════ 7. زر تغيير اللغة ══════
    if text in ["🌐 English", "🌐 العربية"]:
        current = get_lang(uid)
        new_lang = "en" if current == "ar" else "ar"
        set_lang(uid, new_lang)
        if new_lang == "ar":
            resp = "✅ تم تغيير اللغة إلى العربية"
        else:
            resp = "✅ Language changed to English"
        bot.send_message(cid, resp, reply_markup=main_keyboard(uid))
        return
    
    # ══════ 8. زر لوحة التحكم ══════
    if text in [TRANSLATIONS["admin_btn"]["ar"], TRANSLATIONS["admin_btn"]["en"]] and uid in ADMIN_IDS:
        admin_panel(message)
        return
    
    # ══════ معالجة حالات الإدخال للإدارة (user_states) ══════
    state = user_states.get(uid)
    
    # إضافة دولة - prefix
    if state == "add_country_prefix":
        prefix = text
        user_states[uid] = ("add_country_name", prefix)
        bot.send_message(cid, "Send country name:")
        return
    
    # إضافة دولة - name
    if isinstance(state, tuple) and state[0] == "add_country_name":
        prefix = state[1]
        name = text
        add_country(prefix, name)
        bot.send_message(cid, f"✅ Added `{name}` ({prefix})", parse_mode="Markdown")
        del user_states[uid]
        return
    
    # إضافة خدمة - key
    if state == "add_service_key":
        key = text.lower()
        user_states[uid] = ("add_service_name", key)
        bot.send_message(cid, "Send service name in English:")
        return
    
    # إضافة خدمة - name
    if isinstance(state, tuple) and state[0] == "add_service_name":
        key = state[1]
        name = text
        user_states[uid] = ("add_service_icon", key, name)
        bot.send_message(cid, "Send icon (one emoji):")
        return
    
    # إضافة خدمة - icon
    if isinstance(state, tuple) and state[0] == "add_service_icon":
        key = state[1]
        name = state[2]
        icon = text
        user_states[uid] = ("add_service_ar", key, name, icon)
        bot.send_message(cid, "Send Arabic name:")
        return
    
    # إضافة خدمة - arabic name
    if isinstance(state, tuple) and state[0] == "add_service_ar":
        key = state[1]
        name = state[2]
        icon = state[3]
        ar_name = text
        add_service(key, name, icon, ar_name)
        bot.send_message(cid, f"✅ Added {icon} {ar_name}", parse_mode="Markdown")
        del user_states[uid]
        return
    
    # إذاعة
    if state == "broadcast":
        users = get_all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.05)
            except:
                pass
        bot.send_message(cid, f"✅ Sent to `{cnt}` users", parse_mode="Markdown")
        del user_states[uid]
        return
    
    # حظر/فك حظر
    if state in ["ban", "unban"]:
        action = state
        try:
            target_uid = int(text)
            conn = get_db()
            conn.cursor().execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (target_uid,))
            conn.commit()
            conn.close()
            action_name = "Banned" if action == "ban" else "Unbanned"
            bot.send_message(cid, f"✅ {action_name} `{target_uid}`", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ Invalid ID")
        del user_states[uid]
        return
    
    # إضافة قناة اشتراك - url
    if state == "addch_url":
        url = text
        user_states[uid] = ("addch_desc", url)
        bot.send_message(cid, "Send description:")
        return
    
    # إضافة قناة اشتراك - desc
    if isinstance(state, tuple) and state[0] == "addch_desc":
        url = state[1]
        desc = text
        conn = get_db()
        conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        conn.commit()
        conn.close()
        bot.send_message(cid, "✅ Added")
        del user_states[uid]
        return
    
    # ══════ لا يوجد تطابق - رسالة افتراضية ══════
    # لا نرسل شيء، فقط نتجاهل

# ════════════════ لوحة الإدارة الكاملة ════════════════
def admin_panel(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = _("admin_open", uid) if get_setting("maintenance") != "1" else _("admin_maint", uid)
    bot_status_text = _("bot_status", uid).replace("{}", status)
    
    markup.add(types.InlineKeyboardButton(bot_status_text, callback_data="toggle_maint"))
    
    markup.add(
        types.InlineKeyboardButton(_("admin_add_country", uid), callback_data="add_country"),
        types.InlineKeyboardButton(_("admin_del_country", uid), callback_data="del_country")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_add_service", uid), callback_data="add_service"),
        types.InlineKeyboardButton(_("admin_del_service", uid), callback_data="del_service")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_broadcast", uid), callback_data="broadcast"),
        types.InlineKeyboardButton(_("admin_users", uid), callback_data="users_list")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_ban", uid), callback_data="ban"),
        types.InlineKeyboardButton(_("admin_unban", uid), callback_data="unban")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_force_sub", uid), callback_data="force_sub"),
        types.InlineKeyboardButton(_("admin_photo", uid), callback_data="set_photo")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_clear", uid), callback_data="clear_data"),
        types.InlineKeyboardButton(_("admin_exit", uid), callback_data="main_menu")
    )
    
    msg = f"*{_('admin_header', uid)}*"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

user_states = {}

# ════════════════ Callbacks لوحة الإدارة ════════════════
@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ Done")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    uid = call.from_user.id
    user_states[uid] = "add_country_prefix"
    bot.edit_message_text(
        "*➕ Add Country*\n\nSend country prefix (e.g. `24910`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        markup.add(types.InlineKeyboardButton(f"{flag} {name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*Delete Country*\nChoose country:", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    prefix = call.data.split("_")[1]
    delete_country(prefix)
    bot.answer_callback_query(call.id, "✅ Deleted")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_service" and c.from_user.id in ADMIN_IDS)
def add_service_start(call):
    uid = call.from_user.id
    user_states[uid] = "add_service_key"
    bot.edit_message_text(
        "*➕ Add Service*\n\nSend service key (e.g. `snapchat`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "del_service" and c.from_user.id in ADMIN_IDS)
def del_service_start(call):
    services = get_all_services()
    markup = types.InlineKeyboardMarkup()
    for key, data in services.items():
        if key != "all":
            markup.add(types.InlineKeyboardButton(f"{data['icon']} {data['ar']}", callback_data=f"delservice_{key}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*Delete Service*\nChoose service:", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delservice_") and c.from_user.id in ADMIN_IDS)
def del_service_confirm(call):
    key = call.data.split("_")[1]
    delete_service(key)
    bot.answer_callback_query(call.id, "✅ Deleted")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    uid = call.from_user.id
    user_states[uid] = "broadcast"
    bot.edit_message_text("*Broadcast*\nSend the message:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"] and c.from_user.id in ADMIN_IDS)
def ban_unban_prompt(call):
    uid = call.from_user.id
    user_states[uid] = call.data
    txt = "*Ban*\nSend user ID:" if call.data == "ban" else "*Unban*\nSend user ID:"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    if not rows:
        msg = "No users yet."
    else:
        msg = "*👥 Last Users:*\n\n"
        for uid, uname, fname in rows:
            name = f"@{uname}" if uname else fname or str(uid)
            msg += f"• `{uid}` - {name}\n"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(
        types.InlineKeyboardButton("➕ Add", callback_data="addch"),
        types.InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    )
    bot.edit_message_text("*🔗 Force Subscription Channels*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    uid = call.from_user.id
    user_states[uid] = "addch_url"
    bot.edit_message_text("*➕ Add Channel*\nSend channel link:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    conn = get_db()
    conn.cursor().execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    force_sub_menu(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    uid = call.from_user.id
    user_states[uid] = "photo"
    bot.edit_message_text("*🖼️ Welcome Photo*\nSend photo:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    uid = message.from_user.id
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ Welcome photo saved")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    conn = get_db()
    c = conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ All data cleared")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            active = get_all_active()
            for alloc_id, number, prefix, service_key, uid in active:
                try:
                    status, otp, raw_msg = api_check_otp(number)
                    
                    if status == "success" and otp:
                        detected_service = detect_service(raw_msg) if raw_msg else "OTP"
                        if detected_service == "OTP":
                            services = get_all_services()
                            detected_service = services.get(service_key, {}).get("name", "OTP")
                        
                        ic = ICONS.get(detected_service, "🔐")
                        countries = get_all_countries()
                        country = countries.get(prefix, prefix)
                        flag = get_flag(prefix)
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
                        
                        # إرسال للمستخدم (في البوت)
                        if uid:
                            try:
                                user_msg = (
                                    f"*🔐 تم استقبال رمز التفعيل*\n\n"
                                    f"📞 *الرقم:* `+{number}`\n"
                                    f"🌍 *الدولة:* {flag} {country}\n"
                                    f"{ic} *التطبيق:* {detected_service}\n"
                                    f"🔢 *الكود:* `{code}`\n\n"
                                    f"انسخ الكود واستخدمه فوراً"
                                )
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                            except:
                                pass
                        
                        # إرسال للجروب (جميع CHAT_IDS)
                        for cid in CHAT_IDS:
                            try:
                                masked = f"{number[:4]}****{number[-3:]}" if len(number) > 7 else number
                                group_msg = (
                                    f"*🔐 كود جديد*\n\n"
                                    f"🌍 {flag} {country} | {ic} {detected_service}\n"
                                    f"📞 `{masked}`\n"
                                    f"🔢 `{code}`"
                                )
                                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                                threading.Thread(
                                    target=lambda cid=cid, mid=sent.message_id: (
                                        time.sleep(DELETE_AFTER),
                                        bot.delete_message(cid, mid)
                                    ),
                                    daemon=True
                                ).start()
                            except:
                                pass
                        
                        # تحديث قاعدة البيانات
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                        c.execute("INSERT INTO otp_logs (number, otp, service, full_message, timestamp, assigned_to) VALUES (?,?,?,?,?,?)",
                                  (number, otp, detected_service, raw_msg, datetime.now().isoformat(), uid))
                        conn.commit()
                        api_delete_number(alloc_id)
                        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                        conn.commit()
                        conn.close()
                    
                    elif status == "expired":
                        api_delete_number(alloc_id)
                        conn = get_db()
                        conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                        conn.commit()
                        conn.close()
                
                except:
                    pass
        except:
            pass
        
        time.sleep(3)

# ════════════════ Flask ════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return "Taker OTP Bot Running"

@app.route('/health')
def health():
    return jsonify(status="ok"), 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ════════════════ تشغيل البوت ════════════════
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ Bot is running (AR/EN) - Single handler mode...")
    bot.infinity_polling()

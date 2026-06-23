# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════╗
 ║       TAKER OTP BOT - Ultimate Edition      ║
 ║       Developer: @hackerTaker               ║
 ║       API: xwdsms.org (Full Integration)     ║
 ╚══════════════════════════════════════════════╝
"""
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات الأساسية ════════════════
BOT_TOKEN = "8686995713:AAEwo-yYV3FxdzFEBdD1gxCv6rsJVZtI5gs"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_final.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, lang TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
    
    # جدول الأرقام النشطة
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
        service TEXT, assigned_to INTEGER, created_at TEXT,
        status TEXT DEFAULT 'waiting', otp TEXT)''')
    
    # جدول سجل الأكواد
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
        otp TEXT, service TEXT, full_message TEXT,
        timestamp TEXT, assigned_to INTEGER)''')
    
    # جدول الإحالات
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE,
        ref_count INTEGER DEFAULT 0)''')
    
    # جدول قنوات الاشتراك الإجباري
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_url TEXT UNIQUE, description TEXT,
        enabled INTEGER DEFAULT 1)''')
    
    # جدول الإعدادات
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    
    # جدول الدول المخصصة
    c.execute('''CREATE TABLE IF NOT EXISTS custom_countries (
        prefix TEXT PRIMARY KEY, name TEXT)''')
    
    # جدول الخدمات المخصصة
    c.execute('''CREATE TABLE IF NOT EXISTS custom_services (
        service_key TEXT PRIMARY KEY, name TEXT, icon TEXT, ar_name TEXT)''')
    
    # إعدادات افتراضية
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
    
    # إدراج الدول الافتراضية
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
    
    # إدراج الخدمات الافتراضية
    for key, data in DEFAULT_SERVICES.items():
        c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)",
                  (key, data['name'], data['icon'], data['ar']))
    
    conn.commit()
    conn.close()

init_db()

# ════════════════ دوال قاعدة البيانات ════════════════
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_all_countries():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix, name FROM custom_countries ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (prefix, name))
    conn.commit()
    conn.close()

def delete_country(prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()

def get_all_services():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT service_key, name, icon, ar_name FROM custom_services ORDER BY ar_name")
    rows = c.fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row[0]] = {"name": row[1], "icon": row[2], "ar": row[3]}
    return result

def add_service(key, name, icon, ar_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
    conn.commit()
    conn.close()

def delete_service(key):
    if key == "all": return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (key,))
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row

def set_lang(uid, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
    conn.commit()
    conn.close()

# ════════════════ دوال مساعدة ════════════════
def save_user(message):
    uid = message.from_user.id
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def release_user_number(uid):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at, status) VALUES (?,?,?,?,?,?,?)",
              (alloc_id, number, prefix, service, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_all_active():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, service, assigned_to FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0, None, None)

def get_user_balance(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()
    c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
    refs = c.fetchone()
    conn.close()
    return (bal[0] if bal else 0), (refs[0] if refs else 0)

def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
    conn.commit()
    conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

def process_referral(ref_code, new_uid):
    conn = sqlite3.connect(DB_PATH)
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

def mask_number(number):
    num = str(number)
    return num[:4] + "****" + num[-3:] if len(num) > 8 else num

def format_time(iso_str):
    if not iso_str: return "غير معروف"
    try: return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M")
    except: return iso_str

def check_subscription(uid):
    conn = sqlite3.connect(DB_PATH)
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

def sub_markup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels: return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك في القناة", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return mk

# ════════════════ نصوص ثنائية اللغة ════════════════
TXT = {
    "lang_select": {"ar": "🌐 *اختر لغتك*\n\nاختر اللغة التي تريد استخدام البوت بها:", "en": "🌐 *Select Your Language*\n\nChoose the language you want to use:"},
    "lang_set": {"ar": "✅ تم تعيين اللغة العربية", "en": "✅ English language set"},
    "lang_changed": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to English"},
    "welcome": {"ar": "✨ *أهلاً بك في بوت Taker OTP*\n\n• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n• ادعُ أصدقاءك واربح رصيداً\n\n*اختر الخدمة:*", "en": "✨ *Welcome to Taker OTP*\n\n• Select the service you want\n• Then select the country\n• Receive the code instantly\n• Invite friends and earn credit\n\n*Select service:*"},
    "choose_country": {"ar": "اختر الدولة لخدمة", "en": "Select country for"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم جديد*\n\n📞 *الرقم:* `+{number}`\n🌍 *الدولة:* {flag} {name}\n🛠 *الخدمة:* {svc}\n🕒 *الوقت:* {now}\n⏳ *الحالة:* في انتظار رمز التفعيل", "en": "✅ *Number Assigned*\n\n📞 *Number:* `+{number}`\n🌍 *Country:* {flag} {name}\n🛠 *Service:* {svc}\n🕒 *Time:* {now}\n⏳ *Status:* Waiting for code"},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 *الرقم الجديد:* `+{number}`\n🌍 *الدولة:* {flag} {name}\n🛠 *الخدمة:* {svc}\n🕒 *الوقت:* {now}\n⏳ *الحالة:* في انتظار رمز التفعيل", "en": "🔄 *Number Changed*\n\n📞 *New Number:* `+{number}`\n🌍 *Country:* {flag} {name}\n🛠 *Service:* {svc}\n🕒 *Time:* {now}\n⏳ *Status:* Waiting for code"},
    "maintenance": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", "en": "⚠️ *Bot under maintenance*\nPlease try again later."},
    "subscribe": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 *إجمالي الطلبات:* `{r}`\n🔷 *الأكواد المستلمة:* `{o}`\n🔷 *أول استخدام:* `{f}`\n🔷 *آخر استخدام:* `{l}`", "en": "📊 *Your Stats*\n\n🔷 *Total Requests:* `{r}`\n🔷 *OTPs Received:* `{o}`\n🔷 *First Seen:* `{f}`\n🔷 *Last Seen:* `{l}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 *رصيدك:* `{b:.3f} USDT`\n👤 *الإحالات:* `{ref}`\n🏦 *رصيد الموقع:* `{site}`\n🏦 *الحد الأدنى للسحب:* `18.0 USDT`\n\n💡 *اربح `0.05 USDT` عن كل صديق تدعوه*", "en": "💰 *Your Balance*\n\n💎 *Balance:* `{b:.3f} USDT`\n👤 *Referrals:* `{ref}`\n🏦 *Site Balance:* `{site}`\n🏦 *Min Withdrawal:* `18.0 USDT`\n\n💡 *Earn `0.05 USDT` per friend*"},
    "invite": {"ar": "🤝 *دعوة الأصدقاء*\n\n🔗 *رابط الدعوة الخاص بك:*\n`{link}`\n\n💰 *الربح:* `0.05 USDT` عن كل صديق\n📤 *شارك الرابط مع أصدقائك*", "en": "🤝 *Invite Friends*\n\n🔗 *Your referral link:*\n`{link}`\n\n💰 *Earn:* `0.05 USDT` per friend\n📤 *Share the link with your friends*"},
    "traffic": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers at the moment."},
    "prefix_added": {"ar": "✅ *تمت إضافة الدولة*\n\n🌍 {flag} {name}\n🔢 `{p}`", "en": "✅ *Country Added*\n\n🌍 {flag} {name}\n🔢 `{p}`"},
    "service_added": {"ar": "✅ *تمت إضافة الخدمة*\n\n{icon} {ar}", "en": "✅ *Service Added*\n\n{icon} {en}"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*\n\nمرحباً بك في لوحة إدارة البوت.", "en": "*⚙️ Admin Panel*\n\nWelcome to the bot control panel."},
    "otp_user": {"ar": "*🔐 تم استقبال رمز التفعيل*\n\n📞 *الرقم:* `+{num}`\n🌍 *الدولة:* {flag} {country}\n{icon} *التطبيق:* {svc}\n🔢 *الكود:* `{code}`\n\nانسخ الكود واستخدمه فوراً", "en": "*🔐 Activation Code Received*\n\n📞 *Number:* `+{num}`\n🌍 *Country:* {flag} {country}\n{icon} *Service:* {svc}\n🔢 *Code:* `{code}`\n\nCopy the code and use it immediately"},
    "otp_group": {"ar": "*🔐 كود جديد*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`", "en": "*🔐 New OTP*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`"},
    "countries_list": {"ar": "🌍 *الدول المتاحة:*\n\n", "en": "🌍 *Available Countries:*\n\n"},
}

def t(key, uid=None, **kw):
    lang = "ar"
    if uid:
        u = get_user(uid)
        if u and len(u) > 4 and u[4]: lang = u[4]
    txt = TXT.get(key, {}).get(lang, TXT.get(key, {}).get("ar", key))
    return txt.format(**kw) if kw else txt

# ════════════════ أسماء الأزرار ثنائية اللغة ════════════════
BTN = {
    "new": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries": {"ar": "🌍 الدول المتاحة", "en": "🌍 Countries"},
    "stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "traffic": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "admin": {"ar": "⚙️ لوحة التحكم", "en": "⚙️ Admin Panel"},
    "lang": {"ar": "🌐 اللغة", "en": "🌐 Language"},
}

def btn(key, uid):
    u = get_user(uid); lang = u[4] if u and len(u) > 4 and u[4] else "ar"
    return BTN[key][lang]

def lang_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    return mk

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton(btn("new", uid)),
        types.KeyboardButton(btn("countries", uid)),
        types.KeyboardButton(btn("stats", uid))
    )
    kb.add(
        types.KeyboardButton(btn("balance", uid)),
        types.KeyboardButton(btn("invite", uid)),
        types.KeyboardButton(btn("traffic", uid))
    )
    kb.add(types.KeyboardButton(btn("lang", uid)))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(btn("admin", uid)))
    return kb

def services_menu():
    services = get_all_services()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for key, data in services.items():
        if key != "all":
            buttons.append(types.InlineKeyboardButton(
                f"{data['icon']} {data['ar']}", callback_data=f"svc_{key}"))
    if "all" in services:
        buttons.append(types.InlineKeyboardButton(
            f"{services['all']['icon']} {services['all']['ar']}", callback_data="svc_all"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup

def countries_for_service(service_key):
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for prefix, name in sorted(countries.items()):
        flag = get_flag(prefix)
        buttons.append(types.InlineKeyboardButton(
            f"{flag} {name}", callback_data=f"get_{prefix}_{service_key}"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    markup.row(types.InlineKeyboardButton("↩️ رجوع للخدمات", callback_data="menu_services"))
    return markup

def number_actions(prefix, service_key, alloc_id, uid):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{prefix}_{service_key}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data=f"svc_{service_key}")
    )
    mk.row(
        types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
    )
    return mk

def show_home(cid, uid):
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown")
        return
    
    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(cid, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return
    
    photo = get_setting("welcome_photo")
    txt = t("welcome", uid)
    mk = services_menu()
    
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    bot.send_message(cid, "استخدم الأزرار أدناه للتنقل:", reply_markup=main_keyboard(uid))

# ════════════════ أوامر البوت ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    save_user(message)
    
    u = get_user(uid)
    if not u or not u[4]:
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
        return
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data in ["lang_ar", "lang_en"])
def set_lang_cb(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = "ar" if call.data == "lang_ar" else "en"
    set_lang(uid, lang)
    bot.answer_callback_query(call.id, t("lang_set", uid))
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح")
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        show_home(call.message.chat.id, call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    uid = call.from_user.id
    service_key = call.data.split("_")[1]
    services = get_all_services()
    svc_data = services.get(service_key, {"ar": service_key})
    
    bot.edit_message_text(
        f"*{t('choose_country', uid)} {svc_data['ar']}:*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=countries_for_service(service_key)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
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
        svc_name = services.get(service_key, {}).get("ar", service_key)
        now = datetime.now().strftime("%H:%M")
        
        msg = t("number_assigned", uid, number=number, flag=flag, name=name, svc=svc_name, now=now)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]
    service_key = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    if old_alloc:
        api_delete_number(old_alloc)
        conn = sqlite3.connect(DB_PATH)
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
        svc_name = services.get(service_key, {}).get("ar", service_key)
        now = datetime.now().strftime("%H:%M")
        
        msg = t("number_changed", uid, number=number, flag=flag, name=name, svc=svc_name, now=now)
        
        bot.edit_message_text(
            msg,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    if call.data == "menu_services":
        bot.edit_message_text(
            t("welcome", uid),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=services_menu()
        )
    else:
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        show_home(call.message.chat.id, uid)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text

    # حالات الإدارة
    state = admin_states.get(uid)
    if state == "add_country_prefix":
        admin_states[uid] = ("add_country_name", txt.strip())
        bot.send_message(cid, "أرسل اسم الدولة:")
        return
    if isinstance(state, tuple) and state[0] == "add_country_name":
        add_country(state[1], txt.strip())
        flag = get_flag(state[1])
        bot.send_message(cid, t("prefix_added", uid, flag=flag, name=txt.strip(), p=state[1]), parse_mode="Markdown")
        del admin_states[uid]
        return
    if state == "add_service_key":
        admin_states[uid] = ("add_service_name", txt.strip().lower())
        bot.send_message(cid, "أرسل اسم الخدمة بالإنجليزية:")
        return
    if isinstance(state, tuple) and state[0] == "add_service_name":
        admin_states[uid] = ("add_service_icon", state[1], txt.strip())
        bot.send_message(cid, "أرسل أيقونة الخدمة (إيموجي واحد):")
        return
    if isinstance(state, tuple) and state[0] == "add_service_icon":
        admin_states[uid] = ("add_service_ar", state[1], state[2], txt.strip())
        bot.send_message(cid, "أرسل اسم الخدمة بالعربية:")
        return
    if isinstance(state, tuple) and state[0] == "add_service_ar":
        add_service(state[1], state[2], state[3], txt.strip())
        bot.send_message(cid, t("service_added", uid, icon=state[3], ar=txt.strip(), en=state[2]), parse_mode="Markdown")
        del admin_states[uid]
        return
    if state == "broadcast":
        users = get_all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.05)
            except: pass
        bot.send_message(cid, f"✅ تم الإرسال إلى `{cnt}` مستخدم", parse_mode="Markdown")
        del admin_states[uid]
        return
    if state in ["ban", "unban"]:
        try:
            target = int(txt)
            conn = sqlite3.connect(DB_PATH)
            conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
            bot.send_message(cid, f"✅ تم {'حظر' if state=='ban' else 'فك حظر'} `{target}`", parse_mode="Markdown")
        except: bot.send_message(cid, "❌ معرف غير صحيح")
        del admin_states[uid]
        return
    if state == "addch_url":
        admin_states[uid] = ("addch_desc", txt.strip())
        bot.send_message(cid, "أرسل وصفاً للقناة:")
        return
    if isinstance(state, tuple) and state[0] == "addch_desc":
        url = state[1]
        desc = txt.strip()
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        conn.commit()
        conn.close()
        bot.send_message(cid, "✅ تمت الإضافة")
        del admin_states[uid]
        return

    # زر اللغة
    if txt in [btn("lang", uid)]:
        u = get_user(uid)
        cur = u[4] if u and len(u) > 4 and u[4] else "ar"
        new_lang = "en" if cur == "ar" else "ar"
        set_lang(uid, new_lang)
        bot.send_message(cid, t("lang_changed", uid), parse_mode="Markdown")
        bot.send_message(cid, "• • •", reply_markup=main_keyboard(uid))
        return

    # باقي الأزرار
    if txt in [btn("new", uid)]:
        bot.send_message(cid, t("welcome", uid), parse_mode="Markdown", reply_markup=services_menu())
    elif txt in [btn("countries", uid)]:
        countries = get_all_countries()
        msg = t("countries_list", uid) + "\n".join(f"{get_flag(p)} {n}" for p, n in sorted(countries.items()))
        bot.send_message(cid, msg, parse_mode="Markdown")
    elif txt in [btn("stats", uid)]:
        r, o, first, last = get_user_stats(uid)
        f = format_time(first) if first else "—"
        l = format_time(last) if last else "—"
        bot.send_message(cid, t("stats", uid, r=r, o=o, f=f, l=l), parse_mode="Markdown")
    elif txt in [btn("balance", uid)]:
        bal, refs = get_user_balance(uid)
        site = api_get_balance()
        bot.send_message(cid, t("balance", uid, b=bal, ref=refs, site=site), parse_mode="Markdown")
    elif txt in [btn("invite", uid)]:
        link = get_ref_link(uid)
        bot.send_message(cid, t("invite", uid, link=link), parse_mode="Markdown")
    elif txt in [btn("traffic", uid)]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, service, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix, service ORDER BY COUNT(*) DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        if not rows:
            bot.send_message(cid, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic", uid), ""]
            for p, svc, cnt in rows:
                name = get_all_countries().get(p, p)
                flag = get_flag(p)
                icon = get_all_services().get(svc, {}).get("icon", "🔐")
                lines.append(f"{flag} {name} {icon}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
    elif txt in [btn("admin", uid)] and uid in ADMIN_IDS:
        admin_panel(cid, uid)

# ════════════════ لوحة الإدارة الكاملة ════════════════
def admin_panel(cid, uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 Active" if get_setting("maintenance") != "1" else "🔴 Maintenance"
    markup.add(types.InlineKeyboardButton(f"Status: {status}", callback_data="toggle_maint"))
    markup.add(
        types.InlineKeyboardButton("➕ Add Country", callback_data="add_country"),
        types.InlineKeyboardButton("➖ Del Country", callback_data="del_country")
    )
    markup.add(
        types.InlineKeyboardButton("➕ Add Service", callback_data="add_service"),
        types.InlineKeyboardButton("➖ Del Service", callback_data="del_service")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 Users", callback_data="users_list")
    )
    markup.add(
        types.InlineKeyboardButton("🚫 Ban", callback_data="ban"),
        types.InlineKeyboardButton("✅ Unban", callback_data="unban")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 Force Sub", callback_data="force_sub"),
        types.InlineKeyboardButton("🖼️ Photo", callback_data="set_photo")
    )
    markup.add(
        types.InlineKeyboardButton("🗑️ Clear", callback_data="clear_data"),
        types.InlineKeyboardButton("↩️ Exit", callback_data="main_menu")
    )
    bot.send_message(cid, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

admin_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint")
def toggle_maint(call):
    cur = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "add_country")
def add_country_btn(call):
    admin_states[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text("*➕ Add Country*\n\nSend country prefix (e.g.: `24910`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "del_country")
def del_country_btn(call):
    countries = get_all_countries()
    mk = types.InlineKeyboardMarkup()
    for p, n in countries.items():
        mk.add(types.InlineKeyboardButton(f"{get_flag(p)} {n}", callback_data=f"delc_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*➖ Delete Country*\n\nSelect country:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "add_service")
def add_service_btn(call):
    admin_states[call.from_user.id] = "add_service_key"
    bot.edit_message_text("*➕ Add Service*\n\nSend service key (e.g.: `snapchat`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "del_service")
def del_service_btn(call):
    services = get_all_services()
    mk = types.InlineKeyboardMarkup()
    for k, d in services.items():
        if k != "all":
            mk.add(types.InlineKeyboardButton(f"{d['icon']} {d['ar']}", callback_data=f"dels_{k}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*➖ Delete Service*\n\nSelect service:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dels_"))
def dels(call):
    delete_service(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast_btn(call):
    admin_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 Broadcast*\n\nSend message:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"])
def ban_unban_btn(call):
    admin_states[call.from_user.id] = call.data
    txt = "*🚫 Ban*\n\nSend user ID:" if call.data == "ban" else "*✅ Unban*\n\nSend user ID:"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "users_list")
def users_list_btn(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15")
    rows = c.fetchall()
    conn.close()
    txt = "*👥 Users:*\n\n" + "\n".join(f"• `{u}` @{un or '—'}" for u, un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "force_sub")
def force_sub_btn(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    chs = c.fetchall()
    conn.close()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ Add", callback_data="addch"), types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*🔗 Force Subscribe*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch_btn(call):
    admin_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*Send channel URL:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch_btn(call):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (int(call.data.split("_")[1]),))
    conn.commit()
    conn.close()
    force_sub_btn(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo")
def set_photo_btn(call):
    admin_states[call.from_user.id] = "photo"
    bot.edit_message_text("*Send photo:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: admin_states.get(m.from_user.id) == "photo")
def save_photo(msg):
    set_setting("welcome_photo", msg.photo[-1].file_id)
    bot.send_message(msg.chat.id, "✅ Photo saved")
    del admin_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data")
def clear_data_btn(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    bot.answer_callback_query(call.id, "✅ Cleared")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back_btn(call):
    admin_panel(call.message.chat.id, call.from_user.id)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, service_key, uid in get_all_active():
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
                        
                        # إرسال للمستخدم
                        if uid:
                            try:
                                user_msg = t("otp_user", uid, num=number, flag=flag, country=country, icon=ic, svc=detected_service, code=code)
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                            except: pass
                        
                        # إرسال للجروب
                        for cid in CHAT_IDS:
                            try:
                                masked = mask_number(number)
                                group_msg = t("otp_group", None, flag=flag, country=country, icon=ic, svc=detected_service, masked=masked, code=code)
                                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                                threading.Thread(target=lambda: (time.sleep(DELETE_AFTER), bot.delete_message(cid, sent.message_id)), daemon=True).start()
                            except: pass
                        
                        # تحديث قاعدة البيانات
                        conn = sqlite3.connect(DB_PATH)
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
                        conn = sqlite3.connect(DB_PATH)
                        conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                        conn.commit()
                        conn.close()
                
                except: pass
        except: pass
        
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
    logger.info("✅ البوت يعمل...")
    bot.infinity_polling()

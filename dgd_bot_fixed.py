# -*- coding: utf-8 -*-
import time, requests, json, re, os, sqlite3, threading, traceback, random, logging
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ================ الإعدادات ================
BOT_TOKEN = "8686995713:AAFcYLSqdXl6O3x_PVvhkT8WOdJA_MQKHAE"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "xwdsms_bot.db"

# ================ إعدادات التسجيل ================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================ الدول الافتراضية ================
DEFAULT_COUNTRIES = {
    "22501": "ساحل العاج",
    "23276": "سيراليون",
    "26134": "مدغشقر",
    "44740": "المملكة المتحدة",
    "23490": "نيجيريا",
    "25471": "كينيا",
    "24910": "السودان 10",

    "22507": "ساحل العاج VIP",
    "49155": "ألمانيا",
    "23762": "الكاميرون",
    "22178": "السنغال",
    "22901": "بنين",
    "22898": "توجو",
}

# ================ جميع دول العالم (للحصول على العلم تلقائياً) ================
ALL_COUNTRIES = {
    "1": ("USA", "🇺🇸"), "7": ("Russia", "🇷🇺"), "20": ("Egypt", "🇪🇬"),
    "27": ("South Africa", "🇿🇦"), "30": ("Greece", "🇬🇷"), "31": ("Netherlands", "🇳🇱"),
    "32": ("Belgium", "🇧🇪"), "33": ("France", "🇫🇷"), "34": ("Spain", "🇪🇸"),
    "36": ("Hungary", "🇭🇺"), "39": ("Italy", "🇮🇹"), "40": ("Romania", "🇷🇴"),
    "41": ("Switzerland", "🇨🇭"), "43": ("Austria", "🇦🇹"), "44": ("United Kingdom", "🇬🇧"),
    "45": ("Denmark", "🇩🇰"), "46": ("Sweden", "🇸🇪"), "47": ("Norway", "🇳🇴"),
    "48": ("Poland", "🇵🇱"), "49": ("Germany", "🇩🇪"), "51": ("Peru", "🇵🇪"),
    "52": ("Mexico", "🇲🇽"), "54": ("Argentina", "🇦🇷"), "55": ("Brazil", "🇧🇷"),
    "56": ("Chile", "🇨🇱"), "57": ("Colombia", "🇨🇴"), "58": ("Venezuela", "🇻🇪"),
    "60": ("Malaysia", "🇲🇾"), "61": ("Australia", "🇦🇺"), "62": ("Indonesia", "🇮🇩"),
    "63": ("Philippines", "🇵🇭"), "64": ("New Zealand", "🇳🇿"), "65": ("Singapore", "🇸🇬"),
    "66": ("Thailand", "🇹🇭"), "81": ("Japan", "🇯🇵"), "82": ("South Korea", "🇰🇷"),
    "84": ("Vietnam", "🇻🇳"), "86": ("China", "🇨🇳"), "90": ("Turkey", "🇹🇷"),
    "91": ("India", "🇮🇳"), "92": ("Pakistan", "🇵🇰"), "93": ("Afghanistan", "🇦🇫"),
    "94": ("Sri Lanka", "🇱🇰"), "95": ("Myanmar", "🇲🇲"), "98": ("Iran", "🇮🇷"),
    "211": ("South Sudan", "🇸🇸"), "212": ("Morocco", "🇲🇦"), "213": ("Algeria", "🇩🇿"),
    "216": ("Tunisia", "🇹🇳"), "218": ("Libya", "🇱🇾"), "220": ("Gambia", "🇬🇲"),
    "221": ("Senegal", "🇸🇳"), "222": ("Mauritania", "🇲🇷"), "223": ("Mali", "🇲🇱"),
    "224": ("Guinea", "🇬🇳"), "225": ("Ivory Coast", "🇨🇮"), "226": ("Burkina Faso", "🇧🇫"),
    "227": ("Niger", "🇳🇪"), "228": ("Togo", "🇹🇬"), "229": ("Benin", "🇧🇯"),
    "230": ("Mauritius", "🇲🇺"), "231": ("Liberia", "🇱🇷"), "232": ("Sierra Leone", "🇸🇱"),
    "233": ("Ghana", "🇬🇭"), "234": ("Nigeria", "🇳🇬"), "235": ("Chad", "🇹🇩"),
    "236": ("Central African Rep", "🇨🇫"), "237": ("Cameroon", "🇨🇲"),
    "240": ("Equatorial Guinea", "🇬🇶"), "241": ("Gabon", "🇬🇦"),
    "242": ("Congo", "🇨🇬"), "243": ("DR Congo", "🇨🇩"), "244": ("Angola", "🇦🇴"),
    "248": ("Seychelles", "🇸🇨"), "249": ("Sudan", "🇸🇩"), "250": ("Rwanda", "🇷🇼"),
    "251": ("Ethiopia", "🇪🇹"), "252": ("Somalia", "🇸🇴"), "253": ("Djibouti", "🇩🇯"),
    "254": ("Kenya", "🇰🇪"), "255": ("Tanzania", "🇹🇿"), "256": ("Uganda", "🇺🇬"),
    "257": ("Burundi", "🇧🇮"), "258": ("Mozambique", "🇲🇿"), "260": ("Zambia", "🇿🇲"),
    "261": ("Madagascar", "🇲🇬"), "263": ("Zimbabwe", "🇿🇼"), "264": ("Namibia", "🇳🇦"),
    "265": ("Malawi", "🇲🇼"), "266": ("Lesotho", "🇱🇸"), "267": ("Botswana", "🇧🇼"),
    "350": ("Gibraltar", "🇬🇮"), "351": ("Portugal", "🇵🇹"), "352": ("Luxembourg", "🇱🇺"),
    "353": ("Ireland", "🇮🇪"), "354": ("Iceland", "🇮🇸"), "355": ("Albania", "🇦🇱"),
    "356": ("Malta", "🇲🇹"), "357": ("Cyprus", "🇨🇾"), "358": ("Finland", "🇫🇮"),
    "359": ("Bulgaria", "🇧🇬"), "370": ("Lithuania", "🇱🇹"), "371": ("Latvia", "🇱🇻"),
    "372": ("Estonia", "🇪🇪"), "373": ("Moldova", "🇲🇩"), "374": ("Armenia", "🇦🇲"),
    "375": ("Belarus", "🇧🇾"), "376": ("Andorra", "🇦🇩"), "377": ("Monaco", "🇲🇨"),
    "380": ("Ukraine", "🇺🇦"), "381": ("Serbia", "🇷🇸"), "385": ("Croatia", "🇭🇷"),
    "386": ("Slovenia", "🇸🇮"), "387": ("Bosnia", "🇧🇦"), "389": ("North Macedonia", "🇲🇰"),
    "420": ("Czech Republic", "🇨🇿"), "421": ("Slovakia", "🇸🇰"),
    "501": ("Belize", "🇧🇿"), "502": ("Guatemala", "🇬🇹"), "503": ("El Salvador", "🇸🇻"),
    "504": ("Honduras", "🇭🇳"), "505": ("Nicaragua", "🇳🇮"), "506": ("Costa Rica", "🇨🇷"),
    "507": ("Panama", "🇵🇦"), "509": ("Haiti", "🇭🇹"), "591": ("Bolivia", "🇧🇴"),
    "592": ("Guyana", "🇬🇾"), "593": ("Ecuador", "🇪🇨"), "595": ("Paraguay", "🇵🇾"),
    "597": ("Suriname", "🇸🇷"), "598": ("Uruguay", "🇺🇾"),
    "852": ("Hong Kong", "🇭🇰"), "855": ("Cambodia", "🇰🇭"), "856": ("Laos", "🇱🇦"),
    "880": ("Bangladesh", "🇧🇩"), "886": ("Taiwan", "🇹🇼"),
    "960": ("Maldives", "🇲🇻"), "961": ("Lebanon", "🇱🇧"), "962": ("Jordan", "🇯🇴"),
    "963": ("Syria", "🇸🇾"), "964": ("Iraq", "🇮🇶"), "965": ("Kuwait", "🇰🇼"),
    "966": ("Saudi Arabia", "🇸🇦"), "967": ("Yemen", "🇾🇪"), "968": ("Oman", "🇴🇲"),
    "970": ("Palestine", "🇵🇸"), "971": ("UAE", "🇦🇪"), "972": ("Israel", "🇮🇱"),
    "973": ("Bahrain", "🇧🇭"), "974": ("Qatar", "🇶🇦"), "975": ("Bhutan", "🇧🇹"),
    "976": ("Mongolia", "🇲🇳"), "977": ("Nepal", "🇳🇵"),
    "992": ("Tajikistan", "🇹🇯"), "993": ("Turkmenistan", "🇹🇲"),
    "994": ("Azerbaijan", "🇦🇿"), "995": ("Georgia", "🇬🇪"), "996": ("Kyrgyzstan", "🇰🇬"),
    "998": ("Uzbekistan", "🇺🇿"),
}

SERVICE_ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "Google": "🔍", "Twitter/X": "🐦", "Discord": "🎮", "Snapchat": "👻",
    "TikTok": "🎵", "Amazon": "📦", "Apple": "🍎", "Microsoft": "🪟",
    "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️", "OTP": "🔐",
}

# ================ API Functions ================
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=15)
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
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("status"), data.get("otp")
        return None, None
    except:
        return None, None

def api_delete_number(alloc_id):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=10)
        return resp.json().get("success", False)
    except:
        return False

def api_get_balance():
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=10)
        return resp.json().get("balance", "0")
    except:
        return "0"

# ================ قاعدة البيانات ================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
    # إضافة عمود اللغة إذا لم يكن موجوداً
    try:
        c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT NULL")
    except:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
        assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting', otp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
        service TEXT, timestamp TEXT, assigned_to INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
        description TEXT, enabled INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        prefix TEXT PRIMARY KEY, name TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('welcome_photo', '')")
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO countries (prefix, name) VALUES (?, ?)", (prefix, name))
    conn.commit()
    conn.close()

init_db()

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
    c.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_all_countries():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix, name FROM countries ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO countries (prefix, name) VALUES (?, ?)", (prefix, name))
    conn.commit()
    conn.close()

def delete_country(prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM countries WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()

# ================ دوال اللغة ================
def get_user_lang(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def set_user_lang(uid, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
    conn.commit()
    conn.close()

# نصوص قابلة للترجمة
T = {
    "welcome": {"ar": "*✨ أهلاً بك في بوت Taker OTP*\n\n• احصل على أرقام وهمية لتفعيل حساباتك\n• استقبل رموز التفعيل بشكل فوري\n• ادعُ أصدقاءك واربح رصيداً\n\n*🌍 اختر الدولة:*",
                "en": "*✨ Welcome to Taker OTP Bot*\n\n• Get virtual numbers for activation\n• Receive codes instantly\n• Invite friends and earn credit\n\n*🌍 Select country:*"},
    "choose_country": {"ar": "*🌍 اختر الدولة:*", "en": "*🌍 Select country:*"},
    "number_assigned": {"ar": "*✅ تم تخصيص رقم جديد*\n\n📞 *الرقم:* `{number}`\n🌍 *الدولة:* {country}\n🕒 *الوقت:* {now}\n⏳ *الحالة:* في انتظار رمز التفعيل",
                        "en": "*✅ Number Assigned*\n\n📞 *Number:* `{number}`\n🌍 *Country:* {country}\n🕒 *Time:* {now}\n⏳ *Status:* Waiting for OTP"},
    "number_changed": {"ar": "*🔄 تم تغيير الرقم*\n\n📞 *الرقم الجديد:* `{number}`\n🌍 *الدولة:* {country}\n🕒 *الوقت:* {now}\n⏳ *الحالة:* في انتظار رمز التفعيل",
                       "en": "*🔄 Number Changed*\n\n📞 *New Number:* `{number}`\n🌍 *Country:* {country}\n🕒 *Time:* {now}\n⏳ *Status:* Waiting for OTP"},
    "maintenance": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", "en": "⚠️ *Bot under maintenance*\nPlease try later."},
    "subscribe": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "stats": {"ar": "*📊 إحصائياتك*\n\n🔷 *إجمالي الطلبات:* `{req}`\n🔷 *الأكواد المستلمة:* `{otp}`\n🔷 *أول استخدام:* `{first}`\n🔷 *آخر استخدام:* `{last}`",
              "en": "*📊 Your Statistics*\n\n🔷 *Total Requests:* `{req}`\n🔷 *OTPs Received:* `{otp}`\n🔷 *First Seen:* `{first}`\n🔷 *Last Seen:* `{last}`"},
    "balance": {"ar": "*💰 رصيدك*\n\n💎 *رصيدك:* `{bal:.3f} USDT`\n👤 *الإحالات:* `{refs}`\n🏦 *رصيد الموقع:* `{site}`\n🏦 *الحد الأدنى للسحب:* `18.0 USDT`\n\n💡 *اربح `0.05 USDT` عن كل صديق*",
                "en": "*💰 Your Balance*\n\n💎 *Balance:* `{bal:.3f} USDT`\n👤 *Referrals:* `{refs}`\n🏦 *Site Balance:* `{site}`\n🏦 *Min Withdrawal:* `18.0 USDT`\n\n💡 *Earn `0.05 USDT` per friend*"},
    "invite": {"ar": "*🤝 دعوة الأصدقاء*\n\n🔗 *رابط الدعوة الخاص بك:*\n`{link}`\n\n💰 *الربح:* `0.05 USDT` عن كل صديق\n📤 *شارك الرابط مع أصدقائك*",
               "en": "*🤝 Invite Friends*\n\n🔗 *Your referral link:*\n`{link}`\n\n💰 *Earn:* `0.05 USDT` per friend\n📤 *Share the link*"},
    "traffic": {"ar": "*🟢 حركة المرور*\n\n", "en": "*🟢 Live Traffic*\n\n"},
    "no_active": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers at the moment."},
    "check_verified": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_failed": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ You haven't subscribed to all channels"},
}

def t(key, uid, **kwargs):
    lang = get_user_lang(uid) or "ar"
    text = T.get(key, {}).get(lang, T.get(key, {}).get("ar", ""))
    return text.format(**kwargs) if kwargs else text

# أزرار الكيبورد
def main_keyboard(uid):
    lang = get_user_lang(uid) or "ar"
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    if lang == "ar":
        kb.add("📱 احصل على رقم", "🌍 الدول المتاحة", "📊 إحصائياتي")
        kb.add("💰 رصيدي", "🤝 دعوة الأصدقاء", "🟢 حركة المرور")
        kb.add("🌐 اللغة")
    else:
        kb.add("📱 Get Number", "🌍 Countries", "📊 My Stats")
        kb.add("💰 Balance", "🤝 Invite", "🟢 Traffic")
        kb.add("🌐 Language")
    if uid in ADMIN_IDS:
        kb.add("⚙️ لوحة التحكم" if lang == "ar" else "⚙️ Admin Panel")
    return kb

# الحصول على علم الدولة من الـ prefix
def get_flag(prefix):
    best_code = None
    best_len = 0
    for code in ALL_COUNTRIES:
        if prefix.startswith(code) and len(code) > best_len:
            best_code = code
            best_len = len(code)
    if best_code:
        return ALL_COUNTRIES[best_code][1]
    return "🏳"

def country_inline(page=0):
    countries = list(get_all_countries().items())
    markup = types.InlineKeyboardMarkup(row_width=2)
    per_page = 8
    start = page * per_page
    chunk = countries[start:start+per_page]
    for prefix, name in chunk:
        flag = get_flag(prefix)
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"getnum_{prefix}"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("‹ السابق" if get_user_lang(None)=="ar" else "‹ Prev", callback_data=f"countries_{page-1}"))
    if start + per_page < len(countries):
        nav.append(types.InlineKeyboardButton("التالي ›" if get_user_lang(None)=="ar" else "Next ›", callback_data=f"countries_{page+1}"))
    if nav:
        markup.row(*nav)
    return markup

def number_actions(prefix, alloc_id, uid):
    lang = get_user_lang(uid) or "ar"
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم" if lang=="ar" else "🔄 Change Number", callback_data=f"change_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة" if lang=="ar" else "🌍 Change Country", callback_data="country_menu")
    )
    markup.row(
        types.InlineKeyboardButton("📞 قناة الأكواد" if lang=="ar" else "📞 Codes Channel", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ رجوع" if lang=="ar" else "↩️ Back", callback_data="main_menu")
    )
    return markup

# ================ دوال مساعدة ================
def save_user(message):
    uid = message.from_user.id
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, first_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
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

def assign_number(uid, alloc_id, number, prefix):
    release_user_number(uid)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # إزالة علامة + إن وجدت
    clean_number = number.replace("+", "")
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, assigned_to, created_at) VALUES (?,?,?,?,?)",
              (alloc_id, clean_number, prefix, uid, datetime.now().isoformat()))
    c.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def release_user_number(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    for row in c.fetchall():
        try:
            api_delete_number(row[0])
        except:
            pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (row[0],))
    conn.commit()
    conn.close()

def get_all_active():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall()
    conn.close()
    return rows

def save_otp(alloc_id, otp):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
    c.execute("UPDATE users SET total_otps = total_otps + 1 WHERE user_id=(SELECT assigned_to FROM active_numbers WHERE alloc_id=?)", (alloc_id,))
    conn.commit()
    conn.close()

def delete_active(alloc_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
    conn.commit()
    conn.close()

def log_otp(number, otp, service, uid=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, service, timestamp, assigned_to) VALUES (?,?,?,?,?)",
              (number, otp, service, datetime.now().isoformat(), uid))
    conn.commit()
    conn.close()

def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?,?)", (uid, ref))
    conn.commit()
    conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

def process_referral(ref_code, new_uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,))
    row = c.fetchone()
    if row:
        referrer = row[0]
        c.execute("UPDATE referrals SET ref_count = ref_count + 1 WHERE user_id=?", (referrer,))
        c.execute("UPDATE users SET balance = balance + 0.05 WHERE user_id=?", (referrer,))
    conn.commit()
    conn.close()

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
    row = c.fetchone()
    c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
    refs = c.fetchone()
    conn.close()
    return (row[0] if row else 0), (refs[0] if refs else 0)

def check_subscription(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return True
    for (url,) in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return None
    lang = get_user_lang(uid) or "ar"
    markup = types.InlineKeyboardMarkup()
    for url, desc in channels:
        text = f"📢 {desc}" if desc else ("📢 اشترك في القناة" if lang=="ar" else "📢 Subscribe")
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك" if lang=="ar" else "✅ Check Subscription", callback_data="check_sub"))
    return markup

def extract_otp(text):
    nums = re.findall(r'\d{4,8}', text)
    return nums[0] if nums else "N/A"

def detect_service(text):
    text = text.lower()
    services = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام", "telegram"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستا"],
        "Google": ["google", "gmail", "جوجل"],
        "Twitter / X": ["twitter", "تويتر", "x.com"],
        "Discord": ["discord", "ديسكورد"],
        "Snapchat": ["snapchat", "سناب شات", "سناب"],
        "TikTok": ["tiktok", "تيك توك"],
        "Amazon": ["amazon", "امازون"],
        "Apple": ["apple", "ابل", "icloud"],
        "Microsoft": ["microsoft", "مايكروسوفت"],
        "Uber": ["uber", "اوبر"],
        "Netflix": ["netflix", "نتفلكس"],
        "YouTube": ["youtube", "يوتيوب"],
    }
    for service, keywords in services.items():
        for kw in keywords:
            if kw in text:
                return service
    return "OTP"

def mask_number(number):
    num = str(number)
    return num[:4] + "****" + num[-3:] if len(num) > 8 else num

def format_time(iso_str):
    if not iso_str:
        return "غير معروف"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d-%m-%Y %H:%M")
    except:
        return iso_str

# ================ بوت تيليجرام ================
bot = telebot.TeleBot(BOT_TOKEN)

# ================ أوامر البوت ================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    save_user(message)
    lang = get_user_lang(uid)

    # إذا لم يختر اللغة بعد
    if lang is None:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
               types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"))
        bot.send_message(message.chat.id, "🌐 *اختر لغتك / Select your language*", parse_mode="Markdown", reply_markup=mk)
        return

    # فحص الصيانة
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(message.chat.id, t("maintenance", uid), parse_mode="Markdown")
        return

    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)

    # فحص الاشتراك الإجباري
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(message.chat.id, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return

    photo = get_setting("welcome_photo")
    txt = t("welcome", uid)
    mk = country_inline()
    if photo:
        try:
            bot.send_photo(message.chat.id, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(message.chat.id, "• • •", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data in ["setlang_ar", "setlang_en"])
def set_language(call):
    uid = call.from_user.id
    lang = "ar" if call.data == "setlang_ar" else "en"
    set_user_lang(uid, lang)
    bot.answer_callback_query(call.id, "✅ تم تعيين العربية" if lang=="ar" else "✅ English set")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    # إعادة تشغيل start لعرض القائمة باللغة الجديدة
    start(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, t("check_verified", uid))
        start(call.message)
    else:
        bot.answer_callback_query(call.id, t("check_failed", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("countries_"))
def countries_page(call):
    page = int(call.data.split("_")[1])
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=country_inline(page))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def get_number(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release_user_number(uid)
    try:
        alloc_id, number = api_get_number(prefix)
        clean_num = number.replace("+", "")
        assign_number(uid, alloc_id, clean_num, prefix)
        name = get_all_countries().get(prefix, prefix)
        flag = get_flag(prefix)
        now = datetime.now().strftime("%H:%M")
        msg = t("number_assigned", uid, number=clean_num, country=f"{flag} {name}", now=now)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=number_actions(prefix, alloc_id, uid))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]
    old_alloc = parts[2] if len(parts) > 2 else None
    if old_alloc:
        api_delete_number(old_alloc)
        delete_active(old_alloc)
    release_user_number(uid)
    try:
        alloc_id, number = api_get_number(prefix)
        clean_num = number.replace("+", "")
        assign_number(uid, alloc_id, clean_num, prefix)
        name = get_all_countries().get(prefix, prefix)
        flag = get_flag(prefix)
        now = datetime.now().strftime("%H:%M")
        msg = t("number_changed", uid, number=clean_num, country=f"{flag} {name}", now=now)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=number_actions(prefix, alloc_id, uid))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    if call.data == "country_menu":
        bot.edit_message_text(t("choose_country", uid), call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=country_inline())
    else:
        start(call.message)

# ================ الكيبورد السفلي ================
@bot.message_handler(func=lambda m: m.text in [
    "📱 احصل على رقم", "📱 Get Number",
    "🌍 الدول المتاحة", "🌍 Countries",
    "📊 إحصائياتي", "📊 My Stats",
    "💰 رصيدي", "💰 Balance",
    "🤝 دعوة الأصدقاء", "🤝 Invite",
    "🟢 حركة المرور", "🟢 Traffic",
    "🌐 اللغة", "🌐 Language"
])
def bottom_buttons(message):
    uid = message.from_user.id
    lang = get_user_lang(uid) or "ar"
    txt = message.text

    if txt in ["📱 احصل على رقم", "📱 Get Number"]:
        bot.send_message(message.chat.id, t("choose_country", uid), parse_mode="Markdown", reply_markup=country_inline())
    elif txt in ["🌍 الدول المتاحة", "🌍 Countries"]:
        countries = get_all_countries()
        text = (t("choose_country", uid) + "\n" if False else "*🌍 الدول المتاحة:*\n\n" if lang=="ar" else "*🌍 Available Countries:*\n\n") + \
               "\n".join(f"{get_flag(p)} {name} (`{p}`)" for p, name in countries.items())
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    elif txt in ["📊 إحصائياتي", "📊 My Stats"]:
        req, otp, first, last = get_user_stats(uid)
        msg = t("stats", uid, req=req, otp=otp, first=format_time(first), last=format_time(last))
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif txt in ["💰 رصيدي", "💰 Balance"]:
        bal, refs = get_user_balance(uid)
        site_bal = api_get_balance()
        msg = t("balance", uid, bal=bal, refs=refs, site=site_bal)
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif txt in ["🤝 دعوة الأصدقاء", "🤝 Invite"]:
        link = get_ref_link(uid)
        msg = t("invite", uid, link=link)
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif txt in ["🟢 حركة المرور", "🟢 Traffic"]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()
        if not rows:
            text = t("traffic", uid) + t("no_active", uid)
        else:
            lines = [t("traffic", uid)]
            for prefix, cnt in rows:
                name = get_all_countries().get(prefix, prefix)
                flag = get_flag(prefix)
                lines.append(f"{flag} {name}: `{cnt}`")
            text = "\n".join(lines)
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    elif txt in ["🌐 اللغة", "🌐 Language"]:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
               types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en"))
        bot.send_message(message.chat.id, "اختر اللغة / Select language", reply_markup=mk)

# ================ لوحة الإدارة (كما هي بدون تغيير) ================
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة التحكم" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if get_setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
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
        types.InlineKeyboardButton("🔗 الاشتراك", callback_data="force_sub"),
        types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="set_photo")
    )
    markup.add(
        types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="clear_data"),
        types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu")
    )
    msg = "*⚙️ لوحة التحكم*\n\nمرحباً بك في لوحة إدارة البوت."
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "تم تغيير الحالة")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    user_states[call.from_user.id] = "add_country_prefix"
    msg = "*➕ إضافة دولة*\n\nأرسل Prefix الدولة (مثال: `24910`):"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_country_prefix")
def add_country_prefix(message):
    prefix = message.text.strip()
    user_states[message.from_user.id] = ("add_country_name", prefix)
    bot.send_message(message.chat.id, "أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_country_name")
def add_country_name(message):
    prefix = user_states[message.from_user.id][1]
    name = message.text.strip()
    add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ تمت إضافة `{name}` ({prefix})", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*➖ حذف دولة*\nاختر الدولة:", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    prefix = call.data.split("_")[1]
    delete_country(prefix)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 إذاعة*\nأرسل الرسالة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = get_all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(message.chat.id, f"✅ تم الإرسال إلى `{cnt}` مستخدم", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    if not rows:
        msg = "لا يوجد مستخدمون بعد."
    else:
        msg = "*👥 آخر المستخدمين:*\n\n"
        for uid, uname, fname in rows:
            name = f"@{uname}" if uname else fname or str(uid)
            msg += f"• `{uid}` - {name}\n"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "ban" and c.from_user.id in ADMIN_IDS)
def ban_prompt(call):
    user_states[call.from_user.id] = "ban"
    bot.edit_message_text("*🚫 حظر*\nأرسل ID المستخدم:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ban")
def ban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ تم حظر `{uid}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ معرف غير صحيح")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "unban" and c.from_user.id in ADMIN_IDS)
def unban_prompt(call):
    user_states[call.from_user.id] = "unban"
    bot.edit_message_text("*✅ فك حظر*\nأرسل ID المستخدم:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "unban")
def unban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ تم فك حظر `{uid}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ معرف غير صحيح")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك الإجباري*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    url = message.text.strip()
    user_states[message.from_user.id] = ("addch_desc", url)
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تمت الإضافة")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    force_sub_menu(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*🖼️ صورة الترحيب*\nأرسل الصورة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم حفظ صورة الترحيب")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM active_numbers")
    c.execute("DELETE FROM otp_logs")
    c.execute("DELETE FROM referrals")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ================ حلقة فحص OTP مع الحذف التلقائي ================
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, uid in get_all_active():
                try:
                    status, otp = api_check_otp(number)
                    if status == "success" and otp:
                        service = detect_service(otp)
                        icon = SERVICE_ICONS.get(service, "🔐")
                        country = get_all_countries().get(prefix, prefix)
                        flag = get_flag(prefix)
                        # إرسال للمستخدم
                        if uid:
                            try:
                                msg = (
                                    f"*🔐 تم استقبال رمز التفعيل*\n\n"
                                    f"📞 *الرقم:* `+{number}`\n"
                                    f"🌍 *الدولة:* {flag} {country}\n"
                                    f"{icon} *التطبيق:* {service}\n"
                                    f"🔢 *الكود:* `{otp}`\n\n"
                                    f"انسخ الكود واستخدمه فوراً"
                                )
                                bot.send_message(uid, msg, parse_mode="Markdown")
                            except:
                                pass
                        # إرسال للجروب وحذف بعد 3 دقائق
                        for cid in CHAT_IDS:
                            try:
                                msg = (
                                    f"*🔐 كود جديد*\n\n"
                                    f"📞 `{mask_number(number)}`\n"
                                    f"🌍 {flag} {country}\n"
                                    f"{icon} {service}\n"
                                    f"🔢 `{otp}`"
                                )
                                sent = bot.send_message(cid, msg, parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id), daemon=True).start()
                            except:
                                pass
                        save_otp(alloc_id, otp)
                        log_otp(number, otp, service, uid)
                        api_delete_number(alloc_id)
                        delete_active(alloc_id)
                    elif status == "expired":
                        api_delete_number(alloc_id)
                        delete_active(alloc_id)
                except:
                    pass
        except:
            pass
        time.sleep(3)

def delete_later(chat_id, message_id, delay=180):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ================ Flask ================
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

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    print("✅ البوت يعمل...")
    bot.infinity_polling()

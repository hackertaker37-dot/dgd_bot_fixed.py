# -*- coding: utf-8 -*-
import time, requests, json, re, os, sqlite3, threading, traceback, random, logging
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8686995713:AAG6fy9oZlGIn8SvnQUY_zMq_Eeo6OJYqRY"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_final.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ قاعدة بيانات الدول ════════════════
COUNTRIES_DB = {
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

DEFAULT_PREFIXES = [
    "22501", "23276", "26134", "44740", "23490", "25471",
    "24910", "49155", "23762", "22178", "22901", "22898",
]

# ════════════════ الترجمة ════════════════
TEXTS = {
    "lang_select": {
        "ar": "🌐 *اختر لغتك*\n\nاختر اللغة التي تريد استخدام البوت بها:",
        "en": "🌐 *Select Your Language*\n\nChoose the language you want to use:"
    },
    "lang_set_ar": {"ar": "✅ تم تعيين اللغة العربية", "en": "✅ Arabic language set"},
    "lang_set_en": {"ar": "✅ English language set", "en": "✅ English language set"},
    "welcome": {
        "ar": "🔰 أهلاً بك في بوت Taker OTP\n\n• احصل على أرقام وهمية للتفعيل\n• استقبل الأكواد بشكل فوري\n• ادعُ أصدقاءك واربح رصيداً\n\n*اختر الدولة:*",
        "en": "🔰 Welcome to Taker OTP Bot\n\n• Get virtual numbers for activation\n• Receive codes instantly\n• Invite friends and earn credit\n\n*Select country:*"
    },
    "choose_country": {"ar": "🌍 اختر الدولة:", "en": "🌍 Select country:"},
    "number_assigned": {
        "ar": "✅ تم تخصيص رقم\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ في انتظار الكود...",
        "en": "✅ Number assigned\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ Waiting for code..."
    },
    "number_changed": {
        "ar": "🔄 تم تغيير الرقم\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ في انتظار الكود...",
        "en": "🔄 Number changed\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ Waiting for code..."
    },
    "maintenance": {"ar": "⚠️ البوت في وضع الصيانة", "en": "⚠️ Bot under maintenance"},
    "subscribe": {"ar": "🔒 اشترك أولاً", "en": "🔒 Subscribe first"},
    "banned": {"ar": "🚫 أنت محظور", "en": "🚫 You are banned"},
    "already_lang": {"ar": "لغتك الحالية هي العربية", "en": "Your current language is English"},
    "btn_new_number": {"ar": "📱 رقم جديد", "en": "📱 New Number"},
    "btn_countries": {"ar": "🌍 الدول", "en": "🌍 Countries"},
    "btn_stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "btn_balance": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "btn_invite": {"ar": "🤝 دعوة", "en": "🤝 Invite"},
    "btn_traffic": {"ar": "🟢 المرور", "en": "🟢 Traffic"},
    "btn_admin": {"ar": "⚙️ الإدارة", "en": "⚙️ Admin"},
    "btn_lang": {"ar": "🌐 اللغة", "en": "🌐 Language"},
    "stats": {
        "ar": "📊 إحصائياتك\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`",
        "en": "📊 Your Stats\n\n🔷 Requests: `{req}`\n🔷 OTPs: `{otp}`"
    },
    "balance": {
        "ar": "💰 رصيدك\n\n💎 رصيدك: `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 رصيد الموقع: `{site}`\n🏦 الحد الأدنى: `18.0 USDT`",
        "en": "💰 Balance\n\n💎 Your balance: `{bal:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site balance: `{site}`\n🏦 Min withdrawal: `18.0 USDT`"
    },
    "invite": {
        "ar": "🤝 دعوة الأصدقاء\n\n🔗 رابطك:\n`{link}`\n\n💰 تربح `0.05 USDT` عن كل صديق",
        "en": "🤝 Invite Friends\n\n🔗 Your link:\n`{link}`\n\n💰 Earn `0.05 USDT` per friend"
    },
    "traffic_title": {"ar": "🟢 حركة المرور", "en": "🟢 Live Traffic"},
    "no_active": {"ar": "لا توجد أرقام نشطة", "en": "No active numbers"},
    "high_traffic": {"ar": "🔥 {flag} {name} حركة مرور عالية", "en": "🔥 {flag} {name} High Traffic"},
    "prefix_added": {"ar": "✅ تمت إضافة دولة: {flag} {name}", "en": "✅ Country added: {flag} {name}"},
    "prefix_removed": {"ar": "✅ تم حذف الدولة", "en": "✅ Country removed"},
    "prefix_not_found": {"ar": "❌ كود الدولة غير معروف", "en": "❌ Unknown country code"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*", "en": "*⚙️ Admin Panel*"},
    "admin_add_prefix": {"ar": "*➕ أرسل رمز الدولة فقط (مثال: 22501):*", "en": "*➕ Send country code only (e.g.: 22501):*"},
    "admin_del_prefix": {"ar": "*اختر الدولة للحذف:*", "en": "*Select country to delete:*"},
    "admin_broadcast": {"ar": "*📢 أرسل الرسالة:*", "en": "*📢 Send message:*"},
    "admin_ban_unban": {"ar": "*أرسل ID المستخدم:*", "en": "*Send user ID:*"},
    "admin_done": {"ar": "✅ تم", "en": "✅ Done"},
    "admin_broadcast_done": {"ar": "✅ `{cnt}` مستخدم", "en": "✅ `{cnt}` users"},
    "admin_photo": {"ar": "*أرسل الصورة:*", "en": "*Send photo:*"},
    "admin_photo_done": {"ar": "✅ تم حفظ الصورة", "en": "✅ Photo saved"},
    "admin_clear_done": {"ar": "✅ تم مسح البيانات", "en": "✅ Data cleared"},
    "status_open": {"ar": "🟢 مفتوح", "en": "🟢 Open"},
    "status_maint": {"ar": "🔴 صيانة", "en": "🔴 Maintenance"},
    "btn_add_prefix": {"ar": "➕ إضافة دولة", "en": "➕ Add Country"},
    "btn_del_prefix": {"ar": "➖ حذف دولة", "en": "➖ Delete Country"},
    "btn_broadcast": {"ar": "📢 إذاعة", "en": "📢 Broadcast"},
    "btn_ban": {"ar": "🚫 حظر", "en": "🚫 Ban"},
    "btn_unban": {"ar": "✅ فك حظر", "en": "✅ Unban"},
    "btn_force_sub": {"ar": "🔗 اشتراك", "en": "🔗 Force Sub"},
    "btn_photo": {"ar": "🖼️ صورة", "en": "🖼️ Photo"},
    "btn_clear": {"ar": "🗑️ مسح", "en": "🗑️ Clear"},
    "btn_exit": {"ar": "↩️ خروج", "en": "↩️ Exit"},
    "btn_back": {"ar": "🔙 رجوع", "en": "🔙 Back"},
    "inline_change": {"ar": "🔄 تغيير", "en": "🔄 Change"},
    "inline_other_country": {"ar": "🌍 دولة أخرى", "en": "🌍 Other Country"},
    "inline_codes_channel": {"ar": "📞 قناة الأكواد", "en": "📞 Codes Channel"},
    "inline_back": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "inline_subscribe": {"ar": "📢 اشترك", "en": "📢 Subscribe"},
    "inline_check": {"ar": "✅ تحقق", "en": "✅ Check"},
    "inline_add_channel": {"ar": "➕ إضافة قناة", "en": "➕ Add Channel"},
    "otp_user": {
        "ar": "*🔐 كود تفعيل جديد*\n\n🌍 الدولة: {name} {flag}\n📱 الرقم: `{number}`\n🔑 الكود: `{code}`\n{icon} التطبيق: {service}\n🏆 المكافأة: 0.0030\n💵 الرصيد: 0.0030",
        "en": "*🔐 New Activation Code*\n\n🌍 Country: {name} {flag}\n📱 Number: `{number}`\n🔑 Code: `{code}`\n{icon} Service: {service}\n🏆 Reward: 0.0030\n💵 Balance: 0.0030"
    },
    "otp_group": {
        "ar": "*🔐 كود جديد*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`\n💲 السعر: 0.001$\n\n_⏳ تُحذف تلقائياً بعد 3 دقائق_",
        "en": "*🔐 New OTP*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`\n💲 Rate: 0.001$\n\n_⏳ Auto-delete in 3 minutes_"
    },
    "countries_list": {"ar": "🌍 *الدول المتاحة:*\n\n", "en": "🌍 *Available countries:*\n\n"},
    "check_verified": {"ar": "✅ تم التحقق", "en": "✅ Verified"},
    "check_failed": {"ar": "❌ لم تشترك", "en": "❌ Not subscribed"},
}

def t(key, uid=None, **kwargs):
    lang = "ar"
    if uid:
        user = db.get_user(uid)
        if user and user[3]:
            lang = user[3]
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ar", key))
    if kwargs:
        text = text.format(**kwargs)
    return text

def kb(key, uid=None):
    return t(key, uid)

# ════════════════ قاعدة البيانات ════════════════
class Database:
    def __init__(self, path):
        self.path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                lang TEXT DEFAULT NULL, balance REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0, total_requests INTEGER DEFAULT 0,
                total_otps INTEGER DEFAULT 0, first_seen TEXT, last_seen TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
                alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
                assigned_to INTEGER, created_at TEXT,
                status TEXT DEFAULT 'waiting', otp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
                otp TEXT, service TEXT, country TEXT, timestamp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE,
                ref_count INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT UNIQUE, description TEXT,
                enabled INTEGER DEFAULT 1)''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_prefixes (
                prefix TEXT PRIMARY KEY, name TEXT, added_at TEXT)''')
            c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
            c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
            for p in DEFAULT_PREFIXES:
                if p in COUNTRIES_DB:
                    c.execute("INSERT OR IGNORE INTO active_prefixes (prefix, name, added_at) VALUES (?,?,?)",
                              (p, COUNTRIES_DB[p][0], datetime.now().isoformat()))
            conn.commit()

    def setting(self, key, value=None):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            if value is not None:
                c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
                conn.commit()
                return value
            c.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = c.fetchone()
            return row[0] if row else None

    def active_prefixes(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT prefix, name FROM active_prefixes")
            return {r[0]: r[1] for r in c.fetchall()}

    def add_prefix(self, prefix):
        if prefix in COUNTRIES_DB:
            name = COUNTRIES_DB[prefix][0]
            with sqlite3.connect(self.path) as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO active_prefixes VALUES (?,?,?)",
                          (prefix, name, datetime.now().isoformat()))
                conn.commit()
            return name
        return None

    def remove_prefix(self, prefix):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM active_prefixes WHERE prefix=?", (prefix,))
            conn.commit()

    def get_user(self, uid):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
            return c.fetchone()

    def save_user(self, message):
        uid = message.from_user.id
        now = datetime.now().isoformat()
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
            if not c.fetchone():
                c.execute("INSERT INTO users (user_id, username, first_name, first_seen, last_seen) VALUES (?,?,?,?,?)",
                          (uid, message.from_user.username, message.from_user.first_name, now, now))
            else:
                c.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now, uid))
            conn.commit()

    def set_lang(self, uid, lang):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
            conn.commit()

    def get_lang(self, uid):
        user = self.get_user(uid)
        return user[3] if user else None

    def all_users(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE is_banned=0")
            return [r[0] for r in c.fetchall()]

db = Database(DB_PATH)

# ════════════════ API ════════════════
class XWDSMS:
    def __init__(self):
        self.base = BASE_URL
        self.key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.key, "Content-Type": "application/json"})

    def get_number(self, prefix):
        try:
            resp = self.session.post(f"{self.base}/api/v1/get-number",
                                     json={"range": prefix}, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise Exception(data.get("message", "Failed"))
            return data["id"], data["number"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("Country not available")
            raise Exception("Server error")
        except Exception as e:
            raise Exception(str(e))

    def check_otp(self, number):
        try:
            resp = self.session.get(f"{self.base}/api/v1/check-otp",
                                    params={"number": number}, timeout=6)
            data = resp.json()
            if data.get("success"):
                return data.get("status"), data.get("otp")
            return None, None
        except:
            return None, None

    def delete_number(self, alloc_id):
        try:
            self.session.post(f"{self.base}/api/v1/delete-number",
                              json={"id": alloc_id}, timeout=4)
        except:
            pass

    def get_balance(self):
        try:
            resp = self.session.get(f"{self.base}/api/v1/balance", timeout=6)
            return resp.json().get("balance", "0")
        except:
            return "0"

api = XWDSMS()

# ════════════════ دوال مساعدة ════════════════
def clean_phone(num):
    return str(num).replace("+", "").strip()

def extract_otp(text):
    nums = re.findall(r'\d{4,8}', str(text))
    return nums[0] if nums else "N/A"

def detect_service(text):
    t = str(text).lower()
    services = [
        ("WhatsApp", ["whatsapp", "واتساب", "واتس"]),
        ("Telegram", ["telegram", "تيليجرام", "تليجرام"]),
        ("Facebook", ["facebook", "فيسبوك", "fb"]),
        ("Instagram", ["instagram", "انستقرام", "انستا"]),
        ("Google", ["google", "gmail", "جوجل"]),
        ("Twitter/X", ["twitter", "تويتر"]),
        ("Discord", ["discord", "ديسكورد"]),
        ("Snapchat", ["snapchat", "سناب"]),
        ("TikTok", ["tiktok", "تيك توك"]),
        ("Amazon", ["amazon", "امازون"]),
        ("Apple", ["apple", "ابل", "icloud"]),
        ("Microsoft", ["microsoft", "مايكروسوفت"]),
        ("Uber", ["uber", "اوبر"]),
        ("Netflix", ["netflix", "نتفلكس"]),
        ("YouTube", ["youtube", "يوتيوب"]),
    ]
    for svc, keywords in services:
        if any(kw in t for kw in keywords):
            return svc
    return "OTP"

def get_country_info(prefix):
    if prefix in COUNTRIES_DB:
        return COUNTRIES_DB[prefix]
    return (prefix, "🏳")

def mask_number(num):
    n = str(num)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

def release_user_number(uid):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
        for (alloc_id,) in c.fetchall():
            api.delete_number(alloc_id)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
        conn.commit()

def assign_number(uid, alloc_id, number, prefix):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
                  (alloc_id, clean_phone(number), prefix, uid, datetime.now().isoformat(), 'waiting'))
        c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
        conn.commit()

def get_active():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'")
        return c.fetchall()

def check_subscription(uid):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
        channels = [r[0] for r in c.fetchall()]
    if not channels:
        return True
    for url in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            member = bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
        channels = c.fetchall()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(t("inline_subscribe", uid), url=url))
    mk.add(types.InlineKeyboardButton(t("inline_check", uid), callback_data="check_sub"))
    return mk

def lang_select_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")
    )
    return mk

def delete_message_later(chat_id, message_id, delay=180):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        logger.info(f"🗑️ تم حذف الرسالة {message_id} من {chat_id}")
    except Exception as e:
        logger.error(f"❌ فشل حذف الرسالة: {e}")

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(
        types.KeyboardButton(kb("btn_new_number", uid)),
        types.KeyboardButton(kb("btn_countries", uid)),
        types.KeyboardButton(kb("btn_stats", uid))
    )
    kb.add(
        types.KeyboardButton(kb("btn_balance", uid)),
        types.KeyboardButton(kb("btn_invite", uid)),
        types.KeyboardButton(kb("btn_traffic", uid))
    )
    kb.add(types.KeyboardButton(kb("btn_lang", uid)))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(kb("btn_admin", uid)))
    return kb

def build_countries_menu():
    prefixes = db.active_prefixes()
    mk = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for prefix in sorted(prefixes.keys()):
        name, flag = get_country_info(prefix)
        buttons.append(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"get_{prefix}"))
    for i in range(0, len(buttons), 2):
        mk.row(*buttons[i:i+2])
    return mk

def number_actions(uid, prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(kb("inline_change", uid), callback_data=f"ch_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton(kb("inline_other_country", uid), callback_data="menu_countries")
    )
    mk.row(
        types.InlineKeyboardButton(kb("inline_codes_channel", uid), url="https://t.me/numhj"),
        types.InlineKeyboardButton(kb("inline_back", uid), callback_data="menu_main")
    )
    return mk

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id

    db.save_user(message)

    lang = db.get_lang(uid)
    if lang is None:
        txt = "🌐 *اختر لغتك / Select Your Language*\n\nاختر اللغة التي تريد استخدام البوت بها:\nChoose the language you want to use:"
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=lang_select_markup())
        return

    show_main_menu(cid, uid)

def show_main_menu(cid, uid):
    """عرض القائمة الرئيسية مع جميع الأزرار"""
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown")
        return

    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return

    photo = db.setting("welcome_photo")
    txt = t("welcome", uid)
    mk = build_countries_menu()
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    # ✅ إرسال الكيبورد السفلي دائماً
    bot.send_message(cid, "استخدم الأزرار أدناه:", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data.startswith("setlang_"))
def set_lang(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = call.data.split("_")[1]
    db.set_lang(uid, lang)
    bot.answer_callback_query(call.id, t(f"lang_set_{lang}", uid))
    
    # حذف رسالة اختيار اللغة
    try:
        bot.delete_message(cid, call.message.message_id)
    except:
        pass
    
    # عرض القائمة الرئيسية كاملة مع الكيبورد
    show_main_menu(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, t("check_verified", uid))
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        show_main_menu(cid, uid)
    else:
        bot.answer_callback_query(call.id, t("check_failed", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release_user_number(uid)
    try:
        alloc_id, number = api.get_number(prefix)
        number = clean_phone(number)
        assign_number(uid, alloc_id, number, prefix)
        name, flag = get_country_info(prefix)
        now = datetime.now().strftime("%H:%M:%S")
        msg = t("number_assigned", uid, number=number, flag=flag, country=name, time=now)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=number_actions(uid, prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    uid = call.from_user.id
    _, prefix, old_alloc = call.data.split("_")
    if old_alloc:
        api.delete_number(old_alloc)
    release_user_number(uid)
    try:
        alloc_id, number = api.get_number(prefix)
        number = clean_phone(number)
        assign_number(uid, alloc_id, number, prefix)
        name, flag = get_country_info(prefix)
        now = datetime.now().strftime("%H:%M:%S")
        msg = t("number_changed", uid, number=number, flag=flag, country=name, time=now)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=number_actions(uid, prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries", "menu_main"])
def menu_back(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if call.data == "menu_countries":
        bot.edit_message_text(t("choose_country", uid),
                              cid, call.message.message_id,
                              parse_mode="Markdown", reply_markup=build_countries_menu())
    else:
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        show_main_menu(cid, uid)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text

    # ✅ فحص الأزرار باستخدام دوال الترجمة
    if text == kb("btn_new_number", uid):
        bot.send_message(cid, t("choose_country", uid), parse_mode="Markdown", reply_markup=build_countries_menu())
    elif text == kb("btn_countries", uid):
        prefixes = db.active_prefixes()
        txt = t("countries_list", uid) + "\n".join(f"{get_country_info(p)[1]} {name}" for p, name in sorted(prefixes.items()))
        bot.send_message(cid, txt, parse_mode="Markdown")
    elif text == kb("btn_stats", uid):
        user = db.get_user(uid)
        reqs = user[6] if user else 0
        otps = user[7] if user else 0
        bot.send_message(cid, t("stats", uid, req=reqs, otp=otps), parse_mode="Markdown")
    elif text == kb("btn_balance", uid):
        user = db.get_user(uid)
        bal = user[4] if user else 0
        site = api.get_balance()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
            refs = c.fetchone()
        ref_count = refs[0] if refs else 0
        bot.send_message(cid, t("balance", uid, bal=bal, ref=ref_count, site=site), parse_mode="Markdown")
    elif text == kb("btn_invite", uid):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            ref_code = f"ref{uid}"
            c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?,?)", (uid, ref_code))
            conn.commit()
        link = f"https://t.me/Taker_OTP_BOT?start={ref_code}"
        bot.send_message(cid, t("invite", uid, link=link), parse_mode="Markdown")
    elif text == kb("btn_traffic", uid):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10")
            rows = c.fetchall()
        if not rows:
            bot.send_message(cid, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic_title", uid) + "\n"]
            for prefix, cnt in rows:
                name, flag = get_country_info(prefix)
                if cnt > 5:
                    lines.append(t("high_traffic", uid, flag=flag, name=name))
                else:
                    lines.append(f"{flag} {name}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
    elif text == kb("btn_lang", uid):
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_select_markup())
    elif text == kb("btn_admin", uid) and uid in ADMIN_IDS:
        admin_panel(cid, uid)

# ════════════════ لوحة الإدارة ════════════════
def admin_panel(cid, uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    status = t("status_open", uid) if db.setting("maintenance") != "1" else t("status_maint", uid)
    mk.add(types.InlineKeyboardButton(f"الحالة: {status}", callback_data="tog_maint"))
    mk.add(
        types.InlineKeyboardButton(t("btn_add_prefix", uid), callback_data="add_prefix_btn"),
        types.InlineKeyboardButton(t("btn_del_prefix", uid), callback_data="del_prefix")
    )
    mk.add(
        types.InlineKeyboardButton(t("btn_broadcast", uid), callback_data="broadcast"),
        types.InlineKeyboardButton(t("btn_ban", uid), callback_data="ban")
    )
    mk.add(
        types.InlineKeyboardButton(t("btn_unban", uid), callback_data="unban"),
        types.InlineKeyboardButton(t("btn_force_sub", uid), callback_data="force_sub")
    )
    mk.add(
        types.InlineKeyboardButton(t("btn_photo", uid), callback_data="set_photo"),
        types.InlineKeyboardButton(t("btn_clear", uid), callback_data="clear_data")
    )
    mk.add(types.InlineKeyboardButton(t("btn_exit", uid), callback_data="menu_main"))
    bot.send_message(cid, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "tog_maint")
def tog_maint(call):
    uid = call.from_user.id
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, t("admin_done", uid))
    admin_panel(call.message.chat.id, uid)

@bot.callback_query_handler(func=lambda c: c.data == "add_prefix_btn")
def add_prefix_btn(call):
    uid = call.from_user.id
    user_states[uid] = "add_prefix"
    bot.edit_message_text(t("admin_add_prefix", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix_exec(message):
    uid = message.from_user.id
    prefix = message.text.strip()
    name = db.add_prefix(prefix)
    if name:
        _, flag = get_country_info(prefix)
        bot.send_message(message.chat.id, t("prefix_added", uid, flag=flag, name=name), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, t("prefix_not_found", uid), parse_mode="Markdown")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data == "del_prefix")
def del_prefix_menu(call):
    uid = call.from_user.id
    prefixes = db.active_prefixes()
    mk = types.InlineKeyboardMarkup()
    for p, name in sorted(prefixes.items()):
        _, flag = get_country_info(p)
        mk.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"delp_{p}"))
    mk.add(types.InlineKeyboardButton(t("btn_back", uid), callback_data="admin_back"))
    bot.edit_message_text(t("admin_del_prefix", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delp_"))
def delp(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    db.remove_prefix(prefix)
    bot.answer_callback_query(call.id, t("prefix_removed", uid))
    admin_panel(call.message.chat.id, uid)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast(call):
    uid = call.from_user.id
    user_states[uid] = "broadcast"
    bot.edit_message_text(t("admin_broadcast", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    uid = message.from_user.id
    users = db.all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.03)
        except:
            pass
    bot.send_message(message.chat.id, t("admin_broadcast_done", uid, cnt=cnt), parse_mode="Markdown")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"])
def ban_unban(call):
    uid = call.from_user.id
    user_states[uid] = call.data
    bot.edit_message_text(t("admin_ban_unban", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    uid = message.from_user.id
    action = user_states[uid]
    try:
        target_uid = int(message.text)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (target_uid,))
            conn.commit()
        bot.send_message(message.chat.id, t("admin_done", uid))
    except:
        bot.send_message(message.chat.id, "❌")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data == "force_sub")
def force_sub(call):
    uid = call.from_user.id
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM force_channels WHERE enabled=1")
        chs = c.fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton(t("inline_add_channel", uid), callback_data="addch"))
    mk.add(types.InlineKeyboardButton(t("btn_back", uid), callback_data="admin_back"))
    bot.edit_message_text("*🔗*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch(call):
    uid = call.from_user.id
    user_states[uid] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    uid = message.from_user.id
    user_states[uid] = ("addch_desc", message.text.strip())
    bot.send_message(message.chat.id, "أرسل وصفاً:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    uid = message.from_user.id
    url = user_states[uid][1]
    desc = message.text.strip()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        conn.commit()
    bot.send_message(message.chat.id, "✅")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    ch_id = int(call.data.split("_")[1])
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
        conn.commit()
    force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo")
def set_photo(call):
    uid = call.from_user.id
    user_states[uid] = "photo"
    bot.edit_message_text(t("admin_photo", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    uid = message.from_user.id
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, t("admin_photo_done", uid))
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data")
def clear_data(call):
    uid = call.from_user.id
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for t in ["users", "active_numbers", "otp_logs", "referrals"]:
            c.execute(f"DELETE FROM {t}")
        conn.commit()
    bot.answer_callback_query(call.id, t("admin_clear_done", uid))
    admin_panel(call.message.chat.id, uid)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back(call):
    admin_panel(call.message.chat.id, call.from_user.id)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, uid in get_active():
                try:
                    status, otp = api.check_otp(number)
                    if status == "success" and otp:
                        service = detect_service(otp)
                        icon = SERVICE_ICONS.get(service, "🔐")
                        name, flag = get_country_info(prefix)
                        code_parts = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp

                        if uid:
                            try:
                                user_msg = t("otp_user", uid, name=name, flag=flag, number=number,
                                            code=code_parts, icon=icon, service=service)
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                            except:
                                pass

                        for cid in CHAT_IDS:
                            try:
                                group_msg = t("otp_group", None, flag=flag, name=name, icon=icon,
                                             service=service, masked=mask_number(number), code=code_parts)
                                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                                threading.Thread(target=delete_message_later,
                                               args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except:
                                pass

                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO otp_logs (number, otp, service, country, timestamp) VALUES (?,?,?,?,?)",
                                      (number, otp, service, name, datetime.now().isoformat()))
                            c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
                            c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                            conn.commit()

                        api.delete_number(alloc_id)
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                            conn.commit()

                    elif status == "expired":
                        api.delete_number(alloc_id)
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
                            conn.commit()
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# ════════════════ تشغيل ════════════════
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ Taker OTP Bot Running...")
    bot.infinity_polling()

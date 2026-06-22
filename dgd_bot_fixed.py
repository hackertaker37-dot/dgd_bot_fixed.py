# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════╗
 ║        TAKER OTP BOT - Final Version        ║
 ║        Developer: @hackerTaker              ║
 ║        API: xwdsms.org (Full Integration)    ║
 ╚══════════════════════════════════════════════╝
"""
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

# ════════════════ السجل ════════════════
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ قاعدة بيانات الدول مع الأعلام ════════════════
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

# ════════════════ التطبيقات مع الأيقونات ════════════════
SERVICE_ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "Google": "🔍", "Twitter/X": "🐦", "Discord": "🎮", "Snapchat": "👻",
    "TikTok": "🎵", "Amazon": "📦", "Apple": "🍎", "Microsoft": "🪟",
    "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️", "OTP": "🔐",
}

# ════════════════ الدول المتاحة افتراضياً ════════════════
DEFAULT_PREFIXES = [
    "22501", "23276", "26134", "44740", "23490", "25471",
    "24910", "49155", "23762", "22178", "22901", "22898",
]

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
                lang TEXT DEFAULT 'ar', balance REAL DEFAULT 0,
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
            c.execute("INSERT OR IGNORE INTO settings VALUES ('lang', 'ar')")
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

    def all_users(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE is_banned=0")
            return [r[0] for r in c.fetchall()]

db = Database(DB_PATH)

# ════════════════ الترجمة ════════════════
TEXTS = {
    "welcome": {"ar": "🔰 أهلاً بك في بوت Taker OTP\n\n• احصل على أرقام وهمية للتفعيل\n• استقبل الأكواد بشكل فوري\n• ادعُ أصدقاءك واربح رصيداً\n\n*اختر الدولة:*",
                "en": "🔰 Welcome to Taker OTP Bot\n\n• Get virtual numbers for activation\n• Receive codes instantly\n• Invite friends and earn credit\n\n*Select country:*"},
    "choose_country": {"ar": "🌍 اختر الدولة:", "en": "🌍 Select country:"},
    "number_assigned": {"ar": "✅ تم تخصيص رقم\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ في انتظار الكود...",
                        "en": "✅ Number assigned\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 تم تغيير الرقم\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ في انتظار الكود...",
                       "en": "🔄 Number changed\n\n📞 `{number}`\n🌍 {flag} {country}\n🕒 {time}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ البوت في وضع الصيانة", "en": "⚠️ Bot under maintenance"},
    "subscribe": {"ar": "🔒 اشترك أولاً", "en": "🔒 Subscribe first"},
    "banned": {"ar": "🚫 أنت محظور", "en": "🚫 You are banned"},
    "stats": {"ar": "📊 إحصائياتك\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`",
              "en": "📊 Your Stats\n\n🔷 Requests: `{req}`\n🔷 OTPs: `{otp}`"},
    "balance": {"ar": "💰 رصيدك\n\n💎 رصيدك: `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 رصيد الموقع: `{site}`\n🏦 الحد الأدنى: `18.0 USDT`",
                "en": "💰 Balance\n\n💎 Your balance: `{bal:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site balance: `{site}`\n🏦 Min withdrawal: `18.0 USDT`"},
    "invite": {"ar": "🤝 دعوة الأصدقاء\n\n🔗 رابطك:\n`{link}`\n\n💰 تربح `0.05 USDT` عن كل صديق",
               "en": "🤝 Invite Friends\n\n🔗 Your link:\n`{link}`\n\n💰 Earn `0.05 USDT` per friend"},
    "traffic": {"ar": "🟢 حركة المرور", "en": "🟢 Live Traffic"},
    "no_active": {"ar": "لا توجد أرقام نشطة", "en": "No active numbers"},
    "prefix_added": {"ar": "✅ تمت إضافة دولة: {flag} {name}", "en": "✅ Country added: {flag} {name}"},
    "prefix_removed": {"ar": "✅ تم حذف الدولة", "en": "✅ Country removed"},
    "prefix_not_found": {"ar": "❌ كود الدولة غير معروف", "en": "❌ Unknown country code"},
    "stock_added": {"ar": "🆕 مخزون جديد 🔥\n\n{flag} {name} 📱 | {icon} {service}\n💲 السعر: 0.001$",
                    "en": "🆕 New Stock Added 🔥\n\n{flag} {name} 📱 | {icon} {service}\n💲 Rate: 0.001$"},
    "high_traffic": {"ar": "🔥 حركة مرور عالية\n\n{flag} {name} {service} High Traffic 🔥🔥",
                     "en": "🔥 High Traffic\n\n{flag} {name} {service} High Traffic 🔥🔥"},
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
                raise Exception(data.get("message", "فشل"))
            return data["id"], data["number"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("هذه الدولة غير متوفرة حالياً")
            raise Exception("خطأ في الخادم")
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
    """إزالة علامة + من الرقم إذا كانت موجودة"""
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

def find_country_by_number(number):
    num = clean_phone(number)
    for code in sorted(COUNTRIES_DB.keys(), key=len, reverse=True):
        if num.startswith(code):
            return code
    return None

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

def sub_markup():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
        channels = c.fetchall()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return mk

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("📱 رقم جديد", "🌍 الدول", "📊 إحصائياتي")
    kb.add("💰 رصيدي", "🤝 دعوة", "🟢 المرور")
    if uid in ADMIN_IDS:
        kb.add("⚙️ الإدارة", "🌐 لغة")
    else:
        kb.add("🌐 لغة")
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

def number_actions(prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 دولة أخرى", callback_data="menu_countries")
    )
    mk.row(
        types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_main")
    )
    return mk

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id

    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown")
        return

    db.save_user(message)

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (args[1],))
            row = c.fetchone()
            if row:
                c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
                c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (row[0],))
            conn.commit()

    if not check_subscription(uid):
        mk = sub_markup()
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
    bot.send_message(cid, "استخدم الأزرار:", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك", show_alert=True)

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
                              parse_mode="Markdown", reply_markup=number_actions(prefix, alloc_id))
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
                              parse_mode="Markdown", reply_markup=number_actions(prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries", "menu_main"])
def menu_back(call):
    if call.data == "menu_countries":
        bot.edit_message_text(t("choose_country", call.from_user.id),
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=build_countries_menu())
    else:
        start(call.message)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: m.text in [
    "📱 رقم جديد", "🌍 الدول", "📊 إحصائياتي",
    "💰 رصيدي", "🤝 دعوة", "🟢 المرور", "🌐 لغة"
])
def handle_buttons(message):
    uid = message.from_user.id
    if message.text == "📱 رقم جديد":
        bot.send_message(message.chat.id, t("choose_country", uid), parse_mode="Markdown", reply_markup=build_countries_menu())
    elif message.text == "🌍 الدول":
        prefixes = db.active_prefixes()
        txt = "🌍 *الدول المتاحة:*\n\n" + "\n".join(f"{get_country_info(p)[1]} {name}" for p, name in sorted(prefixes.items()))
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    elif message.text == "📊 إحصائياتي":
        user = db.get_user(uid)
        reqs = user[6] if user else 0
        otps = user[7] if user else 0
        bot.send_message(message.chat.id, t("stats", uid, req=reqs, otp=otps), parse_mode="Markdown")
    elif message.text == "💰 رصيدي":
        user = db.get_user(uid)
        bal = user[4] if user else 0
        site = api.get_balance()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
            refs = c.fetchone()
        ref_count = refs[0] if refs else 0
        bot.send_message(message.chat.id, t("balance", uid, bal=bal, ref=ref_count, site=site), parse_mode="Markdown")
    elif message.text == "🤝 دعوة":
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            ref_code = f"ref{uid}"
            c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?,?)", (uid, ref_code))
            conn.commit()
        link = f"https://t.me/Taker_OTP_BOT?start={ref_code}"
        bot.send_message(message.chat.id, t("invite", uid, link=link), parse_mode="Markdown")
    elif message.text == "🟢 المرور":
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10")
            rows = c.fetchall()
        if not rows:
            bot.send_message(message.chat.id, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic", uid)]
            for prefix, cnt in rows:
                name, flag = get_country_info(prefix)
                svc = detect_service("")
                icon = SERVICE_ICONS.get(svc, "🔐")
                if cnt > 5:
                    lines.append(f"🔥 {flag} {name} {icon} High Traffic")
                else:
                    lines.append(f"{flag} {name}: `{cnt}`")
            bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")
    elif message.text == "🌐 لغة":
        mk = types.InlineKeyboardMarkup()
        mk.add(
            types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        )
        bot.send_message(message.chat.id, "*اختر اللغة / Select language:*", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_lang(call):
    uid = call.from_user.id
    lang = call.data.split("_")[1]
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
        conn.commit()
    bot.answer_callback_query(call.id, "✅ Done / تم" if lang == "en" else "✅ تم")
    start(call.message)

# ════════════════ لوحة الإدارة ════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    mk = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if db.setting("maintenance") != "1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {status}", callback_data="tog_maint"))
    mk.add(types.InlineKeyboardButton("➕ إضافة دولة (رمز)", callback_data="add_prefix_btn"))
    mk.add(types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_prefix"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"))
    mk.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"), types.InlineKeyboardButton("✅ فك", callback_data="unban"))
    mk.add(types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"), types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"), types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main"))
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم*", parse_mode="Markdown", reply_markup=mk)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "tog_maint")
def tog_maint(call):
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ تم")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_prefix_btn")
def add_prefix_btn(call):
    user_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text("*➕ أرسل رمز الدولة فقط (مثال: 22501):*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix_exec(message):
    prefix = message.text.strip()
    name = db.add_prefix(prefix)
    if name:
        _, flag = get_country_info(prefix)
        bot.send_message(message.chat.id, f"✅ تمت إضافة دولة: {flag} {name}", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ كود الدولة غير معروف في قاعدة البيانات", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_prefix")
def del_prefix_menu(call):
    prefixes = db.active_prefixes()
    mk = types.InlineKeyboardMarkup()
    for p, name in sorted(prefixes.items()):
        _, flag = get_country_info(p)
        mk.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"delp_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*اختر الدولة للحذف:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delp_"))
def delp(call):
    prefix = call.data.split("_")[1]
    db.remove_prefix(prefix)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 أرسل الرسالة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = db.all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.03)
        except:
            pass
    bot.send_message(message.chat.id, f"✅ `{cnt}` مستخدم", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"])
def ban_unban(call):
    user_states[call.from_user.id] = call.data
    bot.edit_message_text("*أرسل ID المستخدم:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    action = user_states[message.from_user.id]
    try:
        uid = int(message.text)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (uid,))
            conn.commit()
        bot.send_message(message.chat.id, "✅ تم")
    except:
        bot.send_message(message.chat.id, "❌ خطأ")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "force_sub")
def force_sub(call):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM force_channels WHERE enabled=1")
        chs = c.fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"))
    mk.add(types.InlineKeyboardButton("🔙", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    user_states[message.from_user.id] = ("addch_desc", message.text.strip())
    bot.send_message(message.chat.id, "أرسل وصفاً:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        conn.commit()
    bot.send_message(message.chat.id, "✅ تمت")
    del user_states[message.from_user.id]

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
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data")
def clear_data(call):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for t in ["users", "active_numbers", "otp_logs", "referrals"]:
            c.execute(f"DELETE FROM {t}")
        conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back(call):
    admin_panel(call.message)

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

                        # رسالة للمستخدم
                        if uid:
                            try:
                                user_msg = (
                                    f"*🔐 كود تفعيل جديد*\n\n"
                                    f"🌍 Country: {name} {flag}\n"
                                    f"📱 Phone: `{number}`\n"
                                    f"🔑 OTP: `{code_parts}`\n"
                                    f"{icon} Service: {service}\n"
                                    f"🏆 Reward: 0.0030\n"
                                    f"💵 Balance: 0.0030"
                                )
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                            except:
                                pass

                        # رسالة للجروب
                        for cid in CHAT_IDS:
                            try:
                                group_msg = (
                                    f"*🔐 New OTP Received*\n\n"
                                    f"🌍 {flag} {name} | {icon} {service}\n"
                                    f"📱 `{mask_number(number)}`\n"
                                    f"🔑 `{code_parts}`\n"
                                    f"💲 Rate: 0.001$"
                                )
                                bot.send_message(cid, group_msg, parse_mode="Markdown")
                            except:
                                pass

                        # حفظ في السجلات
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

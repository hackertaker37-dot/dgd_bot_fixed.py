# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════════╗
 ║           TAKER OTP BOT - Professional          ║
 ║           Developer: @hackerTaker               ║
 ║           API: xwdsms.org                        ║
 ╚══════════════════════════════════════════════════╝
"""
import time, requests, json, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8686995713:AAG6fy9oZlGIn8SvnQUY_zMq_Eeo6OJYqRY"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ جميع دول العالم ════════════════
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

DEFAULT_PREFIXES = [
    "22501", "23276", "26134", "44740", "23490", "25471",
    "24910", "49155", "23762", "22178", "22901", "22898",
]

# ════════════════ النصوص ════════════════
T = {
    "lang_select": {"ar": "🌐 *اختر لغتك*\n\nاختر اللغة التي تريد استخدام البوت بها:", "en": "🌐 *Select Your Language*\n\nChoose the language you want to use:"},
    "lang_set": {"ar": "✅ تم تعيين اللغة العربية", "en": "✅ English language set"},
    "welcome": {"ar": "🔰 *أهلاً بك في Taker OTP*\n\n• احصل على أرقام وهمية للتفعيل\n• استقبل الأكواد بشكل فوري\n• ادعُ أصدقاءك واربح رصيداً\n\n*اختر الدولة:*", "en": "🔰 *Welcome to Taker OTP*\n\n• Get virtual numbers for activation\n• Receive codes instantly\n• Invite friends and earn credit\n\n*Select country:*"},
    "choose_country": {"ar": "🌍 *اختر الدولة:*", "en": "🌍 *Select country:*"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم جديد*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ في انتظار الكود...", "en": "✅ *Number Assigned*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ في انتظار الكود...", "en": "🔄 *Number Changed*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً", "en": "⚠️ *Bot under maintenance*\nPlease try again later"},
    "subscribe": {"ar": "🔒 *يجب الاشتراك في القنوات أولاً*", "en": "🔒 *You must subscribe to the channels first*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 إجمالي الطلبات: `{req}`\n🔷 الأكواد المستلمة: `{otp}`", "en": "📊 *Your Statistics*\n\n🔷 Total Requests: `{req}`\n🔷 OTPs Received: `{otp}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 رصيدك: `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 رصيد الموقع: `{site}`\n🏦 الحد الأدنى للسحب: `18.0 USDT`\n\n💡 اربح `0.05 USDT` عن كل صديق", "en": "💰 *Your Balance*\n\n💎 Balance: `{bal:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site Balance: `{site}`\n🏦 Min Withdrawal: `18.0 USDT`\n\n💡 Earn `0.05 USDT` per friend"},
    "invite": {"ar": "🤝 *دعوة الأصدقاء*\n\n🔗 رابط الدعوة الخاص بك:\n`{link}`\n\n💰 تربح `0.05 USDT` عن كل صديق\n📤 شارك الرابط مع أصدقائك", "en": "🤝 *Invite Friends*\n\n🔗 Your referral link:\n`{link}`\n\n💰 Earn `0.05 USDT` per friend\n📤 Share the link with your friends"},
    "traffic_title": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "⚠️ لا توجد أرقام نشطة حالياً", "en": "⚠️ No active numbers at the moment"},
    "high_traffic": {"ar": "🔥 {flag} {name} | حركة مرور عالية", "en": "🔥 {flag} {name} | High Traffic"},
    "prefix_added": {"ar": "✅ *تمت إضافة الدولة بنجاح*\n\n🌍 {flag} {name}\n🔢 الكود: `{prefix}`\n\nأصبحت متاحة للمستخدمين الآن", "en": "✅ *Country Added Successfully*\n\n🌍 {flag} {name}\n🔢 Code: `{prefix}`\n\nNow available for users"},
    "prefix_exists": {"ar": "⚠️ *الدولة موجودة مسبقاً*\n\n🌍 {flag} {name}\n🔢 الكود: `{prefix}`\n\nهذه الدولة موجودة بالفعل في القائمة", "en": "⚠️ *Country Already Exists*\n\n🌍 {flag} {name}\n🔢 Code: `{prefix}`\n\nThis country is already in the list"},
    "prefix_not_found": {"ar": "❌ *كود الدولة غير معروف*\n\nالكود `{prefix}` غير موجود في قاعدة البيانات العالمية\n\nتأكد من الكود وأعد المحاولة", "en": "❌ *Unknown Country Code*\n\nCode `{prefix}` not found in global database\n\nCheck the code and try again"},
    "prefix_removed": {"ar": "✅ *تم حذف الدولة بنجاح*", "en": "✅ *Country Removed Successfully*"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*\n\nمرحباً بك في لوحة إدارة البوت", "en": "*⚙️ Admin Panel*\n\nWelcome to the bot control panel"},
    "admin_add_prefix": {"ar": "*➕ إضافة دولة جديدة*\n\nأرسل كود الدولة فقط\nمثال: `22501`", "en": "*➕ Add New Country*\n\nSend country code only\nExample: `22501`"},
    "admin_del_prefix": {"ar": "*➖ حذف دولة*\n\nاختر الدولة التي تريد حذفها:", "en": "*➖ Delete Country*\n\nSelect the country to delete:"},
    "admin_broadcast": {"ar": "*📢 إذاعة*\n\nأرسل الرسالة التي تريد إرسالها لجميع المستخدمين:", "en": "*📢 Broadcast*\n\nSend the message to all users:"},
    "admin_ban": {"ar": "*🚫 حظر مستخدم*\n\nأرسل ID المستخدم:", "en": "*🚫 Ban User*\n\nSend user ID:"},
    "admin_unban": {"ar": "*✅ فك حظر*\n\nأرسل ID المستخدم:", "en": "*✅ Unban User*\n\nSend user ID:"},
    "admin_done": {"ar": "✅ *تم بنجاح*", "en": "✅ *Done Successfully*"},
    "admin_broadcast_done": {"ar": "✅ *تم الإرسال*\n\nعدد المستلمين: `{cnt}`", "en": "✅ *Sent*\n\nRecipients: `{cnt}`"},
    "otp_user": {"ar": "*🔐 كود تفعيل جديد*\n\n🌍 الدولة: {name} {flag}\n📱 الرقم: `{number}`\n🔑 الكود: `{code}`\n{icon} التطبيق: {service}\n🏆 المكافأة: 0.0030\n💵 الرصيد: 0.0030", "en": "*🔐 New Activation Code*\n\n🌍 Country: {name} {flag}\n📱 Number: `{number}`\n🔑 Code: `{code}`\n{icon} Service: {service}\n🏆 Reward: 0.0030\n💵 Balance: 0.0030"},
    "otp_group": {"ar": "*🔐 كود جديد*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`\n💲 السعر: 0.001$\n\n_⏳ تُحذف تلقائياً بعد 3 دقائق_", "en": "*🔐 New OTP*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`\n💲 Rate: 0.001$\n\n_⏳ Auto-delete in 3 minutes_"},
    "countries_list": {"ar": "🌍 *الدول المتاحة:*\n\n", "en": "🌍 *Available Countries:*\n\n"},
    "check_verified": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified Successfully"},
    "check_failed": {"ar": "❌ لم تشترك بعد", "en": "❌ Not subscribed yet"},
}

def t(key, uid=None, **kw):
    lang = "ar"
    if uid:
        u = db.get_user(uid)
        if u and u[3]:
            lang = u[3]
    txt = T.get(key, {}).get(lang, T.get(key, {}).get("ar", key))
    return txt.format(**kw) if kw else txt

# ════════════════ أسماء الأزرار ════════════════
BTN = {
    "new_num": {"ar": "📱 رقم جديد", "en": "📱 New Number"},
    "countries": {"ar": "🌍 الدول", "en": "🌍 Countries"},
    "stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite": {"ar": "🤝 دعوة", "en": "🤝 Invite"},
    "traffic": {"ar": "🟢 المرور", "en": "🟢 Traffic"},
    "admin": {"ar": "⚙️ الإدارة", "en": "⚙️ Admin"},
    "lang": {"ar": "🌐 اللغة", "en": "🌐 Language"},
}

def btn(key, uid):
    u = db.get_user(uid)
    lang = u[3] if u and u[3] else "ar"
    return BTN[key][lang]

# ════════════════ قاعدة البيانات ════════════════
class Database:
    def __init__(self, path):
        self.path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as c:
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                lang TEXT DEFAULT NULL, balance REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0, total_requests INTEGER DEFAULT 0,
                total_otps INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
                alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
                assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting', otp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
                otp TEXT, service TEXT, country TEXT, timestamp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
                description TEXT, enabled INTEGER DEFAULT 1)''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_prefixes (
                prefix TEXT PRIMARY KEY, name TEXT)''')
            c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
            c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
            for p in DEFAULT_PREFIXES:
                if p in ALL_COUNTRIES:
                    c.execute("INSERT OR IGNORE INTO active_prefixes VALUES (?,?)", (p, ALL_COUNTRIES[p][0]))
            c.commit()

    def setting(self, key, val=None):
        with sqlite3.connect(self.path) as c:
            if val is not None:
                c.execute("REPLACE INTO settings VALUES (?,?)", (key, val))
                c.commit()
                return val
            r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return r[0] if r else None

    def prefixes(self):
        with sqlite3.connect(self.path) as c:
            return {r[0]: r[1] for r in c.execute("SELECT prefix, name FROM active_prefixes").fetchall()}

    def add_prefix(self, p):
        if p in ALL_COUNTRIES:
            name = ALL_COUNTRIES[p][0]
            with sqlite3.connect(self.path) as c:
                # نفحص إذا كانت موجودة مسبقاً
                exists = c.execute("SELECT 1 FROM active_prefixes WHERE prefix=?", (p,)).fetchone()
                if exists:
                    return "exists", name  # موجودة مسبقاً
                c.execute("INSERT OR REPLACE INTO active_prefixes VALUES (?,?)", (p, name))
                c.commit()
            return "added", name  # تمت الإضافة
        return "not_found", None  # غير موجودة

    def remove_prefix(self, p):
        with sqlite3.connect(self.path) as c:
            c.execute("DELETE FROM active_prefixes WHERE prefix=?", (p,))
            c.commit()

    def get_user(self, uid):
        with sqlite3.connect(self.path) as c:
            return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

    def save_user(self, msg):
        uid = msg.from_user.id
        with sqlite3.connect(self.path) as c:
            if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
                c.execute("INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)",
                         (uid, msg.from_user.username, msg.from_user.first_name))
            c.commit()

    def set_lang(self, uid, lang):
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
            c.commit()

    def all_users(self):
        with sqlite3.connect(self.path) as c:
            return [r[0] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]

db = Database(DB_PATH)

# ════════════════ API ════════════════
class API:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"x-api-key": API_KEY, "Content-Type": "application/json"})

    def get(self, p):
        r = self.s.post(f"{BASE_URL}/api/v1/get-number", json={"range": p}, timeout=8)
        d = r.json()
        if not d.get("success"):
            raise Exception(d.get("message", "Error"))
        return d["id"], d["number"]

    def check(self, n):
        try:
            r = self.s.get(f"{BASE_URL}/api/v1/check-otp", params={"number": n}, timeout=6)
            d = r.json()
            return (d.get("status"), d.get("otp")) if d.get("success") else (None, None)
        except:
            return None, None

    def delete(self, aid):
        try:
            self.s.post(f"{BASE_URL}/api/v1/delete-number", json={"id": aid}, timeout=4)
        except:
            pass

    def balance(self):
        try:
            return self.s.get(f"{BASE_URL}/api/v1/balance", timeout=6).json().get("balance", "0")
        except:
            return "0"

api = API()

# ════════════════ دوال مساعدة ════════════════
def clean(n):
    return str(n).replace("+", "").strip()

def extract_otp(txt):
    nums = re.findall(r'\d{4,8}', str(txt))
    return nums[0] if nums else "N/A"

def detect_service(txt):
    t = str(txt).lower()
    for svc, kws in [("WhatsApp",["whatsapp","واتساب"]),("Telegram",["telegram","تيليجرام"]),
        ("Facebook",["facebook","فيسبوك"]),("Instagram",["instagram","انستقرام"]),
        ("Google",["google","gmail","جوجل"]),("Twitter/X",["twitter","تويتر"]),
        ("Discord",["discord"]),("Snapchat",["snapchat","سناب"]),("TikTok",["tiktok"]),
        ("Amazon",["amazon"]),("Apple",["apple","icloud"]),("Microsoft",["microsoft"]),
        ("Uber",["uber"]),("Netflix",["netflix"]),("YouTube",["youtube"])]:
        if any(k in t for k in kws):
            return svc
    return "OTP"

def cinfo(p):
    return ALL_COUNTRIES.get(p, (p, "🏳"))

def mask(n):
    n = str(n)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

def release(uid):
    with sqlite3.connect(DB_PATH) as c:
        for (aid,) in c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)).fetchall():
            api.delete(aid)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
        c.commit()

def assign(uid, aid, num, p):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
                 (aid, clean(num), p, uid, datetime.now().isoformat(), 'waiting'))
        c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
        c.commit()

def get_active():
    with sqlite3.connect(DB_PATH) as c:
        return c.execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'").fetchall()

def check_sub(uid):
    with sqlite3.connect(DB_PATH) as c:
        chs = [r[0] for r in c.execute("SELECT channel_url FROM force_channels WHERE enabled=1").fetchall()]
    if not chs:
        return True
    for url in chs:
        try:
            ch = "@"+url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch, uid).status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    with sqlite3.connect(DB_PATH) as c:
        chs = c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1").fetchall()
    if not chs:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in chs:
        mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return mk

def lang_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    return mk

def delete_later(cid, mid, delay=180):
    time.sleep(delay)
    try:
        bot.delete_message(cid, mid)
    except:
        pass

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(btn("new_num", uid), btn("countries", uid), btn("stats", uid))
    kb.add(btn("balance", uid), btn("invite", uid), btn("traffic", uid))
    kb.add(btn("lang", uid))
    if uid in ADMIN_IDS:
        kb.add(btn("admin", uid))
    return kb

def countries_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for p in sorted(db.prefixes().keys()):
        n, f = cinfo(p)
        btns.append(types.InlineKeyboardButton(f"{f} {n}", callback_data=f"get_{p}"))
    for i in range(0, len(btns), 2):
        mk.row(*btns[i:i+2])
    return mk

def num_actions(uid, p, aid):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{p}_{aid}"),
           types.InlineKeyboardButton("🌍 دولة أخرى", callback_data="menu_countries"))
    mk.row(types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
           types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_main"))
    return mk

def show_home(cid, uid):
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown")
        return

    if not check_sub(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return

    photo = db.setting("welcome_photo")
    txt = t("welcome", uid)
    mk = countries_menu()
    
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    cid = msg.chat.id
    db.save_user(msg)

    args = msg.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        with sqlite3.connect(DB_PATH) as c:
            ref = c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (args[1],)).fetchone()
            if ref:
                c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (ref[0],))
                c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (ref[0],))
            c.commit()

    u = db.get_user(uid)
    if not u or not u[3]:
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
        return

    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data in ["lang_ar", "lang_en"])
def set_lang(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = "ar" if call.data == "lang_ar" else "en"
    db.set_lang(uid, lang)
    bot.answer_callback_query(call.id, "✅ تم" if lang == "ar" else "✅ Done")
    try:
        bot.delete_message(cid, call.message.message_id)
    except:
        pass
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_cb(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if check_sub(uid):
        bot.answer_callback_query(call.id, t("check_verified", uid))
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        show_home(cid, uid)
    else:
        bot.answer_callback_query(call.id, t("check_failed", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_num(call):
    uid = call.from_user.id
    p = call.data.split("_")[1]
    release(uid)
    try:
        aid, num = api.get(p)
        num = clean(num)
        assign(uid, aid, num, p)
        n, f = cinfo(p)
        bot.edit_message_text(t("number_assigned", uid, number=num, flag=f, country=n),
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, p, aid))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def ch_num(call):
    uid = call.from_user.id
    _, p, oa = call.data.split("_")
    if oa:
        api.delete(oa)
    release(uid)
    try:
        aid, num = api.get(p)
        num = clean(num)
        assign(uid, aid, num, p)
        n, f = cinfo(p)
        bot.edit_message_text(t("number_changed", uid, number=num, flag=f, country=n),
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, p, aid))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries", "menu_main"])
def menu_back(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if call.data == "menu_countries":
        bot.edit_message_text(t("choose_country", uid), cid, call.message.message_id,
                              parse_mode="Markdown", reply_markup=countries_menu())
    else:
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        show_home(cid, uid)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text

    if txt == btn("new_num", uid):
        bot.send_message(cid, t("choose_country", uid), parse_mode="Markdown", reply_markup=countries_menu())
    elif txt == btn("countries", uid):
        pfx = db.prefixes()
        msg = t("countries_list", uid) + "\n".join(f"{cinfo(p)[1]} {n}" for p, n in sorted(pfx.items()))
        bot.send_message(cid, msg, parse_mode="Markdown")
    elif txt == btn("stats", uid):
        u = db.get_user(uid)
        bot.send_message(cid, t("stats", uid, req=u[6] if u else 0, otp=u[7] if u else 0), parse_mode="Markdown")
    elif txt == btn("balance", uid):
        u = db.get_user(uid)
        with sqlite3.connect(DB_PATH) as c:
            ref = c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        bot.send_message(cid, t("balance", uid, bal=u[4] if u else 0, ref=ref[0] if ref else 0, site=api.balance()), parse_mode="Markdown")
    elif txt == btn("invite", uid):
        with sqlite3.connect(DB_PATH) as c:
            rc = f"ref{uid}"
            c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, rc))
            c.commit()
        bot.send_message(cid, t("invite", uid, link=f"https://t.me/Taker_OTP_BOT?start={rc}"), parse_mode="Markdown")
    elif txt == btn("traffic", uid):
        with sqlite3.connect(DB_PATH) as c:
            rows = c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
        if not rows:
            bot.send_message(cid, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic_title", uid), ""]
            for p, cnt in rows:
                n, f = cinfo(p)
                lines.append(t("high_traffic", uid, flag=f, name=n) if cnt > 5 else f"{f} {n}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
    elif txt == btn("lang", uid):
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
    elif txt == btn("admin", uid) and uid in ADMIN_IDS:
        admin_panel(cid, uid)

# ════════════════ لوحة الإدارة ════════════════
def admin_panel(cid, uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 مفتوح" if db.setting("maintenance") != "1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {st}", callback_data="tog"))
    mk.add(types.InlineKeyboardButton("➕ إضافة دولة", callback_data="addp"),
           types.InlineKeyboardButton("➖ حذف دولة", callback_data="delp"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="bcast"),
           types.InlineKeyboardButton("🚫 حظر", callback_data="ban"))
    mk.add(types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"),
           types.InlineKeyboardButton("🔗 اشتراك", callback_data="fsub"))
    mk.add(types.InlineKeyboardButton("🖼️ صورة", callback_data="photo"),
           types.InlineKeyboardButton("🗑️ مسح", callback_data="clear"))
    mk.add(types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main"))
    bot.send_message(cid, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

ustates = {}

@bot.callback_query_handler(func=lambda c: c.data == "tog")
def tog(call):
    db.setting("maintenance", "0" if db.setting("maintenance") == "1" else "1")
    bot.answer_callback_query(call.id, "✅")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "addp")
def addp(call):
    ustates[call.from_user.id] = "addp"
    bot.edit_message_text(t("admin_add_prefix", call.from_user.id),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: ustates.get(m.from_user.id) == "addp")
def addp_exe(msg):
    uid = msg.from_user.id
    p = msg.text.strip()
    status, name = db.add_prefix(p)
    
    if status == "added":
        _, f = cinfo(p)
        bot.send_message(msg.chat.id, t("prefix_added", uid, flag=f, name=name, prefix=p), parse_mode="Markdown")
    elif status == "exists":
        _, f = cinfo(p)
        bot.send_message(msg.chat.id, t("prefix_exists", uid, flag=f, name=name, prefix=p), parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, t("prefix_not_found", uid, prefix=p), parse_mode="Markdown")
    
    del ustates[uid]

@bot.callback_query_handler(func=lambda c: c.data == "delp")
def delp(call):
    uid = call.from_user.id
    pfx = db.prefixes()
    if not pfx:
        bot.answer_callback_query(call.id, "لا توجد دول", show_alert=True)
        return
    mk = types.InlineKeyboardMarkup()
    for p, n in sorted(pfx.items()):
        _, f = cinfo(p)
        mk.add(types.InlineKeyboardButton(f"{f} {n}", callback_data=f"delpp_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admback"))
    bot.edit_message_text(t("admin_del_prefix", uid), call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delpp_"))
def delpp(call):
    db.remove_prefix(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "bcast")
def bcast(call):
    ustates[call.from_user.id] = "bcast"
    bot.edit_message_text(t("admin_broadcast", call.from_user.id),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: ustates.get(m.from_user.id) == "bcast")
def bcast_exe(msg):
    uid = msg.from_user.id
    cnt = 0
    for u in db.all_users():
        try:
            bot.copy_message(u, msg.chat.id, msg.message_id)
            cnt += 1
            time.sleep(0.03)
        except:
            pass
    bot.send_message(msg.chat.id, t("admin_broadcast_done", uid, cnt=cnt), parse_mode="Markdown")
    del ustates[uid]

@bot.callback_query_handler(func=lambda c: c.data == "ban")
def ban_p(call):
    ustates[call.from_user.id] = "ban"
    bot.edit_message_text(t("admin_ban", call.from_user.id),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "unban")
def unban_p(call):
    ustates[call.from_user.id] = "unban"
    bot.edit_message_text(t("admin_unban", call.from_user.id),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: ustates.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exe(msg):
    act = ustates[msg.from_user.id]
    try:
        uid = int(msg.text)
        with sqlite3.connect(DB_PATH) as c:
            c.execute(f"UPDATE users SET is_banned={'1' if act=='ban' else '0'} WHERE user_id=?", (uid,))
            c.commit()
        bot.send_message(msg.chat.id, t("admin_done", msg.from_user.id), parse_mode="Markdown")
    except:
        bot.send_message(msg.chat.id, "❌ خطأ")
    del ustates[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "fsub")
def fsub(call):
    uid = call.from_user.id
    with sqlite3.connect(DB_PATH) as c:
        chs = c.execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admback"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch(call):
    ustates[call.from_user.id] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: ustates.get(m.from_user.id) == "addch_url")
def addch_url(msg):
    ustates[msg.from_user.id] = ("addch_desc", msg.text.strip())
    bot.send_message(msg.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(ustates.get(m.from_user.id), tuple))
def addch_desc(msg):
    url = ustates[msg.from_user.id][1]
    desc = msg.text.strip()
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        c.commit()
    bot.send_message(msg.chat.id, "✅ تمت الإضافة")
    del ustates[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (int(call.data.split("_")[1]),))
        c.commit()
    fsub(call)

@bot.callback_query_handler(func=lambda c: c.data == "photo")
def photo(call):
    ustates[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: ustates.get(m.from_user.id) == "photo")
def photo_save(msg):
    db.setting("welcome_photo", msg.photo[-1].file_id)
    bot.send_message(msg.chat.id, "✅ تم حفظ الصورة")
    del ustates[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear")
def clear(call):
    with sqlite3.connect(DB_PATH) as c:
        for t in ["users", "active_numbers", "otp_logs", "referrals"]:
            c.execute(f"DELETE FROM {t}")
        c.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "admback")
def admback(call):
    admin_panel(call.message.chat.id, call.from_user.id)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for aid, num, p, uid in get_active():
                try:
                    st, otp = api.check(num)
                    if st == "success" and otp:
                        svc = detect_service(otp)
                        ic = SERVICE_ICONS.get(svc, "🔐")
                        n, f = cinfo(p)
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
                        if uid:
                            try:
                                bot.send_message(uid, t("otp_user", uid, name=n, flag=f, number=num, code=code, icon=ic, service=svc), parse_mode="Markdown")
                            except:
                                pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid, t("otp_group", None, flag=f, name=n, icon=ic, service=svc, masked=mask(num), code=code), parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except:
                                pass
                        with sqlite3.connect(DB_PATH) as c:
                            c.execute("INSERT INTO otp_logs (number, otp, service, country, timestamp) VALUES (?,?,?,?,?)",
                                     (num, otp, svc, n, datetime.now().isoformat()))
                            c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, aid))
                            c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                            c.commit()
                        api.delete(aid)
                        with sqlite3.connect(DB_PATH) as c:
                            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
                            c.commit()
                    elif st == "expired":
                        api.delete(aid)
                        with sqlite3.connect(DB_PATH) as c:
                            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
                            c.commit()
                except:
                    pass
        except:
            pass
        time.sleep(3)

# ════════════════ Flask ════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

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

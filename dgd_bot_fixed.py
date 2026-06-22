# -*- coding: utf-8 -*-
import time, requests, re, os, sqlite3, threading, logging
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
DB_PATH = "taker_otp_final.db"
DELETE_AFTER = 180  # 3 دقائق

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# جميع دول العالم (للتعرف على الاسم والعلم)
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

# نصوص الترجمة
TEXTS = {
    "lang_select": {"ar": "🌐 *اختر لغتك*", "en": "🌐 *Select Language*"},
    "welcome": {"ar": "🔰 *أهلاً بك في Taker OTP*\n\n• أرقام وهمية للتفعيل\n• أكواد فورية\n\n*اختر الدولة:*", "en": "🔰 *Welcome to Taker OTP*\n\n• Virtual numbers\n• Instant codes\n\n*Select country:*"},
    "choose_country": {"ar": "🌍 *اختر الدولة:*", "en": "🌍 *Select country:*"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...", "en": "✅ *Number Assigned*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...", "en": "🔄 *Number Changed*\n\n📞 `{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ *البوت في الصيانة*", "en": "⚠️ *Bot under maintenance*"},
    "subscribe": {"ar": "🔒 *اشترك في القنوات أولاً*", "en": "🔒 *Subscribe first*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`", "en": "📊 *Your Stats*\n\n🔷 Requests: `{req}`\n🔷 OTPs: `{otp}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 الموقع: `{site}`", "en": "💰 *Balance*\n\n💎 `{bal:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site: `{site}`"},
    "invite": {"ar": "🤝 *دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق", "en": "🤝 *Invite*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` per friend"},
    "traffic_title": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "⚠️ لا توجد أرقام نشطة", "en": "⚠️ No active numbers"},
    "prefix_added": {"ar": "✅ *تمت إضافة الدولة بنجاح*\n\n🌍 {flag} {name}\n🔢 `{prefix}`\n\nأصبحت متاحة للمستخدمين الآن", "en": "✅ *Country Added Successfully*\n\n🌍 {flag} {name}\n🔢 `{prefix}`\n\nNow available for users"},
    "prefix_exists": {"ar": "⚠️ *الدولة موجودة مسبقاً*\n\n🌍 {flag} {name}\n🔢 `{prefix}`", "en": "⚠️ *Country Already Exists*\n\n🌍 {flag} {name}\n🔢 `{prefix}`"},
    "prefix_not_found": {"ar": "❌ *كود غير معروف*\n\n`{prefix}` غير موجود في قاعدة البيانات الدولية\nتأكد من الكود وأعد المحاولة", "en": "❌ *Unknown Code*\n\n`{prefix}` not found in international database\nCheck the code and try again"},
    "prefix_removed": {"ar": "✅ *تم حذف الدولة بنجاح*", "en": "✅ *Country Removed Successfully*"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*", "en": "*⚙️ Admin Panel*"},
    "admin_add_prefix": {"ar": "*➕ أرسل كود الدولة*\nمثال: `22501`\n\nسيتم التعرف على الدولة تلقائياً", "en": "*➕ Send country code*\nExample: `22501`\n\nThe country will be recognized automatically"},
    "admin_del_prefix": {"ar": "*اختر الدولة للحذف:*", "en": "*Select country to delete:*"},
    "admin_broadcast": {"ar": "*📢 أرسل الرسالة:*", "en": "*📢 Send message:*"},
    "admin_ban": {"ar": "*🚫 أرسل ID المستخدم:*", "en": "*🚫 Send user ID:*"},
    "admin_unban": {"ar": "*✅ أرسل ID المستخدم:*", "en": "*✅ Send user ID:*"},
    "admin_done": {"ar": "✅ *تم*", "en": "✅ *Done*"},
    "admin_broadcast_done": {"ar": "✅ *تم الإرسال*\n`{cnt}` مستخدم", "en": "✅ *Sent*\n`{cnt}` users"},
    "otp_user": {"ar": "*🔐 كود جديد*\n\n🌍 {name} {flag}\n📱 `{number}`\n🔑 `{code}`\n{icon} {service}", "en": "*🔐 New OTP*\n\n🌍 {name} {flag}\n📱 `{number}`\n🔑 `{code}`\n{icon} {service}"},
    "otp_group": {"ar": "*🔐 كود جديد*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`", "en": "*🔐 New OTP*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`"},
    "countries_list": {"ar": "🌍 *الدول المتاحة:*\n\n", "en": "🌍 *Available Countries:*\n\n"},
}

def t(key, uid=None, **kw):
    lang = "ar"
    if uid:
        u = db.get_user(uid)
        if u and u[3]:
            lang = u[3]
    txt = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ar", key))
    return txt.format(**kw) if kw else txt

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

# قاعدة البيانات
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            lang TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
            total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
            assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting', otp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
            service TEXT, country TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
            description TEXT, enabled INTEGER DEFAULT 1)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_prefixes (prefix TEXT PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS custom_prefixes 
                     (prefix TEXT PRIMARY KEY, name TEXT, flag TEXT)''')
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        for p in DEFAULT_PREFIXES:
            c.execute("INSERT OR IGNORE INTO active_prefixes VALUES (?)", (p,))
        self.conn.commit()

    def setting(self, key, val=None):
        c = self.conn.cursor()
        if val is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, val))
            self.conn.commit()
            return val
        return c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()[0]

    def prefixes(self):
        return [r[0] for r in self.conn.cursor().execute("SELECT prefix FROM active_prefixes ORDER BY prefix").fetchall()]

    def get_country_from_prefix(self, prefix):
        prefix = re.sub(r'[^\d]', '', str(prefix))
        best_code = None
        best_len = 0
        for code in ALL_COUNTRIES:
            if prefix.startswith(code) and len(code) > best_len:
                best_code = code
                best_len = len(code)
        if best_code:
            return ALL_COUNTRIES[best_code]
        return None

    def add_prefix(self, prefix):
        prefix = re.sub(r'[^\d]', '', str(prefix))
        country = self.get_country_from_prefix(prefix)
        if not country:
            return "not_found", None, None
        name, flag = country
        c = self.conn.cursor()
        if c.execute("SELECT 1 FROM active_prefixes WHERE prefix=?", (prefix,)).fetchone():
            return "exists", name, flag
        c.execute("INSERT OR IGNORE INTO active_prefixes VALUES (?)", (prefix,))
        self.conn.commit()
        return "added", name, flag

    def add_custom_prefix(self, prefix, name, flag=""):
        prefix = re.sub(r'[^\d]', '', str(prefix))
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO active_prefixes VALUES (?)", (prefix,))
        c.execute("INSERT OR REPLACE INTO custom_prefixes VALUES (?,?,?)", (prefix, name, flag))
        self.conn.commit()
        return "added"

    def get_country_info(self, prefix):
        country = self.get_country_from_prefix(prefix)
        if country:
            return country
        c = self.conn.cursor()
        c.execute("SELECT name, flag FROM custom_prefixes WHERE prefix=?", (prefix,))
        row = c.fetchone()
        if row:
            return (row[0], row[1] if row[1] else "")
        return (prefix, "")

    def remove_prefix(self, prefix):
        self.conn.cursor().execute("DELETE FROM active_prefixes WHERE prefix=?", (prefix,))
        self.conn.cursor().execute("DELETE FROM custom_prefixes WHERE prefix=?", (prefix,))
        self.conn.commit()

    def get_user(self, uid):
        return self.conn.cursor().execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

    def save_user(self, msg):
        uid = msg.from_user.id
        c = self.conn.cursor()
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            c.execute("INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)",
                     (uid, msg.from_user.username, msg.from_user.first_name))
            self.conn.commit()

    def set_lang(self, uid, lang):
        self.conn.cursor().execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
        self.conn.commit()

    def all_users(self):
        return [r[0] for r in self.conn.cursor().execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]

db = Database(DB_PATH)

# API
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

# دوال مساعدة
def clean_phone(num):
    return re.sub(r'[^\d]', '', str(num))

def detect_service(txt):
    t = str(txt).lower()
    for svc, kws in [("WhatsApp",["whatsapp","واتساب"]),("Telegram",["telegram","تيليجرام"]),
        ("Facebook",["facebook","فيسبوك"]),("Instagram",["instagram","انستقرام"]),
        ("Google",["google","gmail","جوجل"]),("Twitter/X",["twitter","تويتر"]),
        ("Discord",["discord"]),("Snapchat",["snapchat","سناب"]),("TikTok",["tiktok"]),
        ("Amazon",["amazon"]),("Apple",["apple","icloud"]),("Microsoft",["microsoft"]),
        ("Uber",["uber"]),("Netflix",["netflix"]),("YouTube",["youtube"])]:
        if any(k in t for k in kws): return svc
    return "OTP"

def mask_phone(n):
    n = str(n)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

def release(uid):
    c = db.conn.cursor()
    for (aid,) in c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)).fetchall():
        api.delete(aid)
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    db.conn.commit()

def assign(uid, aid, num, p):
    c = db.conn.cursor()
    c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
             (aid, clean_phone(num), p, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    db.conn.commit()

def get_active():
    return db.conn.cursor().execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'").fetchall()

def check_sub(uid):
    chs = [r[0] for r in db.conn.cursor().execute("SELECT channel_url FROM force_channels WHERE enabled=1").fetchall()]
    if not chs: return True
    for url in chs:
        try:
            ch = "@"+url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch, uid).status not in ["member","administrator","creator"]: return False
        except: return False
    return True

def sub_markup():
    chs = db.conn.cursor().execute("SELECT channel_url, description FROM force_channels WHERE enabled=1").fetchall()
    if not chs: return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in chs: mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return mk

def lang_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    return mk

def delete_later(cid, mid, delay=180):
    time.sleep(delay)
    try: bot.delete_message(cid, mid)
    except: pass

def find_flag_by_name(name):
    for c_name, c_flag in ALL_COUNTRIES.values():
        if name.lower() == c_name.lower():
            return c_flag
    return ""

# البوت
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(btn("new_num", uid), btn("countries", uid), btn("stats", uid))
    kb.add(btn("balance", uid), btn("invite", uid), btn("traffic", uid))
    kb.add(btn("lang", uid))
    if uid in ADMIN_IDS: kb.add(btn("admin", uid))
    return kb

def countries_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(f"{db.get_country_info(p)[1]} {db.get_country_info(p)[0]}".strip(), callback_data=f"get_{p}") for p in db.prefixes()]
    for i in range(0, len(btns), 2): mk.row(*btns[i:i+2])
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
        bot.send_message(cid, t("maintenance", uid), parse_mode="Markdown"); return
    if not check_sub(uid):
        mk = sub_markup()
        if mk: bot.send_message(cid, t("subscribe", uid), parse_mode="Markdown", reply_markup=mk)
        return
    photo = db.setting("welcome_photo")
    txt = t("welcome", uid)
    mk = countries_menu()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

@bot.message_handler(commands=['start'])
def start(msg):
    uid, cid = msg.from_user.id, msg.chat.id
    db.save_user(msg)
    args = msg.text.split()
    if len(args)>1 and args[1].startswith("ref"):
        c = db.conn.cursor()
        ref = c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (args[1],)).fetchone()
        if ref:
            c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (ref[0],))
            c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (ref[0],))
            db.conn.commit()
    if not db.get_user(uid) or not db.get_user(uid)[3]:
        bot.send_message(cid, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
        return
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data in ["lang_ar","lang_en"])
def set_lang(call):
    uid, cid = call.from_user.id, call.message.chat.id
    db.set_lang(uid, "ar" if call.data=="lang_ar" else "en")
    bot.answer_callback_query(call.id, "✅")
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data=="check_sub")
def check_sub_cb(call):
    uid, cid = call.from_user.id, call.message.chat.id
    if check_sub(uid):
        bot.answer_callback_query(call.id, "✅ تم التحقق")
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        show_home(cid, uid)
    else: bot.answer_callback_query(call.id, "❌ لم تشترك", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_num(call):
    uid, p = call.from_user.id, call.data.split("_")[1]
    release(uid)
    try:
        aid, num = api.get(p)
        clean_num = clean_phone(num)
        assign(uid, aid, clean_num, p)
        name, flag = db.get_country_info(p)
        flag_display = f"{flag} " if flag else ""
        bot.edit_message_text(
            f"✅ *تم تخصيص رقم*\n\n📞 `{clean_num}`\n🌍 {flag_display}{name}\n⏳ بانتظار الكود...",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=num_actions(uid, p, aid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def ch_num(call):
    uid, _, p, oa = call.from_user.id, *call.data.split("_")
    if oa: api.delete(oa)
    release(uid)
    try:
        aid, num = api.get(p)
        clean_num = clean_phone(num)
        assign(uid, aid, clean_num, p)
        name, flag = db.get_country_info(p)
        flag_display = f"{flag} " if flag else ""
        bot.edit_message_text(
            f"🔄 *تم تغيير الرقم*\n\n📞 `{clean_num}`\n🌍 {flag_display}{name}\n⏳ بانتظار الكود...",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=num_actions(uid, p, aid)
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries","menu_main"])
def menu_back(call):
    uid, cid = call.from_user.id, call.message.chat.id
    if call.data=="menu_countries":
        bot.edit_message_text(t("choose_country", uid), cid, call.message.message_id,
                              parse_mode="Markdown", reply_markup=countries_menu())
    else:
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        show_home(cid, uid)

# handlers الإدارة
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix_handler(message):
    uid = message.from_user.id
    prefix = message.text.strip()
    status, name, flag = db.add_prefix(prefix)
    if status == "added":
        flag_display = f"{flag} " if flag else ""
        bot.send_message(message.chat.id, f"✅ *تمت إضافة الدولة بنجاح*\n\n🌍 {flag_display}{name}\n🔢 `{prefix}`\n\nأصبحت متاحة للمستخدمين الآن", parse_mode="Markdown")
    elif status == "exists":
        flag_display = f"{flag} " if flag else ""
        bot.send_message(message.chat.id, f"⚠️ *الدولة موجودة مسبقاً*\n\n🌍 {flag_display}{name}\n🔢 `{prefix}`", parse_mode="Markdown")
    else:
        user_states[uid] = ("add_name", prefix)
        bot.send_message(message.chat.id, "لم يتم التعرف على الدولة تلقائياً.\nأرسل اسم الدولة (بالعربية أو الإنجليزية):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_name")
def add_name_handler(message):
    uid = message.from_user.id
    prefix = user_states[uid][1]
    name = message.text.strip()
    flag = find_flag_by_name(name)
    db.add_custom_prefix(prefix, name, flag)
    flag_display = f"{flag} " if flag else ""
    bot.send_message(message.chat.id,
                     f"✅ *تمت إضافة الدولة بنجاح*\n\n🌍 {flag_display}{name}\n🔢 `{prefix}`\n\nأصبحت متاحة للمستخدمين الآن",
                     parse_mode="Markdown")
    del user_states[uid]

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
        except: pass
    bot.send_message(message.chat.id, f"✅ *تم الإرسال*\n`{cnt}` مستخدم", parse_mode="Markdown")
    del user_states[uid]

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    uid = message.from_user.id
    action = user_states[uid]
    try:
        target = int(message.text)
        c = db.conn.cursor()
        c.execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (target,))
        db.conn.commit()
        bot.send_message(message.chat.id, "✅ *تم*", parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ خطأ")
    del user_states[uid]

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url_handler(message):
    user_states[message.from_user.id] = ("addch_desc", message.text.strip())
    bot.send_message(message.chat.id, "أرسل وصفاً:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc_handler(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    c = db.conn.cursor()
    c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    db.conn.commit()
    bot.send_message(message.chat.id, "✅ تمت الإضافة")
    del user_states[message.from_user.id]

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo_handler(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم حفظ الصورة")
    del user_states[message.from_user.id]

# الأزرار العادية
@bot.message_handler(func=lambda m: m.text in [
    "📱 رقم جديد", "🌍 الدول", "📊 إحصائياتي",
    "💰 رصيدي", "🤝 دعوة", "🟢 المرور",
    "📱 New Number", "🌍 Countries", "📊 My Stats",
    "💰 Balance", "🤝 Invite", "🟢 Traffic",
    "🌐 اللغة", "🌐 Language",
    "⚙️ الإدارة", "⚙️ Admin"
])
def handle_buttons(message):
    uid = message.from_user.id
    txt = message.text

    if txt in [btn("new_num", uid)]:
        bot.send_message(message.chat.id, t("choose_country", uid), parse_mode="Markdown", reply_markup=countries_menu())
    elif txt in [btn("countries", uid)]:
        pfx = db.prefixes()
        lines = [f"{db.get_country_info(p)[1]} {db.get_country_info(p)[0]} (`{p}`)".strip() for p in pfx]
        bot.send_message(message.chat.id, t("countries_list", uid) + "\n".join(lines), parse_mode="Markdown")
    elif txt in [btn("stats", uid)]:
        u = db.get_user(uid)
        bot.send_message(message.chat.id, t("stats", uid, req=u[6] if u else 0, otp=u[7] if u else 0), parse_mode="Markdown")
    elif txt in [btn("balance", uid)]:
        u = db.get_user(uid)
        ref = db.conn.cursor().execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        bot.send_message(message.chat.id, t("balance", uid, bal=u[4] if u else 0, ref=ref[0] if ref else 0, site=api.balance()), parse_mode="Markdown")
    elif txt in [btn("invite", uid)]:
        c = db.conn.cursor()
        rc = f"ref{uid}"
        c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, rc))
        db.conn.commit()
        bot.send_message(message.chat.id, t("invite", uid, link=f"https://t.me/Taker_OTP_BOT?start={rc}"), parse_mode="Markdown")
    elif txt in [btn("traffic", uid)]:
        rows = db.conn.cursor().execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
        if not rows: bot.send_message(message.chat.id, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic_title", uid), ""]
            for p, cnt in rows:
                name, flag = db.get_country_info(p)
                display = f"{flag} {name}" if flag else name
                lines.append(f"{display}: `{cnt}`")
            bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")
    elif txt in [btn("lang", uid)]:
        bot.send_message(message.chat.id, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())
    elif txt in [btn("admin", uid)] and uid in ADMIN_IDS:
        admin_panel(message)

# لوحة الإدارة
def admin_panel(message):
    uid = message.from_user.id
    cid = message.chat.id
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 مفتوح" if db.setting("maintenance")!="1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {st}", callback_data="tog_maint"))
    mk.add(types.InlineKeyboardButton("➕ إضافة دولة", callback_data="add_country"),
           types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_country"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
           types.InlineKeyboardButton("🚫 حظر", callback_data="ban"))
    mk.add(types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"),
           types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"))
    mk.add(types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"),
           types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"))
    mk.add(types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main"))
    bot.send_message(cid, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="tog_maint")
def tog_maint(call):
    cur = db.setting("maintenance")=="1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="add_country")
def add_country_cb(call):
    uid = call.from_user.id
    user_states[uid] = "add_prefix"
    bot.edit_message_text(t("admin_add_prefix", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="del_country")
def del_country_cb(call):
    uid = call.from_user.id
    pfx = db.prefixes()
    if not pfx: bot.answer_callback_query(call.id, "لا توجد دول", show_alert=True); return
    mk = types.InlineKeyboardMarkup()
    for p in pfx:
        name, flag = db.get_country_info(p)
        display = f"{flag} {name}".strip()
        mk.add(types.InlineKeyboardButton(display, callback_data=f"delc_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text(t("admin_del_prefix", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    db.remove_prefix(call.data.split("_")[1])
    bot.answer_callback_query(call.id, t("prefix_removed", call.from_user.id))
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def broadcast_cb(call):
    uid = call.from_user.id
    user_states[uid] = "broadcast"
    bot.edit_message_text(t("admin_broadcast", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="ban")
def ban_cb(call):
    uid = call.from_user.id
    user_states[uid] = "ban"
    bot.edit_message_text(t("admin_ban", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="unban")
def unban_cb(call):
    uid = call.from_user.id
    user_states[uid] = "unban"
    bot.edit_message_text(t("admin_unban", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="force_sub")
def force_sub_cb(call):
    uid = call.from_user.id
    chs = db.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="addch")
def addch_cb(call):
    uid = call.from_user.id
    user_states[uid] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch_cb(call):
    ch_id = int(call.data.split("_")[1])
    c = db.conn.cursor()
    c.execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
    db.conn.commit()
    force_sub_cb(call)

@bot.callback_query_handler(func=lambda c: c.data=="set_photo")
def set_photo_cb(call):
    uid = call.from_user.id
    user_states[uid] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="clear_data")
def clear_data_cb(call):
    for t in ["users","active_numbers","otp_logs","referrals"]:
        db.conn.cursor().execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="admin_back")
def admin_back_cb(call):
    admin_panel(call.message)

# حلقة OTP
def otp_loop():
    while True:
        try:
            for aid, num, p, uid in get_active():
                try:
                    st, otp = api.check(num)
                    if st=="success" and otp:
                        svc=detect_service(otp); ic=SERVICE_ICONS.get(svc,"🔐")
                        name, flag = db.get_country_info(p)
                        code=f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try: bot.send_message(uid, t("otp_user", uid, name=name, flag=flag, number=num, code=code, icon=ic, service=svc), parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent=bot.send_message(cid, t("otp_group", None, flag=flag, name=name, icon=ic, service=svc, masked=mask_phone(num), code=code), parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except: pass
                        c=db.conn.cursor(); c.execute("INSERT INTO otp_logs VALUES (NULL,?,?,?,?,?)", (num,otp,svc,name,datetime.now().isoformat()))
                        c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, aid))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                        db.conn.commit(); api.delete(aid); c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,)); db.conn.commit()
                    elif st=="expired": api.delete(aid); c=db.conn.cursor(); c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,)); db.conn.commit()
                except: pass
        except: pass
        time.sleep(3)

# Flask
app = Flask(__name__)
@app.route('/'): return "OK"
@app.route('/health'): return jsonify(status="ok"), 200

def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ Taker OTP Bot Started")
    bot.infinity_polling()

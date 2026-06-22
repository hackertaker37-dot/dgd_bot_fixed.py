# -*- coding: utf-8 -*-
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8686995713:AAFcYLSqdXl6O3x_PVvhkT8WOdJA_MQKHAE"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ جميع دول العالم (للتعرف التلقائي) ════════════════
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

# ════════════════ نصوص الترجمة ════════════════
TEXTS = {
    "lang_select": {"ar": "🌐 *اختر لغتك*", "en": "🌐 *Select Language*"},
    "lang_changed": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to English"},
    "welcome": {"ar": "🔰 *أهلاً بك في Taker OTP*\n\n• أرقام وهمية للتفعيل\n• أكواد فورية\n\n*اختر الدولة:*", "en": "🔰 *Welcome to Taker OTP*\n\n• Virtual numbers\n• Instant codes\n\n*Select country:*"},
    "choose_country": {"ar": "🌍 *اختر الدولة:*", "en": "🌍 *Select country:*"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...", "en": "✅ *Number Assigned*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...", "en": "🔄 *Number Changed*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ *البوت في الصيانة*", "en": "⚠️ *Bot under maintenance*"},
    "subscribe": {"ar": "🔒 *اشترك في القنوات أولاً*", "en": "🔒 *Subscribe first*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`", "en": "📊 *Your Stats*\n\n🔷 Requests: `{req}`\n🔷 OTPs: `{otp}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 الموقع: `{site}`", "en": "💰 *Balance*\n\n💎 `{bal:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site: `{site}`"},
    "invite": {"ar": "🤝 *دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق", "en": "🤝 *Invite*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` per friend"},
    "traffic_title": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "⚠️ لا توجد أرقام نشطة", "en": "⚠️ No active numbers"},
    "prefix_added": {"ar": "✅ *تمت إضافة الدولة*\n\n🌍 {flag} {name}\n🔢 `{prefix}`", "en": "✅ *Country Added*\n\n🌍 {flag} {name}\n🔢 `{prefix}`"},
    "prefix_exists": {"ar": "⚠️ *موجودة مسبقاً*\n\n🌍 {flag} {name}\n🔢 `{prefix}`", "en": "⚠️ *Already Exists*\n\n🌍 {flag} {name}\n🔢 `{prefix}`"},
    "prefix_unknown": {"ar": "❓ *دولة غير معروفة*\n\nأرسل اسم الدولة:", "en": "❓ *Unknown country*\n\nSend country name:"},
    "prefix_removed": {"ar": "✅ *تم حذف الدولة*", "en": "✅ *Country Removed*"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*", "en": "*⚙️ Admin Panel*"},
    "admin_add_prefix": {"ar": "*➕ أرسل كود الدولة*\nمثال: `22501`", "en": "*➕ Send country code*\nExample: `22501`"},
    "admin_del_prefix": {"ar": "*اختر الدولة للحذف:*", "en": "*Select country to delete:*"},
    "admin_broadcast": {"ar": "*📢 أرسل الرسالة:*", "en": "*📢 Send message:*"},
    "admin_ban": {"ar": "*🚫 أرسل ID المستخدم:*", "en": "*🚫 Send user ID:*"},
    "admin_unban": {"ar": "*✅ أرسل ID المستخدم:*", "en": "*✅ Send user ID:*"},
    "admin_done": {"ar": "✅ *تم*", "en": "✅ *Done*"},
    "admin_broadcast_done": {"ar": "✅ *تم الإرسال*\n`{cnt}` مستخدم", "en": "✅ *Sent*\n`{cnt}` users"},
    "admin_stats": {"ar": "📊 *إحصائيات البوت*\n\n👥 المستخدمين: `{users}`\n📱 الأرقام النشطة: `{active}`\n🔑 إجمالي الأكواد: `{otps}`", "en": "📊 *Bot Stats*\n\n👥 Users: `{users}`\n📱 Active numbers: `{active}`\n🔑 Total OTPs: `{otps}`"},
    "otp_user": {"ar": "*🔐 كود جديد*\n\n🌍 {name} {flag}\n📱 `+{number}`\n🔑 `{code}`\n{icon} {service}", "en": "*🔐 New OTP*\n\n🌍 {name} {flag}\n📱 `+{number}`\n🔑 `{code}`\n{icon} {service}"},
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

# ════════════════ قاعدة البيانات ════════════════
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
        c.execute('''CREATE TABLE IF NOT EXISTS custom_prefixes (prefix TEXT PRIMARY KEY, name TEXT)''')
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        for p in DEFAULT_PREFIXES:
            if p in ALL_COUNTRIES:
                c.execute("INSERT OR IGNORE INTO custom_prefixes VALUES (?,?)", (p, ALL_COUNTRIES[p][0]))
        self.conn.commit()

    def setting(self, key, val=None):
        c = self.conn.cursor()
        if val is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, val))
            self.conn.commit()
            return val
        return c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()[0]

    def prefixes(self):
        return [r[0] for r in self.conn.cursor().execute("SELECT prefix FROM custom_prefixes ORDER BY prefix").fetchall()]

    def get_countries(self):
        countries = {}
        for prefix in self.prefixes():
            if prefix in ALL_COUNTRIES:
                countries[prefix] = ALL_COUNTRIES[prefix]
            else:
                name = self.conn.cursor().execute("SELECT name FROM custom_prefixes WHERE prefix=?", (prefix,)).fetchone()
                countries[prefix] = (name[0] if name else prefix, "🏳")
        return countries

    def add_country(self, prefix, name=None):
        if name:
            self.conn.cursor().execute("REPLACE INTO custom_prefixes VALUES (?,?)", (prefix, name))
            self.conn.commit()
            return "added", name, "🏳"
        if prefix in ALL_COUNTRIES:
            name, flag = ALL_COUNTRIES[prefix]
            self.conn.cursor().execute("REPLACE INTO custom_prefixes VALUES (?,?)", (prefix, name))
            self.conn.commit()
            return "added", name, flag
        return "unknown", None, None

    def delete_country(self, prefix):
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
def clean(n): return str(n).replace("+", "").strip()

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

def mask(n): n=str(n); return f"{n[:4]}****{n[-3:]}" if len(n)>7 else n

def release(uid):
    c = db.conn.cursor()
    for (aid,) in c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)).fetchall():
        api.delete(aid)
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    db.conn.commit()

def assign(uid, aid, num, p):
    c = db.conn.cursor()
    c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
             (aid, clean(num), p, uid, datetime.now().isoformat(), 'waiting'))
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

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(btn("new_num", uid), btn("countries", uid), btn("stats", uid))
    kb.add(btn("balance", uid), btn("invite", uid), btn("traffic", uid))
    kb.add(btn("lang", uid))
    if uid in ADMIN_IDS: kb.add(btn("admin", uid))
    return kb

def countries_menu():
    """قائمة الدول بشكل 3 أعمدة احترافية (بدون صفحات)"""
    countries = sorted(db.get_countries().items())
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(f"{flag} {prefix}", callback_data=f"get_{prefix}") for prefix, (name, flag) in countries]
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    mk.row(types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_main"))
    return mk

def num_actions(uid, prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{prefix}_{alloc_id}"),
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

# ════════════════ أوامر ════════════════
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
    lang = "ar" if call.data=="lang_ar" else "en"
    db.set_lang(uid, lang)
    bot.answer_callback_query(call.id, t("lang_changed", uid))
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    # تحديث الكيبورد فقط دون إعادة إرسال الترحيب
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

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
        aid, num = api.get(p); num = clean(num); assign(uid, aid, num, p)
        name, flag = db.get_countries().get(p, (p, "🏳"))
        bot.edit_message_text(t("number_assigned", uid, number=num, flag=flag, country=name),
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, p, aid))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def ch_num(call):
    uid, _, p, oa = call.from_user.id, *call.data.split("_")
    if oa: api.delete(oa)
    release(uid)
    try:
        aid, num = api.get(p); num = clean(num); assign(uid, aid, num, p)
        name, flag = db.get_countries().get(p, (p, "🏳"))
        bot.edit_message_text(t("number_changed", uid, number=num, flag=flag, country=name),
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, p, aid))
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

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: m.text in [
    "📱 رقم جديد", "📱 New Number", "🌍 الدول", "🌍 Countries",
    "📊 إحصائياتي", "📊 My Stats", "💰 رصيدي", "💰 Balance",
    "🤝 دعوة", "🤝 Invite", "🟢 المرور", "🟢 Traffic",
    "🌐 اللغة", "🌐 Language"
])
def handle_buttons(message):
    uid = message.from_user.id
    if message.text in [btn("new_num", uid)]:
        bot.send_message(message.chat.id, t("choose_country", uid), parse_mode="Markdown", reply_markup=countries_menu())
    elif message.text in [btn("countries", uid)]:
        countries = db.get_countries()
        txt = t("countries_list", uid) + "\n".join(f"{flag} {name}" for _, (name, flag) in sorted(countries.items()))
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    elif message.text in [btn("stats", uid)]:
        u = db.get_user(uid)
        bot.send_message(message.chat.id, t("stats", uid, req=u[6] if u else 0, otp=u[7] if u else 0), parse_mode="Markdown")
    elif message.text in [btn("balance", uid)]:
        u = db.get_user(uid)
        ref = db.conn.cursor().execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        bot.send_message(message.chat.id, t("balance", uid, bal=u[4] if u else 0, ref=ref[0] if ref else 0, site=api.balance()), parse_mode="Markdown")
    elif message.text in [btn("invite", uid)]:
        rc = f"ref{uid}"
        db.conn.cursor().execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, rc))
        db.conn.commit()
        bot.send_message(message.chat.id, t("invite", uid, link=f"https://t.me/Taker_OTP_BOT?start={rc}"), parse_mode="Markdown")
    elif message.text in [btn("traffic", uid)]:
        rows = db.conn.cursor().execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
        if not rows: bot.send_message(message.chat.id, t("no_active", uid), parse_mode="Markdown")
        else:
            lines = [t("traffic_title", uid), ""] + [f"{db.get_countries().get(p, (p,'🏳'))[1]} {db.get_countries().get(p, (p,''))[0]}: `{cnt}`" for p, cnt in rows]
            bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")
    elif message.text in [btn("lang", uid)]:
        bot.send_message(message.chat.id, t("lang_select", uid), parse_mode="Markdown", reply_markup=lang_markup())

# ════════════════ لوحة الإدارة الكاملة ════════════════
@bot.message_handler(func=lambda m: m.text in ["⚙️ الإدارة", "⚙️ Admin"] and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    uid = message.from_user.id
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 مفتوح" if db.setting("maintenance")!="1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {st}", callback_data="tog"))
    mk.add(types.InlineKeyboardButton("➕ دولة", callback_data="add_country"),
           types.InlineKeyboardButton("➖ دولة", callback_data="del_country"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
           types.InlineKeyboardButton("👥 مستخدمين", callback_data="users_list"))
    mk.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
           types.InlineKeyboardButton("✅ فك", callback_data="unban"))
    mk.add(types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats_btn"),
           types.InlineKeyboardButton("📄 تقرير", callback_data="report"))
    mk.add(types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"),
           types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
           types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main"))
    bot.send_message(message.chat.id, t("admin_panel", uid), parse_mode="Markdown", reply_markup=mk)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data=="tog")
def tog(call): db.setting("maintenance","0" if db.setting("maintenance")=="1" else "1"); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="add_country")
def add_country(call):
    user_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text(t("admin_add_prefix", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix_exec(message):
    uid = message.from_user.id
    prefix = message.text.strip()
    status, name, flag = db.add_country(prefix)
    if status == "added":
        bot.send_message(message.chat.id, t("prefix_added", uid, flag=flag, name=name, prefix=prefix), parse_mode="Markdown")
        del user_states[uid]
    elif status == "exists":
        name, flag = ALL_COUNTRIES.get(prefix, (prefix, "🏳"))
        bot.send_message(message.chat.id, t("prefix_exists", uid, flag=flag, name=name, prefix=prefix), parse_mode="Markdown")
        del user_states[uid]
    else:
        user_states[uid] = ("add_name", prefix)
        bot.send_message(message.chat.id, t("prefix_unknown", uid), parse_mode="Markdown")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_name")
def add_name_exec(message):
    uid = message.from_user.id
    prefix = user_states[uid][1]
    name = message.text.strip()
    db.add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ تمت إضافة {name}")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data=="del_country")
def del_country(call):
    uid = call.from_user.id
    countries = db.get_countries()
    if not countries: bot.answer_callback_query(call.id,"لا توجد دول", show_alert=True); return
    mk = types.InlineKeyboardMarkup()
    for prefix, (name, flag) in sorted(countries.items()):
        mk.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"delc_{prefix}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text(t("admin_del_prefix", uid), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    db.delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def broadcast(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text(t("admin_broadcast", call.from_user.id), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

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
    bot.send_message(message.chat.id, t("admin_broadcast_done", uid, cnt=cnt), parse_mode="Markdown")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data=="stats_btn")
def stats_btn(call):
    uid = call.from_user.id
    total_users = len(db.all_users())
    active = len(get_active())
    otps = db.conn.cursor().execute("SELECT COUNT(*) FROM otp_logs").fetchone()[0]
    bot.edit_message_text(t("admin_stats", uid, users=total_users, active=active, otps=otps),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="report")
def report(call):
    import tempfile
    uid = call.from_user.id
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(f"Bot Report - {datetime.now()}\n\n")
        f.write("Users:\n")
        for u in db.conn.cursor().execute("SELECT user_id, username FROM users").fetchall():
            f.write(f"{u[0]} @{u[1] or 'N/A'}\n")
        f.write("\nActive Numbers:\n")
        for n in get_active():
            f.write(f"{n[1]} ({n[2]}) assigned to {n[3]}\n")
        fname = f.name
    with open(fname, 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption="📄 تقرير شامل")
    os.remove(fname)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data in ["ban","unban"])
def ban_unban_prompt(call):
    user_states[call.from_user.id] = call.data
    txt = t("admin_ban", call.from_user.id) if call.data=="ban" else t("admin_unban", call.from_user.id)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban","unban"])
def ban_unban_exec(message):
    uid = message.from_user.id
    action = user_states[uid]
    try:
        target = int(message.text)
        db.conn.cursor().execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (target,))
        db.conn.commit()
        bot.send_message(message.chat.id, t("admin_done", uid), parse_mode="Markdown")
    except: bot.send_message(message.chat.id, "❌ خطأ")
    del user_states[uid]

@bot.callback_query_handler(func=lambda c: c.data=="users_list")
def users_list(call):
    users = db.conn.cursor().execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15").fetchall()
    txt = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{uid}` @{un or '—'}" for uid, un in users)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="force_sub")
def force_sub(call):
    chs = db.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs: mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="addch")
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
    db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    db.conn.commit()
    bot.send_message(message.chat.id, "✅ تمت")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    db.conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (int(call.data.split("_")[1]),))
    db.conn.commit()
    force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data=="set_photo")
def set_photo(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data=="clear_data")
def clear_data(call):
    for t in ["users","active_numbers","otp_logs","referrals"]:
        db.conn.cursor().execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="admin_back")
def admin_back(call): admin_panel(call.message)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for aid, num, p, uid in get_active():
                try:
                    st, otp = api.check(num)
                    if st=="success" and otp:
                        svc = detect_service(otp)
                        ic = SERVICE_ICONS.get(svc, "🔐")
                        name, flag = db.get_countries().get(p, (p, "🏳"))
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try: bot.send_message(uid, t("otp_user", uid, name=name, flag=flag, number=num, code=code, icon=ic, service=svc), parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid, t("otp_group", None, flag=flag, name=name, icon=ic, service=svc, masked=mask(num), code=code), parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except: pass
                        c = db.conn.cursor()
                        c.execute("INSERT INTO otp_logs VALUES (NULL,?,?,?,?,?)", (num, otp, svc, name, datetime.now().isoformat()))
                        c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, aid))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                        db.conn.commit()
                        api.delete(aid)
                        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,)); db.conn.commit()
                    elif st=="expired":
                        api.delete(aid)
                        db.conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,)); db.conn.commit()
                except: pass
        except: pass
        time.sleep(3)

# ════════════════ Flask ════════════════
app = Flask(__name__)
@app.route('/'): return "OK"
@app.route('/health'): return jsonify(status="ok"), 200

def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ Taker OTP Bot Started")
    bot.infinity_polling()

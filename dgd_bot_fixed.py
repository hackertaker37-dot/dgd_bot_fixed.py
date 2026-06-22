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
CHAT_IDS = ["-1003789271722"]               # جروب استقبال الأكواد
ADMIN_IDS = [8728019066, 8972941677]       # أنت والإدمن الثاني
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180                         # حذف رسائل الجروب بعد 3 دقائق

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

# ════════════════ النصوص العربية ════════════════
T = {
    "welcome": "🔰 *أهلاً بك في Taker OTP*\n\n• أرقام وهمية للتفعيل\n• أكواد فورية\n\n*اختر الدولة:*",
    "choose_country": "🌍 *اختر الدولة:*",
    "choose_number": "*اختر رقماً من القائمة:*",
    "number_assigned": "✅ *تم تخصيص رقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...",
    "number_changed": "🔄 *تم تغيير الرقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n⏳ بانتظار الكود...",
    "maintenance": "⚠️ *البوت في الصيانة*",
    "stats": "📊 *إحصائياتك*\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`",
    "balance": "💰 *رصيدك*\n\n💎 `{bal:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 الموقع: `{site}`",
    "invite": "🤝 *دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق",
    "traffic_title": "🟢 *حركة المرور*",
    "no_active": "⚠️ لا توجد أرقام نشطة",
    "prefix_added": "✅ *تمت إضافة الدولة*\n\n🌍 {flag} {name}\n🔢 `{prefix}`",
    "prefix_exists": "⚠️ *موجودة مسبقاً*\n\n🌍 {flag} {name}\n🔢 `{prefix}`",
    "prefix_unknown": "❓ *دولة غير معروفة*\n\nأرسل اسم الدولة:",
    "prefix_removed": "✅ *تم حذف الدولة*",
    "admin_panel": "*⚙️ لوحة التحكم*",
    "admin_add_prefix": "*➕ أرسل كود الدولة*\nمثال: `22501`",
    "admin_del_prefix": "*اختر الدولة للحذف:*",
    "admin_broadcast_all": "*📢 أرسل الرسالة للإذاعة للجميع:*",
    "admin_broadcast_user": "*📨 أرسل ID المستخدم:*",
    "admin_ban": "*🚫 أرسل ID المستخدم للحظر:*",
    "admin_unban": "*✅ أرسل ID المستخدم لفك الحظر:*",
    "admin_user_info": "*👤 أرسل ID المستخدم:*",
    "admin_done": "✅ *تم*",
    "admin_broadcast_done": "✅ *تم الإرسال*\n`{cnt}` مستخدم",
    "admin_stats": "📊 *إحصائيات البوت*\n\n👥 المستخدمين: `{users}`\n📱 الأرقام النشطة: `{active}`\n🔑 إجمالي الأكواد: `{otps}`",
    "otp_user": "*🔐 كود جديد*\n\n🌍 {name} {flag}\n📱 `+{number}`\n🔑 `{code}`\n{icon} {service}",
    "otp_group": "*🔐 كود جديد*\n\n🌍 {flag} {name} | {icon} {service}\n📱 `{masked}`\n🔑 `{code}`",
    "countries_list": "🌍 *الدول المتاحة:*\n\n",
}

# ════════════════ قاعدة البيانات ════════════════
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
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
                countries[prefix] = (name[0] if name else prefix, "🌍")
        return countries

    def add_country(self, prefix, name=None):
        if name:
            self.conn.cursor().execute("REPLACE INTO custom_prefixes VALUES (?,?)", (prefix, name))
            self.conn.commit()
            return "added", name, "🌍"
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
def clean(n): return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

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

def delete_later(cid, mid, delay=180):
    time.sleep(delay)
    try: bot.delete_message(cid, mid)
    except: pass

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("📱 رقم جديد", "🌍 الدول", "📊 إحصائياتي")
    kb.add("💰 رصيدي", "🤝 دعوة", "🟢 المرور")
    return kb

def countries_menu():
    countries = sorted(db.get_countries().items())
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(f"{flag} {prefix}", callback_data=f"choose_{prefix}") for prefix, (name, flag) in countries]
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    mk.row(types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_main"))
    return mk

def num_actions(prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{prefix}_{alloc_id}"),
           types.InlineKeyboardButton("🌍 دولة أخرى", callback_data="menu_countries"))
    mk.row(types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
           types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_main"))
    return mk

def show_home(cid, uid):
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, T["maintenance"], parse_mode="Markdown"); return
    if not check_sub(uid):
        mk = sub_markup()
        if mk: bot.send_message(cid, "🔒 *اشترك في القنوات أولاً*", parse_mode="Markdown", reply_markup=mk)
        return
    photo = db.setting("welcome_photo")
    txt = T["welcome"]
    mk = countries_menu()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_kb())

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

@bot.callback_query_handler(func=lambda c: c.data.startswith("choose_"))
def choose_country(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release(uid)
    numbers = []
    for _ in range(3):
        try:
            aid, num = api.get(prefix)
            numbers.append((aid, clean(num)))
        except: pass
    if not numbers:
        bot.answer_callback_query(call.id, "❌ فشل جلب أرقام", show_alert=True)
        return
    user_data[uid] = {"prefix": prefix, "numbers": numbers}
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, (aid, num) in enumerate(numbers[:3]):
        mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
    mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"choose_{prefix}"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_countries"))
    name, flag = db.get_countries().get(prefix, (prefix, "🌍"))
    bot.edit_message_text(
        f"{T['choose_number']}\n\n🌍 {flag} {name}",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=mk
    )

user_data = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick_number(call):
    uid = call.from_user.id
    if uid not in user_data:
        bot.answer_callback_query(call.id, "انتهت الجلسة", show_alert=True)
        return
    idx = int(call.data.split("_")[1])
    numbers = user_data[uid].get("numbers", [])
    prefix = user_data[uid].get("prefix")
    if idx >= len(numbers):
        bot.answer_callback_query(call.id, "رقم غير صالح")
        return
    aid, num = numbers[idx]
    for i, (a, n) in enumerate(numbers):
        if i != idx:
            api.delete(a)
    assign(uid, aid, num, prefix)
    name, flag = db.get_countries().get(prefix, (prefix, "🌍"))
    bot.edit_message_text(T["number_assigned"].format(number=num, flag=flag, country=name),
                          call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=num_actions(prefix, aid))
    del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def ch_num(call):
    uid, _, p, oa = call.from_user.id, *call.data.split("_")
    if oa: api.delete(oa)
    release(uid)
    numbers = []
    for _ in range(3):
        try:
            aid, num = api.get(p)
            numbers.append((aid, clean(num)))
        except: pass
    if not numbers:
        bot.answer_callback_query(call.id, "❌ فشل جلب أرقام جديدة", show_alert=True)
        return
    user_data[uid] = {"prefix": p, "numbers": numbers}
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, (aid, num) in enumerate(numbers[:3]):
        mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
    mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"ch_{p}_0"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="menu_countries"))
    name, flag = db.get_countries().get(p, (p, "🌍"))
    bot.edit_message_text(
        f"{T['choose_number']}\n\n🌍 {flag} {name}",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=mk
    )

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries","menu_main"])
def menu_back(call):
    uid, cid = call.from_user.id, call.message.chat.id
    if call.data=="menu_countries":
        bot.edit_message_text(T["choose_country"], cid, call.message.message_id,
                              parse_mode="Markdown", reply_markup=countries_menu())
    else:
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        show_home(cid, uid)

# ════════════════ المعالج الموحد للرسائل ════════════════
@bot.message_handler(func=lambda m: True)
def universal_handler(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text

    # حالات الإدارة أولاً
    state = admin_states.get(uid)
    if state == "add_prefix":
        prefix = txt.strip()
        status, name, flag = db.add_country(prefix)
        if status == "added":
            bot.send_message(cid, T["prefix_added"].format(flag=flag, name=name, prefix=prefix), parse_mode="Markdown")
        elif status == "exists":
            name, flag = ALL_COUNTRIES.get(prefix, (prefix, "🌍"))
            bot.send_message(cid, T["prefix_exists"].format(flag=flag, name=name, prefix=prefix), parse_mode="Markdown")
        else:
            admin_states[uid] = ("add_name", prefix)
            bot.send_message(cid, T["prefix_unknown"], parse_mode="Markdown")
            return
        del admin_states[uid]
        return

    if state == "broadcast_all":
        users = db.all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.03)
            except: pass
        bot.send_message(cid, T["admin_broadcast_done"].format(cnt=cnt), parse_mode="Markdown")
        del admin_states[uid]
        return

    if state == "broadcast_user":
        try:
            target = int(txt)
            bot.copy_message(target, cid, message.message_id)
            bot.send_message(cid, f"✅ تم الإرسال للمستخدم {target}")
        except: bot.send_message(cid, "❌ فشل الإرسال")
        del admin_states[uid]
        return

    if state in ["ban", "unban"]:
        try:
            target = int(txt)
            db.conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?", (target,))
            db.conn.commit()
            bot.send_message(cid, T["admin_done"], parse_mode="Markdown")
        except: bot.send_message(cid, "❌ خطأ")
        del admin_states[uid]
        return

    if state == "user_info":
        try:
            target = int(txt)
            u = db.get_user(target)
            if u:
                info = f"👤 *معلومات المستخدم*\n🆔: `{u[0]}`\n👤: @{u[1] or '—'}\n🚫: {'محظور' if u[2] else 'نشط'}"
                bot.send_message(cid, info, parse_mode="Markdown")
            else: bot.send_message(cid, "❌ غير موجود")
        except: bot.send_message(cid, "❌ خطأ")
        del admin_states[uid]
        return

    if state == "addch_url":
        admin_states[uid] = ("addch_desc", txt.strip())
        bot.send_message(cid, "أرسل وصفاً:")
        return

    if isinstance(state, tuple) and state[0] == "addch_desc":
        url = state[1]
        desc = txt.strip()
        db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        db.conn.commit()
        bot.send_message(cid, "✅ تمت")
        del admin_states[uid]
        return

    if isinstance(state, tuple) and state[0] == "add_name":
        prefix = state[1]
        name = txt.strip()
        db.add_country(prefix, name)
        bot.send_message(cid, f"✅ تمت إضافة {name}")
        del admin_states[uid]
        return

    # الأزرار العادية
    if txt == "📱 رقم جديد":
        bot.send_message(cid, T["choose_country"], parse_mode="Markdown", reply_markup=countries_menu())
    elif txt == "🌍 الدول":
        countries = db.get_countries()
        msg = T["countries_list"] + "\n".join(f"{flag} {name}" for _, (name, flag) in sorted(countries.items()))
        bot.send_message(cid, msg, parse_mode="Markdown")
    elif txt == "📊 إحصائياتي":
        u = db.get_user(uid)
        bot.send_message(cid, T["stats"].format(req=u[6] if u else 0, otp=u[7] if u else 0), parse_mode="Markdown")
    elif txt == "💰 رصيدي":
        u = db.get_user(uid)
        ref = db.conn.cursor().execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        bot.send_message(cid, T["balance"].format(bal=u[4] if u else 0, ref=ref[0] if ref else 0, site=api.balance()), parse_mode="Markdown")
    elif txt == "🤝 دعوة":
        rc = f"ref{uid}"
        db.conn.cursor().execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, rc))
        db.conn.commit()
        bot.send_message(cid, T["invite"].format(link=f"https://t.me/Taker_OTP_BOT?start={rc}"), parse_mode="Markdown")
    elif txt == "🟢 المرور":
        rows = db.conn.cursor().execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
        if not rows: bot.send_message(cid, T["no_active"], parse_mode="Markdown")
        else:
            lines = [T["traffic_title"], ""] + [f"{db.get_countries().get(p, (p,'🌍'))[1]} {db.get_countries().get(p, (p,''))[0]}: `{cnt}`" for p, cnt in rows]
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
    elif txt == "⚙️ الإدارة" and uid in ADMIN_IDS:
        admin_panel(cid, uid)

# ════════════════ لوحة الإدارة الكاملة ════════════════
def admin_panel(cid, uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 مفتوح" if db.setting("maintenance")!="1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {st}", callback_data="tog"))
    mk.add(types.InlineKeyboardButton("➕ دولة", callback_data="add_country"),
           types.InlineKeyboardButton("➖ دولة", callback_data="del_country"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="broadcast_all_btn"),
           types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="broadcast_user_btn"))
    mk.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban_btn"),
           types.InlineKeyboardButton("✅ فك", callback_data="unban_btn"))
    mk.add(types.InlineKeyboardButton("👤 معلومات", callback_data="user_info_btn"),
           types.InlineKeyboardButton("👥 مستخدمين", callback_data="users_list"))
    mk.add(types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats_btn"),
           types.InlineKeyboardButton("📄 تقرير", callback_data="report"))
    mk.add(types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"),
           types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
           types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main"))
    bot.send_message(cid, T["admin_panel"], parse_mode="Markdown", reply_markup=mk)

admin_states = {}

@bot.callback_query_handler(func=lambda c: c.data=="tog")
def tog(call): db.setting("maintenance","0" if db.setting("maintenance")=="1" else "1"); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="add_country")
def add_country(call):
    admin_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text(T["admin_add_prefix"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="del_country")
def del_country(call):
    uid = call.from_user.id
    countries = db.get_countries()
    if not countries: bot.answer_callback_query(call.id,"لا توجد دول", show_alert=True); return
    mk = types.InlineKeyboardMarkup()
    for prefix, (name, flag) in sorted(countries.items()):
        mk.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"delc_{prefix}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text(T["admin_del_prefix"], call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    db.delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="broadcast_all_btn")
def broadcast_all_btn(call):
    admin_states[call.from_user.id] = "broadcast_all"
    bot.edit_message_text(T["admin_broadcast_all"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="broadcast_user_btn")
def broadcast_user_btn(call):
    admin_states[call.from_user.id] = "broadcast_user"
    bot.edit_message_text(T["admin_broadcast_user"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="ban_btn")
def ban_btn(call):
    admin_states[call.from_user.id] = "ban"
    bot.edit_message_text(T["admin_ban"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="unban_btn")
def unban_btn(call):
    admin_states[call.from_user.id] = "unban"
    bot.edit_message_text(T["admin_unban"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="user_info_btn")
def user_info_btn(call):
    admin_states[call.from_user.id] = "user_info"
    bot.edit_message_text(T["admin_user_info"], call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="users_list")
def users_list(call):
    users = db.conn.cursor().execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15").fetchall()
    txt = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{uid}` @{un or '—'}" for uid, un in users)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="stats_btn")
def stats_btn(call):
    total_users = len(db.all_users())
    active = len(get_active())
    otps = db.conn.cursor().execute("SELECT COUNT(*) FROM otp_logs").fetchone()[0]
    bot.edit_message_text(T["admin_stats"].format(users=total_users, active=active, otps=otps),
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="report")
def report(call):
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(f"Bot Report - {datetime.now()}\n\nUsers:\n")
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

@bot.callback_query_handler(func=lambda c: c.data=="force_sub")
def force_sub(call):
    chs = db.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()
    mk = types.InlineKeyboardMarkup()
    for ch in chs: mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="addch")
def addch(call):
    admin_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    db.conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (int(call.data.split("_")[1]),))
    db.conn.commit()
    force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data=="set_photo")
def set_photo(call):
    admin_states[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: admin_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم")
    del admin_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data=="clear_data")
def clear_data(call):
    for t in ["users","active_numbers","otp_logs","referrals"]:
        db.conn.cursor().execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="admin_back")
def admin_back(call): admin_panel(call.message.chat.id, call.from_user.id)

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
                        name, flag = db.get_countries().get(p, (p, "🌍"))
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try: bot.send_message(uid, T["otp_user"].format(name=name, flag=flag, number=num, code=code, icon=ic, service=svc), parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid, T["otp_group"].format(flag=flag, name=name, icon=ic, service=svc, masked=mask(num), code=code), parse_mode="Markdown")
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

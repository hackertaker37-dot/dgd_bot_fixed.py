# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════╗
 ║     TAKER OTP BOT - نسخة احترافية       ║
 ║     Developer: @hackerTaker             ║
 ║     API: xwdsms.org                      ║
 ╚══════════════════════════════════════════╝
"""
import time, requests, json, re, os, sqlite3, threading, traceback, random, logging
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات الأساسية ════════════════
BOT_TOKEN = "8686995713:AAG6fy9oZlGIn8SvnQUY_zMq_Eeo6OJYqRY"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_bot.db"

# ════════════════ إعدادات التسجيل ════════════════
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ الدول المتاحة (مرة واحدة) ════════════════
AVAILABLE_COUNTRIES = {
    "22501": ("ساحل العاج", "🇨🇮"),
    "22507": ("ساحل العاج", "🇨🇮"),
    "23276": ("سيراليون", "🇸🇱"),
    "26134": ("مدغشقر", "🇲🇬"),
    "44740": ("المملكة المتحدة", "🇬🇧"),
    "23490": ("نيجيريا", "🇳🇬"),
    "25471": ("كينيا", "🇰🇪"),
    "24910": ("السودان", "🇸🇩"),
    "49155": ("ألمانيا", "🇩🇪"),
    "23762": ("الكاميرون", "🇨🇲"),
    "22178": ("السنغال", "🇸🇳"),
    "22901": ("بنين", "🇧🇯"),
    "22898": ("توجو", "🇹🇬"),
}

# ════════════════ قاعدة البيانات ════════════════
class Database:
    def __init__(self, path):
        self.path = path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT,
                first_name TEXT, balance REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0, total_requests INTEGER DEFAULT 0,
                total_otps INTEGER DEFAULT 0, first_seen TEXT, last_seen TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
                alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT,
                assigned_to INTEGER, created_at TEXT,
                status TEXT DEFAULT 'waiting', otp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT,
                otp TEXT, service TEXT, timestamp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE,
                ref_count INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT UNIQUE, description TEXT,
                enabled INTEGER DEFAULT 1)''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS custom_prefixes (
                prefix TEXT PRIMARY KEY, name TEXT)''')
            c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
            c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
            conn.commit()

    def get_setting(self, key):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = c.fetchone()
        return row[0] if row else None

    def set_setting(self, key, value):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
            conn.commit()

    def get_countries(self):
        countries = dict(AVAILABLE_COUNTRIES)
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("SELECT prefix, name FROM custom_prefixes")
            for prefix, name in c.fetchall():
                if prefix not in countries:
                    countries[prefix] = (name, "🏳")
        return countries

    def add_country(self, prefix, name):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO custom_prefixes VALUES (?,?)", (prefix, name))
            conn.commit()

    def delete_country(self, prefix):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM custom_prefixes WHERE prefix=?", (prefix,))
            conn.commit()

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
                                     json={"range": prefix}, timeout=10)
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
                                    params={"number": number}, timeout=8)
            data = resp.json()
            if data.get("success"):
                return data.get("status"), data.get("otp")
            return None, None
        except:
            return None, None

    def delete_number(self, alloc_id):
        try:
            self.session.post(f"{self.base}/api/v1/delete-number",
                              json={"id": alloc_id}, timeout=5)
            return True
        except:
            return False

    def get_balance(self):
        try:
            resp = self.session.get(f"{self.base}/api/v1/balance", timeout=8)
            return resp.json().get("balance", "0")
        except:
            return "0"

api = XWDSMS()

# ════════════════ دوال مساعدة ════════════════
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
                  (alloc_id, number, prefix, uid, datetime.now().isoformat(), 'waiting'))
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
        kb.add("⚙️ الإدارة")
    return kb

def build_countries_menu():
    """قائمة الدول بتصميم احترافي مع الأعلام"""
    countries = db.get_countries()
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for prefix, (name, flag) in sorted(countries.items()):
        display = f"{flag} {name}"
        buttons.append(types.InlineKeyboardButton(display, callback_data=f"get_{prefix}"))
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])
    return markup

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

    if db.get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, "⚠️ *البوت في وضع الصيانة*", parse_mode="Markdown")
        return

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
        if not c.fetchone():
            c.execute("INSERT INTO users (user_id, username, first_name, first_seen, last_seen) VALUES (?,?,?,?,?)",
                      (uid, message.from_user.username, message.from_user.first_name, now, now))
        else:
            c.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now, uid))
        conn.commit()

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
            bot.send_message(cid, "🔒 *اشترك أولاً*", parse_mode="Markdown", reply_markup=mk)
        return

    photo = db.get_setting("welcome_photo")
    txt = (
        "*🔰 أهلاً بك في بوت Taker OTP*\n\n"
        "• احصل على أرقام وهمية للتفعيل\n"
        "• استقبل الأكواد بشكل فوري\n"
        "• ادعُ أصدقاءك واربح رصيداً\n\n"
        "*اختر الدولة:*"
    )
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
        assign_number(uid, alloc_id, number, prefix)
        name, flag = db.get_countries().get(prefix, (prefix, "🏳"))
        now = datetime.now().strftime("%H:%M:%S")
        msg = (
            f"*✅ تم تخصيص رقم*\n\n"
            f"📞 `+{number}`\n"
            f"🌍 {flag} {name}\n"
            f"🕒 {now}\n"
            f"⏳ في انتظار الكود..."
        )
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
        assign_number(uid, alloc_id, number, prefix)
        name, flag = db.get_countries().get(prefix, (prefix, "🏳"))
        now = datetime.now().strftime("%H:%M:%S")
        msg = (
            f"*🔄 تم تغيير الرقم*\n\n"
            f"📞 `+{number}`\n"
            f"🌍 {flag} {name}\n"
            f"🕒 {now}\n"
            f"⏳ في انتظار الكود..."
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=number_actions(prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_countries", "menu_main"])
def menu_back(call):
    if call.data == "menu_countries":
        bot.edit_message_text("*اختر الدولة:*", call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=build_countries_menu())
    else:
        start(call.message)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: m.text in [
    "📱 رقم جديد", "🌍 الدول", "📊 إحصائياتي",
    "💰 رصيدي", "🤝 دعوة", "🟢 المرور"
])
def handle_buttons(message):
    uid = message.from_user.id
    if message.text == "📱 رقم جديد":
        bot.send_message(message.chat.id, "*اختر الدولة:*", parse_mode="Markdown", reply_markup=build_countries_menu())
    elif message.text == "🌍 الدول":
        countries = db.get_countries()
        txt = "*🌍 الدول المتاحة:*\n\n" + "\n".join(f"{flag} {name}" for _, (name, flag) in sorted(countries.items()))
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    elif message.text == "📊 إحصائياتي":
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT total_requests, total_otps FROM users WHERE user_id=?", (uid,))
            row = c.fetchone()
            reqs, otps = row if row else (0, 0)
        msg = f"*📊 إحصائياتك*\n\n🔷 الطلبات: `{reqs}`\n🔷 الأكواد: `{otps}`"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "💰 رصيدي":
        bal = api.get_balance()
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
            ub = c.fetchone()
            c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
            refs = c.fetchone()
        user_bal = ub[0] if ub else 0
        ref_count = refs[0] if refs else 0
        msg = (
            f"*💰 رصيدك*\n\n"
            f"💎 رصيدك: `{user_bal:.3f} USDT`\n"
            f"👤 الإحالات: `{ref_count}`\n"
            f"🏦 رصيد الموقع: `{bal}`\n"
            f"🏦 الحد الأدنى: `18.0 USDT`"
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "🤝 دعوة":
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?,?)", (uid, f"ref{uid}"))
            conn.commit()
        link = f"https://t.me/Taker_OTP_BOT?start=ref{uid}"
        msg = f"*🤝 دعوة الأصدقاء*\n\n🔗 رابطك:\n`{link}`\n\n💰 تربح `0.05 USDT` عن كل صديق"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "🟢 المرور":
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC")
            rows = c.fetchall()
        if not rows:
            txt = "لا توجد أرقام نشطة"
        else:
            countries = db.get_countries()
            lines = []
            for prefix, cnt in rows[:5]:
                name, flag = countries.get(prefix, (prefix, "🏳"))
                lines.append(f"{flag} {name}: `{cnt}`")
            txt = "*🟢 حركة المرور*\n\n" + "\n".join(lines)
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")

# ════════════════ لوحة الإدارة ════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    mk = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if db.get_setting("maintenance") != "1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {status}", callback_data="tog_maint"))
    mk.add(
        types.InlineKeyboardButton("➕ دولة", callback_data="add_country"),
        types.InlineKeyboardButton("➖ دولة", callback_data="del_country")
    )
    mk.add(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 مستخدمين", callback_data="users_list")
    )
    mk.add(
        types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
        types.InlineKeyboardButton("✅ فك", callback_data="unban")
    )
    mk.add(
        types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"),
        types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo")
    )
    mk.add(
        types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
        types.InlineKeyboardButton("↩️ خروج", callback_data="menu_main")
    )
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم*", parse_mode="Markdown", reply_markup=mk)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "tog_maint")
def tog_maint(call):
    cur = db.get_setting("maintenance") == "1"
    db.set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "تم")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country")
def add_country(call):
    user_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text("*➕ أرسل Prefix:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix(message):
    user_states[message.from_user.id] = ("add_name", message.text.strip())
    bot.send_message(message.chat.id, "أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple))
def add_name(message):
    prefix = user_states[message.from_user.id][1]
    name = message.text.strip()
    db.add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ تمت إضافة {name}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country")
def del_country(call):
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup()
    for prefix, (name, flag) in countries.items():
        mk.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"delc_{prefix}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*اختر الدولة:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    prefix = call.data.split("_")[1]
    db.delete_country(prefix)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 أرسل الرسالة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0")
        users = [r[0] for r in c.fetchall()]
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
        bot.send_message(message.chat.id, f"✅ تم")
    except:
        bot.send_message(message.chat.id, "❌ خطأ")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "users_list")
def users_list(call):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15")
        rows = c.fetchall()
    txt = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{uid}` @{un or '—'}" for uid, un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

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
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

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
    db.set_setting("welcome_photo", message.photo[-1].file_id)
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
                        countries = db.get_countries()
                        name, flag = countries.get(prefix, (prefix, "🏳"))
                        if uid:
                            try:
                                bot.send_message(uid,
                                    f"*🔐 كود جديد*\n\n📞 `+{number}`\n🌍 {flag} {name}\n🛠 {service}\n🔢 `{otp}`",
                                    parse_mode="Markdown")
                            except:
                                pass
                        for cid in CHAT_IDS:
                            try:
                                bot.send_message(cid,
                                    f"*🔐 كود جديد*\n📞 `{mask_number(number)}`\n🌍 {flag} {name}\n🛠 {service}\n🔢 `{otp}`",
                                    parse_mode="Markdown")
                            except:
                                pass
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
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
    logger.info("✅ البوت يعمل...")
    bot.infinity_polling()

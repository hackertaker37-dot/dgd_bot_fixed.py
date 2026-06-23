# -*- coding: utf-8 -*-
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8686995713:AAG2nrHUSeGi3UZhbdZCYHe0jdnWxTSqduI"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_bot.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

SERVICE_ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "Google": "🔍", "Twitter/X": "🐦", "Discord": "🎮", "Snapchat": "👻",
    "TikTok": "🎵", "Amazon": "📦", "Apple": "🍎", "Microsoft": "🪟",
    "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️", "OTP": "🔐",
}

# ════════════════ API Functions ════════════════
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        return data["id"], data["number"]
    except Exception as e:
        raise Exception(f"خطأ: {e}")

def api_check_otp(number):
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=10)
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

# ════════════════ قاعدة البيانات ════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO custom_prefixes VALUES (?,?)", (prefix, name))
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
    c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_all_countries():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix, name FROM custom_prefixes ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_prefixes VALUES (?,?)", (prefix, name))
    conn.commit()
    conn.close()

def delete_country(prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM custom_prefixes WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()

# ════════════════ دوال مساعدة ════════════════
def save_user(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)",
                  (uid, message.from_user.username, message.from_user.first_name))
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
    c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
              (alloc_id, number, prefix, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
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

def log_otp(number, otp, service, uid=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, service, country, timestamp) VALUES (?,?,?,?,?)",
              (number, otp, service, get_all_countries().get(uid, ""), datetime.now().isoformat()))
    conn.commit()
    conn.close()

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

def mask_number(num):
    n = str(num)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

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
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            member = bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return mk

def delete_later(cid, mid, delay=180):
    time.sleep(delay)
    try: bot.delete_message(cid, mid)
    except: pass

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
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for prefix, name in sorted(countries.items()):
        flag = "🌍"
        for code, (cname, cflag) in {
            "225": ("ساحل العاج", "🇨🇮"), "232": ("سيراليون", "🇸🇱"),
            "234": ("نيجيريا", "🇳🇬"), "249": ("السودان", "🇸🇩"),
            "254": ("كينيا", "🇰🇪"), "261": ("مدغشقر", "🇲🇬"),
            "44": ("المملكة المتحدة", "🇬🇧"), "49": ("ألمانيا", "🇩🇪"),
            "237": ("الكاميرون", "🇨🇲"), "221": ("السنغال", "🇸🇳"),
            "229": ("بنين", "🇧🇯"), "228": ("توجو", "🇹🇬"),
        }.items():
            if prefix.startswith(code):
                flag = cflag
                break
        buttons.append(types.InlineKeyboardButton(f"{flag} {prefix}", callback_data=f"getnum_{prefix}"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    markup.row(types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return markup

def number_actions(prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{prefix}_{alloc_id}"),
           types.InlineKeyboardButton("🌍 دولة أخرى", callback_data="country_menu"))
    mk.row(types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
           types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return mk

# ════════════════ أوامر البوت ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id

    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, "⚠️ *البوت في وضع الصيانة*", parse_mode="Markdown")
        return

    save_user(message)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)

    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(cid, "🔒 *اشترك أولاً*", parse_mode="Markdown", reply_markup=mk)
        return

    photo = get_setting("welcome_photo")
    txt = ("🔰 *أهلاً بك في Taker OTP*\n\n"
           "• أرقام وهمية للتفعيل\n"
           "• أكواد فورية\n\n"
           "*اختر الدولة:*")
    mk = build_countries_menu()
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def get_number(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release_user_number(uid)
    numbers = []
    for _ in range(3):
        try:
            aid, num = api_get_number(prefix)
            numbers.append((aid, clean(num)))
        except: pass
    if not numbers:
        bot.answer_callback_query(call.id, "❌ فشل جلب أرقام", show_alert=True)
        return
    user_data[uid] = {"prefix": prefix, "numbers": numbers}
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, (aid, num) in enumerate(numbers[:3]):
        mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
    mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"getnum_{prefix}"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="country_menu"))
    name = get_all_countries().get(prefix, prefix)
    bot.edit_message_text(f"*اختر رقماً:*\n\n🌍 {name}", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

user_data = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick_number(call):
    uid = call.from_user.id
    if uid not in user_data: return
    idx = int(call.data.split("_")[1])
    numbers = user_data[uid].get("numbers", [])
    prefix = user_data[uid].get("prefix")
    if idx >= len(numbers): return
    aid, num = numbers[idx]
    for i, (a, n) in enumerate(numbers):
        if i != idx: api_delete_number(a)
    assign_number(uid, aid, num, prefix)
    name = get_all_countries().get(prefix, prefix)
    bot.edit_message_text(f"✅ *تم تخصيص رقم*\n\n📞 `+{num}`\n🌍 {name}\n⏳ بانتظار الكود...",
                          call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=number_actions(prefix, aid))
    del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    uid = call.from_user.id
    _, prefix, old_alloc = call.data.split("_")
    if old_alloc: api_delete_number(old_alloc)
    release_user_number(uid)
    numbers = []
    for _ in range(3):
        try:
            aid, num = api_get_number(prefix)
            numbers.append((aid, clean(num)))
        except: pass
    if not numbers:
        bot.answer_callback_query(call.id, "❌ فشل جلب أرقام جديدة", show_alert=True)
        return
    user_data[uid] = {"prefix": prefix, "numbers": numbers}
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, (aid, num) in enumerate(numbers[:3]):
        mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
    mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"ch_{prefix}_0"))
    mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="country_menu"))
    name = get_all_countries().get(prefix, prefix)
    bot.edit_message_text(f"*اختر رقماً:*\n\n🌍 {name}", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_menu(call):
    if call.data == "country_menu":
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
        countries = get_all_countries()
        txt = "*🌍 الدول المتاحة:*\n\n" + "\n".join(f"• `{p}` - {n}" for p, n in countries.items())
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    elif message.text == "📊 إحصائياتي":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT total_requests, total_otps FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()
        conn.close()
        reqs, otps = row if row else (0, 0)
        bot.send_message(message.chat.id, f"📊 *إحصائياتك*\n\n🔷 الطلبات: `{reqs}`\n🔷 الأكواد: `{otps}`", parse_mode="Markdown")
    elif message.text == "💰 رصيدي":
        bal = api_get_balance()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        ub = c.fetchone()
        c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
        refs = c.fetchone()
        conn.close()
        user_bal = ub[0] if ub else 0
        ref_count = refs[0] if refs else 0
        bot.send_message(message.chat.id, f"💰 *رصيدك*\n\n💎 `{user_bal:.3f} USDT`\n👤 الإحالات: `{ref_count}`\n🏦 الموقع: `{bal}`", parse_mode="Markdown")
    elif message.text == "🤝 دعوة":
        link = get_ref_link(uid)
        bot.send_message(message.chat.id, f"🤝 *دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق", parse_mode="Markdown")
    elif message.text == "🟢 المرور":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()
        if not rows:
            txt = "لا توجد أرقام نشطة"
        else:
            countries = get_all_countries()
            lines = [f"• {countries.get(p, p)}: `{cnt}`" for p, cnt in rows]
            txt = "*🟢 حركة المرور*\n\n" + "\n".join(lines)
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")

# ════════════════ لوحة الإدارة ════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    mk = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if get_setting("maintenance") != "1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {status}", callback_data="tog_maint"))
    mk.add(types.InlineKeyboardButton("➕ دولة", callback_data="add_country"),
           types.InlineKeyboardButton("➖ دولة", callback_data="del_country"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
           types.InlineKeyboardButton("👥 مستخدمين", callback_data="users_list"))
    mk.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
           types.InlineKeyboardButton("✅ فك", callback_data="unban"))
    mk.add(types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"),
           types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
           types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم*", parse_mode="Markdown", reply_markup=mk)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "tog_maint")
def tog_maint(call):
    cur = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "تم")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country")
def add_country_start(call):
    user_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text("*➕ أرسل كود الدولة*\nمثال: `22501`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_prefix")
def add_prefix(message):
    user_states[message.from_user.id] = ("add_name", message.text.strip())
    bot.send_message(message.chat.id, "أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple))
def add_name(message):
    prefix = user_states[message.from_user.id][1]
    name = message.text.strip()
    add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ تمت إضافة {name}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country")
def del_country_start(call):
    countries = get_all_countries()
    mk = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        mk.add(types.InlineKeyboardButton(f"{name} ({prefix})", callback_data=f"delc_{prefix}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*اختر الدولة للحذف:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call):
    delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 أرسل الرسالة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = get_all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.03)
        except: pass
    bot.send_message(message.chat.id, f"✅ `{cnt}` مستخدم", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"])
def ban_unban_prompt(call):
    user_states[call.from_user.id] = call.data
    txt = "*🚫 أرسل ID المستخدم:*" if call.data=="ban" else "*✅ أرسل ID المستخدم:*"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    action = user_states[message.from_user.id]
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"UPDATE users SET is_banned={'1' if action=='ban' else '0'} WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ تم")
    except:
        bot.send_message(message.chat.id, "❌ خطأ")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "users_list")
def users_list(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 15")
    rows = c.fetchall()
    conn.close()
    txt = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{uid}` @{un or '—'}" for uid, un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "force_sub")
def force_sub(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    chs = c.fetchall()
    conn.close()
    mk = types.InlineKeyboardMarkup()
    for ch in chs:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙", callback_data="admin_back"))
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

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple))
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تمت")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    ch_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo")
def set_photo(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "clear_data")
def clear_data(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم مسح البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back(call):
    admin_panel(call.message)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, uid in get_all_active():
                try:
                    status, otp = api_check_otp(number)
                    if status == "success" and otp:
                        service = detect_service(otp)
                        ic = SERVICE_ICONS.get(service, "🔐")
                        country = get_all_countries().get(prefix, prefix)
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try:
                                bot.send_message(uid, f"*🔐 كود جديد*\n\n🌍 {country}\n📱 `+{number}`\n🔑 `{code}`\n{ic} {service}", parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid, f"*🔐 كود جديد*\n\n🌍 {country} | {ic} {service}\n📱 `{mask_number(number)}`\n🔑 `{code}`", parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except: pass
                        log_otp(number, otp, service, uid)
                        api_delete_number(alloc_id)
                        conn = sqlite3.connect(DB_PATH)
                        conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ البوت يعمل...")
    bot.infinity_polling()

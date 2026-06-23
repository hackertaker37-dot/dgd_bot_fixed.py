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
    "22501": "ساحل العاج", "23276": "سيراليون", "26134": "مدغشقر",
    "44740": "المملكة المتحدة", "23490": "نيجيريا", "25471": "كينيا",
    "24910": "السودان 10", "24911": "السودان 11", "24912": "السودان 12",
    "24913": "السودان 13", "24914": "السودان 14", "24915": "السودان 15",
    "24916": "السودان 16", "24917": "السودان 17", "24918": "السودان 18",
    "24919": "السودان 19", "22507": "ساحل العاج VIP", "49155": "ألمانيا",
    "23762": "الكاميرون", "22178": "السنغال", "22901": "بنين", "22898": "توجو",
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
            return data.get("status"), data.get("otp")
        return None, None
    except:
        return None, None

def api_delete_number(alloc_id):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=5)
        return resp.json().get("success", False)
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
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
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
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO countries (prefix, name) VALUES (?,?)", (prefix, name))
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
    c.execute("SELECT prefix, name FROM countries ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO countries VALUES (?,?)", (prefix, name))
    conn.commit()
    conn.close()

def delete_country(prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM countries WHERE prefix=?", (prefix,))
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
    return [r[0] for r in c.fetchall()]

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

def assign_number(uid, alloc_id, number, prefix):
    release_user_number(uid)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO active_numbers VALUES (?,?,?,?,?,?,NULL)",
              (alloc_id, number, prefix, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_all_active():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'")
    return c.fetchall()

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
    t = text.lower()
    services = [
        ("WhatsApp", ["whatsapp", "واتساب", "واتس"]),
        ("Telegram", ["telegram", "تيليجرام", "تليجرام"]),
        ("Facebook", ["facebook", "فيسبوك", "fb"]),
        ("Instagram", ["instagram", "انستقرام", "انستا"]),
        ("Google", ["google", "gmail", "جوجل"]),
        ("Twitter / X", ["twitter", "تويتر", "x.com"]),
        ("Discord", ["discord", "ديسكورد"]),
        ("Snapchat", ["snapchat", "سناب شات", "سناب"]),
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
    return "Unknown Service"

def mask_number(num):
    n = str(num)
    return f"{n[:4]}****{n[-3:]}" if len(n) > 7 else n

def format_time(iso_str):
    if not iso_str: return "غير معروف"
    try:
        return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M")
    except:
        return iso_str

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
        except:
            return False
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

def delete_later(cid, mid, delay=180):
    time.sleep(delay)
    try: bot.delete_message(cid, mid)
    except: pass

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add("📱 احصل على رقم", "🌍 الدول المتاحة", "📊 إحصائياتي")
    kb.add("💰 رصيدي", "🤝 دعوة الأصدقاء", "🟢 حركة المرور")
    if uid in ADMIN_IDS:
        kb.add("⚙️ لوحة التحكم")
    return kb

def country_inline(page=0):
    countries = list(get_all_countries().items())
    markup = types.InlineKeyboardMarkup(row_width=2)
    per_page = 8
    start = page * per_page
    chunk = countries[start:start+per_page]
    for prefix, name in chunk:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"getnum_{prefix}"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("‹ السابق", callback_data=f"countries_{page-1}"))
    if start + per_page < len(countries):
        nav.append(types.InlineKeyboardButton("التالي ›", callback_data=f"countries_{page+1}"))
    if nav: markup.row(*nav)
    return markup

def number_actions(prefix, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{prefix}_{alloc_id}"),
           types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="country_menu"))
    mk.row(types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
           types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return mk

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", parse_mode="Markdown")
        return
    save_user(message)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(cid, "🔒 *يجب الاشتراك في القنوات أولاً*", parse_mode="Markdown", reply_markup=mk)
        return
    photo = get_setting("welcome_photo")
    txt = ("*✨ أهلاً بك في بوت Taker OTP*\n\n"
           "• احصل على أرقام وهمية لتفعيل حساباتك\n"
           "• استقبل رموز التفعيل بشكل فوري\n"
           "• ادعُ أصدقاءك واربح رصيداً\n\n"
           "*🌍 اختر الدولة:*")
    mk = country_inline()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "استخدم الأزرار أدناه للتنقل:", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("countries_"))
def countries_page(call):
    page = int(call.data.split("_")[1])
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=country_inline(page))

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def get_number(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release_user_number(uid)
    try:
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
        bot.edit_message_text(f"*اختر رقماً من القائمة:*\n\n🌍 {name}",
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=mk)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

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
    now = datetime.now().strftime("%H:%M")
    bot.edit_message_text(
        f"*✅ تم تخصيص رقم جديد*\n\n📞 *الرقم:* `+{num}`\n🌍 *الدولة:* {name}\n🕒 *الوقت:* {now}\n⏳ *الحالة:* في انتظار رمز التفعيل",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown",
        reply_markup=number_actions(prefix, aid))
    del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]
    old_alloc = parts[2] if len(parts) > 2 else None
    if old_alloc:
        api_delete_number(old_alloc)
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (old_alloc,))
        conn.commit()
        conn.close()
    release_user_number(uid)
    try:
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
        mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"change_{prefix}_0"))
        mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="country_menu"))
        name = get_all_countries().get(prefix, prefix)
        bot.edit_message_text(f"*اختر رقماً من القائمة:*\n\n🌍 {name}",
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=mk)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_menu(call):
    if call.data == "country_menu":
        bot.edit_message_text("*🌍 اختر الدولة:*", call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=country_inline())
    else:
        start(call.message)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: m.text in [
    "📱 احصل على رقم", "🌍 الدول المتاحة", "📊 إحصائياتي",
    "💰 رصيدي", "🤝 دعوة الأصدقاء", "🟢 حركة المرور"
])
def bottom_buttons(message):
    uid = message.from_user.id
    if message.text == "📱 احصل على رقم":
        bot.send_message(message.chat.id, "*🌍 اختر الدولة:*", parse_mode="Markdown", reply_markup=country_inline())
    elif message.text == "🌍 الدول المتاحة":
        countries = get_all_countries()
        text = "*🌍 الدول المتاحة:*\n\n" + "\n".join(f"• `{p}` - {n}" for p, n in countries.items())
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    elif message.text == "📊 إحصائياتي":
        requests, otps, first, last = get_user_stats(uid)
        msg = (f"*📊 إحصائياتك*\n\n"
               f"🔷 *إجمالي الطلبات:* `{requests}`\n"
               f"🔷 *الأكواد المستلمة:* `{otps}`\n"
               f"🔷 *أول استخدام:* `{format_time(first)}`\n"
               f"🔷 *آخر استخدام:* `{format_time(last)}`")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "💰 رصيدي":
        bal, refs = get_user_balance(uid)
        site_bal = api_get_balance()
        msg = (f"*💰 رصيدك*\n\n"
               f"💎 *رصيدك:* `{bal:.3f} USDT`\n"
               f"👤 *الإحالات:* `{refs}`\n"
               f"🏦 *رصيد الموقع:* `{site_bal}`\n"
               f"🏦 *الحد الأدنى للسحب:* `18.0 USDT`\n\n"
               f"💡 *اربح `0.05 USDT` عن كل صديق تدعوه*")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "🤝 دعوة الأصدقاء":
        link = get_ref_link(uid)
        msg = (f"*🤝 دعوة الأصدقاء*\n\n"
               f"🔗 *رابط الدعوة الخاص بك:*\n`{link}`\n\n"
               f"💰 *الربح:* `0.05 USDT` عن كل صديق\n"
               f"📤 *شارك الرابط مع أصدقائك*")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    elif message.text == "🟢 حركة المرور":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix ORDER BY COUNT(*) DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()
        if not rows:
            text = "*🟢 حركة المرور*\n\nلا توجد أرقام نشطة حالياً."
        else:
            total = sum(r[1] for r in rows)
            lines = []
            for i, (prefix, cnt) in enumerate(rows, 1):
                name = get_all_countries().get(prefix, prefix)
                perc = (cnt / total) * 100 if total else 0
                lines.append(f"{i}️⃣ `{name}` → `{perc:.1f}%`")
            text = "*🟢 حركة المرور*\n\n" + "\n".join(lines)
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ════════════════ لوحة الإدارة ════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة التحكم" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if get_setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
    markup.add(types.InlineKeyboardButton("➕ إضافة دولة", callback_data="add_country"),
               types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_country"))
    markup.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
               types.InlineKeyboardButton("👥 المستخدمين", callback_data="users_list"))
    markup.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
               types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"))
    markup.add(types.InlineKeyboardButton("🔗 الاشتراك", callback_data="force_sub"),
               types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="set_photo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="clear_data"),
               types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم*\n\nمرحباً بك في لوحة إدارة البوت.", parse_mode="Markdown", reply_markup=markup)

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
    bot.edit_message_text("*➕ إضافة دولة*\n\nأرسل Prefix الدولة (مثال: `24910`):", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

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
    delete_country(call.data.split("_")[1])
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
            time.sleep(0.03)
        except: pass
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
        conn.cursor().execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
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
        conn.cursor().execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
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
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"),
               types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك الإجباري*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    user_states[message.from_user.id] = ("addch_desc", message.text.strip())
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تمت الإضافة")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
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
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ════════════════ المعالج الموحد للرسائل النصية ════════════════
@bot.message_handler(func=lambda m: True)
def universal_handler(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text

    state = user_states.get(uid)
    if state == "add_country_prefix":
        prefix = txt.strip()
        user_states[uid] = ("add_country_name", prefix)
        bot.send_message(cid, "أرسل اسم الدولة:")
        return

    if isinstance(state, tuple) and state[0] == "add_country_name":
        prefix = state[1]
        name = txt.strip()
        add_country(prefix, name)
        bot.send_message(cid, f"✅ تمت إضافة `{name}` ({prefix})", parse_mode="Markdown")
        del user_states[uid]
        return

    if state == "broadcast":
        users = get_all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.03)
            except: pass
        bot.send_message(cid, f"✅ تم الإرسال إلى `{cnt}` مستخدم", parse_mode="Markdown")
        del user_states[uid]
        return

    if state in ["ban", "unban"]:
        try:
            target = int(txt)
            conn = sqlite3.connect(DB_PATH)
            conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
            bot.send_message(cid, f"✅ تم", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
        del user_states[uid]
        return

    if state == "addch_url":
        user_states[uid] = ("addch_desc", txt.strip())
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
        del user_states[uid]
        return

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
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
                        if uid:
                            try:
                                bot.send_message(uid,
                                    f"*🔐 تم استقبال رمز التفعيل*\n\n📞 *الرقم:* `+{number}`\n🌍 *الدولة:* {country}\n{ic} *التطبيق:* {service}\n🔢 *الكود:* `{code}`",
                                    parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid,
                                    f"*🔐 كود جديد*\n\n📞 `{mask_number(number)}`\n🌍 {country}\n{ic} {service}\n🔢 `{code}`",
                                    parse_mode="Markdown")
                                threading.Thread(target=delete_later, args=(cid, sent.message_id, DELETE_AFTER), daemon=True).start()
                            except: pass
                        conn = sqlite3.connect(DB_PATH)
                        conn.cursor().execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
                        conn.cursor().execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                        conn.commit()
                        conn.close()
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

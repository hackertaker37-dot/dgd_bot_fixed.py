# -*- coding: utf-8 -*-
import time, requests, json, re, os, sqlite3, threading, traceback, random
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ================ الإعدادات ================
BOT_TOKEN = "8686995713:AAFVS08mWY50rSHdINt-hISK5M4iGIajms8"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "xwdsms_bot.db"

# ================ الدول الافتراضية (Prefix التي يقبلها API) ================
DEFAULT_COUNTRIES = {
    "22501": "ساحل العاج",
    "23276": "سيراليون",
    "26134": "مدغشقر",
    "44740": "المملكة المتحدة",
    "23490": "نيجيريا",
    "25471": "كينيا",
    # الإضافات الجديدة
    "24910": "السودان 10",
    "22507": "ساحل العاج VIP",
    "49155": "ألمانيا",
    "26134": "مدغشقر",
    "23762": "الكاميرون",
    "22178": "السنغال",
    "22901": "بنين",
    "22898": "توجو",
    "23276": "سيراليون",
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
            raise Exception("هذه الدولة غير متوفرة حالياً (404)")
        else:
            raise Exception(f"خطأ في الاتصال: {e}")
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
        return resp.json().get("balance", "غير معروف")
    except:
        return "غير معروف"

# ================ قاعدة البيانات ================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0)''')
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
    # إعدادات افتراضية
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('welcome_photo', '')")
    # إدراج الدول الافتراضية
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
    c.execute("SELECT prefix, name FROM countries")
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

# ================ دوال مساعدة ================
def save_user(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, last_name) VALUES (?,?,?,?)",
                  (uid, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
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
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, assigned_to, created_at) VALUES (?,?,?,?,?)",
              (alloc_id, number, prefix, uid, datetime.now().isoformat()))
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

def get_user_active_number(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    row = c.fetchone()
    conn.close()
    return row

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
        c.execute("UPDATE users SET balance = balance + 0.5 WHERE user_id=?", (referrer,))
    conn.commit()
    conn.close()

def check_subscription(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return True
    for ch in channels:
        try:
            member = bot.get_chat_member(ch[1], uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(f"اشترك في {ch[2]}", url=ch[1]))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

def extract_otp(text):
    nums = re.findall(r'\d{4,8}', text)
    return nums[0] if nums else "N/A"

def detect_service(text):
    text = text.lower()
    services = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستا"],
        "Google": ["google", "gmail", "جوجل"],
        "Twitter/X": ["twitter", "تويتر", "x.com"],
        "Discord": ["discord", "ديسكورد"],
        "Snapchat": ["snapchat", "سناب"],
        "TikTok": ["tiktok", "تيك توك"],
        "Amazon": ["amazon", "امازون"],
        "Apple": ["apple", "ابل", "icloud"],
        "Microsoft": ["microsoft", "مايكروسوفت"],
        "Uber": ["uber", "اوبر"],
        "Netflix": ["netflix", "نتفلكس"],
    }
    for service, keywords in services.items():
        for kw in keywords:
            if kw in text:
                return service
    return "OTP"

def mask_number(number):
    num = str(number)
    return num[:4] + "••••" + num[-4:] if len(num) > 8 else num

# ================ بوت تيليجرام ================
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton("📱 احصل على رقم"),
        types.KeyboardButton("🌍 الدول المتاحة"),
        types.KeyboardButton("📊 الإحصائيات"),
        types.KeyboardButton("💰 الرصيد"),
        types.KeyboardButton("💸 سحب الرصيد"),
        types.KeyboardButton("🟢 حركة المرور")
    )
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton("⚙️ لوحة الإدارة"))
    return kb

def country_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = get_all_countries()
    for prefix, name in countries.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"getnum_{prefix}"))
    return markup

def number_actions(prefix, alloc_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="country_menu")
    )
    markup.row(
        types.InlineKeyboardButton("📞 جروب البوت", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ القائمة الرئيسية", callback_data="main_menu")
    )
    return markup

# ================ أوامر البوت ================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⚠️ البوت في وضع الصيانة.")
        return
    save_user(message)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(message.chat.id, "🔒 اشترك في القنوات أولاً:", reply_markup=mk)
        return
    photo = get_setting("welcome_photo")
    txt = "🌍 اختر الدولة:"
    mk = country_inline()
    if photo:
        try:
            bot.send_photo(message.chat.id, photo, caption=txt, reply_markup=mk)
        except:
            bot.send_message(message.chat.id, txt, reply_markup=mk)
    else:
        bot.send_message(message.chat.id, txt, reply_markup=mk)
    bot.send_message(message.chat.id, "استخدم الأزرار:", reply_markup=main_keyboard(uid))

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def get_number(call):
    uid = call.from_user.id
    prefix = call.data.split("_")[1]
    release_user_number(uid)
    try:
        alloc_id, number = api_get_number(prefix)
        assign_number(uid, alloc_id, number, prefix)
        name = get_all_countries().get(prefix, prefix)
        # الشكل المربع
        now = datetime.now().strftime("%H:%M")
        msg = (
            "┌─────────────────────────────────────────────┐\n"
            f"│ SPAMX-Bot V1.0               [المشرف]        │\n"
            "│                                              │\n"
            f"│ 🏳 {name[:10]:10}  {number[:15]:15} │\n"
            f"│ #English                         🕒 {now}    │\n"
            "├─────────────────────────────────────────────┤\n"
            "│                                              │\n"
            f"│        [🔑] [📑] {number[-5:]:>5}                       │\n"
            "│                                              │\n"
            "├─────────────────────────────────────────────┤\n"
            "│                                              │\n"
            "│ [📞] Number Chann  ↗️  [🏃] SPAMX-Bot  ↗️  │\n"
            "│                                              │\n"
            "└─────────────────────────────────────────────┘"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              reply_markup=number_actions(prefix, alloc_id))
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
        assign_number(uid, alloc_id, number, prefix)
        name = get_all_countries().get(prefix, prefix)
        now = datetime.now().strftime("%H:%M")
        msg = (
            "┌─────────────────────────────────────────────┐\n"
            f"│ SPAMX-Bot V1.0               [المشرف]        │\n"
            "│                                              │\n"
            f"│ 🏳 {name[:10]:10}  {number[:15]:15} │\n"
            f"│ #English                         🕒 {now}    │\n"
            "├─────────────────────────────────────────────┤\n"
            "│                                              │\n"
            f"│        [🔑] [📑] {number[-5:]:>5}                       │\n"
            "│                                              │\n"
            "├─────────────────────────────────────────────┤\n"
            "│                                              │\n"
            "│ [📞] Number Chann  ↗️  [🏃] SPAMX-Bot  ↗️  │\n"
            "│                                              │\n"
            "└─────────────────────────────────────────────┘"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              reply_markup=number_actions(prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_menu(call):
    if call.data == "country_menu":
        bot.edit_message_text("اختر الدولة:", call.message.chat.id, call.message.message_id, reply_markup=country_inline())
    else:
        start(call.message)

# ================ الكيبورد السفلي ================
@bot.message_handler(func=lambda m: m.text in [
    "📱 احصل على رقم", "🌍 الدول المتاحة", "📊 الإحصائيات",
    "💰 الرصيد", "💸 سحب الرصيد", "🟢 حركة المرور"
])
def bottom_buttons(message):
    uid = message.from_user.id
    if message.text == "📱 احصل على رقم":
        bot.send_message(message.chat.id, "اختر الدولة:", reply_markup=country_inline())
    elif message.text == "🌍 الدول المتاحة":
        countries = get_all_countries()
        text = "الدول المتاحة:\n" + "\n".join(f"• {name} ({prefix})" for prefix, name in countries.items())
        bot.send_message(message.chat.id, text)
    elif message.text == "📊 الإحصائيات":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
        active = c.fetchone()[0]
        conn.close()
        now = datetime.now().strftime("%H:%M")
        msg = (
            "┌──────────────────────────────────────────────┐\n"
            "│        « 📊 إحصائياتك »                      │\n"
            "│                                               │\n"
            f"│ 🔷 إجمالي المستخدمين: {total:<22} │\n"
            f"│ 🔷 الأرقام النشطة: {active:<22} │\n"
            f"│                                      🕒 {now} │\n"
            "└──────────────────────────────────────────────┘"
        )
        bot.send_message(message.chat.id, msg)
    elif message.text == "💰 الرصيد":
        bal = api_get_balance()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
        refs = c.fetchone()
        ref_count = refs[0] if refs else 0
        conn.close()
        now = datetime.now().strftime("%H:%M")
        msg = (
            "┌──────────────────────────────────────────────┐\n"
            "│                 💰 الرصيد                     │\n"
            "│                                               │\n"
            f"│  📊 رصيدك: USDT {bal:<27} │\n"
            f"│  👤 الإحالات: {ref_count:<27} │\n"
            "│  🏦 الحد الأدنى للسحب: USDT 18.0              │\n"
            "│ ───────────────────────────────────────────── │\n"
            "│  😄 ربح لكل إحالة: USDT 0.05                  │\n"
            "│  🚀 ادعُ أصدقاءك لزيادة رصيدك                 │\n"
            f"│                                      🕒 {now} │\n"
            "└──────────────────────────────────────────────┘"
        )
        bot.send_message(message.chat.id, msg)
    elif message.text == "💸 سحب الرصيد":
        bot.send_message(message.chat.id, "لطلب سحب الرصيد تواصل مع @hackerTaker")
    elif message.text == "🟢 حركة المرور":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix")
        rows = c.fetchall()
        if not rows:
            text = "لا توجد أرقام نشطة"
        else:
            now = datetime.now().strftime("%H:%M")
            lines = []
            total = sum(r[1] for r in rows)
            for i, (prefix, cnt) in enumerate(rows[:5], 1):
                name = get_all_countries().get(prefix, prefix)
                perc = (cnt / total) * 100 if total else 0
                lines.append(f"│ {i}️⃣ {name} → {perc:.1f}%")
            msg = (
                "┌──────────────────────────────────────────┐\n"
                "│ 🟢 حركة المرور                11:09 ✓✓   │\n"
                "├──────────────────────────────────────────┤\n"
                "│ 🟢 Live Traffic                         │\n"
                "│                                          │\n"
                "│ 🗓️ Window: Last 5 minutes                │\n"
                "│ ✅ Results Sent: 100%                    │\n"
                "│ 🏆 Top Country: -                        │\n"
                "│                                          │\n"
                "│ 🌍 Top Countries:                        │\n"
            ) + "\n".join(lines) + f"\n│                                  🕒 {now} │\n" + (
                "├──────────────────────────────────────────┤\n"
                "│             [🔄] Refresh                  │\n"
                "└──────────────────────────────────────────┘"
            )
            bot.send_message(message.chat.id, msg)

# ================ لوحة الإدارة ================
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    status = "🟢 مفعل" if get_setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
    markup.add(types.InlineKeyboardButton("➕ إضافة دولة", callback_data="add_country"))
    markup.add(types.InlineKeyboardButton("➖ حذف دولة", callback_data="del_country"))
    markup.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"))
    markup.add(types.InlineKeyboardButton("🚫 حظر / ✅ فك", callback_data="ban_unban"))
    markup.add(types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="force_sub"))
    markup.add(types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="set_photo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="clear_data"))
    markup.add(types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "<b>لوحة التحكم</b>", parse_mode="HTML", reply_markup=markup)

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
    bot.edit_message_text("أرسل prefix الدولة (مثل 24910):", call.message.chat.id, call.message.message_id)

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
    bot.send_message(message.chat.id, f"✅ تمت إضافة {name} ({prefix})")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("اختر الدولة للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    prefix = call.data.split("_")[1]
    delete_country(prefix)
    bot.answer_callback_query(call.id, "تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("أرسل الرسالة للإذاعة:", call.message.chat.id, call.message.message_id)

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
    bot.send_message(message.chat.id, f"✅ تم الإرسال إلى {cnt} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "ban_unban" and c.from_user.id in ADMIN_IDS)
def ban_unban_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"))
    markup.add(types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("اختر:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "ban" and c.from_user.id in ADMIN_IDS)
def ban_prompt(call):
    user_states[call.from_user.id] = "ban"
    bot.edit_message_text("أرسل ID المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ban")
def ban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"تم حظر {uid}")
    except:
        bot.send_message(message.chat.id, "خطأ في المعرف")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "unban" and c.from_user.id in ADMIN_IDS)
def unban_prompt(call):
    user_states[call.from_user.id] = "unban"
    bot.edit_message_text("أرسل ID المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "unban")
def unban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"تم فك حظر {uid}")
    except:
        bot.send_message(message.chat.id, "خطأ في المعرف")
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
    bot.edit_message_text("قنوات الاشتراك:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("أرسل رابط القناة:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    url = message.text.strip()
    user_states[message.from_user.id] = ("addch_desc", url)
    bot.send_message(message.chat.id, "أرسل وصف القناة:")

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
    bot.edit_message_text("أرسل الصورة:", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم حفظ الصورة")
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
    bot.answer_callback_query(call.id, "تم مسح البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ================ حلقة فحص OTP ================
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, uid in get_all_active():
                try:
                    status, otp = api_check_otp(number)
                    if status == "success" and otp:
                        service = detect_service(otp)
                        # إرسال للمستخدم
                        if uid:
                            try:
                                bot.send_message(uid, f"🔐 الكود: {otp}\nالخدمة: {service}\nالرقم: {number}")
                            except:
                                pass
                        # إرسال للجروب
                        for cid in CHAT_IDS:
                            try:
                                bot.send_message(cid, f"📱 رقم: {mask_number(number)}\n🔢 الكود: {otp}\n🛠 الخدمة: {service}")
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

# ================ Flask ================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

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

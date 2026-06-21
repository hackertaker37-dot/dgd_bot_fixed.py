# -*- coding: utf-8 -*-
import time, requests, json, re, os, sqlite3, threading, traceback, random
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ================= إعدادات أساسية =================
BOT_TOKEN = "8686995713:AAFTesnEDbFJcSgtM3IrURU0WtPdNkJtO4c"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "xwdsms_bot.db"

# ================= الدول المتاحة فقط =================
AVAILABLE_COUNTRIES = {
    "22501": "ساحل العاج",
    "23276": "سيراليون",
    "26134": "مدغشقر",
    "44740": "المملكة المتحدة",
    "23490": "نيجيريا",
    "25471": "كينيا"
}

# ================= دوال API الخاصة بالموقع =================
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
        raise Exception(f"خطأ في API get-number: {e}")

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

# ================= قاعدة البيانات =================
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
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('welcome_photo', '')")
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

# ================= دوال مساعدة =================
def save_user(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
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
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, assigned_to, created_at) VALUES (?, ?, ?, ?, ?)",
              (alloc_id, number, prefix, uid, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def release_user_number(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    rows = c.fetchall()
    for row in rows:
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
    c.execute("INSERT INTO otp_logs (number, otp, service, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, service, datetime.now().isoformat(), uid))
    conn.commit()
    conn.close()

def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?, ?)", (uid, ref))
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

def get_force_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    rows = c.fetchall()
    conn.close()
    return rows

def check_subscription(uid):
    channels = get_force_channels()
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
    channels = get_force_channels()
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
    if "whatsapp" in text or "واتساب" in text: return "WhatsApp"
    if "telegram" in text or "تيليجرام" in text: return "Telegram"
    if "facebook" in text or "فيسبوك" in text: return "Facebook"
    if "instagram" in text or "انستقرام" in text: return "Instagram"
    if "google" in text or "gmail" in text: return "Google"
    if "twitter" in text or "x.com" in text: return "Twitter"
    if "discord" in text: return "Discord"
    if "snapchat" in text: return "Snapchat"
    if "tiktok" in text: return "TikTok"
    if "amazon" in text: return "Amazon"
    if "apple" in text: return "Apple"
    if "microsoft" in text: return "Microsoft"
    if "uber" in text: return "Uber"
    if "netflix" in text: return "Netflix"
    return "OTP"

def mask_number(number):
    num = str(number)
    return num[:4] + "••••" + num[-4:] if len(num) > 8 else num

# ================= بوت تيليجرام =================
bot = telebot.TeleBot(BOT_TOKEN)

# الكيبورد السفلي (الأزرار الأساسية)
def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [
        "📥 الحصول على رقم", "💰 الرصيد", "🤝 شارك واربح",
        "💵 سحب الرصيد", "📊 الإحصائيات", "🌐 الترافيك المباشر"
    ]
    kb.add(*[types.KeyboardButton(b) for b in buttons])
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton("⚙️ لوحة الإدارة"))
    return kb

# قائمة الدول (Inline)
def country_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in AVAILABLE_COUNTRIES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"getnum_{code}"))
    return markup

# أزرار التحكم بعد الحصول على رقم
def number_actions(prefix, alloc_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="country_menu")
    )
    markup.row(
        types.InlineKeyboardButton("📢 جروب البوت", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ القائمة الرئيسية", callback_data="main_menu")
    )
    return markup

# ================= أوامر البوت =================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id

    # فحص الصيانة
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, "⚠️ البوت في وضع الصيانة حالياً.")
        return

    save_user(message)

    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)

    # الاشتراك الإجباري
    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(cid, "🔒 يجب الاشتراك في القنوات أولاً:", reply_markup=mk)
        return

    # رسالة الترحيب
    photo = get_setting("welcome_photo")
    txt = "<b>مرحباً بك في بوت Taker OTP</b>\nاختر الدولة للحصول على رقم:"
    mk = country_inline()
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="HTML", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="HTML", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="HTML", reply_markup=mk)
    bot.send_message(cid, "استخدم الأزرار:", reply_markup=main_keyboard(uid))

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
    if prefix not in AVAILABLE_COUNTRIES:
        bot.answer_callback_query(call.id, "دولة غير مدعومة")
        return

    release_user_number(uid)  # حذف القديم من API و DB
    try:
        alloc_id, number = api_get_number(prefix)
        assign_number(uid, alloc_id, number, prefix)
        name = AVAILABLE_COUNTRIES[prefix]
        msg = f"<b>تم تخصيص رقم:</b>\n📞 <code>{number}</code>\n🌍 {name}\n⏳ في انتظار الكود..."
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="HTML", reply_markup=number_actions(prefix, alloc_id))
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
        name = AVAILABLE_COUNTRIES[prefix]
        msg = f"<b>تم تغيير الرقم:</b>\n📞 <code>{number}</code>\n🌍 {name}\n⏳ في انتظار الكود..."
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="HTML", reply_markup=number_actions(prefix, alloc_id))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["country_menu", "main_menu"])
def back_to_menu(call):
    if call.data == "country_menu":
        bot.edit_message_text("اختر الدولة:", call.message.chat.id, call.message.message_id,
                              reply_markup=country_inline())
    else:
        start(call.message)

# ================= الكيبورد السفلي =================
@bot.message_handler(func=lambda m: m.text in [
    "📥 الحصول على رقم", "💰 الرصيد", "🤝 شارك واربح",
    "💵 سحب الرصيد", "📊 الإحصائيات", "🌐 الترافيك المباشر"
])
def bottom_buttons(message):
    uid = message.from_user.id
    if message.text == "📥 الحصول على رقم":
        bot.send_message(message.chat.id, "اختر الدولة:", reply_markup=country_inline())
    elif message.text == "💰 الرصيد":
        bal = api_get_balance()
        bot.send_message(message.chat.id, f"💰 الرصيد الحالي: {bal}")
    elif message.text == "🤝 شارك واربح":
        link = get_ref_link(uid)
        bot.send_message(message.chat.id, f"🔗 رابط الدعوة الخاص بك:\n{link}\n\nشاركه واربح رصيداً!")
    elif message.text == "💵 سحب الرصيد":
        bot.send_message(message.chat.id, "لطلب سحب الرصيد، تواصل مع الإدارة @hackerTaker")
    elif message.text == "📊 الإحصائيات":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
        active_nums = c.fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"📊 المستخدمين: {total_users}\n📱 الأرقام النشطة: {active_nums}")
    elif message.text == "🌐 الترافيك المباشر":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix")
        rows = c.fetchall()
        if not rows:
            msg = "لا توجد أرقام نشطة حالياً."
        else:
            msg = "📡 الترافيك المباشر:\n"
            for prefix, cnt in rows:
                name = AVAILABLE_COUNTRIES.get(prefix, prefix)
                msg += f"• {name}: {cnt} رقم\n"
        conn.close()
        bot.send_message(message.chat.id, msg)

# ================= لوحة الإدارة =================
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    status = "🟢 مفعل" if get_setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
    markup.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"))
    markup.add(types.InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="manage_users"))
    markup.add(types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="force_sub"))
    markup.add(types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="set_photo"))
    markup.add(types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="clear_data"))
    markup.add(types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "<b>لوحة التحكم</b>", parse_mode="HTML", reply_markup=markup)

user_states = {}

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    current = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if current else "1")
    bot.answer_callback_query(call.id, "تم تغيير الحالة")
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

@bot.callback_query_handler(func=lambda c: c.data == "manage_users" and c.from_user.id in ADMIN_IDS)
def manage_users(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"), types.InlineKeyboardButton("✅ فك حظر", callback_data="unban"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("اختر الإجراء:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "ban" and c.from_user.id in ADMIN_IDS)
def ban_prompt(call):
    user_states[call.from_user.id] = "ban"
    bot.edit_message_text("أرسل معرف المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ban")
def ban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"تم حظر المستخدم {uid}")
    except:
        bot.send_message(message.chat.id, "معرف غير صحيح")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "unban" and c.from_user.id in ADMIN_IDS)
def unban_prompt(call):
    user_states[call.from_user.id] = "unban"
    bot.edit_message_text("أرسل معرف المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "unban")
def unban_exec(message):
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"تم فك حظر المستخدم {uid}")
    except:
        bot.send_message(message.chat.id, "معرف غير صحيح")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    channels = get_force_channels()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("قنوات الاشتراك:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def add_ch_prompt(call):
    user_states[call.from_user.id] = "add_ch_url"
    bot.edit_message_text("أرسل رابط القناة (https://t.me/xxx):", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_ch_url")
def add_ch_url(message):
    url = message.text.strip()
    user_states[message.from_user.id] = ("add_ch_desc", url)
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_ch_desc")
def add_ch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?, ?)", (url, desc))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ تمت الإضافة")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def edit_ch(call):
    ch_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    force_sub_menu(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def photo_prompt(call):
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

# ================= حلقة فحص OTP التلقائية =================
def otp_loop():
    while True:
        try:
            actives = get_all_active()
            for alloc_id, number, prefix, uid in actives:
                try:
                    status, otp = api_check_otp(number)
                    if status == "success" and otp:
                        # إرسال للمستخدم
                        if uid:
                            try:
                                bot.send_message(uid, f"<b>🔐 كود التفعيل</b>\n<code>{otp}</code>\nالرقم: {number}",
                                                 parse_mode="HTML")
                            except:
                                pass
                        # إرسال للجروب
                        name = AVAILABLE_COUNTRIES.get(prefix, "غير معروف")
                        masked = mask_number(number)
                        for cid in CHAT_IDS:
                            try:
                                bot.send_message(cid, f"📱 رقم: {masked}\n🌍 {name}\n🔢 الكود: <code>{otp}</code>",
                                                 parse_mode="HTML")
                            except:
                                pass
                        save_otp(alloc_id, otp)
                        log_otp(number, otp, detect_service(otp), uid)
                        api_delete_number(alloc_id)
                        delete_active(alloc_id)
                    elif status == "expired":
                        api_delete_number(alloc_id)
                        delete_active(alloc_id)
                except Exception as e:
                    print(f"Check error: {e}")
        except Exception as e:
            print(f"OTP loop error: {e}")
        time.sleep(3)

# ================= Flask =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Taker OTP Bot Running"

@app.route('/health')
def health():
    return jsonify(status="ok"), 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= بدء التشغيل =================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    print("✅ البوت يعمل...")
    bot.infinity_polling()

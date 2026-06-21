# ======================================================
#  𝐃𝐆𝐃 𝐍𝐄𝐓𝐖𝐎𝐑𝐊 - 𝐎𝐓𝐏 𝐁𝐎𝐓
# ======================================================

import time
import requests
import json
import re
import os
import sqlite3
import threading
import traceback
import random
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify
import telebot
from telebot import types

# ======================================================
# 📌 الإعدادات الأساسية (عدلها هنا أو من المتغيرات البيئية)
# ======================================================
BOT_TOKEN = "8686995713:AAGWEXfbnyrF1jUKdsrJsSwR3wWpvGbm8b8"
ADMIN_IDS = [8728019066, 8972941677]  # الآيدي الخاص بك وآيدي الثاني
CHAT_IDS = ["-1003789271722"]         # آيدي الجروب
DB_PATH = "dgd_bot.db"

# ======================================================
# 🔑 مفاتيح الاتصال بـ DGD
# ======================================================
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"
DGD_BASE_URL = "https://dgddigital.com"

# إعداد البوت
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ======================================================
# 🌍 قائمة الدول والرينجات المتاحة (حسب طلبك)
# ======================================================
AVAILABLE_RANGES = [
    "224655311XXX", "22465520XXX", "224655XXX", "23276XXX", "2327651XXX",
    "2327653XXX", "2290194323XXX", "225071800XXX", "261345XXX", "2250709726XXX",
    "225071860XXX", "225073XXX", "225077897XXX", "2250787XXX", "232764XXX",
    "22507XXX", "23276959XXX", "23672308XXX", "23276575XXX", "23276559XXX",
    "2367230XXX", "23672736XXX"
]

# جعل الرينجات تبدو واضحة في الأزرار (تجميع حسب الدولة)
COUNTRY_MAP = {}
for rng in AVAILABLE_RANGES:
    # استخراج كود الدولة من بداية الرينج
    code = rng[:3]
    if code not in COUNTRY_MAP:
        COUNTRY_MAP[code] = []
    COUNTRY_MAP[code].append(rng)

COUNTRY_NAMES = {
    "224": ("غينيا", "🇬🇳"),
    "232": ("سيراليون", "🇸🇱"),
    "229": ("بنين", "🇧🇯"),
    "225": ("ساحل العاج", "🇨🇮"),
    "261": ("مدغشقر", "🇲🇬"),
    "236": ("جمهورية أفريقيا الوسطى", "🇨🇫"),
}

# ======================================================
# 🗄️ إدارة قاعدة البيانات (SQLite)
# ======================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT, first_name TEXT, last_name TEXT,
        country_code TEXT, assigned_number TEXT,
        is_banned INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        number TEXT PRIMARY KEY, country_code TEXT, combo_index INTEGER,
        assigned_to INTEGER, requested_at TEXT, status TEXT DEFAULT 'WAITING',
        otp_code TEXT, last_check TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
        full_message TEXT, timestamp TEXT, assigned_to INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
    conn.commit()
    conn.close()
    logging.info("✅ قاعدة البيانات جاهزة")

init_db()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        user = get_user(user_id)
        if user:
            if country_code is None: country_code = user[4]
            if assigned_number is None: assigned_number = user[5]
        c.execute("""REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned)
                     VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0))""",
                  (user_id, username, first_name, last_name, country_code, assigned_number, user_id))
        conn.commit()
    except Exception as e:
        logging.error(f"Save user error: {e}")
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()
    return number

def add_active_number(number, country_code, assigned_to=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, requested_at, status, last_check) VALUES (?, ?, ?, ?, 'WAITING', ?)",
              (number, country_code, assigned_to, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_active_number(number, status=None, otp_code=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if otp_code:
        c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=?, last_check=? WHERE number=?", (otp_code, datetime.now().isoformat(), number))
    elif status:
        c.execute("UPDATE active_numbers SET status=?, last_check=? WHERE number=?", (status, datetime.now().isoformat(), number))
    conn.commit()
    conn.close()

def get_active_numbers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT number, assigned_to FROM active_numbers WHERE status='WAITING' OR status='WIT'")
    rows = c.fetchall()
    conn.close()
    return rows

def remove_active_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_numbers WHERE number=?", (number,))
    conn.commit()
    conn.close()

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

# ======================================================
# 🛠️ دوال مساعدة
# ======================================================
def clean_number(number):
    return re.sub(r'\D', '', str(number))

def mask_number(number):
    """تخفي الرقم لإظهار 3-4 أرقام أولى و 3-4 أرقام أخيرة"""
    num = str(number)
    if len(num) <= 8: return num
    return num[:4] + "××××" + num[-4:]

def extract_otp(text):
    patterns = [r'(?:code|رمز|كود|verification|otp|pin)[:\s]+[‎]?(\d{4,8})', r'\b(\d{4,8})\b']
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m: return m.group(1)
    nums = re.findall(r'\d{4,8}', text)
    return nums[0] if nums else "N/A"

def detect_service(text):
    text = text.lower()
    services = {
        "#WP": ["whatsapp", "واتساب"], "#FB": ["facebook", "فيسبوك"],
        "#IG": ["instagram", "انستقرام"], "#TG": ["telegram", "تيليجرام"],
        "#TW": ["twitter", "تويتر"], "#GG": ["google", "gmail"],
        "#DC": ["discord"], "#TT": ["tiktok", "تيك توك"],
        "#AMZ": ["amazon"], "#APL": ["apple", "icloud"],
        "#MS": ["microsoft"], "#NF": ["netflix"], "#SP": ["spotify"],
        "#YT": ["youtube"], "#UB": ["uber"], "#BK": ["booking"]
    }
    for code, keywords in services.items():
        for kw in keywords:
            if kw in text: return code
    return "UNKNOWN"

# ======================================================
# 📡 دوال الاتصال بـ DGD API
# ======================================================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/api/v1/user/getnum"
    headers = {
        "X-API-KEY": DGD_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            # البحث عن الرقم في الحقول المختلفة
            number = data.get("data", {}).get("number") or data.get("number")
            if number: return str(number)
        elif resp.status_code == 404:
            raise Exception("الرينج غير متاح أو انتهى")
        else:
            raise Exception(data.get("message", f"فشل طلب الرقم - الحالة: {resp.status_code}"))
    except Exception as e:
        logging.error(f"dgd_get_number error: {e}")
        raise

def dgd_check_number(phone):
    url = f"{DGD_BASE_URL}/api/v1/user/checknum"
    headers = {"X-API-KEY": DGD_API_KEY, "Accept": "application/json"}
    params = {"nomor": phone}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()
        if not data.get("ok") and resp.status_code != 200:
            raise Exception(data.get("message", "فشل التحقق من الرقم"))
        info = data.get("data", {})
        return {"status": info.get("status", "WAIT"), "otp": info.get("kode_otp")}
    except Exception as e:
        logging.error(f"dgd_check_number error: {e}")
        raise

# ======================================================
# 🔐 لوحة التحكم (Admin Panel)
# ======================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

@bot.message_handler(commands=['admin'])
def admin_panel_msg(message):
    if is_admin(message.from_user.id):
        show_admin_panel(message.chat.id, message.message_id)

def show_admin_panel(chat_id, msg_id=None):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast_all")
    )
    markup.row(
        types.InlineKeyboardButton("🚫 حظر/فك", callback_data="admin_ban"),
        types.InlineKeyboardButton("📥 إضافة رينج", callback_data="admin_add_combo")
    )
    markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_to_start"))
    text = "<b>🔐 لوحة تحكم المطور</b>\nاختر أحد الخيارات:"
    try:
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)
    except:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# ======================================================
# ⏳ حلقة فحص الأرقام النشطة (تعمل في الخلفية لجلب OTP بسرعة)
# ======================================================
def check_numbers_loop():
    while True:
        try:
            active_list = get_active_numbers()
            for phone, user_id in active_list:
                try:
                    result = dgd_check_number(phone)
                    if result["status"] == "SUKSES" and result["otp"]:
                        # جاهز للإرسال!
                        otp = result["otp"]
                        update_active_number(phone, otp_code=otp)
                        
                        # 1. تنسيق الرسالة للمستخدم
                        service = detect_service(f"OTP: {otp}")
                        user_msg = f"✨ <b><u>DEVIL NUMBER 𝗢𝗧𝗣</u></b>\n\n" \
                                   f"☎ <b>الرقم:</b> <code>+{phone}</code>\n" \
                                   f"⚙ <b>الخدمة:</b> {service}\n" \
                                   f"🕒 <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}\n\n" \
                                   f"🔐 <b>الكود:</b> {otp}\n\n" \
                                   f"<b>كود {service} {otp[:3]}-{otp[3:]} ؟</b>"
                        
                        user_markup = types.InlineKeyboardMarkup()
                        user_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        user_markup.add(types.InlineKeyboardButton("👑 المطور", url="https://t.me/hackerTaker"))

                        # 2. تنسيق الرسالة للجروب (مع الرقم المخفي)
                        masked_phone = mask_number(phone)
                        group_msg = f"✨ <b><u>DEVIL NUMBER 𝗢𝗧𝗣</u></b>\n\n" \
                                    f"☎ <b>الرقم:</b> <code>+{masked_phone}</code>\n" \
                                    f"⚙ <b>الخدمة:</b> {service}\n" \
                                    f"🕒 <b>الوقت:</b> {datetime.now().strftime('%H:%M:%S')}\n\n" \
                                    f"🔐 <b>الكود:</b> {otp}\n\n" \
                                    f"<b>كود {service} {otp[:3]}-{otp[3:]} ؟</b>"

                        group_markup = types.InlineKeyboardMarkup()
                        group_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        group_markup.add(types.InlineKeyboardButton("🤖 بوت البوت", url="https://t.me/Taker_OTP_BOT"))

                        # 3. الإرسال
                        if user_id:
                            try:
                                bot.send_message(user_id, user_msg, parse_mode="HTML", reply_markup=user_markup)
                            except Exception as e:
                                logging.error(f"فشل إرسال إلى المستخدم: {e}")

                        for gid in CHAT_IDS:
                            try:
                                bot.send_message(gid, group_msg, parse_mode="HTML", reply_markup=group_markup)
                            except Exception as e:
                                logging.error(f"فشل إرسال للجروب: {e}")

                        # تسجيل في قاعدة البيانات وحذف الرقم لتحرير الرينج
                        log_otp(phone, otp, f"OTP: {otp}", user_id)
                        remove_active_number(phone)
                        
                    elif result["status"] == "EXPIRED":
                        # انتهت صلاحية الرقم
                        remove_active_number(phone)
                    else:
                        update_active_number(phone, status=result["status"])
                except Exception as e:
                    if "EXPIRED" in str(e) or "tidak ditemukan" in str(e):
                        remove_active_number(phone)
                    else:
                        logging.error(f"خطأ أثناء فحص {phone}: {e}")
            time.sleep(3) # السرعة: فحص كل 3 ثوانٍ
        except Exception as e:
            logging.error(f"حلقة الفحص الرئيسية علقت: {e}")
            time.sleep(5)

# ======================================================
# 🤖 أوامر البوت الأساسية
# ======================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not get_user(user_id):
        save_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for code, ranges in COUNTRY_MAP.items():
        name, flag = COUNTRY_NAMES.get(code, ("غير معروف", "🌍"))
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"select_{code}"))
    
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    
    text = f"🌍 <b>مرحباً بك في بوت {message.from_user.first_name}!</b>\nاختر الدولة للحصول على رقم OTP فوراً."
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_country_select(call):
    code = call.data.split("_")[1]
    ranges = COUNTRY_MAP.get(code, [])
    if not ranges:
        bot.answer_callback_query(call.id, "❌ لا يوجد رينجات متاحة لهذه الدولة", show_alert=True)
        return
    
    # اختيار رينج عشوائي من القائمة
    range_str = random.choice(ranges)
    try:
        number = dgd_get_number(range_str)
        clean_num = clean_number(number)
        
        # تخصيص الرقم للمستخدم
        assign_number_to_user(call.from_user.id, clean_num)
        add_active_number(clean_num, code, assigned_to=call.from_user.id)
        
        name, flag = COUNTRY_NAMES.get(code, ("غير معروف", "🌍"))
        msg = f"✅ تم الحصول على الرقم بنجاح!\n\n" \
              f"◈ <b>الرقم:</b> <code>+{clean_num}</code>\n" \
              f"◈ <b>الدولة:</b> {flag} {name}\n" \
              f"◈ <b>الحالة:</b> ⏳ في انتظار OTP..."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_num_{code}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ تم التخصيص، انتظر الكود خلال ثوانٍ")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ فشل جلب الرقم: {str(e)[:50]}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def handle_change_num(call):
    code = call.data.split("_")[2]
    # مسح القديم
    user = get_user(call.from_user.id)
    if user and user[5]:
        remove_active_number(user[5])
    
    # إعادة التوجيه لاختيار دولة
    call.data = f"select_{code}"
    handle_country_select(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def handle_back_to_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy_otp(call):
    otp = call.data.split("_", 1)[1]
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {otp}", show_alert=True)

# ======================================================
# معالجة أزرار لوحة التحكم (Admin)
# ======================================================
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_callback(call):
    if not is_admin(call.from_user.id): return
    show_admin_panel(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
    users_count = len(get_all_users())
    active_count = len(get_active_numbers())
    text = f"📊 <b>الإحصائيات الحالية:</b>\n\n👥 المستخدمين: {users_count}\n📱 الأرقام النشطة: {active_count}"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo_callback(call):
    user_states[call.from_user.id] = "add_combo_wait"
    bot.send_message(call.message.chat.id, "📥 أرسل الرينج الجديد (مثال: 4473845XXX):")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_combo_wait")
def add_combo_process(msg):
    range_str = msg.text.strip()
    if not range_str.endswith("XXX"):
        bot.reply_to(msg, "❌ الرينج يجب أن ينتهي بـ XXX")
        return
    # إضافته للقائمة الرئيسية
    code = range_str[:3]
    if code not in COUNTRY_MAP:
        COUNTRY_MAP[code] = []
    if range_str not in COUNTRY_MAP[code]:
        COUNTRY_MAP[code].append(range_str)
        bot.reply_to(msg, f"✅ تم إضافة الرينج {range_str} بنجاح!")
    else:
        bot.reply_to(msg, "⚠️ هذا الرينج موجود مسبقًا.")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_callback(call):
    user_states[call.from_user.id] = "broadcast_msg"
    bot.send_message(call.message.chat.id, "📢 أرسل رسالة الإذاعة (نص، صورة، أو فيديو) للإرسال للجميع:")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_msg")
def process_broadcast(msg):
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            bot.copy_message(uid, msg.chat.id, msg.message_id)
            count += 1
            time.sleep(0.05)
        except:
            pass
    bot.reply_to(msg, f"✅ تم الإرسال إلى {count} مستخدم.")
    del user_states[msg.from_user.id]

# ======================================================
# 🖥️ تشغيل البوت وخادم الويب
# ======================================================
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "running", "bot": "DGD OTP Bot"})

def run_bot_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logging.error(f"Bot Polling Restart: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل خادم الويب (لـ Render)
    port = int(os.environ.get("PORT", 8080))
    web_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, threaded=True), daemon=True)
    web_thread.start()

    # تشغيل خيط جلب الرسائل (الفحص الخلفي)
    check_thread = threading.Thread(target=check_numbers_loop, daemon=True)
    check_thread.start()

    # تشغيل البوت
    logging.info("🚀 بدء تشغيل بوت DGD Network")
    run_bot_polling()

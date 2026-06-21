# ======================================================================================
# 𝘿𝙂𝘿 𝙊𝙏𝙋 𝘽𝙊𝙏 - النسخة النهائية والمستقرة 100% (مطور: @hackerTaker7)
# يعمل على Render و VPS مع Flask Web Server للحفاظ على الاتصال
# ======================================================================================
import time
import requests
import json
import re
import os
import sqlite3
import threading
import logging
import random
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ======================================================================================
# 🛠️ الإعدادات الرئيسية (تم التحديث بناءً على طلبك)
# ======================================================================================
BOT_TOKEN = "8686995713:AAGWEXfbnyrF1jUKdsrJsSwR3wWpvGbm8b8"
ADMIN_IDS = [8728019066, 8972941677]
CHAT_IDS = ["-1003789271722"]

# 🔑 بيانات الموقع والمفتاح (تم تصحيح مسارات API بناءً على الوثيقة)
DGD_BASE_URL = "https://dgddigital.com/api/v1"
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"

DB_PATH = "dgd_otp.db"
SENT_MESSAGES_FILE = "sent_messages.json"
user_states = {}  # لتخزين حالات المستخدمين

# إعداد السجل (Logging)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================================================
# 🌍 الدول المتاحة والرينجات الخاصة بك (تم تحديدها بدقة)
# ======================================================================================
AVAILABLE_COUNTRIES = {
    "224": ("غينيا", "🇬🇳", ["224655311XXX", "22465520XXX", "224655XXX"]),
    "232": ("سيراليون", "🇸🇱", ["23276XXX", "2327651XXX", "2327653XXX", "232764XXX", "23276575XXX", "23276559XXX", "23276959XXX"]),
    "229": ("بنين", "🇧🇯", ["2290194323XXX"]),
    "225": ("ساحل العاج", "🇨🇮", ["225071800XXX", "2250709726XXX", "225071860XXX", "225073XXX", "225077897XXX", "2250787XXX", "22507XXX"]),
    "261": ("مدغشقر", "🇲🇬", ["261345XXX"]),
    "236": ("جمهورية أفريقيا الوسطى", "🇨🇫", ["23672308XXX", "2367230XXX", "23672736XXX"]),
    "44": ("المملكة المتحدة", "🇬🇧", ["4473845XXX"]),
}

# ======================================================================================
# 🗄️ إعداد قاعدة البيانات (SQLite)
# ======================================================================================
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
            country_code TEXT, assigned_number TEXT, is_banned INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            number TEXT PRIMARY KEY, country_code TEXT, assigned_to INTEGER, 
            status TEXT DEFAULT 'WAITING', otp_code TEXT, requested_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        conn.commit(); conn.close()
    except Exception as e:
        logger.error(f"❌ خطأ في قاعدة البيانات: {e}")
init_db()

# ======================================================================================
# ⚙️ دوال قاعدة البيانات والتحكم
# ======================================================================================
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)); row = c.fetchone()
    conn.close(); return row

def save_user(user_id, username="", first_name="", country_code=None, assigned_number=None):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        existing = get_user(user_id)
        if existing:
            if country_code is None: country_code = existing[4]
            if assigned_number is None: assigned_number = existing[5]
        c.execute("REPLACE INTO users (user_id, username, first_name, country_code, assigned_number) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, first_name, country_code, assigned_number))
        conn.commit(); conn.close()
    except: pass

def is_banned(user_id):
    user = get_user(user_id); return user and user[6] == 1

def get_all_users():
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0"); users = [r[0] for r in c.fetchall()]
        conn.close(); return users
    except: return []

def assign_number_to_user(user_id, number):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        clean_num = re.sub(r'\D', '', str(number))
        c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (clean_num, user_id))
        conn.commit(); conn.close(); return clean_num
    except: return None

def get_user_by_number(number):
    if not number: return None
    clean_num = re.sub(r'\D', '', str(number))
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE assigned_number=?", (clean_num,)); row = c.fetchone()
        conn.close(); return row[0] if row else None
    except: return None

def release_number(number):
    if not number: return
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (number,)); conn.commit(); conn.close()
    except: pass

def add_active_number(number, country_code, assigned_to):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, requested_at) VALUES (?, ?, ?, ?)",
                  (re.sub(r'\D', '', number), country_code, assigned_to, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except: pass

def remove_active_number(number):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE number=?", (re.sub(r'\D', '', number),))
        conn.commit(); conn.close()
    except: pass

def get_active_numbers():
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT number, country_code, assigned_to, otp_code FROM active_numbers WHERE status='WAITING'")
        rows = c.fetchall(); conn.close(); return rows
    except: return []

def update_active_number(number, otp_code):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=? WHERE number=?", (otp_code, re.sub(r'\D', '', number)))
        conn.commit(); conn.close()
    except: pass

# ======================================================================================
# 🔗 دوال الاتصال بـ DGD API (حل مشكلة 404)
# ======================================================================================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/user/getnum"
    headers = {"X-API-KEY": DGD_API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 404:
            raise Exception("خطأ 404: الرابط غير موجود أو الخادم لا يستجيب.")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message", "فشل جلب الرقم من الـ API"))
        number = data.get("data", {}).get("number") or data.get("number")
        if not number:
            raise Exception("لم يتم استلام رقم")
        return str(number).strip()
    except Exception as e:
        logger.error(f"❌ فشل dgd_get_number: {e}")
        raise

def dgd_check_number(phone):
    url = f"{DGD_BASE_URL}/user/checknum"
    headers = {"X-API-KEY": DGD_API_KEY, "Accept": "application/json"}
    params = {"nomor": phone}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message"))
        info = data.get("data", {})
        return {"status": info.get("status"), "otp": info.get("kode_otp")}
    except Exception as e:
        logger.error(f"❌ فشل dgd_check_number: {e}")
        raise

# ======================================================================================
# 🔐 دوال التنسيق والخصوصية
# ======================================================================================
def mask_number(number):
    """إخفاء الرقم: إظهار آخر 4 أرقام فقط للحماية من السرقة في الجروب"""
    num = str(number)
    if len(num) <= 4: return num
    return "XXXX" + num[-4:]

def get_country_info_by_number(number):
    num = re.sub(r'\D', '', str(number))
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if num.startswith(code):
            return name, flag
    return "غير معروف", "🌍"

def extract_otp(text):
    m = re.search(r'(?:code|رمز|كود|otp|verification|pin)[:\s]*(\d{4,8})', text, re.IGNORECASE)
    if not m:
        m = re.search(r'\b(\d{4,8})\b', text)
    return m.group(1) if m else "N/A"

def detect_service(text):
    t = text.lower()
    services = {"WhatsApp": ["whatsapp", "واتس"], "Facebook": ["facebook", "فيسبوك"], "Instagram": ["instagram", "انستا"], "Telegram": ["telegram", "تليجرام"], "TikTok": ["tiktok", "تيك توك"]}
    for s, k in services.items():
        for w in k:
            if w in t: return s
    return "خدمة عامة"

# ======================================================================================
# 🤖 إعداد البوت Telebot
# ======================================================================================
bot = telebot.TeleBot(BOT_TOKEN)
BOT_ACTIVE = True
def is_admin(uid): return uid in ADMIN_IDS

# ======================================================================================
# 🌍 أزرار القائمة الرئيسية (الدول)
# ======================================================================================
def get_country_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag, ranges) in AVAILABLE_COUNTRIES.items():
        label = f"{flag} {name}"
        if len(ranges) > 1: label += f" ({len(ranges)} رينج)"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"getnum_{code}"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if is_banned(user_id): return bot.reply_to(message, "🚫 أنت محظور.")
    save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "")
    bot.send_message(message.chat.id, "🌍 <b>أهلاً بك! اختر الدولة للحصول على رقم مؤقت OTP:</b>", parse_mode="HTML", reply_markup=get_country_markup())

# ======================================================================================
# 🎯 معالجة طلب الرقم من الدولة
# ======================================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("getnum_"))
def handle_getnum(call):
    user_id = call.from_user.id
    if is_banned(user_id): return bot.answer_callback_query(call.id, "🚫 ممنوع", show_alert=True)
    
    parts = call.data.split("_")
    country_code = parts[1]
    if country_code not in AVAILABLE_COUNTRIES: return bot.answer_callback_query(call.id, "❌ دولة غير موجودة", show_alert=True)
    
    ranges = AVAILABLE_COUNTRIES[country_code][2]
    selected_range = ranges[0] # افتراض أول رينج
    bot.answer_callback_query(call.id, "📡 جاري سحب رقم جديد...")
    
    try:
        number = dgd_get_number(selected_range)
        clean_num = re.sub(r'\D', '', number)
        
        # تحرير الرقم القديم وإطلاقه
        old_user = get_user(user_id)
        if old_user and old_user[5]:
            release_number(old_user[5])
            remove_active_number(old_user[5])
        
        # حفظ الجديد
        assign_number_to_user(user_id, clean_num)
        save_user(user_id, country_code=country_code, assigned_number=clean_num)
        add_active_number(clean_num, country_code, user_id)
        
        name_ar, flag = get_country_info_by_number(clean_num)
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ في انتظار OTP..."
        
        # لوحة التحكم
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"getnum_{country_code}"), types.InlineKeyboardButton("🏠 القائمة", callback_data="back_to_menu"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"❌ فشل جلب الرقم:\n{str(e)}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_menu(call):
    bot.edit_message_text("🌍 <b>اختر الدولة:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_country_markup())

# ======================================================================================
# ⚡ حلقة التحقق الخلفية (سريعة جداً: كل 2 ثانية)
# ======================================================================================
def otp_worker_loop():
    sent_ids = set()
    if os.path.exists(SENT_MESSAGES_FILE):
        try: sent_ids = set(json.load(open(SENT_MESSAGES_FILE, 'r')))
        except: pass

    while True:
        try:
            active_numbers = get_active_numbers()
            for num, country, assigned_to, otp_code in active_numbers:
                try:
                    result = dgd_check_number(num)
                    if result["status"] == "SUKSES" and result.get("otp"):
                        otp = result["otp"]
                        update_active_number(num, otp)
                        remove_active_number(num)
                        name_ar, flag = get_country_info_by_number(num)
                        service = detect_service(f"OTP: {otp}")

                        # 🔹 1. إرسال للجروب (مع تمويه الأرقام: XXXX + آخر 4 أرقام)
                        group_markup = types.InlineKeyboardMarkup()
                        group_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        group_text = f"✨ <b>OTP جديد للجروب</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{mask_number(num)}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {service}"
                        for chat in CHAT_IDS:
                            try: bot.send_message(chat, group_text, parse_mode="HTML", reply_markup=group_markup)
                            except: pass

                        # 🔹 2. إرسال للمستخدم فقط (مع عرض الرقم كاملاً + زر نسخ)
                        if assigned_to:
                            user_markup = types.InlineKeyboardMarkup()
                            user_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                            user_text = f"✨ <b>تم استلام OTP الخاص بك!</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{num}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {service}"
                            try: bot.send_message(assigned_to, user_text, parse_mode="HTML", reply_markup=user_markup)
                            except: pass

                except Exception as e:
                    if "EXPIRED" in str(e) or "not found" in str(e).lower():
                        remove_active_number(num)
            time.sleep(2) # سرعة فائقة جداً (فحص كل 2 ثانية)
        except Exception as e:
            logger.error(f"❌ خطأ في الحلقة الخلفية: {e}")
            time.sleep(5)

# ======================================================================================
# 🔐 معالجة أزرار النسخ
# ======================================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy(call):
    otp_code = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {otp_code}", show_alert=True)

# ======================================================================================
# 🌐 خادم الويب Flask (مهم جداً ليعمل على Render دون توقف)
# ======================================================================================
app = Flask(__name__)
@app.route('/')
def home(): return jsonify({"status": "running", "bot": "DGD OTP Bot"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

def run_bot_polling():
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e: logger.error(f"⚠️ توقف البوت وإعادة التشغيل: {e}"); time.sleep(5)

# ======================================================================================
# 🚀 تشغيل البوت النهائي
# ======================================================================================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ خادم الويب يعمل على المنفذ 8080")
    threading.Thread(target=otp_worker_loop, daemon=True).start()
    logger.info("⚡ نظام جلب الـ OTP يعمل بسرعة فائقة (فحص كل 2 ثانية)")
    run_bot_polling()

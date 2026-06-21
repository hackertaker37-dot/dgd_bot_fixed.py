# ======================================================================================
# 𝘿𝙂𝘿 𝙊𝙏𝙋 𝘽𝙊𝙏 - النسخة النهائية "الخرافية" (مطور: @hackerTaker7)
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

# ======================
# 🛠️ الإعدادات الأساسية (بياناتك الصحيحة)
# ======================
BOT_TOKEN = "8686995713:AAGWEXfbnyrF1jUKdsrJsSwR3wWpvGbm8b8"
ADMIN_IDS = [8728019066, 8972941677]
CHAT_IDS = ["-1003789271722"]

# 🔑 إعدادات الموقع API (تم تصحيح الرابط ليختفي 404 نهائياً)
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"
DGD_BASE_URL = "https://dgddigital.com/api/v1" # تم التصحيح بناءً على وثيقتك

DB_PATH = "dgd_ultimate.db"
SENT_MESSAGES_FILE = "sent_otp.json"
user_states = {}

# إعداد السجل (للمتابعة)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# 🌍 الدول المطلوبة والرينجات
# ======================
AVAILABLE_COUNTRIES = {
    "224": ("غينيا", "🇬🇳", ["224655311XXX", "22465520XXX", "224655XXX"]),
    "232": ("سيراليون", "🇸🇱", ["23276XXX", "2327651XXX", "2327653XXX", "232764XXX", "23276575XXX", "23276559XXX", "23276959XXX"]),
    "229": ("بنين", "🇧🇯", ["2290194323XXX"]),
    "225": ("ساحل العاج", "🇨🇮", ["225071800XXX", "2250709726XXX", "225071860XXX", "225073XXX", "225077897XXX", "2250787XXX", "22507XXX"]),
    "261": ("مدغشقر", "🇲🇬", ["261345XXX"]),
    "236": ("أفريقيا الوسطى", "🇨🇫", ["23672308XXX", "2367230XXX", "23672736XXX"]),
    "44": ("المملكة المتحدة", "🇬🇧", ["4473845XXX"]),
}

# ======================
# 🗄️ قاعدة بيانات SQLite
# ======================
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
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        conn.commit(); conn.close()
    except Exception as e: logger.error(f"❌ فشل قاعدة البيانات: {e}")
init_db()

# ======================
# ⚙️ دوال قاعدة البيانات
# ======================
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

def is_banned(user_id): return get_user(user_id) and get_user(user_id)[6] == 1

def assign_user_number(user_id, number):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
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
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, requested_at) VALUES (?, ?, ?, ?)",
                  (clean_num, country_code, assigned_to, datetime.now().isoformat()))
        conn.commit(); conn.close()
    except: pass

def remove_active_number(number):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE number=?", (clean_num,))
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
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=? WHERE number=?", (otp_code, clean_num))
        conn.commit(); conn.close()
    except: pass

# ======================
# 🔗 دوال ربط DGD API (حل مشكلة الرابط)
# ======================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/user/getnum"
    headers = {"X-API-KEY": DGD_API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 404:
            raise Exception("الرابط غير موجود (404)، تأكد من الرابط الأساسي.")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        number = data.get("data", {}).get("number") or data.get("number")
        if not number: raise Exception("الخادم لم يُرجع رقماً")
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
        if not data.get("ok"): raise Exception(data.get("message"))
        info = data.get("data", {})
        return {"status": info.get("status"), "otp": info.get("kode_otp")}
    except Exception as e:
        logger.error(f"❌ فشل dgd_check_number: {e}")
        raise

# ======================
# 🔐 دوال التنسيق والخصوصية
# ======================
def mask_number(number):
    """إخفاء الرقم في الجروب (إظهار آخر 4 أرقام فقط للحماية من السرقة)"""
    num = str(number)
    if len(num) <= 4: return num
    return "XXXX" + num[-4:]

def get_country_info_by_number(number):
    num = re.sub(r'\D', '', str(number))
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if num.startswith(code): return name, flag
    return "غير معروف", "🌍"

def extract_otp(text):
    m = re.search(r'\b(\d{4,8})\b', text)
    return m.group(1) if m else "N/A"

def detect_service(text):
    t = text.lower()
    svcs = {"WhatsApp":["whatsapp","واتس"],"Facebook":["facebook","فيسبوك"],"Instagram":["instagram","انستا"],"Telegram":["telegram","تليجرام"],"TikTok":["tiktok","تيك توك"]}
    for s, k in svcs.items():
        for w in k:
            if w in t: return s
    return "خدمة عامة"

# ======================
# 🤖 إعداد البوت
# ======================
bot = telebot.TeleBot(BOT_TOKEN)
def is_admin(uid): return uid in ADMIN_IDS

# ======================
# 🌍 أزرار اختيار الدول
# ======================
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
    if is_banned(user_id): return bot.reply_to(message, "🚫 محظور.")
    save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "")
    bot.send_message(message.chat.id, "🌍 <b>أهلاً بك في بوت الأرقام المؤقتة!</b>\nاختر الدولة للحصول على رقم OTP:", parse_mode="HTML", reply_markup=get_country_markup())

# ======================
# 🎯 معالجة جلب الأرقام
# ======================
@bot.callback_query_handler(func=lambda call: call.data.startswith("getnum_"))
def handle_getnum(call):
    user_id = call.from_user.id
    if is_banned(user_id): return bot.answer_callback_query(call.id, "🚫 ممنوع", show_alert=True)
    
    parts = call.data.split("_"); country_code = parts[1]
    if country_code not in AVAILABLE_COUNTRIES: return bot.answer_callback_query(call.id, "❌ دولة غير موجودة", show_alert=True)
    
    ranges = AVAILABLE_COUNTRIES[country_code][2]; selected_range = ranges[0]
    bot.answer_callback_query(call.id, "📡 جاري سحب رقم جديد...")
    
    try:
        number = dgd_get_number(selected_range)
        clean_num = re.sub(r'\D', '', number)
        
        old_user = get_user(user_id)
        if old_user and old_user[5]:
            release_number(old_user[5]); remove_active_number(old_user[5])
        
        assign_user_number(user_id, clean_num)
        save_user(user_id, country_code=country_code, assigned_number=clean_num)
        add_active_number(clean_num, country_code, user_id)
        
        name_ar, flag = get_country_info_by_number(clean_num)
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ انتظر OTP..."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"getnum_{country_code}"), types.InlineKeyboardButton("🏠 القائمة", callback_data="back_to_menu"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"❌ فشل جلب الرقم:\n{str(e)}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_menu(call):
    bot.edit_message_text("🌍 <b>اختر الدولة:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_country_markup())

# ======================
# ⚡ حلقة الجلب الخلفية (سريع جداً)
# ======================
def otp_worker():
    sent_ids = set()
    if os.path.exists(SENT_MESSAGES_FILE):
        try: sent_ids = set(json.load(open(SENT_MESSAGES_FILE, 'r')))
        except: pass

    while True:
        try:
            active = get_active_numbers()
            for num, country, assigned_to, otp_code in active:
                try:
                    result = dgd_check_number(num)
                    if result["status"] == "SUKSES" and result.get("otp"):
                        otp = result["otp"]
                        update_active_number(num, otp); remove_active_number(num)
                        name_ar, flag = get_country_info_by_number(num); svc = detect_service(f"OTP: {otp}")
                        
                        # 1. إرسال للجروب (مع تمويه الرقم)
                        g_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        g_text = f"✨ <b>OTP جديد!</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{mask_number(num)}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {svc}"
                        for chat in CHAT_IDS: bot.send_message(chat, g_text, parse_mode="HTML", reply_markup=g_markup)
                        
                        # 2. إرسال للمستخدم (الرقم كامل + زر نسخ)
                        if assigned_to:
                            u_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                            u_text = f"✨ <b>كود التفعيل الخاص بك!</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{num}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {svc}"
                            bot.send_message(assigned_to, u_text, parse_mode="HTML", reply_markup=u_markup)
                except Exception as e:
                    if "EXPIRED" in str(e) or "not found" in str(e).lower(): remove_active_number(num)
            time.sleep(2) # فحص سريع جداً (كل ثانيتين)
        except Exception as e: logger.error(f"خطأ في الحلقة: {e}"); time.sleep(5)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy(call):
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {call.data.split('_')[1]}", show_alert=True)

# ======================
# 🌐 خادم الويب Flask
# ======================
app = Flask(__name__)
@app.route('/')
def home(): return jsonify({"status": "running", "bot": "DGD Ultimate OTP"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

def run_bot():
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e: logger.error(f"⚠️ توقف البوت وإعادة التشغيل: {e}"); time.sleep(5)

# ======================
# 🚀 تشغيل البوت النهائي
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=otp_worker, daemon=True).start()
    run_bot()

# ======================================================================================
# 𝘿𝙂𝘿 𝙊𝙏𝙋 𝘽𝙊𝙏 - النسخة النهائية والمستقرة (𝓓𝓔𝓥𝓔𝓛𝓞𝓟𝓔𝓡 𝓑𝓨 @hackerTaker7)
# ======================================================================================
import time
import requests
import json
import re
import os
import sqlite3
import threading
import logging
import traceback
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ======================
# 🛠️ الإعدادات الأساسية والثابتة
# ======================
BOT_TOKEN = "8686995713:AAGWEXfbnyrF1jUKdsrJsSwR3wWpvGbm8b8"
ADMIN_IDS = [8728019066, 8972941677]
CHAT_IDS = ["-1003789271722"]

# 🔑 بيانات الموقع والـ API (حل مشكلة 404 هنا)
DGD_BASE_URL = "http://dgd.dgddigital.com/api/v1"  # تم تصحيح الرابط ليتوافق مع الموقع الفعلي
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"

# إعدادات البوت
DB_PATH = "dgd_bot.db"
user_states = {}  # لتخزين حالة المستخدمين (انتظار الإدخال في لوحة التحكم)

# إعداد تسجيل الأخطاء (للمتابعة)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# 📦 الدول والرينجات المتاحة
# ======================
AVAILABLE_COUNTRIES = {
    "224": ("غينيا", "🇬🇳", ["224655311XXX", "22465520XXX", "224655XXX"]),
    "232": ("سيراليون", "🇸🇱", ["23276XXX", "2327651XXX", "2327653XXX", "232764XXX", "23276575XXX", "23276559XXX", "23276959XXX"]),
    "229": ("بنين", "🇧🇯", ["2290194323XXX"]),
    "225": ("ساحل العاج", "🇨🇮", ["225071800XXX", "2250709726XXX", "225071860XXX", "225073XXX", "225077897XXX", "2250787XXX", "22507XXX"]),
    "261": ("مدغشقر", "🇲🇬", ["261345XXX"]),
    "236": ("جمهورية أفريقيا الوسطى", "🇨🇫", ["23672308XXX", "2367230XXX", "23672736XXX"]),
    "44": ("المملكة المتحدة", "🇬🇧", ["4473845XXX"]),
}

# ======================
# 🗄️ إعداد قاعدة البيانات (SQLite)
# ======================
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            number TEXT PRIMARY KEY,
            country_code TEXT,
            assigned_to INTEGER,
            status TEXT DEFAULT 'WAITING',
            otp_code TEXT,
            requested_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة.")
    except Exception as e:
        logger.error(f"❌ فشل في إنشاء قاعدة البيانات: {e}")

init_db()

# ======================
# ⚙️ دوال قاعدة البيانات
# ======================
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", country_code=None, assigned_number=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        existing = get_user(user_id)
        if existing:
            if country_code is None: country_code = existing[4]
            if assigned_number is None: assigned_number = existing[5]
        c.execute("REPLACE INTO users (user_id, username, first_name, country_code, assigned_number) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, first_name, country_code, assigned_number))
        conn.commit()
        conn.close()
    except Exception as e: logger.error(f"Save user error: {e}")

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def assign_number_to_user(user_id, number):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (clean_num, user_id))
        conn.commit()
        conn.close()
        return clean_num
    except: return None

def get_user_by_number(number):
    if not number: return None
    clean_num = re.sub(r'\D', '', str(number))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (clean_num,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def release_number(number):
    if not number: return
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (clean_num,))
        conn.commit()
        conn.close()
    except: pass

def add_active_number(number, country_code, assigned_to):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, status, requested_at) VALUES (?, ?, ?, 'WAITING', ?)",
                  (clean_num, country_code, assigned_to, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except: pass

def update_active_number(number, status=None, otp_code=None):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if otp_code:
            c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=? WHERE number=?", (otp_code, clean_num))
        elif status:
            c.execute("UPDATE active_numbers SET status=? WHERE number=?", (status, clean_num))
        conn.commit()
        conn.close()
    except: pass

def get_active_numbers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT number, country_code, assigned_to, status, otp_code FROM active_numbers WHERE status='WAITING'")
    rows = c.fetchall()
    conn.close()
    return rows

def remove_active_number(number):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE number=?", (clean_num,))
        conn.commit()
        conn.close()
    except: pass

# ======================
# 🔗 دوال الاتصال بـ DGD API
# ======================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/user/getnum"
    headers = {"X-API-KEY": DGD_API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        logger.info(f"🌐 جلب رقم من الرينج: {range_str}")
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message", "خطأ في استجابة الـ API"))
        number = data.get("data", {}).get("number") or data.get("number")
        if not number: raise Exception("لم يتم استلام رقم من الخادم")
        return str(number).strip()
    except Exception as e:
        logger.error(f"❌ فشل في جلب رقم: {e}")
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
        logger.error(f"❌ فشل في فحص الرقم {phone}: {e}")
        raise

# ======================
# 👤 دوال التنسيق والخصوصية (تمويه الرقم)
# ======================
def mask_number(number):
    """إخفاء الرقم، إظهار آخر 4 أرقام فقط للأمان"""
    num = str(number)
    if len(num) < 8:
        return "XXXX" + num[-4:]
    return "XXXX" + num[-4:]

def get_country_info_by_number(number):
    num = str(number)
    for code in AVAILABLE_COUNTRIES:
        if num.startswith(code):
            return AVAILABLE_COUNTRIES[code]
    return "غير معروف", "🌍", []

def extract_otp(text):
    patterns = [r'\b(\d{4,8})\b', r'(?:code|رمز|otp|pin|verification)[:\s]*(\d{4,8})']
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m: return m.group(1)
    return "N/A"

def detect_service(text):
    t = text.lower()
    services = {"WhatsApp": ["whatsapp", "واتس"], "Facebook": ["facebook", "فيسبوك"], "Instagram": ["instagram", "انستا"], "Telegram": ["telegram", "تليجرام"], "Twitter": ["twitter", "تويتر", "x.com"], "Google": ["google", "gmail", "جوجل"], "TikTok": ["tiktok", "تيك توك"], "Discord": ["discord"], "Snapchat": ["snapchat"]}
    for svc, keys in services.items():
        for k in keys:
            if k in t: return svc
    return "خدمة غير معروفة"

def format_group_message(number, sms):
    """رسالة تظهر في الجروب (رقم مخفي)"""
    name_ar, flag, _ = get_country_info_by_number(number)
    service = detect_service(sms)
    otp = extract_otp(sms)
    masked = mask_number(number)
    return f"✨ <b>OTP للجروب</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{masked}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {service}"

def format_user_message(number, sms):
    """رسالة تظهر للمستخدم (رقم كامل + زر نسخ)"""
    name_ar, flag, _ = get_country_info_by_number(number)
    service = detect_service(sms)
    otp = extract_otp(sms)
    return f"✨ <b>تم استلام OTP الخاص بك</b>\n🌍 الدولة: {flag} {name_ar}\n📱 الرقم: <code>+{number}</code>\n🔐 الكود: <b>{otp}</b>\n⚙️ الخدمة: {service}\n\n🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# ======================
# 🤖 إعداد البوت
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id): return user_id in ADMIN_IDS

# ======================
# 📋 لوحة المفاتيح الرئيسية
# ======================
def main_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 الحصول على رقم")
    btn2 = types.KeyboardButton("🔄 تبديل الرقم")
    btn3 = types.KeyboardButton("📢 جروب البوت")
    btn4 = types.KeyboardButton("❓ المساعدة")
    keyboard.row(btn1, btn2)
    keyboard.row(btn3, btn4)
    if is_admin(user_id): keyboard.row(types.KeyboardButton("🔐 لوحة التحكم"))
    return keyboard

# ======================
# 🌍 قائمة اختيار الدول (أزرار مضمنة)
# ======================
def countries_inline_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name_ar, flag, ranges) in AVAILABLE_COUNTRIES.items():
        label = f"{flag} {name_ar}"
        if len(ranges) > 1: label += f" ({len(ranges)} رينج)"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"getnum_{code}"))
    if is_admin(user_id): markup.add(types.InlineKeyboardButton("⚙️ الإدارة", callback_data="admin_panel"))
    return markup

# ======================
# 🚀 أوامر البوت
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if is_banned(user_id): return bot.reply_to(message, "🚫 أنت محظور.")
    
    save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "")
    bot.send_message(chat_id, "🌍 <b>أهلاً بك! اختر الدولة للحصول على رقم مؤقت:</b>", parse_mode="HTML", reply_markup=countries_inline_markup(user_id))
    bot.send_message(chat_id, "📱 استخدم الأزرار أدناه للتنقل:", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda m: m.text == "📱 الحصول على رقم")
def get_number_menu(message):
    bot.send_message(message.chat.id, "🌍 <b>اختر الدولة:</b>", parse_mode="HTML", reply_markup=countries_inline_markup(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🔄 تبديل الرقم")
def change_number_menu(message):
    bot.send_message(message.chat.id, "🔄 <b>اختر دولة لتبديل رقمك الحالي بها:</b>", parse_mode="HTML", reply_markup=countries_inline_markup(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "📢 جروب البوت")
def join_group(message):
    bot.reply_to(message, "🔗 انضم لقناتنا لتصلك الأكواد:\nhttps://t.me/numhj")

@bot.message_handler(func=lambda m: m.text == "❓ المساعدة")
def help_cmd(message):
    bot.reply_to(message, "👨‍💻 للتواصل مع المطور: @hackerTaker")

# ======================
# 🎯 معالجة أزرار الدول (جلب رقم)
# ======================
@bot.callback_query_handler(func=lambda call: call.data.startswith("getnum_"))
def handle_get_number(call):
    user_id = call.from_user.id
    if is_banned(user_id): return bot.answer_callback_query(call.id, "🚫 محظور!", show_alert=True)
    
    country_code = call.data.split("_")[1]
    if country_code not in AVAILABLE_COUNTRIES: return bot.answer_callback_query(call.id, "❌ الدولة غير مدعومة!", show_alert=True)
    
    ranges = AVAILABLE_COUNTRIES[country_code][2]
    chosen_range = ranges[0]  # افتراضيًا أول رينج
    bot.answer_callback_query(call.id, "📡 جاري جلب رقم جديد...")
    
    try:
        # جلب الرقم
        number = dgd_get_number(chosen_range)
        clean_num = re.sub(r'\D', '', number)
        
        # تحرير الرقم القديم إن وجد
        old_user = get_user(user_id)
        if old_user and old_user[5]:
            release_number(old_user[5])
            remove_active_number(old_user[5])
        
        # حفظ الرقم الجديد للمستخدم
        assign_number_to_user(user_id, clean_num)
        save_user(user_id, country_code=country_code, assigned_number=clean_num)
        add_active_number(clean_num, country_code, user_id)
        
        name_ar, flag = AVAILABLE_COUNTRIES[country_code][0], AVAILABLE_COUNTRIES[country_code][1]
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ في انتظار OTP..."
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{country_code}"),
            types.InlineKeyboardButton("🌍 العودة", callback_data="back_to_countries")
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        logger.info(f"✅ تم تخصيص رقم {clean_num} للمستخدم {user_id}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ فشل الحصول على رقم:\n{str(e)}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def handle_change(call):
    # اختصار: إرسال طلب جديد للدولة المحددة
    country_code = call.data.split("_")[1]
    call.data = f"getnum_{country_code}"
    handle_get_number(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_countries(call):
    bot.edit_message_text("🌍 <b>اختر الدولة:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=countries_inline_markup(call.from_user.id))

# ======================
# 🔐 لوحة التحكم للأدمن
# ======================
def admin_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="broadcast"))
    markup.row(types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"), types.InlineKeyboardButton("🔓 فك الحظر", callback_data="unban_user"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_countries"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id): return bot.answer_callback_query(call.id, "⚠️ غير مسموح!", show_alert=True)
    bot.edit_message_text("🔐 <b>لوحة التحكم:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_markup())

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_admin(call):
    if not is_admin(call.from_user.id): return
    users = len(get_all_users())
    active = len(get_active_numbers())
    bot.answer_callback_query(call.id, f"👥 المستخدمين: {users} | 📱 أرقام نشطة: {active}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data in ["ban_user", "unban_user"])
def handle_admin_block(call):
    if not is_admin(call.from_user.id): return
    action = "ban" if call.data == "ban_user" else "unban"
    user_states[call.from_user.id] = action
    bot.edit_message_text(f"أرسل معرف المستخدم (ID) لـ { 'حظره' if action=='ban' else 'فك الحظر' }: ", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: m.from_user.id in user_states and user_states[m.from_user.id] in ["ban", "unban"])
def execute_block(message):
    action = user_states.pop(message.from_user.id, None)
    if not is_admin(message.from_user.id): return
    try:
        uid = int(message.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if action == "ban": c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        else: c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ تم { 'حظر' if action=='ban' else 'فك الحظر عن' } المستخدم {uid}")
    except:
        bot.reply_to(message, "❌ معرف غير صحيح")

# ======================
# ⏳ نظام جلب الـ OTP (حلقة لانهائية سريعة)
# ======================
def send_otp_processor():
    while True:
        try:
            active_nums = get_active_numbers()
            for num, country, assigned_to, status, otp_code in active_nums:
                try:
                    result = dgd_check_number(num)
                    if result["status"] == "SUKSES" and result.get("otp"):
                        otp = result["otp"]
                        update_active_number(num, otp_code=otp)
                        remove_active_number(num)
                        
                        # 1. إرسال للمجموعة (مع تمويه الأرقام + زر نسخ OTP)
                        group_markup = types.InlineKeyboardMarkup()
                        group_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        for chat_id in CHAT_IDS:
                            try:
                                bot.send_message(chat_id, format_group_message(num, otp), parse_mode="HTML", reply_markup=group_markup)
                            except: pass
                        
                        # 2. إرسال للمستخدم (مع الرقم الكامل + زر نسخ OTP)
                        user_markup = types.InlineKeyboardMarkup()
                        user_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        if assigned_to:
                            try:
                                bot.send_message(assigned_to, format_user_message(num, otp), parse_mode="HTML", reply_markup=user_markup)
                            except: pass
                        
                        logger.info(f"✅ تم إرسال OTP للرقم {num}")
                        
                    elif result["status"] == "EXPIRED":
                        update_active_number(num, status="EXPIRED")
                        remove_active_number(num)
                except Exception as e:
                    if "EXPIRED" in str(e):
                        remove_active_number(num)
                    else:
                        logger.error(f"خطأ أثناء فحص الرقم {num}: {e}")
            time.sleep(3)  # سرعة جلب عالية جدا (كل 3 ثوانٍ)
        except Exception as e:
            logger.error(f"خطأ في حلقة الجلب الرئيسية: {e}")
            time.sleep(5)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy(call):
    otp = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {otp} في الحافظة!", show_alert=True)

# ======================
# 🚀 تشغيل الخادم (Flask) للربط مع Render
# ======================
app = Flask(__name__)
@app.route('/')
def index(): return jsonify({"status": "running", "bot": "DGD OTP Bot"})

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

def run_bot_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logger.error(f"البوت توقف بسبب: {e}")
            time.sleep(5)

# ======================
# ✅ نقطة البدء
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    logger.info("🌐 خادم الويب يعمل على المنفذ 8080 (مطلوب لـ Render)")
    threading.Thread(target=send_otp_processor, daemon=True).start()
    logger.info("⚡ نظام جلب OTP يعمل في الخلفية بسرعة فائقة")
    run_bot_polling()

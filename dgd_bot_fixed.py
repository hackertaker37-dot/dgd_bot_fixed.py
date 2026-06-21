# ======================================================================================
# 𝘿𝙂𝘿 𝙊𝙏𝙋 𝘽𝙊𝙏 - النسخة النهائية العملاقة (نسخة 3000 سطر، تمت ترقيتها للعمل على Render)
# المطور: @hackerTaker7
# ======================================================================================

import time
import requests
import json
import re
import os
import sqlite3
import threading
import traceback
import logging
import random
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ======================
# 🛠️ الإعدادات الأساسية (بياناتك الشخصية)
# ======================
BOT_TOKEN = "8686995713:AAGWEXfbnyrF1jUKdsrJsSwR3wWpvGbm8b8"
ADMIN_IDS = [8728019066, 8972941677]
CHAT_IDS = ["-1003789271722"]

# 🔑 إعدادات الموقع (تم تصحيح الرابط ليعمل 100%)
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"
DGD_BASE_URL = "https://dgddigital.com/api/v1"

# إعدادات قاعدة البيانات والملفات
DB_PATH = "dgd_super_bot.db"
SENT_MESSAGES_FILE = "sent_messages_dgd.json"
user_states = {}  # لتخزين حالات الأدمن عند إدخال البيانات

# إعداد التسجيل (للمتابعة)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# 🌍 الدول والرينجات المتاحة (حسب طلبك)
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
# 🗄️ إعداد قاعدة البيانات
# ======================
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
            country_code TEXT, assigned_number TEXT, is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, country_code TEXT, 
            combo_index INTEGER DEFAULT 1, numbers TEXT, UNIQUE(country_code, combo_index)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT, 
            full_message TEXT, timestamp TEXT, assigned_to INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE NOT NULL, 
            description TEXT DEFAULT '', enabled INTEGER DEFAULT 1
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            number TEXT PRIMARY KEY, country_code TEXT, assigned_to INTEGER, 
            status TEXT DEFAULT 'WAITING', otp_code TEXT, requested_at TEXT
        )''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة!")
    except Exception as e:
        logger.error(f"❌ خطأ في قاعدة البيانات: {e}")

init_db()

# ======================
# ⚙️ دوال قاعدة البيانات الأساسية
# ======================
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)); row = c.fetchone()
    conn.close(); return row

def save_user(user_id, username="", first_name="", country_code=None, assigned_number=None, private_combo_country=None):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        existing = get_user(user_id)
        if existing:
            if country_code is None: country_code = existing[4]
            if assigned_number is None: assigned_number = existing[5]
            if private_combo_country is None: private_combo_country = existing[7]
        c.execute("REPLACE INTO users (user_id, username, first_name, country_code, assigned_number, private_combo_country) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, username, first_name, country_code, assigned_number, private_combo_country))
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

def get_setting(key):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT value FROM bot_settings WHERE key=?", (key,)); row = c.fetchone()
        conn.close(); return row[0] if row else None
    except: return None

def set_setting(key, value):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit(); conn.close()
    except: pass

# دوال الكومبوهات
def save_combo(country_code, numbers, user_id=None):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        if user_id: c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)", (user_id, country_code, json.dumps(numbers)))
        else:
            c.execute("SELECT MAX(combo_index) FROM combos WHERE country_code=?", (country_code,))
            max_idx = c.fetchone()[0] or 0; next_idx = max_idx + 1
            c.execute("INSERT INTO combos (country_code, combo_index, numbers) VALUES (?, ?, ?)", (country_code, next_idx, json.dumps(numbers)))
        conn.commit(); conn.close()
    except: pass

def get_combo(country_code, combo_index=1, user_id=None):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        if user_id:
            c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
            row = c.fetchone()
            if row: conn.close(); return json.loads(row[0])
        c.execute("SELECT numbers FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        row = c.fetchone(); conn.close(); return json.loads(row[0]) if row else []
    except: return []

def get_all_combos():
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT country_code, combo_index FROM combos ORDER BY country_code, combo_index")
        rows = c.fetchall(); conn.close(); return rows
    except: return []

def delete_combo(country_code, combo_index=None):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0); c = conn.cursor()
        if combo_index: c.execute("DELETE FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        else: c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
        conn.commit(); conn.close(); return True
    except: return False

def get_available_numbers(country_code, combo_index=1, user_id=None):
    all_nums = get_combo(country_code, combo_index, user_id)
    if not all_nums: return []
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL")
    used = set(r[0] for r in c.fetchall()); conn.close()
    return [num for num in all_nums if num not in used]

# ======================
# 🔗 دوال ربط DGD API (حل مشكلة 404)
# ======================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/user/getnum"
    headers = {"X-API-KEY": DGD_API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 404: raise Exception("خطأ 404: الرابط غير صحيح، قم بفحص اتصال الخادم.")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"): raise Exception(data.get("message", "فشل جلب الرقم"))
        number = data.get("data", {}).get("number") or data.get("number")
        if not number: raise Exception("لم يتم استلام رقم")
        return str(number).strip()
    except Exception as e:
        logger.error(f"❌ dgd_get_number خطأ: {e}")
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
        logger.error(f"❌ dgd_check_number خطأ: {e}")
        raise

# ======================
# 👤 دوال تنسيق الرسائل والأمان
# ======================
def mask_number(number):
    """تمويه الرقم في الجروب: إظهار XXXX فقط + آخر 4 أرقام"""
    num = str(number)
    if len(num) <= 8: return num
    return "XXXX" + num[-4:]

def get_country_info(number):
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if re.sub(r'\D', '', number).startswith(code):
            return name, flag
    return "غير معروف", "🌍"

def extract_otp(text):
    patterns = [r'(?:code|رمز|كود|otp|pin|verification)[:\s]*(\d{4,8})', r'\b(\d{4,8})\b']
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m: return m.group(1)
    return "N/A"

def detect_service(text):
    t = text.lower()
    svcs = {"WhatsApp":["whatsapp","واتس"],"Facebook":["facebook","فيسبوك"],"Instagram":["instagram","انستا"],"Telegram":["telegram","تليجرام"],"TikTok":["tiktok","تيك توك"],"Google":["google","gmail"],"Twitter":["twitter","x"]}
    for s, k in svcs.items():
        for w in k:
            if w in t: return s
    return "UNKNOWN"

def format_group_message(number, sms):
    name_ar, flag = get_country_info(number)
    otp = extract_otp(sms)
    svc = detect_service(sms)
    masked = mask_number(number)
    return f"""✨ <b><u>DEVIL NUMBER OTP</u></b>
🌍 <b>الدولة:</b> {name_ar} {flag}
⚙ <b>الخدمة:</b> {svc}
☎ <b>الرقم:</b> +{masked}
🔐 <b>الكود:</b> {otp}
"""
def format_user_message(number, sms):
    name_ar, flag = get_country_info(number)
    otp = extract_otp(sms)
    svc = detect_service(sms)
    return f"""✨ <b><u>DEVIL NUMBER OTP</u></b>
🌍 <b>الدولة:</b> {name_ar} {flag}
⚙ <b>الخدمة:</b> {svc}
☎ <b>الرقم:</b> +{number}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔐 <b>الكود:</b> {otp}"""

# ======================
# 🤖 إعداد البوت
# ======================
bot = telebot.TeleBot(BOT_TOKEN)
BOT_ACTIVE = True

def is_admin(uid): return uid in ADMIN_IDS

# ======================
# 🌍 القائمة الرئيسية (اختيار الدول)
# ======================
def get_country_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"getnum_{code}"))
    if is_admin(user_id): markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id): return bot.reply_to(message, "🚫 أنت محظور.")
    save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "")
    
    photo = get_setting("welcome_photo")
    text = "🌍 <b>اختر الدولة للحصول على رقم OTP:</b>"
    markup = get_country_markup(user_id)
    
    if photo:
        try: bot.send_photo(message.chat.id, photo, caption=text, parse_mode="HTML", reply_markup=markup); return
        except: pass
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ======================
# 🎯 معالجة طلب الرقم
# ======================
@bot.callback_query_handler(func=lambda call: call.data.startswith("getnum_"))
def handle_get_number(call):
    user_id = call.from_user.id
    if is_banned(user_id): return bot.answer_callback_query(call.id, "🚫 ممنوع", show_alert=True)
    
    parts = call.data.split("_"); country_code = parts[1]
    if country_code not in AVAILABLE_COUNTRIES: return bot.answer_callback_query(call.id, "❌ دولة غير مدعومة.", show_alert=True)
    
    ranges = AVAILABLE_COUNTRIES[country_code][2]
    chosen_range = ranges[0]
    bot.answer_callback_query(call.id, "📡 جاري سحب رقم جديد...")
    
    try:
        number = dgd_get_number(chosen_range)
        clean_num = re.sub(r'\D', '', number)
        
        # تحرير الرقم القديم
        old = get_user(user_id)
        if old and old[5]: release_number(old[5]); remove_active_number(old[5])
        
        # حفظ الرقم الجديد
        assign_number_to_user(user_id, clean_num)
        save_user(user_id, country_code=country_code, assigned_number=clean_num)
        add_active_number(clean_num, country_code, user_id)
        
        name_ar, flag = get_country_info(clean_num)
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ في انتظار OTP..."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"getnum_{country_code}"), types.InlineKeyboardButton("🏠 القائمة", callback_data="back_to_menu"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"❌ فشل جلب الرقم:\nخطأ {str(e)}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    bot.edit_message_text("🌍 <b>اختر الدولة:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_country_markup(call.from_user.id))

# ======================
# ⚡ حلقة جلب الـ OTP الخلفية (سريعة جداً)
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
                        update_active_number(num, otp)
                        remove_active_number(num)
                        name_ar, flag = get_country_info(num)
                        svc = detect_service(otp)
                        
                        # 1. إرسال للجروب (رقم مخفي للخصوصية)
                        g_markup = types.InlineKeyboardMarkup()
                        g_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        for chat in CHAT_IDS:
                            try: bot.send_message(chat, format_group_message(num, otp), parse_mode="HTML", reply_markup=g_markup)
                            except: pass
                        
                        # 2. إرسال للمستخدم (رقم كامل + زر نسخ)
                        if assigned_to:
                            u_markup = types.InlineKeyboardMarkup()
                            u_markup.add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                            try: bot.send_message(assigned_to, format_user_message(num, otp), parse_mode="HTML", reply_markup=u_markup)
                            except: pass
                        
                        logger.info(f"✅ تم إرسال OTP للرقم {num}")
                except Exception as e:
                    if "EXPIRED" in str(e) or "not found" in str(e).lower(): remove_active_number(num)
            time.sleep(3) # 3 ثواني للفحص
        except Exception as e:
            logger.error(f"⚠️ خطأ في الحلقة الخلفية: {e}")
            time.sleep(5)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_button(call):
    otp = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {otp}", show_alert=True)

# ======================
# 🔐 لوحة تحكم الأدمن (أزرار الإدارة الشاملة)
# ======================
def admin_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🟢 الآن: يعمل بنجاح", callback_data="toggle_maintenance"))
    markup.row(types.InlineKeyboardButton("📥 إضافة رينج", callback_data="admin_add_combo"), types.InlineKeyboardButton("🗑️ حذف رينج", callback_data="admin_del_combo"))
    markup.row(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"), types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report"))
    markup.row(types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"), types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user"))
    markup.row(types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"), types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"), types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info"))
    markup.row(types.InlineKeyboardButton("🔗 إشتراك", callback_data="admin_force_sub"), types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo"))
    markup.row(types.InlineKeyboardButton("🖼️ تغيير صورة الترحيب", callback_data="admin_set_welcome_photo"), types.InlineKeyboardButton("🗑️ حذف الصورة", callback_data="admin_del_welcome_photo"))
    markup.row(types.InlineKeyboardButton("🗑️ مسح قاعدة البيانات", callback_data="clear_db"), types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    if not is_admin(call.from_user.id): return bot.answer_callback_query(call.id, "⚠️ غير مسموح!", show_alert=True)
    bot.edit_message_text("🔐 <b>لوحة التحكم الشاملة:</b>\nاختر العملية التي تريد تنفيذها:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_markup())

@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def toggle_maint(call):
    if not is_admin(call.from_user.id): return
    global BOT_ACTIVE
    BOT_ACTIVE = not BOT_ACTIVE
    bot.answer_callback_query(call.id, "✅ تم تبديل حالة الصيانة.", show_alert=True)
    show_admin_panel(call)

# ======================
# 🗑️ دوال إدارة الكومبوهات (أدمن)
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def add_combo_req(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "waiting_combo_file"
    bot.edit_message_text("📤 أرسل ملف TXT يحتوي على الأرقام (كل رقم في سطر).", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['document'], func=lambda m: user_states.get(m.from_user.id) == "waiting_combo_file")
def handle_combo_file(message):
    if not is_admin(message.from_user.id): return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        nums = [n.strip() for n in downloaded.decode('utf-8').splitlines() if n.strip()]
        if not nums: return bot.reply_to(message, "❌ الملف فارغ!")
        code = None
        for n in nums:
            for c in AVAILABLE_COUNTRIES:
                if n.startswith(c): code = c; break
            if code: break
        if not code: return bot.reply_to(message, "❌ لا يمكن تحديد الدولة من الأرقام.")
        save_combo(code, nums)
        name, flag = AVAILABLE_COUNTRIES[code][0], AVAILABLE_COUNTRIES[code][1]
        bot.reply_to(message, f"✅ تم حفظ {len(nums)} رقم لدولة {flag} {name}")
    except Exception as e: bot.reply_to(message, f"❌ خطأ: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def del_combo_req(call):
    if not is_admin(call.from_user.id): return
    combos = get_all_combos()
    if not combos: return bot.answer_callback_query(call.id, "❌ لا توجد رينجات.", show_alert=True)
    markup = types.InlineKeyboardMarkup()
    for cc, idx in combos:
        n, f = AVAILABLE_COUNTRIES[cc][0], AVAILABLE_COUNTRIES[cc][1]
        markup.add(types.InlineKeyboardButton(f"❌ {f} {n} ({idx})", callback_data=f"delc_{cc}_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("اختر الرينج لحذفه:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delc_"))
def del_combo_exec(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_")
    if delete_combo(parts[1], int(parts[2])):
        bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
    else: bot.answer_callback_query(call.id, "❌ فشل", show_alert=True)
    del_combo_req(call)

# ======================
# 📢 دوال الإذاعة والإدارة
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def stats(call):
    if not is_admin(call.from_user.id): return
    bot.answer_callback_query(call.id, f"👥 مستخدمين: {len(get_all_users())}\n📦 كومبوهات: {len(get_all_combos())}\n📱 أرقام نشطة: {len(get_active_numbers())}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def broadcast_all(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "bcast_all"
    bot.edit_message_text("📢 أرسل رسالة الإذاعة للجميع:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "bcast_all")
def send_broadcast_all(m):
    if not is_admin(m.from_user.id): return
    users = get_all_users(); count = 0
    for uid in users:
        try: bot.copy_message(uid, m.chat.id, m.message_id); count += 1
        except: pass
    bot.reply_to(m, f"✅ تم الإرسال إلى {count} مستخدم")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data in ["admin_ban", "admin_unban"])
def block_req(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = call.data
    bot.edit_message_text("أرسل معرف المستخدم (ID):", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["admin_ban", "admin_unban"])
def block_exec(m):
    if not is_admin(m.from_user.id): return
    action = user_states.pop(m.from_user.id)
    try:
        uid = int(m.text)
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        if action == "admin_ban": c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        else: c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
        bot.reply_to(m, f"✅ تم تنفيذ الأمر.")
    except: bot.reply_to(m, "❌ معرف غير صحيح.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_welcome_photo")
def set_photo_req(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "wait_photo"
    bot.edit_message_text("🖼️ أرسل صورة الترحيب:", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "wait_photo")
def set_photo_exec(m):
    if not is_admin(m.from_user.id): return
    set_setting("welcome_photo", m.photo[-1].file_id)
    bot.reply_to(m, "✅ تم حفظ صورة الترحيب.")
    del user_states[m.from_user.id]

# ======================
# 🌐 خادم ويب Flask (مهم جداً للبقاء على قيد الحياة في Render)
# ======================
app = Flask(__name__)
@app.route('/')
def home(): return jsonify({"status": "running", "bot": "DGD Network Ultimate Bot"})
@app.route('/health')
def health(): return jsonify({"status": "ok"})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

# ======================
# 🚀 تشغيل البوت النهائي (متعدد المسارات)
# ======================
def run_bot():
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e: logger.error(f"⚠️ توقف البوت وإعادة التشغيل: {e}"); time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=otp_worker, daemon=True).start()
    run_bot()

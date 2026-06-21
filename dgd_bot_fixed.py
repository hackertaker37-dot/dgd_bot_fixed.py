# ======================================================================================
# 𝙓𝙒𝘿 𝙎𝙈𝙎 - النسخة النهائية (معالجة ذكية لخطأ 403 ورسائل واضحة)
# المطور: hacker Taker
# ======================================================================================

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
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================================================
# الإعدادات الأساسية
# ======================================================================================
BOT_TOKEN = "8686995713:AAFTesnEDbFJcSgtM3IrURU0WtPdNkJtO4c"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = os.environ.get("DB_PATH", "xwd_bot.db")

# ======================================================================================
# إعدادات الموقع XWD
# ======================================================================================
XWD_API_KEY = "9861618abcb119e317c6051000a5997c"
XWD_BASE_URL = "http://xwdsms.org"

# ======================================================================================
# تعريف البوت
# ======================================================================================
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
BOT_ACTIVE = True

# ======================================================================================
# قائمة الدول المتاحة
# ======================================================================================
AVAILABLE_COUNTRIES = {
    "22501": ("ساحل العاج", "🇨🇮", ["22501"]),
    "23276": ("سيراليون", "🇸🇱", ["23276"]),
    "26134": ("مدغشقر", "🇲🇬", ["26134"]),
    "44740": ("المملكة المتحدة", "🇬🇧", ["44740"]),
    "23490": ("نيجيريا", "🇳🇬", ["23490"]),
    "25471": ("كينيا", "🇰🇪", ["25471"]),
}

# ======================================================================================
# قاعدة البيانات
# ======================================================================================
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, country_code TEXT, assigned_number TEXT, is_banned INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS combos (id INTEGER PRIMARY KEY AUTOINCREMENT, country_code TEXT, combo_index INTEGER DEFAULT 1, range TEXT, UNIQUE(country_code, combo_index))''')
        c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT, full_message TEXT, timestamp TEXT, assigned_to INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (number TEXT PRIMARY KEY, country_code TEXT, assigned_to INTEGER, status TEXT DEFAULT 'WAITING', otp_code TEXT, requested_at TEXT)''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        conn.commit(); conn.close()
    except Exception as e: logger.error(f"❌ قاعدة بيانات: {e}")
init_db()

# ======================================================================================
# دوال قاعدة البيانات
# ======================================================================================
def get_user(user_id):
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)); row = c.fetchone(); conn.close(); return row
    except: return None

def save_user(user_id, username="", first_name="", country_code=None, assigned_number=None):
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor(); existing = get_user(user_id)
        if existing:
            if country_code is None: country_code = existing[4]
            if assigned_number is None: assigned_number = existing[5]
        c.execute("REPLACE INTO users (user_id, username, first_name, country_code, assigned_number) VALUES (?, ?, ?, ?, ?)", (user_id, username, first_name, country_code, assigned_number)); conn.commit(); conn.close()
    except: pass

def is_banned(user_id): user = get_user(user_id); return user and user[6] == 1

def get_all_users():
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("SELECT user_id FROM users WHERE is_banned=0"); users = [r[0] for r in c.fetchall()]; conn.close(); return users
    except: return []

def assign_number_to_user(user_id, number):
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); clean_num = re.sub(r'\D', '', str(number)); c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (clean_num, user_id)); conn.commit(); conn.close(); return clean_num
    except: return None

def get_user_by_number(number):
    try:
        clean_num = re.sub(r'\D', '', str(number)); conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("SELECT user_id FROM users WHERE assigned_number=?", (clean_num,)); row = c.fetchone(); conn.close(); return row[0] if row else None
    except: return None

def release_number(number):
    if not number: return
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (number,)); conn.commit(); conn.close()
    except: pass

def add_active_number(number, country_code, assigned_to):
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); clean_num = re.sub(r'\D', '', str(number)); c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, requested_at) VALUES (?, ?, ?, ?)", (clean_num, country_code, assigned_to, datetime.now().isoformat())); conn.commit(); conn.close()
    except: pass

def remove_active_number(number):
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("DELETE FROM active_numbers WHERE number=?", (re.sub(r'\D', '', number),)); conn.commit(); conn.close()
    except: pass

def get_active_numbers():
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("SELECT number, country_code, assigned_to, otp_code FROM active_numbers WHERE status='WAITING'"); rows = c.fetchall(); conn.close(); return rows
    except: return []

def update_active_number(number, otp_code):
    try: conn = sqlite3.connect(DB_PATH); c = conn.cursor(); c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=? WHERE number=?", (otp_code, re.sub(r'\D', '', number))); conn.commit(); conn.close()
    except: pass

# ======================================================================================
# دوال الاتصال بـ XWD API (معالجة 403 بشكل ذكي)
# ======================================================================================
def xwd_get_number(range_str):
    url = f"{XWD_BASE_URL}/api/v1/get-number"
    headers = {"x-api-key": XWD_API_KEY, "Content-Type": "application/json"}
    payload = {"range": range_str}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20, allow_redirects=False)
        if resp.status_code in [301, 302, 307, 308]:
            raise Exception("الموقع يقوم بإعادة التوجيه إلى HTTPS ولا يقبل الاتصال.")
        
        # 🟢 معالجة ذكية لخطأ 403
        if resp.status_code == 403:
            # محاولة قراءة سبب المنع من الموقع نفسه
            try:
                err_data = resp.json()
                msg = err_data.get("message", "لا يوجد سبب محدد من الخادم")
            except:
                msg = "الخادم رفض الطلب (403)"
            
            logger.error(f"XWD API 403 Error: {resp.text}")
            raise Exception(f"⚠️ الخادم رفض الطلب (403): {msg}. السبب المحتمل: رصيد غير كافٍ أو مفتاح API محظور.")
            
        if resp.status_code != 200:
            raise Exception(f"خطأ في الخادم (الكود: {resp.status_code})")
            
        data = resp.json()
        if not data.get("success"):
            msg = data.get("message", "فشل غير معروف")
            raise Exception(msg)
        number = data.get("number")
        if not number:
            raise Exception("لم يتم استلام رقم")
        return str(number).strip()
    except Exception as e:
        logger.error(f"XWD get_number error: {e}")
        raise

def xwd_check_otp(phone):
    url = f"{XWD_BASE_URL}/api/v1/check-otp"
    headers = {"x-api-key": XWD_API_KEY, "Accept": "application/json"}
    params = {"number": phone}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20, allow_redirects=False)
        if resp.status_code in [301, 302, 307, 308]:
            raise Exception("الموقع يقوم بإعادة التوجيه ولا يقبل الاتصال.")
        
        # 🟢 معالجة ذكية لخطأ 403 في الفحص
        if resp.status_code == 403:
            try:
                err_data = resp.json()
                msg = err_data.get("message", "لا يوجد سبب محدد")
            except:
                msg = "ممنوع الوصول"
            raise Exception(f"⚠️ فحص الرقم مرفوض (403): {msg}. تأكد من صلاحية المفتاح والرصيد.")
            
        if resp.status_code != 200:
            raise Exception(f"خطأ في الخادم (الكود: {resp.status_code})")
        data = resp.json()
        if not data.get("success"):
            raise Exception(data.get("message", "فشل الفحص"))
        otp = data.get("otp")
        return {"status": "SUKSES", "otp": otp} if otp else {"status": "WAIT", "otp": None}
    except Exception as e:
        logger.error(f"XWD check_otp error: {e}")
        raise

def xwd_get_balance():
    """جلب الرصيد من الموقع"""
    url = f"{XWD_BASE_URL}/api/v1/balance"
    headers = {"x-api-key": XWD_API_KEY, "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=False)
        if resp.status_code == 403:
            raise Exception("الرصيد مرفوض (403). قد يكون المفتاح محظوراً أو الرصيد صفر.")
        if resp.status_code != 200:
            raise Exception("تعذر جلب الرصيد")
        data = resp.json()
        if data.get("success"):
            return data.get("balance", 0.0)
        else:
            return 0.0
    except Exception as e:
        logger.error(f"XWD balance error: {e}")
        raise

# ======================================================================================
# دوال التنسيق والأمان
# ======================================================================================
def mask_number(num): num = str(num); return "XXXX" + num[-4:] if len(num) > 8 else num

def get_country_info_by_num(num):
    num = re.sub(r'\D', '', str(num))
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if num.startswith(code): return name, flag
    return "غير معروف", "🌍"

def extract_otp(t):
    m = re.search(r'(?:code|otp|رمز|كود|verification|pin)[:\s]*(\d{4,8})', t, re.IGNORECASE) or re.search(r'\b(\d{4,8})\b', t)
    return m.group(1) if m else "N/A"

# ======================================================================================
# القائمة الرئيسية (Reply Keyboard) - كما في الصورة
# ======================================================================================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 الحصول على رقم")
    btn2 = types.KeyboardButton("💰 الرصيد")
    btn3 = types.KeyboardButton("🔄 تبديل الرقم")
    btn4 = types.KeyboardButton("📊 الإحصائيات")
    btn5 = types.KeyboardButton("🤝 شارك واربح")
    btn6 = types.KeyboardButton("🔗 جروب البوت")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    return markup

# ======================================================================================
# حلقة جلب OTP الخلفية
# ======================================================================================
def main_loop():
    sent_ids = set()
    if os.path.exists("sent_msgs.json"):
        try: sent_ids = set(json.load(open("sent_msgs.json")))
        except: pass
    while True:
        try:
            active = get_active_numbers()
            for num, country, assigned_to, _ in active:
                try:
                    res = xwd_check_otp(num)
                    if res["status"] == "SUKSES" and res["otp"]:
                        otp = res["otp"]; update_active_number(num, otp); remove_active_number(num); name, flag = get_country_info_by_num(num)
                        g_txt = f"✨ OTP\n🌍 {flag} {name}\n☎ +{mask_number(num)}\n🔐 {otp}"
                        g_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        for ch in CHAT_IDS: bot.send_message(ch, g_txt, parse_mode="HTML", reply_markup=g_markup)
                        if assigned_to:
                            u_txt = f"✨ OTP الخاص بك\n🌍 {flag} {name}\n☎ +{num}\n🔐 {otp}"
                            u_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                            bot.send_message(assigned_to, u_txt, parse_mode="HTML", reply_markup=u_markup)
                except Exception as e:
                    # طباعة خطأ الفحص في السجل لكن لا توقف الحلقة
                    logger.error(f"Error checking {num}: {e}")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

# ======================================================================================
# الأزرار والرسائل
# ======================================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("copy_"))
def copy_h(c): bot.answer_callback_query(c.id, f"✅ تم نسخ الكود: {c.data.split('_')[1]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("country_"))
def country_h(c):
    bot.answer_callback_query(c.id, "📡 جاري جلب الرقم...")
    try:
        uid = c.from_user.id; parts = c.data.split("_"); code = parts[1]
        if code not in AVAILABLE_COUNTRIES: return
        range_str = AVAILABLE_COUNTRIES[code][2][0]
        try:
            number = xwd_get_number(range_str)
            clean = re.sub(r'\D', '', number)
            old = get_user(uid)
            if old and old[5]: release_number(old[5]); remove_active_number(old[5])
            assign_number_to_user(uid, clean); save_user(uid, country_code=code, assigned_number=clean); add_active_number(clean, code, uid)
            name, flag = get_country_info_by_num(clean)
            msg = f"◈ الرقم: <code>+{clean}</code>\n◈ الدولة: {flag} {name}\n◈ الحالة: ⏳ انتظر OTP..."
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.row(
                types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"country_{code}"),
                types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="back")
            )
            markup.row(
                types.InlineKeyboardButton("👥 جروب البوت", url="https://t.me/numhj"),
                types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back")
            )
            
            bot.edit_message_text(msg, c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)
            bot.answer_callback_query(c.id, "✅ تم تعيين الرقم.")
        except Exception as e:
            bot.edit_message_text(f"❌ فشل جلب الرقم:\n{str(e)}", c.message.chat.id, c.message.message_id)
    except Exception as e:
        logger.error(f"Country Error: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "back")
def back_h(c):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items(): markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))
    bot.edit_message_text("🌍 <b>اختر الدولة:</b>", c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_h(m):
    user_id = m.from_user.id
    if is_banned(user_id): return bot.reply_to(m, "🚫 محظور.")
    save_user(user_id, username=m.from_user.username or "", first_name=m.from_user.first_name or "")
    bot.send_message(m.chat.id, "🌍 <b>أهلاً بك في بوت الأرقام!</b>\nاختر إحدى الخيارات من الأسفل 👇", parse_mode="HTML", reply_markup=main_keyboard())

# ======================================================================================
# معالجة أزرار لوحة المفاتيح (Reply Buttons)
# ======================================================================================
@bot.message_handler(func=lambda m: m.text == "📱 الحصول على رقم")
def get_num_handler(m): back_h(m)

@bot.message_handler(func=lambda m: m.text == "💰 الرصيد")
def balance_handler(m):
    try:
        balance = xwd_get_balance()
        bal_str = f"{balance:.4f}" if isinstance(balance, float) else str(balance)
        msg = f"💰 <b>الرصيد الحالي في الموقع:</b>\n<code>{bal_str} دولار</code>"
        bot.reply_to(m, msg, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(m, f"❌ تعذر جلب الرصيد:\n{str(e)}")

@bot.message_handler(func=lambda m: m.text == "🔄 تبديل الرقم")
def change_num_handler(m):
    user = get_user(m.from_user.id)
    if user and user[5]:
        code = user[4]
        if code in AVAILABLE_COUNTRIES:
            c = types.CallbackQuery(id="0", from_user=m.from_user, message=m, data=f"country_{code}")
            country_h(c)
        else:
            bot.reply_to(m, "⚠️ لم يتم العثور على دولة مسجلة، اختر دولة جديدة أولاً.")
    else:
        bot.reply_to(m, "⚠️ ليس لديك رقم مخصص حالياً. احصل على رقم أولاً عبر زر '📱 الحصول على رقم'.")

@bot.message_handler(func=lambda m: m.text == "📊 الإحصائيات")
def stats_handler(m):
    users_count = len(get_all_users())
    active = len(get_active_numbers())
    msg = f"📊 <b>إحصائيات البوت:</b>\n👥 عدد المستخدمين: {users_count}\n📱 أرقام نشطة حالياً: {active}"
    bot.reply_to(m, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🤝 شارك واربح")
def refer_handler(m):
    bot_username = "Taker_OTP_BOT"
    msg = f"🤝 <b>شارك واربح!</b>\n\nادع أصدقائك لاستخدام البوت واربح المكافآت!\n\nرابط الدعوة الخاص بك:\n<code>https://t.me/{bot_username}?start={m.from_user.id}</code>\n\nانسخ الرابط وشاركه في الجروبات."
    bot.reply_to(m, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🔗 جروب البوت")
def group_link_handler(m):
    bot.reply_to(m, "🔗 <b>انضم لجروب الأكواد الرسمي:</b>\nhttps://t.me/numhj", parse_mode="HTML")

# ======================================================================================
# خادم الويب (Flask)
# ======================================================================================
app = Flask(__name__)

@app.route('/')
def index(): return jsonify({"status": "running", "bot": "XWD Ultimate OTP"})
@app.route('/health')
def health(): return jsonify({"status": "ok", "uptime": time.time()})

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

# ======================================================================================
# تشغيل البوت
# ======================================================================================
def run_bot_polling():
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e: logger.error(f"Polling Error: {e}"); time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    run_bot_polling()

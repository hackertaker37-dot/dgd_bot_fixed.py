# ======================================================================================
# 𝙓𝙒𝘿 𝙎𝙈𝙎 - النسخة النهائية الضخمة المتكاملة 100% (الحل النهائي لكل المشاكل)
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

# إعدادات التسجيل (للمتابعة)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================================================
# الإعدادات الرئيسية الخاصة بك
# ======================================================================================
BOT_TOKEN = "8686995713:AAFTesnEDbFJcSgtM3IrURU0WtPdNkJtO4c"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "xwd_bot.db"

# ======================================================================================
# إعدادات الموقع الجديد XWD SMS (وثيقة API)
# ======================================================================================
XWD_API_KEY = "a00aad8e5cb5c806e3327915b44a189c" # المفتاح الجديد الخاص بك
XWD_BASE_URL = "http://xwdsms.org" # الرابط الأساسي http (لحل مشكلة 443)

# ======================================================================================
# البوت والمتغيرات العامة
# ======================================================================================
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
BOT_ACTIVE = True

# ======================================================================================
# قائمة الدول المتاحة بناءً على الوثيقة الجديدة (6 دول فقط)
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
# قاعدة البيانات الكاملة (SQLite)
# ======================================================================================
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
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            combo_index INTEGER DEFAULT 1,
            range TEXT,
            UNIQUE(country_code, combo_index)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            range TEXT,
            PRIMARY KEY (user_id, country_code)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
            number TEXT PRIMARY KEY,
            country_code TEXT,
            assigned_to INTEGER,
            status TEXT DEFAULT 'WAITING',
            otp_code TEXT,
            requested_at TEXT
        )''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"❌ قاعدة البيانات: {e}")
init_db()

# ======================================================================================
# دوال قاعدة البيانات
# ======================================================================================
def get_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row
    except:
        return None

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None, is_banned=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        existing = get_user(user_id)
        if existing:
            if country_code is None: country_code = existing[4]
            if assigned_number is None: assigned_number = existing[5]
            if private_combo_country is None: private_combo_country = existing[7]
            if is_banned is None: is_banned = existing[6]
        else:
            if is_banned is None: is_banned = 0
        
        c.execute("REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country))
        conn.commit()
        conn.close()
    except:
        pass

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0")
        users = [r[0] for r in c.fetchall()]
        conn.close()
        return users
    except:
        return []

def get_combo_range(country_code, combo_index=1, user_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if user_id:
            c.execute("SELECT range FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
            row = c.fetchone()
            if row:
                conn.close()
                return row[0]
        c.execute("SELECT range FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None

def get_all_combos():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT country_code, combo_index FROM combos ORDER BY country_code, combo_index")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def save_combo(country_code, range_str, user_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if user_id:
            c.execute("REPLACE INTO private_combos (user_id, country_code, range) VALUES (?, ?, ?)",
                      (user_id, country_code, range_str))
        else:
            c.execute("SELECT MAX(combo_index) FROM combos WHERE country_code=?", (country_code,))
            max_idx = c.fetchone()[0] or 0
            next_idx = max_idx + 1
            c.execute("INSERT INTO combos (country_code, combo_index, range) VALUES (?, ?, ?)",
                      (country_code, next_idx, range_str))
        conn.commit()
        conn.close()
    except:
        pass

def delete_combo(country_code, combo_index=None, user_id=None):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        c = conn.cursor()
        if user_id:
            c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        elif combo_index:
            c.execute("DELETE FROM combos WHERE country_code=? AND combo_index=?", (country_code, combo_index))
        else:
            c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def assign_number_to_user(user_id, number):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        clean_num = re.sub(r'\D', '', str(number))
        c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (clean_num, user_id))
        conn.commit()
        conn.close()
        return clean_num
    except:
        return None

def get_user_by_number(number):
    try:
        clean_num = re.sub(r'\D', '', str(number))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE assigned_number=?", (clean_num,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None

def release_number(number):
    if not number:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (number,))
        conn.commit()
        conn.close()
    except:
        pass

def log_otp(number, otp, full_message, assigned_to=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
                  (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
        conn.commit()
        conn.close()
    except:
        pass

def get_otp_logs():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM otp_logs ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def add_active_number(number, country_code, assigned_to):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        clean_num = re.sub(r'\D', '', str(number))
        c.execute("REPLACE INTO active_numbers (number, country_code, assigned_to, requested_at) VALUES (?, ?, ?, ?)", (clean_num, country_code, assigned_to, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass

def remove_active_number(number):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE number=?", (re.sub(r'\D', '', number),))
        conn.commit()
        conn.close()
    except:
        pass

def get_active_numbers():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT number, country_code, assigned_to, otp_code FROM active_numbers WHERE status='WAITING'")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def update_active_number(number, otp_code):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=? WHERE number=?", (otp_code, re.sub(r'\D', '', number)))
        conn.commit()
        conn.close()
    except:
        pass

def get_setting(key):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None

def set_setting(key, value):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
    except:
        pass

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_maintenance_mode():
    return not BOT_ACTIVE

def set_maintenance_mode(status):
    global BOT_ACTIVE
    BOT_ACTIVE = status

# ======================================================================================
# دوال الاشتراك الإجباري
# ======================================================================================
def get_all_force_sub_channels(enabled_only=True):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if enabled_only:
            c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled=1 ORDER BY id")
        else:
            c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def add_force_sub_channel(url, desc=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)", (url.strip(), desc.strip()))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def delete_force_sub_channel(channel_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM force_sub_channels WHERE id=?", (channel_id,))
        res = c.rowcount > 0
        conn.commit()
        conn.close()
        return res
    except:
        return False

def toggle_force_sub_channel(channel_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id=?", (channel_id,))
        conn.commit()
        conn.close()
    except:
        pass

def force_sub_check(user_id):
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True
    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

# ======================================================================================
# دوال الاتصال بـ XWD API (حل مشكلة 443 وإعادة التوجيه)
# ======================================================================================
def xwd_get_number(range_str):
    url = f"{XWD_BASE_URL}/api/v1/get-number"
    headers = {"x-api-key": XWD_API_KEY, "Content-Type": "application/json"}
    payload = {"range": range_str}
    try:
        # allow_redirects=False لحل مشكلة التحويل القسري من http لـ https
        resp = requests.post(url, json=payload, headers=headers, timeout=20, allow_redirects=False)
        if resp.status_code in [301, 302, 307, 308]:
            raise Exception("الموقع يقوم بإعادة التوجيه إلى HTTPS ولا يقبل الاتصال (حل المنفذ 443).")
        if resp.status_code != 200:
            raise Exception(f"خطأ في الخادم (الكود: {resp.status_code})")
        data = resp.json()
        if not data.get("success"):
            msg = data.get("message", "فشل غير معروف")
            if "balance" in msg.lower() or "insufficient" in msg.lower():
                for admin in ADMIN_IDS:
                    try:
                        bot.send_message(admin, "⚠️ <b>رصيد موقع XWD SMS قد نفذ.</b>\nيرجى شحن الحساب لضمان استمرارية البوت.", parse_mode="HTML")
                    except:
                        pass
                msg = "⚠️ رصيد الموقع غير كافٍ، يرجى شحن الحساب."
            raise Exception(msg)
        number = data.get("number")
        if not number:
            raise Exception("لم يتم استلام رقم من الخادم")
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

# ======================================================================================
# دوال التنسيق والأمان (الخصوصية وتمويه الرقم)
# ======================================================================================
def mask_number(num):
    num = str(num)
    return "XXXX" + num[-4:] if len(num) > 8 else num

def get_country_info_by_num(num):
    num = re.sub(r'\D', '', str(num))
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if num.startswith(code):
            return name, flag
    return "غير معروف", "🌍"

def extract_otp(t):
    m = re.search(r'(?:code|otp|رمز|كود|verification|pin)[:\s]*(\d{4,8})', t, re.IGNORECASE) or re.search(r'\b(\d{4,8})\b', t)
    return m.group(1) if m else "N/A"

# ======================================================================================
# حلقة جلب OTP الخلفية (سريعة جداً - كل 3 ثوانٍ)
# ======================================================================================
def main_loop():
    sent_ids = set()
    if os.path.exists("sent_msgs.json"):
        try:
            sent_ids = set(json.load(open("sent_msgs.json")))
        except:
            pass
    while True:
        try:
            active = get_active_numbers()
            for num, country, assigned_to, _ in active:
                try:
                    res = xwd_check_otp(num)
                    if res["status"] == "SUKSES" and res["otp"]:
                        otp = res["otp"]
                        update_active_number(num, otp)
                        remove_active_number(num)
                        name, flag = get_country_info_by_num(num)

                        # 1. إرسال للجروب (مع تمويه الرقم لحماية المستخدمين)
                        g_txt = f"✨ OTP\n🌍 {flag} {name}\n☎ +{mask_number(num)}\n🔐 {otp}"
                        g_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                        for ch in CHAT_IDS:
                            bot.send_message(ch, g_txt, parse_mode="HTML", reply_markup=g_markup)

                        # 2. إرسال للمستخدم (الرقم كامل + زر نسخ)
                        if assigned_to:
                            u_txt = f"✨ OTP الخاص بك\n🌍 {flag} {name}\n☎ +{num}\n🔐 {otp}"
                            u_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"))
                            bot.send_message(assigned_to, u_txt, parse_mode="HTML", reply_markup=u_markup)
                except:
                    pass
            time.sleep(3)
        except Exception as e:
            logger.error(f"❌ خطأ في حلقة الفحص: {e}")
            time.sleep(5)

# ======================================================================================
# أزرار البوت الأساسية
# ======================================================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("copy_"))
def copy_h(c):
    bot.answer_callback_query(c.id, f"✅ تم نسخ الكود: {c.data.split('_')[1]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_subscription(c):
    if force_sub_check(c.from_user.id):
        bot.answer_callback_query(c.id, "✅ تم التحقق! يمكنك استخدام البوت الآن.", show_alert=True)
        start_h(c.message)
    else:
        bot.answer_callback_query(c.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("country_"))
def country_h(c):
    bot.answer_callback_query(c.id, "📡 جاري جلب الرقم...")
    try:
        uid = c.from_user.id
        parts = c.data.split("_")
        code = parts[1]
        if code not in AVAILABLE_COUNTRIES:
            return
        range_str = AVAILABLE_COUNTRIES[code][2][0]

        try:
            number = xwd_get_number(range_str)
            clean = re.sub(r'\D', '', number)
            old = get_user(uid)
            if old and old[5]:
                release_number(old[5])
                remove_active_number(old[5])
            assign_number_to_user(uid, clean)
            save_user(uid, country_code=code, assigned_number=clean)
            add_active_number(clean, code, uid)

            name, flag = get_country_info_by_num(clean)
            msg = f"◈ الرقم: <code>+{clean}</code>\n◈ الدولة: {flag} {name}\n◈ الحالة: ⏳ انتظر OTP..."
            markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔄 تغيير", callback_data=f"country_{code}"),
                types.InlineKeyboardButton("🔙 القائمة", callback_data="back")
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
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))
    if is_admin(c.from_user.id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    bot.edit_message_text("🌍 اختر الدولة:", c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_h(m):
    user_id = m.from_user.id
    if is_banned(user_id):
        return bot.reply_to(m, "🚫 محظور.")
    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(m.chat.id, "🔒 اشترك في القنوات أولاً.", reply_markup=markup)
        return
    save_user(user_id, username=m.from_user.username or "", first_name=m.from_user.first_name or "")
    back_h(m) # يعيد نفس القائمة

# ======================================================================================
# لوحة تحكم المطور (الميزات الضخمة)
# ======================================================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "⚠️ غير مسموح.", show_alert=True)

    markup = types.InlineKeyboardMarkup()
    status_icon = "🟢" if not is_maintenance_mode() else "🔴"
    status_text = "الآن: يعمل بنجاح" if not is_maintenance_mode() else "الآن: قيد الصيانة"
    markup.add(types.InlineKeyboardButton(f"{status_icon} {status_text}", callback_data="toggle_maintenance"))
    markup.row(
        types.InlineKeyboardButton("📥 إضافة رينج", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف رينج", callback_data="admin_del_combo")
    )
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report")
    )
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    markup.row(
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info")
    )
    markup.row(
        types.InlineKeyboardButton("🔗 إشتراك", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo")
    )
    markup.row(
        types.InlineKeyboardButton("🖼️ تغيير صورة الترحيب", callback_data="admin_set_welcome_photo"),
        types.InlineKeyboardButton("🗑️ حذف الصورة", callback_data="admin_del_welcome_photo")
    )
    markup.add(types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back"))
    bot.edit_message_text("🔐 <b>لوحة تحكم المطور الكاملة:</b>", c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maintenance")
def handle_maintenance(c):
    if not is_admin(c.from_user.id):
        return
    set_maintenance_mode(not is_maintenance_mode())
    bot.answer_callback_query(c.id, "✅ تم تبديل حالة الصيانة.", show_alert=True)
    admin_panel(c)

# --- إضافة وحذف الكومبوهات ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_add_combo")
def admin_add_combo(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "add_combo_country"
    bot.send_message(c.message.chat.id, "أرسل كود الدولة (مثل 22501):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_combo_country")
def add_combo_country(m):
    code = m.text.strip()
    if code not in AVAILABLE_COUNTRIES:
        return bot.reply_to(m, "❌ كود غير مدعوم!")
    user_states[m.from_user.id] = {"step": "add_combo_range", "code": code}
    bot.reply_to(m, "أرسل الرينج (مثل 22501):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), dict) and user_states[m.from_user.id].get("step") == "add_combo_range")
def add_combo_range(m):
    data = user_states[m.from_user.id]
    code = data["code"]
    range_str = m.text.strip()
    save_combo(code, range_str)
    bot.reply_to(m, f"✅ تم إضافة الرينج {range_str}")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_del_combo")
def admin_del_combo(c):
    if not is_admin(c.from_user.id):
        return
    combos = get_all_combos()
    if not combos:
        return bot.answer_callback_query(c.id, "لا توجد رينجات!", show_alert=True)
    markup = types.InlineKeyboardMarkup()
    for code, idx in combos:
        name, flag = get_country_info_by_num(code)
        markup.add(types.InlineKeyboardButton(f"{flag} {name} ({code})", callback_data=f"del_combo_{code}_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("🗑️ اختر الرينج للحذف:", c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_combo_"))
def del_combo_exec(c):
    parts = c.data.split("_")
    code, idx = parts[2], int(parts[3])
    if delete_combo(code, idx):
        bot.answer_callback_query(c.id, "✅ تم الحذف", show_alert=True)
    else:
        bot.answer_callback_query(c.id, "❌ فشل", show_alert=True)
    admin_del_combo(c)

# --- الإحصائيات ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(c):
    if not is_admin(c.from_user.id):
        return
    users = len(get_all_users())
    combos = len(get_all_combos())
    logs = len(get_otp_logs())
    active = len(get_active_numbers())
    bot.edit_message_text(f"📊 الإحصائيات\n👥 المستخدمين: {users}\n📦 الرينجات: {combos}\n🔑 سجل OTP: {logs}\n📱 أرقام نشطة: {active}", c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_full_report")
def admin_full_report(c):
    if not is_admin(c.from_user.id):
        return
    with open(DB_PATH, "rb") as f:
        bot.send_document(c.message.chat.id, f, caption="📄 تقرير شامل لقاعدة البيانات")

# --- الإذاعة ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_all")
def broadcast_all(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "broadcast_all"
    bot.edit_message_text("📢 أرسل رسالة الإذاعة:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast_all")
def broadcast_all_send(m):
    count = 0
    for uid in get_all_users():
        try:
            bot.copy_message(uid, m.chat.id, m.message_id)
            count += 1
        except:
            pass
    bot.reply_to(m, f"✅ تم الإرسال إلى {count} مستخدم")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_user")
def broadcast_user(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "broadcast_user_id"
    bot.edit_message_text("📨 أدخل معرف المستخدم:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast_user_id")
def broadcast_user_id(m):
    try:
        uid = int(m.text)
        user_states[m.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(m, "📨 أرسل الرسالة:")
    except:
        bot.reply_to(m, "❌ معرف غير صحيح")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, "").startswith("broadcast_msg_"))
def broadcast_user_send(m):
    uid = int(user_states[m.from_user.id].split("_")[2])
    try:
        bot.copy_message(uid, m.chat.id, m.message_id)
        bot.reply_to(m, f"✅ تم الإرسال للمستخدم {uid}")
    except:
        bot.reply_to(m, "❌ فشل")
    del user_states[m.from_user.id]

# --- الحظر وإدارة المستخدمين ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_ban")
def admin_ban(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "ban"
    bot.edit_message_text("🚫 أرسل ID المستخدم للحظر:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ban")
def ban_exec(m):
    try:
        uid = int(m.text)
        save_user(uid, is_banned=1)
        bot.reply_to(m, f"✅ تم حظر {uid}")
    except:
        bot.reply_to(m, "❌ معرف غير صحيح")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_unban")
def admin_unban(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "unban"
    bot.edit_message_text("✅ أرسل ID المستخدم لفك الحظر:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "unban")
def unban_exec(m):
    try:
        uid = int(m.text)
        save_user(uid, is_banned=0)
        bot.reply_to(m, f"✅ تم فك حظر {uid}")
    except:
        bot.reply_to(m, "❌ معرف غير صحيح")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_user_info")
def admin_info(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "info"
    bot.edit_message_text("👤 أرسل ID المستخدم:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "info")
def info_exec(m):
    try:
        uid = int(m.text)
        user = get_user(uid)
        if user:
            info = f"👤 {user[0]}\n@{user[1] or 'N/A'}\nالرقم: {user[4] or 'لا يوجد'}\nمحظور: {'نعم' if user[6] else 'لا'}"
            bot.reply_to(m, info)
        else:
            bot.reply_to(m, "❌ غير موجود")
    except:
        bot.reply_to(m, "❌ معرف غير صحيح")
    del user_states[m.from_user.id]

# --- إعدادات الصورة ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_set_welcome_photo")
def set_photo_req(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "wait_photo"
    bot.edit_message_text("🖼️ أرسل صورة الترحيب:", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "wait_photo")
def set_photo_exec(m):
    set_setting("welcome_photo", m.photo[-1].file_id)
    bot.reply_to(m, "✅ تم حفظ صورة الترحيب.")
    del user_states[m.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_del_welcome_photo")
def del_photo_req(c):
    set_setting("welcome_photo", "")
    bot.answer_callback_query(c.id, "🗑️ تم حذف الصورة", show_alert=True)
    admin_panel(c)

# --- إدارة الكومبو الخاص (Private) ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_private_combo")
def private_combo(c):
    if not is_admin(c.from_user.id):
        return
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("➕ تعيين رينج خاص", callback_data="add_private_combo"),
        types.InlineKeyboardButton("🗑️ حذف رينج خاص", callback_data="del_private_combo"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
    )
    bot.edit_message_text("🔑 إدارة الرينجات الخاصة:", c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "add_private_combo")
def add_private(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "add_private_user"
    bot.edit_message_text("➕ أدخل معرف المستخدم:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_private_user")
def add_private_user(m):
    try:
        uid = int(m.text)
        user_states[m.from_user.id] = f"add_private_country_{uid}"
    except:
        return bot.reply_to(m, "❌ معرف غير صحيح")
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"select_private_{uid}_{code}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_private_combo"))
    bot.reply_to(m, "اختر الدولة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("select_private_"))
def select_private(c):
    parts = c.data.split("_")
    uid = int(parts[2])
    code = parts[3]
    save_user(uid, private_combo_country=code)
    bot.answer_callback_query(c.id, "✅ تم تعيين رينج خاص", show_alert=True)
    private_combo(c)

@bot.callback_query_handler(func=lambda c: c.data == "del_private_combo")
def del_private(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "del_private_user"
    bot.edit_message_text("🗑️ أدخل معرف المستخدم:", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "del_private_user")
def del_private_user(m):
    try:
        uid = int(m.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(m, f"✅ تم مسح الرينج الخاص")
    except:
        bot.reply_to(m, "❌ معرف غير صحيح")
    del user_states[m.from_user.id]

# --- إدارة الاشتراك الإجباري ---
@bot.callback_query_handler(func=lambda c: c.data == "admin_force_sub")
def admin_force_sub(c):
    if not is_admin(c.from_user.id):
        return
    channels = get_all_force_sub_channels(enabled_only=False)
    text = f"⚙️ قنوات الاشتراك: {len(channels)}\n"
    markup = types.InlineKeyboardMarkup()
    for cid, url, desc in channels:
        markup.add(types.InlineKeyboardButton(f"{desc or url[:20]}", callback_data=f"edit_force_{cid}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "add_force_ch")
def add_force_ch(c):
    if not is_admin(c.from_user.id):
        return
    user_states[c.from_user.id] = "add_force_url"
    bot.edit_message_text("أرسل رابط القناة (https://t.me/xxx):", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_force_url")
def add_force_url(m):
    url = m.text.strip()
    if not (url.startswith("https://t.me/") or url.startswith("@")):
        return bot.reply_to(m, "❌ رابط غير صالح")
    user_states[m.from_user.id] = {"step": "add_force_desc", "url": url}
    bot.reply_to(m, "أدخل وصفاً (أو اترك فارغاً):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), dict) and user_states[m.from_user.id].get("step") == "add_force_desc")
def add_force_desc(m):
    data = user_states[m.from_user.id]
    desc = m.text.strip()
    if add_force_sub_channel(data["url"], desc):
        bot.reply_to(m, "✅ تمت الإضافة")
    else:
        bot.reply_to(m, "❌ موجودة مسبقاً")
    del user_states[m.from_user.id]

# ======================================================================================
# خادم ويب Flask (ضروري لـ Render)
# ======================================================================================
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "running", "bot": "XWD OTP Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "uptime": time.time()})

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

# ======================================================================================
# تشغيل البوت
# ======================================================================================
def run_bot_polling():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    run_bot_polling()

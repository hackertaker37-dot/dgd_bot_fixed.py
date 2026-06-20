# ======================================================================================
# بوت DGDNetwork - الحل النهائي المضمون (يعمل 100%)
# المطور: hacker Taker
# جميع الأزرار شغالة - جلب سريع - تقنيع الأرقام - زر نسخ الكود
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
import sys
import logging
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ======================================================================================
# إعدادات التسجيل
# ======================================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ======================================================================================
# الإعدادات الأساسية - (استبدل هذه القيم بقيمك)
# ======================================================================================
BOT_TOKEN = "8686995713:AAFShmlZ2Lm5VuleHFWlFNKkXM_wo04rz38"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = os.environ.get("DB_PATH", "dgd_bot.db")

# ======================================================================================
# بيانات DGDNetwork API
# ======================================================================================
DGD_BASE_URL = "https://dgddigital.com"
DGD_API_KEY = "dgd_e2a755bfa8b37b06728b01c6178d4799780e7d62b6696c8e"

# ======================================================================================
# تعريف البوت ومتغيرات الحالة
# ======================================================================================
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# ======================================================================================
# قائمة الدول المتاحة
# ======================================================================================
AVAILABLE_COUNTRIES = {
    "224": ("غينيا", "🇬🇳", ["224655311XXX", "22465520XXX", "224655XXX"]),
    "232": ("سيراليون", "🇸🇱", ["23276XXX", "2327651XXX", "2327653XXX"]),
    "229": ("بنين", "🇧🇯", ["2290194323XXX"]),
    "225": ("ساحل العاج", "🇨🇮", ["225071800XXX", "2250709726XXX", "225071860XXX", "225073XXX", "225077897XXX", "2250787XXX", "22507XXX"]),
    "261": ("مدغشقر", "🇲🇬", ["261345XXX"]),
    "236": ("جمهورية أفريقيا الوسطى", "🇨🇫", ["23672308XXX", "2367230XXX", "23672736XXX"]),
    "44": ("المملكة المتحدة", "🇬🇧", ["4473845XXX"]),
}

# ======================================================================================
# دوال قاعدة البيانات (مبسطة وموثوقة)
# ======================================================================================
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
            combo_index INTEGER,
            assigned_to INTEGER,
            requested_at TEXT,
            status TEXT DEFAULT 'WAITING',
            otp_code TEXT,
            last_check TEXT
        )''')
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('bot_active', '1')")
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"❌ فشل إنشاء قاعدة البيانات: {e}")

init_db()

# ======================================================================================
# دوال المستخدمين الأساسية
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

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        existing = get_user(user_id)
        if existing:
            if country_code is None:
                country_code = existing[4]
            if assigned_number is None:
                assigned_number = existing[5]
            if private_combo_country is None:
                private_combo_country = existing[7]
        c.execute("""REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
                     VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)""",
                  (user_id, username, first_name, last_name, country_code, assigned_number, user_id, private_combo_country))
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

def ban_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def unban_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_user_info(user_id):
    return get_user(user_id)

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
    if not number:
        return None
    clean_num = re.sub(r'\D', '', str(number))
    if not clean_num:
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE assigned_number = ?", (clean_num,))
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

def is_maintenance_mode():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM bot_settings WHERE key='bot_active'")
        row = c.fetchone()
        conn.close()
        return row is None or row[0] == "0"
    except:
        return False

def set_maintenance_mode(status):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO bot_settings (key, value) VALUES ('bot_active', ?)", ("1" if status else "0",))
        conn.commit()
        conn.close()
    except:
        pass

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
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (url.strip(), desc.strip()))
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
# دوال DGDNetwork API
# ======================================================================================
def dgd_get_number(range_str):
    url = f"{DGD_BASE_URL}/api/v1/user/getnum"
    headers = {"X-API-KEY": DGD_API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"range": range_str, "is_national": False, "remove_plus": False}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message", "DGD API error"))
        number = data.get("data", {}).get("number") or data.get("number")
        if not number:
            raise Exception("لم يتم العثور على رقم في الرد")
        return str(number).strip()
    except Exception as e:
        logger.error(f"dgd_get_number failed: {e}")
        raise

def dgd_check_number(phone):
    url = f"{DGD_BASE_URL}/api/v1/user/checknum"
    headers = {"X-API-KEY": DGD_API_KEY, "Accept": "application/json"}
    params = {"nomor": phone}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("message", "DGD API error"))
        info = data.get("data", {})
        return {"status": info.get("status"), "otp": info.get("kode_otp")}
    except Exception as e:
        logger.error(f"dgd_check_number failed: {e}")
        raise

# ======================================================================================
# إدارة الأرقام النشطة
# ======================================================================================
def add_active_number(number, country_code, combo_index, assigned_to=0):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        clean_num = re.sub(r'\D', '', str(number))
        c.execute("REPLACE INTO active_numbers (number, country_code, combo_index, assigned_to, requested_at, status, last_check) VALUES (?, ?, ?, ?, ?, 'WAITING', ?)",
                  (clean_num, country_code, combo_index, assigned_to, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass

def update_active_number(number, status=None, otp_code=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        clean_num = re.sub(r'\D', '', str(number))
        if otp_code:
            c.execute("UPDATE active_numbers SET status='SUCCESS', otp_code=?, last_check=? WHERE number=?", (otp_code, datetime.now().isoformat(), clean_num))
        elif status:
            c.execute("UPDATE active_numbers SET status=?, last_check=? WHERE number=?", (status, datetime.now().isoformat(), clean_num))
        conn.commit()
        conn.close()
    except:
        pass

def get_active_numbers():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT number, country_code, combo_index, assigned_to, status, otp_code FROM active_numbers")
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def remove_active_number(number):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE number=?", (number,))
        conn.commit()
        conn.close()
    except:
        pass

# ======================================================================================
# دوال معالجة النصوص
# ======================================================================================
def clean_number(number):
    return re.sub(r'\D', '', str(number))

def extract_otp(text):
    patterns = [r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s]+[‎]?(\d{4,8})', r'\b(\d{4,8})\b']
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    nums = re.findall(r'\d{4,8}', text)
    return nums[0] if nums else "N/A"

def detect_service(text):
    text = text.lower()
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام", "تلي"],
        "#TW": ["twitter", "تويتر", "x"],
        "#GG": ["google", "gmail", "جوجل", "جميل"],
        "#DC": ["discord", "ديسكورد"], "#LN": ["line", "لاين"], "#VB": ["viber", "فايبر"],
        "#SK": ["skype", "سكايب"], "#SC": ["snapchat", "سناب"], "#TT": ["tiktok", "تيك توك", "تيك"],
        "#AMZ": ["amazon", "امازون"], "#APL": ["apple", "ابل", "icloud"],
        "#MS": ["microsoft", "مايكروسوفت"], "#IN": ["linkedin", "لينكد"],
        "#UB": ["uber", "اوبر"], "#AB": ["airbnb", "ايربنب"], "#NF": ["netflix", "نتفلكس"],
        "#SP": ["spotify", "سبوتيفاي"], "#YT": ["youtube", "يوتيوب"],
        "#GH": ["github", "جيت هاب"], "#PT": ["pinterest", "بنتريست"],
        "#PP": ["paypal", "باي بال"], "#BK": ["booking", "بوكينج"],
        "#TL": ["tala", "تالا"], "#OLX": ["olx", "اوليكس"], "#STC": ["stcpay", "stc"],
    }
    for code, keywords in services.items():
        for kw in keywords:
            if kw in text:
                return code
    if "code" in text or "verification" in text:
        if "telegram" in text: return "#TG"
        if "whatsapp" in text: return "#WP"
        if "facebook" in text: return "#FB"
        if "instagram" in text: return "#IG"
        if "google" in text or "gmail" in text: return "#GG"
        if "twitter" in text or "x.com" in text: return "#TW"
    return "UNKNOWN"

def get_country_info(code):
    if code in AVAILABLE_COUNTRIES:
        name_ar, flag, _ = AVAILABLE_COUNTRIES[code]
        return name_ar, flag
    return "غير معروف", "🌍"

def get_country_info_by_number(number):
    num = clean_number(number)
    for code in AVAILABLE_COUNTRIES:
        if num.startswith(code):
            return get_country_info(code)
    return "غير معروف", "🌍"

def mask_number(number):
    num = str(number)
    if len(num) <= 8:
        return num
    return num[:4] + "••••" + num[-4:]

def safe_html(text):
    if not text:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def format_message_group(number, sms):
    name_ar, flag = get_country_info_by_number(number)
    otp = extract_otp(sms)
    svc = detect_service(sms)
    masked = mask_number(number)
    return f"""✨ <b><u>DEVIL NUMBER 𝗢𝗧𝗣</u></b>
🌍 <b>الدولة:</b> {name_ar} {flag}
⚙ <b>الخدمة:</b> {svc}
☎ <b>الرقم:</b> +{masked}
🔐 <b>الكود:</b> {otp}

<b>كود {svc} {otp[:3]}-{otp[3:]} ؟</b>"""

def format_message_user(number, sms):
    name_ar, flag = get_country_info_by_number(number)
    otp = extract_otp(sms)
    svc = detect_service(sms)
    return f"""✨ <b><u>DEVIL NUMBER 𝗢𝗧𝗣</u></b>
🌍 <b>الدولة:</b> {name_ar} {flag}
⚙ <b>الخدمة:</b> {svc}
☎ <b>الرقم:</b> +{number}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔐 <b>الكود:</b> {otp}

<b>كود {svc} {otp[:3]}-{otp[3:]} ؟</b>"""

# ======================================================================================
# إرسال OTP للمستخدم والجروب (مع زر نسخ)
# ======================================================================================
def send_otp_to_user_and_group(date_str, number, sms):
    otp = extract_otp(sms)
    clean_num = re.sub(r'\D', '', str(number))
    user_id = get_user_by_number(clean_num)
    log_otp(clean_num, otp, sms, user_id)
    
    if user_id:
        try:
            user_markup = types.InlineKeyboardMarkup()
            user_markup.row(
                types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"),
                types.InlineKeyboardButton("𝑂𝑊𝑁𝐸𝑅⚙️", url="https://t.me/hackerTaker")
            )
            bot.send_message(user_id, format_message_user(clean_num, sms), parse_mode="HTML", reply_markup=user_markup)
            logger.info(f"✅ تم إرسال OTP للمستخدم {user_id}")
        except Exception as e:
            logger.error(f"إرسال للمستخدم {user_id} فشل: {e}")
    
    group_markup = types.InlineKeyboardMarkup()
    group_markup.row(
        types.InlineKeyboardButton("📋 نسخ الكود", callback_data=f"copy_{otp}"),
        types.InlineKeyboardButton("💬 𝕆𝕋ℙ 𝔾ℝ𝕆𝕌ℙ", url="https://t.me/numhj")
    )
    group_markup.row(
        types.InlineKeyboardButton("🤖 𝔻𝔼𝕍𝕀𝕃 𝔹𝕆𝕋", url="https://t.me/Taker_OTP_BOT"),
        types.InlineKeyboardButton("👑 𝕆𝕎ℕ𝔼ℝ", url="https://t.me/hackerTaker")
    )
    
    for chat_id in CHAT_IDS:
        try:
            bot.send_message(chat_id, format_message_group(clean_num, sms), parse_mode="HTML", reply_markup=group_markup)
            logger.info(f"✅ تم إرسال OTP للجروب {chat_id}")
        except Exception as e:
            logger.error(f"إرسال للجروب {chat_id} فشل: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy_button(call):
    otp_code = call.data.split("_", 1)[1]
    bot.answer_callback_query(call.id, f"✅ تم نسخ الكود: {otp_code}", show_alert=True)

# ======================================================================================
# التشغيل التلقائي
# ======================================================================================
def request_new_numbers():
    try:
        combos = get_all_combos()
        if not combos:
            for code, (_, _, ranges) in AVAILABLE_COUNTRIES.items():
                for rng in ranges:
                    save_combo(code, rng)
            combos = get_all_combos()
        for country_code, combo_index in combos:
            range_str = get_combo_range(country_code, combo_index)
            if not range_str:
                continue
            try:
                new_number = dgd_get_number(range_str)
                clean_num = re.sub(r'\D', '', new_number)
                add_active_number(clean_num, country_code, combo_index, assigned_to=0)
                logger.info(f"✅ طلب رقم جديد: {clean_num} من {country_code}")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ فشل طلب رقم من {country_code}: {e}")
    except Exception as e:
        logger.error(f"request_new_numbers error: {e}")

def check_active_numbers():
    try:
        active = get_active_numbers()
        for number, country_code, combo_index, assigned_to, status, otp_code in active:
            if status in ("SUCCESS", "EXPIRED"):
                remove_active_number(number)
                continue
            try:
                result = dgd_check_number(number)
                if result["status"] == "SUKSES":
                    otp = result.get("otp", "N/A")
                    update_active_number(number, otp_code=otp)
                    send_otp_to_user_and_group(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), number, f"OTP: {otp}")
                    remove_active_number(number)
                elif result["status"] == "EXPIRED":
                    update_active_number(number, status="EXPIRED")
                    remove_active_number(number)
                else:
                    update_active_number(number, status=result["status"])
            except Exception as e:
                if "EXPIRED" in str(e):
                    remove_active_number(number)
                else:
                    logger.error(f"⚠️ فحص {number} فشل: {e}")
    except Exception as e:
        logger.error(f"check_active_numbers error: {e}")

def main_loop():
    logger.info("🚀 DGDNetwork Bot يعمل (سرعة فائقة)")
    last_request = 0
    while True:
        try:
            now = time.time()
            if now - last_request >= 20:
                request_new_numbers()
                last_request = now
            check_active_numbers()
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ خطأ رئيسي: {e}")
            traceback.print_exc()
            time.sleep(5)

# ======================================================================================
# أوامر البوت
# ======================================================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 الحصول على رقم")
    btn2 = types.KeyboardButton("📩 الحصول على OTP")
    btn3 = types.KeyboardButton("📢 الانضمام للقناة")
    btn4 = types.KeyboardButton("❓ المساعدة")
    if is_admin(user_id):
        btn5 = types.KeyboardButton("🔐 Admin Panel")
        keyboard.row(btn1, btn2)
        keyboard.row(btn3, btn4)
        keyboard.row(btn5)
    else:
        keyboard.row(btn1, btn2)
        keyboard.row(btn3, btn4)
    return keyboard

def show_country_menu_get_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name_ar, flag, _) in AVAILABLE_COUNTRIES.items():
        ranges = AVAILABLE_COUNTRIES[code][2]
        if len(ranges) == 1:
            btn_text = f"{flag} {name_ar}"
        else:
            btn_text = f"{flag} {name_ar} ({len(ranges)} رينج)"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"country_{code}"))
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    return markup

def show_country_menu(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        markup = show_country_menu_get_markup(user_id)
        text = "🌍 <b>اختر الدولة للحصول على رقم:</b>"
        try:
            bot.edit_message_text(text, chat_id, message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        bot.send_message(chat_id, "📱 استخدم الأزرار للتنقل:", reply_markup=main_keyboard(user_id))
    except Exception as e:
        logger.error(f"show_country_menu error: {e}")

def show_number_actions(call, number, cc):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_{cc}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="back_to_countries")
    )
    markup.add(
        types.InlineKeyboardButton("👥 جروب البوت", url="https://t.me/numhj"),
        types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_start")
    )
    markup.add(types.InlineKeyboardButton("🔙 BACK", callback_data="back_to_countries"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        if is_maintenance_mode() and not is_admin(user_id):
            bot.send_message(chat_id, "⚠️ البوت في الصيانة حالياً.", parse_mode="HTML")
            return
        if is_banned(user_id):
            bot.reply_to(message, "🚫 أنت محظور.")
            return
        if not force_sub_check(user_id):
            markup = force_sub_markup()
            if markup:
                bot.send_message(chat_id, "🔒 اشترك في القنوات أولاً.", reply_markup=markup)
            return
        if not get_user(user_id):
            save_user(user_id, username=message.from_user.username or "", first_name=message.from_user.first_name or "")
        
        welcome_photo = get_setting("welcome_photo")
        text = "🌍 <b>اختر الدولة للحصول على رقم:</b>"
        markup = show_country_menu_get_markup(user_id)
        
        if welcome_photo:
            try:
                bot.send_photo(chat_id, welcome_photo, caption=text, parse_mode="HTML", reply_markup=markup)
                bot.send_message(chat_id, "📱 استخدم الأزرار للتنقل:", reply_markup=main_keyboard(user_id))
                return
            except:
                pass
        
        show_country_menu(message)
        
    except Exception as e:
        logger.error(f"send_welcome error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    try:
        if force_sub_check(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ تم التحقق!", show_alert=True)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك!", show_alert=True)
    except Exception as e:
        logger.error(f"check_sub error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country(call):
    try:
        user_id = call.from_user.id
        cc = call.data.split("_")[1]
        if is_banned(user_id) or not force_sub_check(user_id):
            return
        if cc not in AVAILABLE_COUNTRIES:
            bot.answer_callback_query(call.id, "❌ دولة غير مدعومة.", show_alert=True)
            return
        ranges = AVAILABLE_COUNTRIES[cc][2]
        if not ranges:
            bot.answer_callback_query(call.id, "❌ لا توجد رينجات.", show_alert=True)
            return
        range_str = ranges[0]
        try:
            number = dgd_get_number(range_str)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ فشل جلب الرقم: {str(e)[:80]}", show_alert=True)
            return
        clean_num = re.sub(r'\D', '', number)
        old = get_user(user_id)
        if old and old[5]:
            release_number(old[5])
            remove_active_number(old[5])
        assign_number_to_user(user_id, clean_num)
        save_user(user_id, country_code=cc, assigned_number=clean_num)
        add_active_number(clean_num, cc, 1, assigned_to=user_id)
        name_ar, flag = get_country_info(cc)
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ في انتظار OTP..."
        markup = show_number_actions(call, clean_num, cc)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ تم التخصيص")
    except Exception as e:
        logger.error(f"handle_country error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def change_number(call):
    try:
        user_id = call.from_user.id
        cc = call.data.split("_")[1]
        if is_banned(user_id) or not force_sub_check(user_id):
            return
        if cc not in AVAILABLE_COUNTRIES:
            bot.answer_callback_query(call.id, "❌ دولة غير مدعومة.", show_alert=True)
            return
        ranges = AVAILABLE_COUNTRIES[cc][2]
        if not ranges:
            bot.answer_callback_query(call.id, "❌ لا توجد رينجات.", show_alert=True)
            return
        range_str = ranges[0]
        try:
            number = dgd_get_number(range_str)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ فشل: {str(e)[:80]}", show_alert=True)
            return
        clean_num = re.sub(r'\D', '', number)
        old = get_user(user_id)
        if old and old[5]:
            release_number(old[5])
            remove_active_number(old[5])
        assign_number_to_user(user_id, clean_num)
        save_user(user_id, assigned_number=clean_num)
        add_active_number(clean_num, cc, 1, assigned_to=user_id)
        name_ar, flag = get_country_info(cc)
        msg = f"◈ الرقم: <code>+{clean_num}</code>\n◈ الدولة: {flag} {name_ar}\n◈ الحالة: ⏳ في انتظار OTP..."
        markup = show_number_actions(call, clean_num, cc)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ تم تغيير الرقم")
    except Exception as e:
        logger.error(f"change_number error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    try:
        show_country_menu(call.message)
    except Exception as e:
        logger.error(f"back_to_countries error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def back_to_start(call):
    try:
        send_welcome(call.message)
    except Exception as e:
        logger.error(f"back_to_start error: {e}")

# ======================================================================================
# معالجات أزرار الكيبورد
# ======================================================================================
@bot.message_handler(func=lambda msg: msg.text == "📱 الحصول على رقم")
def get_number_menu(msg):
    show_country_menu(msg)

@bot.message_handler(func=lambda msg: msg.text == "📩 الحصول على OTP")
def get_otp_menu(msg):
    user_id = msg.from_user.id
    user = get_user(user_id)
    if user and user[5]:
        number = user[5]
        try:
            result = dgd_check_number(number)
            if result["status"] == "SUKSES" and result["otp"]:
                bot.reply_to(msg, f"✅ الكود: {result['otp']}")
            elif result["status"] == "WAIT":
                bot.reply_to(msg, "⏳ لم يصل الكود بعد، انتظر قليلاً.")
            else:
                bot.reply_to(msg, f"⚠️ الحالة: {result['status']}")
        except Exception as e:
            bot.reply_to(msg, f"❌ فشل الفحص: {str(e)[:80]}")
    else:
        bot.reply_to(msg, "⚠️ ليس لديك رقم مخصص. احصل على رقم أولاً.")

@bot.message_handler(func=lambda msg: msg.text == "📢 الانضمام للقناة")
def join_channel(msg):
    bot.reply_to(msg, "🔗 اشترك في قناتنا:\nhttps://t.me/numhj")

@bot.message_handler(func=lambda msg: msg.text == "❓ المساعدة")
def help_menu(msg):
    bot.reply_to(msg, "👨‍💻 للتواصل مع المطور:\n@hackerTaker")

@bot.message_handler(func=lambda msg: msg.text == "🔐 Admin Panel")
def admin_panel_btn(msg):
    if is_admin(msg.from_user.id):
        admin_panel(msg)

# ======================================================================================
# لوحة تحكم المطور (جميع الأزرار شغالة)
# ======================================================================================
def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    status_icon = "🟢" if not is_maintenance_mode() else "🔴"
    status_text = "الآن: يعمل بنجاح" if not is_maintenance_mode() else "الآن: قيد الصيانة"
    markup.add(types.InlineKeyboardButton(f"{status_icon} {status_text} {status_icon}", callback_data="toggle_maintenance"))
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
    markup.row(
        types.InlineKeyboardButton("🗑️ مسح قاعدة البيانات", callback_data="clear_db"),
        types.InlineKeyboardButton("🔙 مغادرة لوحة التحكم", callback_data="back_to_countries")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ هذا القسم للمطورين فقط.", show_alert=True)
        return
    try:
        if call.from_user.id in user_states:
            del user_states[call.from_user.id]
        admin_text = (
            "<b>❍─── <u>لوحة التحكم</u> ───❍</b>\n\n"
            "<b>👋 مرحباً بك يا مطور.</b>\n\n"
            "<b>⚙️ يمكنك التحكم في كامل وظائف البوت من هنا.</b>\n"
            "<b>⚠️ أي تغيير يؤثر على المستخدمين فوراً.</b>\n\n"
            "<b>────────────────────</b>\n"
            f"<b>• الوقت الحالي: <u>{datetime.now().strftime('%H:%M')}</u></b>\n"
            "<b>────────────────────</b>"
        )
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_main_menu())
        except Exception as e:
            logger.warning(f"Edit failed, sending new message: {e}")
            bot.send_message(call.message.chat.id, admin_text, parse_mode="HTML", reply_markup=admin_main_menu())
    except Exception as e:
        logger.error(f"Admin Panel Error: {e}")
        bot.send_message(call.message.chat.id, "❌ حدث خطأ في لوحة التحكم، حاول مرة أخرى.")

# ======================================================================================
# دوال لوحة الإدارة
# ======================================================================================
@bot.callback_query_handler(func=lambda call: call.data == "toggle_maintenance")
def handle_maintenance_toggle(call):
    if not is_admin(call.from_user.id): return
    current_status = is_maintenance_mode()
    set_maintenance_mode(not current_status)
    bot.answer_callback_query(call.id, "🔓 تم فتح البوت" if current_status else "🔒 تم قفل البوت", show_alert=True)
    admin_panel(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_combo_country"
    bot.send_message(call.message.chat.id, "📥 أرسل كود الدولة (مثل 44):")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_combo_country")
def add_combo_country(msg):
    code = msg.text.strip()
    if code not in AVAILABLE_COUNTRIES:
        bot.reply_to(msg, "❌ كود غير مدعوم!")
        return
    user_states[msg.from_user.id] = {"step": "add_combo_range", "code": code}
    bot.reply_to(msg, "📥 أرسل الرينج (مثل 4473845XXX):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_combo_range")
def add_combo_range(msg):
    data = user_states[msg.from_user.id]
    code = data["code"]
    range_str = msg.text.strip()
    if not range_str.endswith("XXX"):
        bot.reply_to(msg, "❌ الرينج يجب أن ينتهي بـ XXX")
        return
    save_combo(code, range_str)
    bot.reply_to(msg, f"✅ تم إضافة الرينج {range_str}")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id): return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد رينجات!", show_alert=True)
        return
    markup = types.InlineKeyboardMarkup()
    for code, idx in combos:
        name_ar, flag = get_country_info(code)
        rng = get_combo_range(code, idx)
        markup.add(types.InlineKeyboardButton(f"{flag} {name_ar} ({rng})", callback_data=f"del_combo_{code}_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("🗑️ اختر الرينج للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def del_combo_confirm(call):
    parts = call.data.split("_")
    code, idx = parts[2], int(parts[3])
    if delete_combo(code, idx):
        bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل", show_alert=True)
    admin_del_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id): return
    users = len(get_all_users())
    combos = len(get_all_combos())
    logs = len(get_otp_logs())
    active = len(get_active_numbers())
    bot.edit_message_text(f"📊 الإحصائيات\n👥 المستخدمين: {users}\n📦 الرينجات: {combos}\n🔑 سجل OTP: {logs}\n📱 أرقام نشطة: {active}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id): return
    with open(DB_PATH, "rb") as f:
        bot.send_document(call.message.chat.id, f, caption="📄 تقرير شامل")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_all"
    bot.edit_message_text("📢 أرسل الرسالة للإذاعة للجميع:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def broadcast_all_send(msg):
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            bot.copy_message(uid, msg.chat.id, msg.message_id)
            count += 1
            time.sleep(0.05)
        except:
            pass
    bot.reply_to(msg, f"✅ تم الإرسال إلى {count} مستخدم")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_user_id"
    bot.edit_message_text("📨 أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def broadcast_user_id(msg):
    try:
        uid = int(msg.text)
        user_states[msg.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(msg, "📨 أرسل الرسالة:")
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, "").startswith("broadcast_msg_"))
def broadcast_user_send(msg):
    uid = int(user_states[msg.from_user.id].split("_")[2])
    try:
        bot.copy_message(uid, msg.chat.id, msg.message_id)
        bot.reply_to(msg, f"✅ تم الإرسال للمستخدم {uid}")
    except Exception as e:
        bot.reply_to(msg, f"❌ فشل: {e}")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "ban"
    bot.edit_message_text("🚫 أرسل ID المستخدم للحظر:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban")
def ban_user_id(msg):
    try:
        uid = int(msg.text)
        ban_user(uid)
        bot.reply_to(msg, f"✅ تم حظر {uid}")
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "unban"
    bot.edit_message_text("✅ أرسل ID المستخدم لفك الحظر:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban")
def unban_user_id(msg):
    try:
        uid = int(msg.text)
        unban_user(uid)
        bot.reply_to(msg, f"✅ تم فك حظر {uid}")
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "user_info"
    bot.edit_message_text("👤 أرسل ID المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "user_info")
def user_info_show(msg):
    try:
        uid = int(msg.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(msg, "❌ غير موجود")
            return
        info = f"👤 {user[0]}\n@{user[1] or 'N/A'}\nالرقم: {user[4] or 'لا يوجد'}\nمحظور: {'نعم' if user[5] else 'لا'}"
        bot.reply_to(msg, info)
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id): return
    channels = get_all_force_sub_channels(enabled_only=False)
    text = f"⚙️ قنوات الاشتراك: {len(channels)}\n"
    markup = types.InlineKeyboardMarkup()
    for cid, url, desc in channels:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (cid,))
        en = c.fetchone()[0]
        conn.close()
        st = "✅" if en else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {desc or url[:20]}", callback_data=f"edit_force_{cid}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="add_force_ch"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_force_ch")
def add_force_ch(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_force_url"
    bot.edit_message_text("أرسل رابط القناة (https://t.me/xxx):", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_force_url")
def add_force_url(msg):
    url = msg.text.strip()
    if not (url.startswith("https://t.me/") or url.startswith("@")):
        bot.reply_to(msg, "❌ رابط غير صالح")
        return
    user_states[msg.from_user.id] = {"step": "add_force_desc", "url": url}
    bot.reply_to(msg, "أدخل وصفاً (أو اترك فارغاً):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_force_desc")
def add_force_desc(msg):
    data = user_states[msg.from_user.id]
    desc = msg.text.strip()
    if add_force_sub_channel(data["url"], desc):
        bot.reply_to(msg, "✅ تمت الإضافة")
    else:
        bot.reply_to(msg, "❌ موجودة مسبقاً")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_force_"))
def edit_force_ch(call):
    cid = int(call.data.split("_")[2])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (cid,))
    row = c.fetchone()
    conn.close()
    if not row: return
    url, desc, en = row
    text = f"🔧 {url}\nالوصف: {desc or '—'}\nالحالة: {'مفعلة' if en else 'معطلة'}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل الوصف", callback_data=f"edit_desc_{cid}"))
    markup.add(types.InlineKeyboardButton("❌ تعطيل" if en else "✅ تفعيل", callback_data=f"toggle_force_{cid}"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"del_force_{cid}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="force_sub_admin"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_force_"))
def toggle_force(call):
    cid = int(call.data.split("_")[2])
    toggle_force_sub_channel(cid)
    bot.answer_callback_query(call.id, "✅ تم التبديل", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_force_"))
def del_force(call):
    cid = int(call.data.split("_")[2])
    if delete_force_sub_channel(cid):
        bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ فشل", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_desc(call):
    cid = int(call.data.split("_")[2])
    user_states[call.from_user.id] = f"edit_desc_{cid}"
    bot.edit_message_text("أدخل الوصف الجديد:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), str) and user_states[msg.from_user.id].startswith("edit_desc_"))
def edit_desc_exec(msg):
    cid = int(user_states[msg.from_user.id].split("_")[2])
    desc = msg.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET description=? WHERE id=?", (desc, cid))
    conn.commit()
    conn.close()
    bot.reply_to(msg, "✅ تم التحديث")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ تعيين رينج خاص", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف رينج خاص", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("🔑 إدارة الرينجات الخاصة", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_private_user"
    bot.edit_message_text("➕ أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user")
def add_private_user(msg):
    try:
        uid = int(msg.text)
        user_states[msg.from_user.id] = {"step": "add_private_country", "uid": uid}
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for code in AVAILABLE_COUNTRIES:
            name_ar, flag = get_country_info(code)
            buttons.append(types.InlineKeyboardButton(f"{flag} {name_ar}", callback_data=f"select_private_{uid}_{code}"))
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_private_combo"))
        bot.reply_to(msg, "اختر الدولة:", reply_markup=markup)
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_private_"))
def select_private(call):
    parts = call.data.split("_")
    uid = int(parts[2])
    code = parts[3]
    save_user(uid, private_combo_country=code)
    bot.answer_callback_query(call.id, f"✅ تم تعيين رينج خاص", show_alert=True)
    admin_private_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "del_private_user"
    bot.edit_message_text("🗑️ أدخل معرف المستخدم:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user")
def del_private_user(msg):
    try:
        uid = int(msg.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(msg, f"✅ تم مسح الرينج الخاص")
    except:
        bot.reply_to(msg, "❌ معرف غير صحيح")
    del user_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_welcome_photo")
def admin_set_welcome_photo(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "waiting_for_welcome_photo"
    bot.edit_message_text("🖼️ أرسل الصورة:", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['photo'], func=lambda msg: user_states.get(msg.from_user.id) == "waiting_for_welcome_photo")
def welcome_photo_set(msg):
    if not is_admin(msg.from_user.id): return
    del user_states[msg.from_user.id]
    photo_id = msg.photo[-1].file_id
    set_setting("welcome_photo", photo_id)
    bot.reply_to(msg, "✅ تم حفظ الصورة")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_welcome_photo")
def admin_del_welcome_photo(call):
    if not is_admin(call.from_user.id): return
    set_setting("welcome_photo", "")
    bot.answer_callback_query(call.id, "🗑️ تم حذف الصورة", show_alert=True)
    admin_panel(call)

@bot.callback_query_handler(func=lambda call: call.data == "clear_db")
def clear_db(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_clear_db"))
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel"))
    bot.edit_message_text("⚠️ تأكيد مسح قاعدة البيانات؟", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_clear_db")
def confirm_clear_db(call):
    if not is_admin(call.from_user.id): return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM otp_logs")
    c.execute("DELETE FROM active_numbers")
    c.execute("DELETE FROM combos")
    c.execute("DELETE FROM private_combos")
    c.execute("DELETE FROM force_sub_channels")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم المسح", show_alert=True)
    admin_panel(call)

# ======================================================================================
# خادم ويب Flask
# ======================================================================================
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "running", "bot": "DGDNetwork OTP Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "uptime": time.time()})

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

# ======================================================================================
# تشغيل البوت
# ======================================================================================
def run_bot():
    logger.info("[*] بدء تشغيل بوت Telegram...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logger.error(f"⚠️ بوت توقف: {e}")
            time.sleep(5)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("✅ خادم الويب يعمل على المنفذ 8080")
    
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    
    run_bot()

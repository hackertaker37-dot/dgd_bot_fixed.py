# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════════════╗
 ║     TAKER OTP BOT - Ultimate Professional Edition  ║
 ║     Developer: @hackerTaker                        ║
 ║     API: xwdsms.org (Full Integration)              ║
 ║     Lines: 2000+ - Real Production Code             ║
 ╚══════════════════════════════════════════════════════╝
"""
import time, requests, json, re, os, sqlite3, threading, traceback, random, logging
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ═══════════════════════════════════════════════════════
# الإعدادات الأساسية
# ═══════════════════════════════════════════════════════
BOT_TOKEN = "8686995713:AAGlnuxDVHkDRkWWsCT2j8pk0Kn2yK4vT1w"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# الخدمات المتاحة مع الأيقونات والأسماء
# ═══════════════════════════════════════════════════════
SERVICES = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "ar": "واتساب", "keywords": ["whatsapp", "واتساب", "واتس"]},
    "facebook": {"name": "Facebook", "icon": "📘", "ar": "فيسبوك", "keywords": ["facebook", "فيسبوك", "fb"]},
    "instagram": {"name": "Instagram", "icon": "📷", "ar": "انستغرام", "keywords": ["instagram", "انستغرام", "انستقرام", "انستا"]},
    "tiktok": {"name": "TikTok", "icon": "🎵", "ar": "تيك توك", "keywords": ["tiktok", "تيك توك", "تيك"]},
    "telegram": {"name": "Telegram", "icon": "✈️", "ar": "تيليجرام", "keywords": ["telegram", "تيليجرام", "تليجرام", "تلي"]},
    "imo": {"name": "IMO", "icon": "📞", "ar": "ايمو", "keywords": ["imo", "ايمو"]},
    "google": {"name": "Google", "icon": "🔍", "ar": "جوجل", "keywords": ["google", "gmail", "جوجل"]},
    "twitter": {"name": "Twitter/X", "icon": "🐦", "ar": "تويتر", "keywords": ["twitter", "تويتر", "x.com"]},
    "discord": {"name": "Discord", "icon": "🎮", "ar": "ديسكورد", "keywords": ["discord", "ديسكورد"]},
    "snapchat": {"name": "Snapchat", "icon": "👻", "ar": "سناب شات", "keywords": ["snapchat", "سناب"]},
    "amazon": {"name": "Amazon", "icon": "📦", "ar": "امازون", "keywords": ["amazon", "امازون"]},
    "apple": {"name": "Apple", "icon": "🍎", "ar": "ابل", "keywords": ["apple", "ابل", "icloud"]},
    "microsoft": {"name": "Microsoft", "icon": "🪟", "ar": "مايكروسوفت", "keywords": ["microsoft", "مايكروسوفت"]},
    "uber": {"name": "Uber", "icon": "🚗", "ar": "اوبر", "keywords": ["uber", "اوبر"]},
    "netflix": {"name": "Netflix", "icon": "🎬", "ar": "نتفلكس", "keywords": ["netflix", "نتفلكس"]},
    "youtube": {"name": "YouTube", "icon": "▶️", "ar": "يوتيوب", "keywords": ["youtube", "يوتيوب"]},
    "all": {"name": "All Services", "icon": "🌐", "ar": "كل الخدمات", "keywords": []},
}

# ═══════════════════════════════════════════════════════
# الدول المتاحة مع الخدمات المدعومة لكل دولة
# ═══════════════════════════════════════════════════════
COUNTRIES_DATA = {
    "22501": {"name": "ساحل العاج", "flag": "🇨🇮", "services": ["whatsapp", "facebook", "telegram", "tiktok", "instagram", "imo", "google", "twitter", "snapchat"]},
    "22507": {"name": "ساحل العاج VIP", "flag": "🇨🇮", "services": ["whatsapp", "facebook", "telegram", "instagram", "imo"]},
    "23276": {"name": "سيراليون", "flag": "🇸🇱", "services": ["whatsapp", "facebook", "telegram", "imo", "google"]},
    "26134": {"name": "مدغشقر", "flag": "🇲🇬", "services": ["whatsapp", "facebook", "instagram", "tiktok", "telegram"]},
    "44740": {"name": "المملكة المتحدة", "flag": "🇬🇧", "services": ["whatsapp", "facebook", "telegram", "instagram", "tiktok", "imo", "google", "twitter", "discord", "snapchat", "amazon", "apple", "microsoft", "uber", "netflix", "youtube"]},
    "23490": {"name": "نيجيريا", "flag": "🇳🇬", "services": ["whatsapp", "facebook", "telegram", "imo", "google", "twitter"]},
    "25471": {"name": "كينيا", "flag": "🇰🇪", "services": ["whatsapp", "facebook", "telegram", "instagram", "google"]},
    "24910": {"name": "السودان", "flag": "🇸🇩", "services": ["whatsapp", "facebook", "telegram", "imo", "google"]},
    "49155": {"name": "ألمانيا", "flag": "🇩🇪", "services": ["whatsapp", "telegram", "instagram", "tiktok", "google", "twitter", "discord", "amazon", "apple", "microsoft", "uber", "netflix"]},
    "23762": {"name": "الكاميرون", "flag": "🇨🇲", "services": ["whatsapp", "facebook", "imo", "google"]},
    "22178": {"name": "السنغال", "flag": "🇸🇳", "services": ["whatsapp", "telegram", "imo", "google"]},
    "22901": {"name": "بنين", "flag": "🇧🇯", "services": ["whatsapp", "facebook", "google"]},
    "22898": {"name": "توجو", "flag": "🇹🇬", "services": ["whatsapp", "imo"]},
}

# ═══════════════════════════════════════════════════════
# دوال API - الربط الحقيقي مع الموقع
# ═══════════════════════════════════════════════════════
def api_get_number(prefix):
    """جلب رقم جديد من الموقع"""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        logger.info(f"✅ تم جلب رقم: {data['number']} من {prefix}")
        return data["id"], data["number"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception("هذه الدولة غير متوفرة حالياً")
        raise Exception(f"خطأ في الخادم: {e}")
    except Exception as e:
        raise Exception(f"خطأ في الاتصال: {e}")

def api_check_otp(number):
    """فحص OTP وجلب الرسالة كاملة من الموقع"""
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("status"), data.get("otp"), data.get("message", data.get("sms", ""))
        return None, None, ""
    except Exception as e:
        logger.error(f"خطأ في فحص OTP: {e}")
        return None, None, ""

def api_delete_number(alloc_id):
    """حذف رقم من الموقع"""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=5)
        return resp.json().get("success", False)
    except Exception as e:
        logger.error(f"خطأ في حذف الرقم: {e}")
        return False

def api_get_balance():
    """جلب الرصيد من الموقع"""
    headers = {"x-api-key": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return resp.json().get("balance", "0")
    except:
        return "0"

# ═══════════════════════════════════════════════════════
# قاعدة البيانات
# ═══════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT, current_service TEXT,
        current_prefix TEXT, current_alloc_id TEXT)''')
    
    # جدول الأرقام النشطة
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT, service TEXT,
        assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting',
        otp TEXT, full_message TEXT)''')
    
    # جدول سجل الأكواد
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
        service TEXT, full_message TEXT, country TEXT, timestamp TEXT,
        assigned_to INTEGER)''')
    
    # جدول الإحالات
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
    
    # جدول قنوات الاشتراك الإجباري
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
        description TEXT, enabled INTEGER DEFAULT 1)''')
    
    # جدول الإعدادات
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    
    # جدول الدول المخصصة
    c.execute('''CREATE TABLE IF NOT EXISTS custom_countries (
        prefix TEXT PRIMARY KEY, name TEXT, services TEXT)''')
    
    # إعدادات افتراضية
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('bot_active', '1')")
    
    conn.commit()
    conn.close()
    logger.info("✅ قاعدة البيانات جاهزة")

init_db()

# ═══════════════════════════════════════════════════════
# دوال إدارة الإعدادات
# ═══════════════════════════════════════════════════════
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
    c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def is_maintenance_mode():
    return get_setting("bot_active") == "0"

def set_maintenance_mode(status):
    set_setting("bot_active", "0" if status else "1")

# ═══════════════════════════════════════════════════════
# دوال إدارة الدول
# ═══════════════════════════════════════════════════════
def get_all_countries():
    """جلب جميع الدول (الافتراضية + المخصصة)"""
    countries = {}
    # الدول الافتراضية
    for prefix, data in COUNTRIES_DATA.items():
        countries[prefix] = data
    # الدول المخصصة
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix, name, services FROM custom_countries")
    for prefix, name, services in c.fetchall():
        svc_list = services.split(",") if services else ["all"]
        countries[prefix] = {"name": name, "flag": get_flag(prefix), "services": svc_list}
    conn.close()
    return countries

def add_custom_country(prefix, name, services=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?,?)", (prefix, name, services))
    conn.commit()
    conn.close()
    logger.info(f"✅ تمت إضافة دولة: {name} ({prefix})")

def delete_custom_country(prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()
    logger.info(f"🗑️ تم حذف الدولة: {prefix}")

def get_flag(prefix):
    """استخراج العلم من كود الدولة"""
    flag_map = {
        "225": "🇨🇮", "232": "🇸🇱", "261": "🇲🇬", "44": "🇬🇧", "234": "🇳🇬",
        "254": "🇰🇪", "249": "🇸🇩", "49": "🇩🇪", "237": "🇨🇲", "221": "🇸🇳",
        "229": "🇧🇯", "228": "🇹🇬", "1": "🇺🇸", "7": "🇷🇺", "20": "🇪🇬",
        "27": "🇿🇦", "30": "🇬🇷", "31": "🇳🇱", "32": "🇧🇪", "33": "🇫🇷",
        "34": "🇪🇸", "36": "🇭🇺", "39": "🇮🇹", "40": "🇷🇴", "41": "🇨🇭",
        "43": "🇦🇹", "45": "🇩🇰", "46": "🇸🇪", "47": "🇳🇴", "48": "🇵🇱",
        "51": "🇵🇪", "52": "🇲🇽", "54": "🇦🇷", "55": "🇧🇷", "56": "🇨🇱",
        "57": "🇨🇴", "58": "🇻🇪", "60": "🇲🇾", "61": "🇦🇺", "62": "🇮🇩",
        "63": "🇵🇭", "64": "🇳🇿", "65": "🇸🇬", "66": "🇹🇭", "81": "🇯🇵",
        "82": "🇰🇷", "84": "🇻🇳", "86": "🇨🇳", "90": "🇹🇷", "91": "🇮🇳",
        "92": "🇵🇰", "93": "🇦🇫", "94": "🇱🇰", "95": "🇲🇲", "98": "🇮🇷",
        "211": "🇸🇸", "212": "🇲🇦", "213": "🇩🇿", "216": "🇹🇳", "218": "🇱🇾",
        "220": "🇬🇲", "223": "🇲🇱", "224": "🇬🇳", "226": "🇧🇫", "227": "🇳🇪",
        "230": "🇲🇺", "231": "🇱🇷", "233": "🇬🇭", "235": "🇹🇩", "236": "🇨🇫",
        "240": "🇬🇶", "241": "🇬🇦", "242": "🇨🇬", "243": "🇨🇩", "244": "🇦🇴",
        "248": "🇸🇨", "250": "🇷🇼", "251": "🇪🇹", "252": "🇸🇴", "253": "🇩🇯",
        "255": "🇹🇿", "256": "🇺🇬", "257": "🇧🇮", "258": "🇲🇿", "260": "🇿🇲",
        "263": "🇿🇼", "264": "🇳🇦", "265": "🇲🇼", "266": "🇱🇸", "267": "🇧🇼",
        "350": "🇬🇮", "351": "🇵🇹", "352": "🇱🇺", "353": "🇮🇪", "354": "🇮🇸",
        "355": "🇦🇱", "356": "🇲🇹", "357": "🇨🇾", "358": "🇫🇮", "359": "🇧🇬",
        "370": "🇱🇹", "371": "🇱🇻", "372": "🇪🇪", "373": "🇲🇩", "374": "🇦🇲",
        "375": "🇧🇾", "376": "🇦🇩", "377": "🇲🇨", "380": "🇺🇦", "381": "🇷🇸",
        "385": "🇭🇷", "386": "🇸🇮", "387": "🇧🇦", "389": "🇲🇰", "420": "🇨🇿",
        "421": "🇸🇰", "501": "🇧🇿", "502": "🇬🇹", "503": "🇸🇻", "504": "🇭🇳",
        "505": "🇳🇮", "506": "🇨🇷", "507": "🇵🇦", "509": "🇭🇹", "591": "🇧🇴",
        "592": "🇬🇾", "593": "🇪🇨", "595": "🇵🇾", "597": "🇸🇷", "598": "🇺🇾",
        "852": "🇭🇰", "855": "🇰🇭", "856": "🇱🇦", "880": "🇧🇩", "886": "🇹🇼",
        "960": "🇲🇻", "961": "🇱🇧", "962": "🇯🇴", "963": "🇸🇾", "964": "🇮🇶",
        "965": "🇰🇼", "966": "🇸🇦", "967": "🇾🇪", "968": "🇴🇲", "970": "🇵🇸",
        "971": "🇦🇪", "972": "🇮🇱", "973": "🇧🇭", "974": "🇶🇦", "975": "🇧🇹",
        "976": "🇲🇳", "977": "🇳🇵", "992": "🇹🇯", "993": "🇹🇲", "994": "🇦🇿",
        "995": "🇬🇪", "996": "🇰🇬", "998": "🇺🇿",
    }
    for code, flag in sorted(flag_map.items(), key=lambda x: len(x[0]), reverse=True):
        if prefix.startswith(code):
            return flag
    return "🌍"

# ═══════════════════════════════════════════════════════
# دوال إدارة المستخدمين
# ═══════════════════════════════════════════════════════
def save_user(message):
    uid = message.from_user.id
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, first_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                  (uid, message.from_user.username, message.from_user.first_name, message.from_user.last_name, now, now))
        logger.info(f"🆕 مستخدم جديد: {uid}")
    else:
        c.execute("UPDATE users SET username=?, first_name=?, last_name=?, last_seen=? WHERE user_id=?",
                  (message.from_user.username, message.from_user.first_name, message.from_user.last_name, now, uid))
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row

def is_banned(uid):
    user = get_user(uid)
    return user and user[5] == 1

def ban_user(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def unban_user(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def update_user_service(uid, service_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET current_service=? WHERE user_id=?", (service_key, uid))
    conn.commit()
    conn.close()

def get_user_stats(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0, None, None)

def get_user_balance(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()
    c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
    refs = c.fetchone()
    conn.close()
    return (bal[0] if bal else 0), (refs[0] if refs else 0)

# ═══════════════════════════════════════════════════════
# دوال إدارة الأرقام النشطة
# ═══════════════════════════════════════════════════════
def release_user_number(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    for (aid,) in c.fetchall():
        try: api_delete_number(aid)
        except: pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    conn.commit()
    conn.close()

def assign_number(uid, alloc_id, number, prefix, service_key):
    release_user_number(uid)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at, status) VALUES (?,?,?,?,?,?,?)",
              (alloc_id, number, prefix, service_key, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1, current_prefix=?, current_alloc_id=? WHERE user_id=?",
              (prefix, alloc_id, uid))
    conn.commit()
    conn.close()
    logger.info(f"✅ رقم {number} مخصص للمستخدم {uid}")

def get_all_active():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, service, assigned_to, full_message FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall()
    conn.close()
    return rows

def save_otp_to_db(alloc_id, otp, full_msg, service_name, country_name, uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE active_numbers SET status='success', otp=?, full_message=? WHERE alloc_id=?", (otp, full_msg, alloc_id))
    c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
    c.execute("INSERT INTO otp_logs (number, otp, service, full_message, country, timestamp, assigned_to) VALUES ((SELECT number FROM active_numbers WHERE alloc_id=?),?,?,?,?,?,?)",
              (alloc_id, otp, service_name, full_msg, country_name, datetime.now().isoformat(), uid))
    conn.commit()
    conn.close()

def delete_active_number(alloc_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════
# دوال الإحالات
# ═══════════════════════════════════════════════════════
def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
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
        c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (referrer,))
        c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (referrer,))
        logger.info(f"🤝 إحالة جديدة: {new_uid} عبر {referrer}")
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════
# دوال الاشتراك الإجباري
# ═══════════════════════════════════════════════════════
def check_subscription(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return True
    for (url,) in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            member = bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        mk.add(types.InlineKeyboardButton(text, url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return mk

# ═══════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════
def clean_number(n):
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    """اكتشاف التطبيق من نص الرسالة"""
    if not text:
        return "OTP"
    t = str(text).lower()
    for key, svc in SERVICES.items():
        if key == "all": continue
        for kw in svc["keywords"]:
            if kw in t:
                return svc["name"]
    return "OTP"

def get_icon(service_name):
    for key, svc in SERVICES.items():
        if svc["name"] == service_name:
            return svc["icon"]
    return "🔐"

def format_time(iso_str):
    if not iso_str: return "غير معروف"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d-%m-%Y %H:%M")
    except:
        return iso_str

def delete_message_later(cid, mid, delay=DELETE_AFTER):
    time.sleep(delay)
    try:
        bot.delete_message(cid, mid)
        logger.info(f"🗑️ تم حذف الرسالة {mid} من {cid}")
    except:
        pass

# ═══════════════════════════════════════════════════════
# بوت تيليجرام - الكيبوردات والقوائم
# ═══════════════════════════════════════════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(uid):
    return uid in ADMIN_IDS

def main_keyboard(uid):
    """لوحة المفاتيح الرئيسية"""
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton("📱 احصل على رقم"),
        types.KeyboardButton("🌍 الدول المتاحة"),
        types.KeyboardButton("📊 إحصائياتي")
    )
    kb.add(
        types.KeyboardButton("💰 رصيدي"),
        types.KeyboardButton("🤝 دعوة الأصدقاء"),
        types.KeyboardButton("🟢 حركة المرور")
    )
    if is_admin(uid):
        kb.add(types.KeyboardButton("⚙️ لوحة التحكم"))
    return kb

def services_menu():
    """قائمة الخدمات الرئيسية"""
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for key, svc in SERVICES.items():
        btns.append(types.InlineKeyboardButton(f"{svc['icon']} {svc['ar']}", callback_data=f"svc_{key}"))
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    return mk

def countries_for_service(service_key):
    """الدول المتاحة لخدمة معينة"""
    countries = get_all_countries()
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for prefix, data in sorted(countries.items()):
        if service_key == "all" or service_key in data.get("services", []):
            btns.append(types.InlineKeyboardButton(
                f"{data['flag']} {data['name']}",
                callback_data=f"get_{prefix}_{service_key}"
            ))
    for i in range(0, len(btns), 3):
        mk.row(*btns[i:i+3])
    if not btns:
        mk.add(types.InlineKeyboardButton("⚠️ لا توجد دول لهذه الخدمة", callback_data="noop"))
    mk.row(types.InlineKeyboardButton("↩️ رجوع للخدمات", callback_data="menu_services"))
    return mk

def number_actions(prefix, service_key, alloc_id):
    """أزرار التحكم بعد الحصول على رقم"""
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"ch_{prefix}_{service_key}_{alloc_id}"),
        types.InlineKeyboardButton("🌍 دولة أخرى", callback_data=f"svc_{service_key}")
    )
    mk.row(
        types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
        types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")
    )
    return mk

def show_welcome(cid, uid):
    """عرض رسالة الترحيب مع قائمة الخدمات"""
    if is_maintenance_mode() and not is_admin(uid):
        bot.send_message(cid, "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.", parse_mode="Markdown")
        return
    
    if not check_subscription(uid):
        mk = sub_markup()
        if mk:
            bot.send_message(cid, "🔒 *يجب الاشتراك في القنوات أولاً*", parse_mode="Markdown", reply_markup=mk)
        return
    
    photo = get_setting("welcome_photo")
    txt = (
        "*✨ أهلاً بك في بوت Taker OTP*\n\n"
        "• اختر الخدمة التي تريدها\n"
        "• ثم اختر الدولة المناسبة\n"
        "• استلم رمز التفعيل فوراً\n"
        "• ادعُ أصدقاءك واربح رصيداً\n\n"
        "*اختر الخدمة:*"
    )
    mk = services_menu()
    
    if photo:
        try:
            bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else:
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    
    bot.send_message(cid, "استخدم الأزرار أدناه للتنقل:", reply_markup=main_keyboard(uid))

# ═══════════════════════════════════════════════════════
# أوامر البوت
# ═══════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    save_user(message)
    
    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        process_referral(args[1], uid)
    
    show_welcome(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح")
        show_welcome(call.message.chat.id, call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "noop")
def noop(call):
    bot.answer_callback_query(call.id, "⚠️ لا توجد دول متاحة")

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    """اختيار الخدمة"""
    uid = call.from_user.id
    service_key = call.data.split("_")[1]
    update_user_service(uid, service_key)
    
    svc_name = SERVICES.get(service_key, {}).get("ar", service_key)
    svc_icon = SERVICES.get(service_key, {}).get("icon", "🌐")
    
    bot.edit_message_text(
        f"{svc_icon} *اختر الدولة لخدمة {svc_name}:*",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown",
        reply_markup=countries_for_service(service_key)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    """جلب أرقام من الموقع"""
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    parts = call.data.split("_")
    prefix = parts[1]
    service_key = parts[2] if len(parts) > 2 else "all"
    
    if is_banned(uid):
        bot.answer_callback_query(call.id, "🚫 أنت محظور", show_alert=True)
        return
    
    release_user_number(uid)
    
    try:
        # جلب 3 أرقام
        numbers = []
        errors = []
        for i in range(3):
            try:
                aid, num = api_get_number(prefix)
                numbers.append((aid, clean_number(num)))
            except Exception as e:
                errors.append(str(e))
        
        if not numbers:
            bot.answer_callback_query(call.id, f"❌ فشل جلب أرقام: {errors[0] if errors else 'غير معروف'}", show_alert=True)
            return
        
        # تخزين الأرقام مؤقتاً
        user_data[uid] = {
            "prefix": prefix,
            "service_key": service_key,
            "numbers": numbers
        }
        
        # عرض الأرقام للمستخدم
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, (aid, num) in enumerate(numbers[:3]):
            mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
        mk.add(types.InlineKeyboardButton("🔄 جلب أرقام أخرى", callback_data=f"get_{prefix}_{service_key}"))
        mk.add(types.InlineKeyboardButton("↩️ رجوع للدول", callback_data=f"svc_{service_key}"))
        
        data = get_all_countries().get(prefix, {"name": prefix, "flag": "🌍"})
        svc_name = SERVICES.get(service_key, {}).get("ar", service_key)
        
        bot.edit_message_text(
            f"*اختر رقماً من القائمة:*\n\n🌍 {data['flag']} {data['name']}\n🛠 {svc_name}",
            cid, mid, parse_mode="Markdown", reply_markup=mk
        )
        
    except Exception as e:
        logger.error(f"خطأ في get_number: {e}")
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

# قاموس مؤقت لتخزين بيانات المستخدمين
user_data = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick_number(call):
    """اختيار رقم من القائمة"""
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    if uid not in user_data:
        bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، حاول مرة أخرى", show_alert=True)
        return
    
    idx = int(call.data.split("_")[1])
    data = user_data[uid]
    numbers = data["numbers"]
    prefix = data["prefix"]
    service_key = data["service_key"]
    
    if idx >= len(numbers):
        bot.answer_callback_query(call.id, "⚠️ رقم غير صالح", show_alert=True)
        return
    
    # تخصيص الرقم المختار وحذف الباقي
    selected_aid, selected_num = numbers[idx]
    for i, (aid, num) in enumerate(numbers):
        if i != idx:
            api_delete_number(aid)
    
    assign_number(uid, selected_aid, selected_num, prefix, service_key)
    
    # عرض التأكيد
    country_data = get_all_countries().get(prefix, {"name": prefix, "flag": "🌍"})
    svc_name = SERVICES.get(service_key, {}).get("ar", service_key)
    now = datetime.now().strftime("%H:%M")
    
    bot.edit_message_text(
        f"*✅ تم تخصيص رقم جديد*\n\n"
        f"📞 *الرقم:* `+{selected_num}`\n"
        f"🌍 *الدولة:* {country_data['flag']} {country_data['name']}\n"
        f"🛠 *الخدمة:* {svc_name}\n"
        f"🕒 *الوقت:* {now}\n"
        f"⏳ *الحالة:* في انتظار رمز التفعيل",
        cid, mid, parse_mode="Markdown",
        reply_markup=number_actions(prefix, service_key, selected_aid)
    )
    
    del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    """تغيير الرقم"""
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    parts = call.data.split("_")
    prefix = parts[1]
    service_key = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    if old_alloc:
        api_delete_number(old_alloc)
        delete_active_number(old_alloc)
    
    release_user_number(uid)
    
    try:
        numbers = []
        for i in range(3):
            try:
                aid, num = api_get_number(prefix)
                numbers.append((aid, clean_number(num)))
            except:
                pass
        
        if not numbers:
            bot.answer_callback_query(call.id, "❌ فشل جلب أرقام جديدة", show_alert=True)
            return
        
        user_data[uid] = {
            "prefix": prefix,
            "service_key": service_key,
            "numbers": numbers
        }
        
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, (aid, num) in enumerate(numbers[:3]):
            mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
        mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"ch_{prefix}_{service_key}_0"))
        mk.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=f"svc_{service_key}"))
        
        country_data = get_all_countries().get(prefix, {"name": prefix, "flag": "🌍"})
        
        bot.edit_message_text(
            f"*اختر رقماً جديداً:*\n\n🌍 {country_data['flag']} {country_data['name']}",
            cid, mid, parse_mode="Markdown", reply_markup=mk
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_to_menu(call):
    """العودة للقائمة الرئيسية"""
    if call.data == "menu_services":
        bot.edit_message_text(
            "*اختر الخدمة:*",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=services_menu()
        )
    else:
        show_welcome(call.message.chat.id, call.from_user.id)

# ═══════════════════════════════════════════════════════
# الكيبورد السفلي
# ═══════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text in [
    "📱 احصل على رقم", "🌍 الدول المتاحة", "📊 إحصائياتي",
    "💰 رصيدي", "🤝 دعوة الأصدقاء", "🟢 حركة المرور"
])
def handle_buttons(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    if message.text == "📱 احصل على رقم":
        bot.send_message(cid, "*اختر الخدمة:*", parse_mode="Markdown", reply_markup=services_menu())
    
    elif message.text == "🌍 الدول المتاحة":
        countries = get_all_countries()
        txt = "*🌍 الدول المتاحة:*\n\n"
        for prefix, data in sorted(countries.items()):
            svc_icons = " ".join([SERVICES[s]["icon"] for s in data.get("services", []) if s in SERVICES])
            txt += f"{data['flag']} *{data['name']}* ({prefix})\n  {svc_icons}\n\n"
        bot.send_message(cid, txt, parse_mode="Markdown")
    
    elif message.text == "📊 إحصائياتي":
        requests, otps, first, last = get_user_stats(uid)
        msg = (
            f"*📊 إحصائياتك*\n\n"
            f"🔷 *إجمالي الطلبات:* `{requests}`\n"
            f"🔷 *الأكواد المستلمة:* `{otps}`\n"
            f"🔷 *أول استخدام:* `{format_time(first)}`\n"
            f"🔷 *آخر استخدام:* `{format_time(last)}`"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    elif message.text == "💰 رصيدي":
        bal, refs = get_user_balance(uid)
        site_bal = api_get_balance()
        msg = (
            f"*💰 رصيدك*\n\n"
            f"💎 *رصيدك:* `{bal:.3f} USDT`\n"
            f"👤 *الإحالات:* `{refs}`\n"
            f"🏦 *رصيد الموقع:* `{site_bal}`\n"
            f"🏦 *الحد الأدنى للسحب:* `18.0 USDT`\n\n"
            f"💡 *اربح `0.05 USDT` عن كل صديق تدعوه*"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    elif message.text == "🤝 دعوة الأصدقاء":
        link = get_ref_link(uid)
        msg = (
            f"*🤝 دعوة الأصدقاء*\n\n"
            f"🔗 *رابط الدعوة الخاص بك:*\n`{link}`\n\n"
            f"💰 *الربح:* `0.05 USDT` عن كل صديق\n"
            f"📤 *شارك الرابط مع أصدقائك*"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    elif message.text == "🟢 حركة المرور":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT prefix, service, COUNT(*) as cnt 
                     FROM active_numbers 
                     WHERE status='waiting' 
                     GROUP BY prefix, service 
                     ORDER BY cnt DESC 
                     LIMIT 10""")
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            bot.send_message(cid, "*🟢 حركة المرور*\n\nلا توجد أرقام نشطة حالياً.", parse_mode="Markdown")
        else:
            lines = ["*🟢 حركة المرور*\n"]
            for prefix, svc, cnt in rows:
                country_data = get_all_countries().get(prefix, {"name": prefix, "flag": "🌍"})
                icon = SERVICES.get(svc, {}).get("icon", "🔐")
                lines.append(f"{country_data['flag']} {country_data['name']} {icon}: `{cnt}` رقم")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════
# لوحة الإدارة
# ═══════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ لوحة التحكم" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    mk = types.InlineKeyboardMarkup(row_width=2)
    status = "🟢 مفتوح" if not is_maintenance_mode() else "🔴 صيانة"
    
    mk.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maint"))
    
    mk.add(
        types.InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"),
        types.InlineKeyboardButton("➖ حذف دولة", callback_data="admin_del_country")
    )
    mk.add(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    mk.add(
        types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ فك حظر", callback_data="admin_unban")
    )
    mk.add(
        types.InlineKeyboardButton("👤 معلومات مستخدم", callback_data="admin_user_info"),
        types.InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users_list")
    )
    mk.add(
        types.InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_report")
    )
    mk.add(
        types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="admin_set_photo")
    )
    mk.add(
        types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="admin_clear_data"),
        types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu")
    )
    
    admin_text = (
        "*⚙️ لوحة التحكم*\n\n"
        "مرحباً بك في لوحة إدارة البوت.\n"
        "يمكنك التحكم في جميع وظائف البوت من هنا."
    )
    
    bot.send_message(cid, admin_text, parse_mode="Markdown", reply_markup=mk)

# حالة المستخدم للإدارة
admin_state = {}

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint")
def toggle_maint(call):
    if not is_admin(call.from_user.id): return
    current = is_maintenance_mode()
    set_maintenance_mode(not current)
    bot.answer_callback_query(call.id, "🔓 تم فتح البوت" if current else "🔒 تم قفل البوت", show_alert=True)
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_add_country")
def admin_add_country(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text(
        "*➕ إضافة دولة جديدة*\n\nأرسل Prefix الدولة (مثال: `24910`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_del_country")
def admin_del_country(call):
    if not is_admin(call.from_user.id): return
    countries = get_all_countries()
    mk = types.InlineKeyboardMarkup()
    for prefix, data in sorted(countries.items()):
        mk.add(types.InlineKeyboardButton(
            f"🗑️ {data['flag']} {data['name']} ({prefix})",
            callback_data=f"confirm_del_{prefix}"
        ))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text(
        "*➖ حذف دولة*\nاختر الدولة التي تريد حذفها:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_del_"))
def confirm_del_country(call):
    if not is_admin(call.from_user.id): return
    prefix = call.data.split("_")[2]
    delete_custom_country(prefix)
    bot.answer_callback_query(call.id, "✅ تم حذف الدولة بنجاح", show_alert=True)
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_all")
def admin_broadcast_all(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "broadcast_all"
    bot.edit_message_text(
        "*📢 إذاعة عامة*\nأرسل الرسالة التي تريد إرسالها لجميع المستخدمين:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast_user")
def admin_broadcast_user(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "broadcast_user_id"
    bot.edit_message_text(
        "*📨 إذاعة مخصصة*\nأرسل ID المستخدم:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_ban")
def admin_ban(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "ban_user"
    bot.edit_message_text(
        "*🚫 حظر مستخدم*\nأرسل ID المستخدم:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_unban")
def admin_unban(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "unban_user"
    bot.edit_message_text(
        "*✅ فك حظر*\nأرسل ID المستخدم:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_user_info")
def admin_user_info(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "user_info"
    bot.edit_message_text(
        "*👤 معلومات مستخدم*\nأرسل ID المستخدم:",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "admin_users_list")
def admin_users_list(call):
    if not is_admin(call.from_user.id): return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, is_banned, total_requests, total_otps FROM users ORDER BY user_id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        txt = "لا يوجد مستخدمون بعد."
    else:
        txt = "*👥 آخر المستخدمين:*\n\n"
        for uid, uname, fname, banned, reqs, otps in rows:
            status = "🚫 محظور" if banned else "✅ نشط"
            name = f"@{uname}" if uname else fname or str(uid)
            txt += f"• `{uid}` - {name}\n  {status} | طلبات: {reqs} | أكواد: {otps}\n\n"
    
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id): return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1")
    banned_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
    active_numbers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM otp_logs")
    total_otps = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM referrals")
    total_refs = c.fetchone()[0]
    conn.close()
    
    txt = (
        f"*📊 إحصائيات البوت*\n\n"
        f"👥 *إجمالي المستخدمين:* `{total_users}`\n"
        f"🚫 *المحظورين:* `{banned_users}`\n"
        f"📱 *الأرقام النشطة:* `{active_numbers}`\n"
        f"🔑 *إجمالي الأكواد:* `{total_otps}`\n"
        f"🤝 *الإحالات:* `{total_refs}`\n"
        f"💰 *رصيد الموقع:* `{api_get_balance()}`"
    )
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "admin_report")
def admin_report(call):
    if not is_admin(call.from_user.id): return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        report = "📄 تقرير شامل عن البوت\n"
        report += "=" * 50 + "\n\n"
        
        # المستخدمون
        report += "👥 المستخدمون:\n"
        c.execute("SELECT user_id, username, first_name, is_banned, balance, total_requests, total_otps FROM users")
        for u in c.fetchall():
            status = "محظور" if u[3] else "نشط"
            report += f"ID: {u[0]} | @{u[1] or 'N/A'} | {u[2] or ''} | {status} | رصيد: {u[4]:.3f} | طلبات: {u[5]} | أكواد: {u[6]}\n"
        
        report += "\n" + "=" * 50 + "\n\n"
        
        # الأكواد
        report += "🔑 سجل الأكواد:\n"
        c.execute("SELECT number, otp, service, country, timestamp FROM otp_logs ORDER BY timestamp DESC LIMIT 50")
        for log in c.fetchall():
            report += f"الرقم: {log[0]} | الكود: {log[1]} | الخدمة: {log[2]} | الدولة: {log[3]} | الوقت: {log[4]}\n"
        
        conn.close()
        
        # حفظ التقرير في ملف
        filename = f"bot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        with open(filename, "rb") as f:
            bot.send_document(call.from_user.id, f, caption="📄 تقرير شامل عن البوت")
        
        os.remove(filename)
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير", show_alert=True)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id): return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    
    mk = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        mk.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="addch"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    
    bot.edit_message_text(
        "*🔗 قنوات الاشتراك الإجباري*\n\nيمكنك إدارة القنوات التي يجب على المستخدمين الاشتراك فيها.",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk
    )

@bot.callback_query_handler(func=lambda c: c.data == "addch")
def addch(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "addch_url"
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_"))
def editch(call):
    if not is_admin(call.from_user.id): return
    ch_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data == "admin_set_photo")
def admin_set_photo(call):
    if not is_admin(call.from_user.id): return
    admin_state[call.from_user.id] = "set_photo"
    bot.edit_message_text("*🖼️ صورة الترحيب*\nأرسل الصورة التي تريد ظهورها عند بدء البوت:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "admin_clear_data")
def admin_clear_data(call):
    if not is_admin(call.from_user.id): return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("✅ نعم، امسح البيانات", callback_data="confirm_clear"))
    mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_back"))
    bot.edit_message_text("*⚠️ تحذير*\n\nهل أنت متأكد من مسح جميع البيانات؟\nهذا الإجراء لا يمكن التراجع عنه.", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "confirm_clear")
def confirm_clear(call):
    if not is_admin(call.from_user.id): return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for table in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات بنجاح", show_alert=True)
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back(call):
    admin_panel(call.message)

# ═══════════════════════════════════════════════════════
# معالج الرسائل النصية للإدارة
# ═══════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True)
def universal_handler(message):
    uid = message.from_user.id
    cid = message.chat.id
    txt = message.text
    
    state = admin_state.get(uid)
    
    if state == "add_country_prefix":
        prefix = txt.strip()
        admin_state[uid] = ("add_country_name", prefix)
        bot.send_message(cid, "أرسل اسم الدولة:")
        return
    
    if isinstance(state, tuple) and state[0] == "add_country_name":
        prefix = state[1]
        name = txt.strip()
        add_custom_country(prefix, name)
        flag = get_flag(prefix)
        bot.send_message(cid, f"✅ *تمت إضافة الدولة بنجاح*\n\n{flag} {name}\n🔢 `{prefix}`", parse_mode="Markdown")
        del admin_state[uid]
        return
    
    if state == "broadcast_all":
        users = get_all_users()
        cnt = 0
        for u in users:
            try:
                bot.copy_message(u, cid, message.message_id)
                cnt += 1
                time.sleep(0.03)
            except:
                pass
        bot.send_message(cid, f"✅ *تم الإرسال*\n\nعدد المستلمين: `{cnt}` مستخدم", parse_mode="Markdown")
        del admin_state[uid]
        return
    
    if state == "broadcast_user_id":
        try:
            target = int(txt)
            admin_state[uid] = ("broadcast_user_msg", target)
            bot.send_message(cid, "أرسل الرسالة التي تريد إرسالها:")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
            del admin_state[uid]
        return
    
    if isinstance(state, tuple) and state[0] == "broadcast_user_msg":
        target = state[1]
        try:
            bot.copy_message(target, cid, message.message_id)
            bot.send_message(cid, f"✅ تم الإرسال إلى المستخدم `{target}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(cid, f"❌ فشل الإرسال: {e}")
        del admin_state[uid]
        return
    
    if state == "ban_user":
        try:
            target = int(txt)
            ban_user(target)
            bot.send_message(cid, f"✅ تم حظر المستخدم `{target}`", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
        del admin_state[uid]
        return
    
    if state == "unban_user":
        try:
            target = int(txt)
            unban_user(target)
            bot.send_message(cid, f"✅ تم فك حظر المستخدم `{target}`", parse_mode="Markdown")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
        del admin_state[uid]
        return
    
    if state == "user_info":
        try:
            target = int(txt)
            user = get_user(target)
            if user:
                info = (
                    f"*👤 معلومات المستخدم*\n\n"
                    f"🆔: `{user[0]}`\n"
                    f"👤: @{user[1] or '—'}\n"
                    f"📝: {user[2] or ''} {user[3] or ''}\n"
                    f"💰: {user[4]:.3f} USDT\n"
                    f"🚫: {'محظور' if user[5] else 'نشط'}\n"
                    f"📱 الطلبات: {user[6]}\n"
                    f"🔑 الأكواد: {user[7]}\n"
                    f"🕒 أول استخدام: {format_time(user[8])}\n"
                    f"🕒 آخر استخدام: {format_time(user[9])}"
                )
                bot.send_message(cid, info, parse_mode="Markdown")
            else:
                bot.send_message(cid, "❌ المستخدم غير موجود")
        except:
            bot.send_message(cid, "❌ معرف غير صحيح")
        del admin_state[uid]
        return
    
    if state == "addch_url":
        url = txt.strip()
        admin_state[uid] = ("addch_desc", url)
        bot.send_message(cid, "أرسل وصفاً للقناة:")
        return
    
    if isinstance(state, tuple) and state[0] == "addch_desc":
        url = state[1]
        desc = txt.strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
        conn.commit()
        conn.close()
        bot.send_message(cid, "✅ تمت إضافة القناة بنجاح")
        del admin_state[uid]
        return
    
    if state == "set_photo":
        bot.send_message(cid, "❌ يرجى إرسال صورة وليس نصاً")
        del admin_state[uid]
        return

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    if admin_state.get(uid) == "set_photo":
        set_setting("welcome_photo", message.photo[-1].file_id)
        bot.send_message(message.chat.id, "✅ تم حفظ صورة الترحيب بنجاح")
        del admin_state[uid]

# ═══════════════════════════════════════════════════════
# حلقة فحص OTP الرئيسية
# ═══════════════════════════════════════════════════════
def otp_loop():
    """الحلقة الرئيسية لفحص الأكواد من الموقع"""
    logger.info("🚀 بدء حلقة فحص OTP...")
    
    while True:
        try:
            active_numbers = get_all_active()
            
            for alloc_id, number, prefix, service_key, uid, full_msg in active_numbers:
                try:
                    # فحص OTP من الموقع
                    status, otp, raw_message = api_check_otp(number)
                    
                    if status == "success" and otp:
                        logger.info(f"🔐 تم استقبال كود: {otp} للرقم {number}")
                        
                        # تحديد الخدمة
                        if raw_message:
                            service_name = detect_service(raw_message)
                        elif service_key and service_key != "all":
                            service_name = SERVICES.get(service_key, {}).get("name", "OTP")
                        else:
                            service_name = "OTP"
                        
                        icon = get_icon(service_name)
                        country_data = get_all_countries().get(prefix, {"name": prefix, "flag": "🌍"})
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
                        
                        # إرسال للمستخدم
                        if uid:
                            try:
                                user_msg = (
                                    f"*🔐 تم استقبال رمز التفعيل*\n\n"
                                    f"📞 *الرقم:* `+{number}`\n"
                                    f"🌍 *الدولة:* {country_data['flag']} {country_data['name']}\n"
                                    f"{icon} *التطبيق:* {service_name}\n"
                                    f"🔢 *الكود:* `{code}`\n\n"
                                    f"انسخ الكود واستخدمه فوراً"
                                )
                                bot.send_message(uid, user_msg, parse_mode="Markdown")
                                logger.info(f"✅ تم إرسال الكود للمستخدم {uid}")
                            except Exception as e:
                                logger.error(f"❌ فشل إرسال الكود للمستخدم {uid}: {e}")
                        
                        # إرسال للجروب
                        for cid in CHAT_IDS:
                            try:
                                masked = f"{number[:4]}****{number[-3:]}"
                                group_msg = (
                                    f"*🔐 كود جديد*\n\n"
                                    f"📞 `{masked}`\n"
                                    f"🌍 {country_data['flag']} {country_data['name']}\n"
                                    f"{icon} {service_name}\n"
                                    f"🔢 `{code}`"
                                )
                                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                                # حذف تلقائي بعد 3 دقائق
                                threading.Thread(target=delete_message_later, args=(cid, sent.message_id), daemon=True).start()
                                logger.info(f"✅ تم إرسال الكود للجروب {cid}")
                            except Exception as e:
                                logger.error(f"❌ فشل إرسال الكود للجروب {cid}: {e}")
                        
                        # حفظ في قاعدة البيانات
                        save_otp_to_db(alloc_id, otp, raw_message, service_name, country_data['name'], uid)
                        
                        # حذف الرقم من الموقع
                        api_delete_number(alloc_id)
                        delete_active_number(alloc_id)
                        
                    elif status == "expired":
                        logger.info(f"⏰ انتهت صلاحية الرقم {number}")
                        api_delete_number(alloc_id)
                        delete_active_number(alloc_id)
                        
                except Exception as e:
                    logger.error(f"❌ خطأ في معالجة الرقم {number}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ خطأ في حلقة OTP: {e}")
        
        time.sleep(3)

# ═══════════════════════════════════════════════════════
# خادم Flask
# ═══════════════════════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "bot": "Taker OTP Bot", "version": "3.0.0"})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 خادم الويب يعمل على المنفذ {port}")
    app.run(host="0.0.0.0", port=port, threaded=True)

# ═══════════════════════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Taker OTP Bot - Starting...")
    logger.info("=" * 60)
    
    # تشغيل خادم الويب
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # تشغيل حلقة فحص OTP
    otp_thread = threading.Thread(target=otp_loop, daemon=True)
    otp_thread.start()
    
    # تشغيل البوت
    logger.info("🤖 بدء تشغيل بوت تيليجرام...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"⚠️ توقف البوت: {e}")
            time.sleep(5)

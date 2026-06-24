# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     TAKER OTP BOT - ULTIMATE MEGA EDITION v5.0                            ║
║     Developer: @hackerTaker                                               ║
║     API: xwdsms.org (Full Integration)                                    ║
║     Features: AR/EN | Fast | Stable | OTP to Groups | Auto Delete        ║
║     Architecture: Hybrid LongPolling + Flask + ThreadPool                 ║
║     Threads: 32 Workers | Auto Retry | Cache System                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import time
import requests
import re
import os
import sqlite3
import threading
import logging
import json
import hashlib
import functools
import random
import string
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot import types, TeleBot, apihelper
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from flask import Flask, jsonify, request as flask_request, Response, send_file
from functools import lru_cache
from io import BytesIO
import csv

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - OPTIMIZED FOR MAX PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN = "8686995713:AAG0JXX0P9TQSW97Mq19Glj_kSm2TsgKvmg"
API_KEY = "97257ac6fe5efd03c28b43af34a887b3"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_mega.db"
DELETE_AFTER = 1800  # نصف ساعة
MAX_WORKERS = 32  # 32 thread متوازي
CACHE_TTL = 30
POLLING_TIMEOUT = 10
LONG_POLLING_TIMEOUT = 5
SESSION_TTL = 300
OTP_CHECK_INTERVAL = 1.5  # فحص كل 1.5 ثانية
MIN_WITHDRAW = 18.0
REFERRAL_BONUS = 0.05

# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TUNING
# ═══════════════════════════════════════════════════════════════════════════════
apihelper.SESSION_TIME_TO_LIVE = SESSION_TTL
apihelper.ENABLE_MIDDLEWARE = False
apihelper.READ_TIMEOUT = 5
apihelper.CONNECT_TIMEOUT = 3

# Thread Pool Executor للمهام المتوازية
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Cache متقدم
_cache = {}
_cache_time = {}
_cache_ttl = {}

def cached(ttl=CACHE_TTL):
    """ديكورتر للكاش المؤقت المتقدم"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            now = time.time()
            if key in _cache and now - _cache_time.get(key, 0) < ttl:
                return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_time[key] = now
            return result
        return wrapper
    return decorator

def clear_cache():
    """مسح الكاش بالكامل"""
    global _cache, _cache_time
    _cache = {}
    _cache_time = {}

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING - COMPLETE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# إضافة ملف سجل
try:
    fh = logging.FileHandler('taker_bot.log', encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(fh)
except:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATION DICTIONARY - COMPLETE AR/EN (250+ Keys)
# ═══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # ===== MAIN =====
    "welcome_title": {"ar": "✨ أهلاً بك في بوت Taker OTP", "en": "✨ Welcome to Taker OTP Bot"},
    "welcome_desc": {
        "ar": "• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n• ادعُ أصدقاءك واربح رصيداً",
        "en": "• Choose the service you want\n• Then choose the country\n• Receive OTP instantly\n• Invite friends and earn credit"
    },
    "choose_service": {"ar": "📱 اختـــر الخــدمــة:", "en": "📱 Choose Service:"},
    "choose_country": {"ar": "🌍 اختر الدولة لخدمة {}", "en": "🌍 Choose country for {}"},
    "use_buttons": {"ar": "📌 استخدم الأزرار أدناه:", "en": "📌 Use the buttons below:"},
    "back": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "unknown": {"ar": "غير معروف", "en": "Unknown"},
    "maintenance": {"ar": "⚠️ البوت في وضع الصيانة\nيرجى المحاولة لاحقاً", "en": "⚠️ Bot under maintenance\nPlease try later"},
    "general_error": {"ar": "❌ خطأ: {}", "en": "❌ Error: {}"},
    "api_error": {"ar": "❌ خطأ في الاتصال بالـ API", "en": "❌ API Connection Error"},
    
    # ===== NUMBER =====
    "new_number": {"ar": "✅ تم تخصيص رقم جديد", "en": "✅ New number allocated"},
    "number": {"ar": "📞 الرقم", "en": "📞 Number"},
    "country": {"ar": "🌍 الدولة", "en": "🌍 Country"},
    "service": {"ar": "🛠 الخدمة", "en": "🛠 Service"},
    "time": {"ar": "🕒 الوقت", "en": "🕒 Time"},
    "status_waiting": {"ar": "⏳ في انتظار رمز التفعيل...", "en": "⏳ Waiting for OTP..."},
    "change_number": {"ar": "🔄 تغيير الرقم", "en": "🔄 Change Number"},
    "change_country": {"ar": "🌍 تغيير الدولة", "en": "🌍 Change Country"},
    "otp_channel": {"ar": "📞 قناة الأكواد", "en": "📞 OTP Channel"},
    "change_number_title": {"ar": "🔄 تم تغيير الرقم", "en": "🔄 Number Changed"},
    "new_number_msg": {"ar": "📞 الرقم الجديد", "en": "📞 New Number"},
    "no_country": {"ar": "❌ الدولة غير متوفرة حالياً", "en": "❌ Country unavailable"},
    "no_active_numbers": {"ar": "🚫 لا توجد أرقام نشطة حالياً", "en": "🚫 No active numbers currently"},
    
    # ===== OTP =====
    "otp_received": {"ar": "🔐 تم استقبال رمز التفعيل", "en": "🔐 OTP Received"},
    "app": {"ar": "📱 التطبيق", "en": "📱 Application"},
    "code": {"ar": "🔢 الكود", "en": "🔢 Code"},
    "copy_code": {"ar": "📋 انسخ الكود واستخدمه فوراً", "en": "📋 Copy the code and use it immediately"},
    "otp_group": {"ar": "🔐 كود جديد", "en": "🔐 New OTP"},
    
    # ===== BUTTONS =====
    "get_number_btn": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries_btn": {"ar": "🌍 الدول", "en": "🌍 Countries"},
    "stats_btn": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance_btn": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite_btn": {"ar": "🤝 دعوة", "en": "🤝 Invite"},
    "traffic_btn": {"ar": "🟢 المرور", "en": "🟢 Traffic"},
    "admin_btn": {"ar": "⚙️ تحكم", "en": "⚙️ Admin"},
    "back_to_services": {"ar": "↩️ رجوع للخدمات", "en": "↩️ Back to Services"},
    
    # ===== STATS =====
    "my_stats": {"ar": "📊 إحصائياتك", "en": "📊 Your Statistics"},
    "total_requests": {"ar": "📤 إجمالي الطلبات", "en": "📤 Total Requests"},
    "otps_received": {"ar": "📥 الأكواد المستلمة", "en": "📥 OTPs Received"},
    "first_use": {"ar": "🟢 أول استخدام", "en": "🟢 First Use"},
    "last_use": {"ar": "🔵 آخر استخدام", "en": "🔵 Last Use"},
    
    # ===== BALANCE =====
    "my_balance": {"ar": "💰 رصيدك", "en": "💰 Your Balance"},
    "your_balance": {"ar": "💎 رصيدك", "en": "💎 Your Balance"},
    "referrals": {"ar": "👥 الإحالات", "en": "👥 Referrals"},
    "site_balance": {"ar": "🏦 رصيد الموقع", "en": "🏦 Site Balance"},
    "min_withdraw": {"ar": "🏦 الحد الأدنى للسحب", "en": "🏦 Min Withdrawal"},
    "earn_tip": {"ar": "💡 اربح 0.05 USDT عن كل صديق", "en": "💡 Earn 0.05 USDT per friend"},
    
    # ===== INVITE =====
    "invite_friends": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "your_link": {"ar": "🔗 رابط الدعوة الخاص بك:\n`{}`", "en": "🔗 Your invite link:\n`{}`"},
    "share_link": {"ar": "📤 شارك الرابط مع أصدقائك", "en": "📤 Share the link with friends"},
    
    # ===== TRAFFIC =====
    "active_numbers": {"ar": "🟢 حركة المرور - الأرقام النشطة", "en": "🟢 Traffic - Active Numbers"},
    "traffic_stats": {"ar": "📊 إحصائيات المرور", "en": "📊 Traffic Statistics"},
    "total_active": {"ar": "📊 إجمالي النشط", "en": "📊 Total Active"},
    "percentage": {"ar": "نسبة", "en": "Percentage"},
    
    # ===== ADMIN =====
    "admin_header": {"ar": "⚙️ لوحة التحكم\n\nمرحباً بك في لوحة إدارة البوت", "en": "⚙️ Admin Panel\n\nWelcome to bot admin panel"},
    "admin_status": {"ar": "📊 حالة: {}", "en": "📊 Status: {}"},
    "admin_open": {"ar": "🟢 مفتوح", "en": "🟢 Open"},
    "admin_maint": {"ar": "🔴 صيانة", "en": "🔴 Maintenance"},
    "add_country_btn": {"ar": "➕ دولة", "en": "➕ Country"},
    "del_country_btn": {"ar": "➖ دولة", "en": "➖ Country"},
    "add_service_btn": {"ar": "➕ خدمة", "en": "➕ Service"},
    "del_service_btn": {"ar": "➖ خدمة", "en": "➖ Service"},
    "broadcast_btn": {"ar": "📢 إذاعة", "en": "📢 Broadcast"},
    "users_btn": {"ar": "👥 مستخدمين", "en": "👥 Users"},
    "ban_btn": {"ar": "🚫 حظر", "en": "🚫 Ban"},
    "unban_btn": {"ar": "✅ فك حظر", "en": "✅ Unban"},
    "force_sub_btn": {"ar": "🔗 اشتراك إجباري", "en": "🔗 Force Sub"},
    "photo_btn": {"ar": "🖼️ صورة ترحيب", "en": "🖼️ Welcome Photo"},
    "clear_btn": {"ar": "🗑️ مسح البيانات", "en": "🗑️ Clear Data"},
    "exit_btn": {"ar": "↩️ خروج", "en": "↩️ Exit"},
    "report_btn": {"ar": "📄 تقرير شامل", "en": "📄 Full Report"},
    
    # ===== FORCE SUB =====
    "force_sub": {"ar": "🔒 يجب الاشتراك في القنوات أولاً", "en": "🔒 Subscribe to channels first"},
    "sub_btn": {"ar": "📢 اشترك الآن", "en": "📢 Subscribe Now"},
    "check_sub_btn": {"ar": "✅ تحقق", "en": "✅ Check"},
    "check_sub_ok": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_sub_fail": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ Not subscribed to all channels"},
    
    # ===== LANGUAGE =====
    "language_changed_ar": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to Arabic"},
    "language_changed_en": {"ar": "✅ تم تغيير اللغة إلى English", "en": "✅ Language changed to English"},
    "choose_language": {"ar": "🌐 اختر لغتك", "en": "🌐 Choose your language"},
    
    # ===== COUNTRIES & SERVICES =====
    "countries_services": {"ar": "🌍 الدول والخدمات المتاحة:", "en": "🌍 Available countries & services:"},
    "services_count": {"ar": "📊 عدد الخدمات", "en": "📊 Services Count"},
    "countries_count": {"ar": "🌍 عدد الدول", "en": "🌍 Countries Count"},
    
    # ===== STATUS =====
    "status_success": {"ar": "✅ نجاح", "en": "✅ Success"},
    "status_failed": {"ar": "❌ فشل", "en": "❌ Failed"},
    "status_waiting_short": {"ar": "⏳ انتظار", "en": "⏳ Waiting"},
    "status_expired": {"ar": "⏰ منتهي", "en": "⏰ Expired"},
    
    # ===== MISC =====
    "bot_name": {"ar": "🤖 بوت Taker OTP", "en": "🤖 Taker OTP Bot"},
    "version": {"ar": "الإصدار 5.0", "en": "Version 5.0"},
    "developed_by": {"ar": "👨‍💻 المطور: @hackerTaker", "en": "👨‍💻 Developer: @hackerTaker"},
    "api_source": {"ar": "🔗 API: xwdsms.org", "en": "🔗 API: xwdsms.org"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE UTILS - Ultra Fast with Persistent Cache
# ═══════════════════════════════════════════════════════════════════════════════
_lang_cache = {}
_lang_cache_time = {}

def get_lang(uid):
    """جلب لغة المستخدم مع كاش متقدم"""
    uid_str = str(uid)
    now = time.time()
    if uid_str in _lang_cache and now - _lang_cache_time.get(uid_str, 0) < 300:
        return _lang_cache[uid_str]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (f"lang_{uid}",))
        row = c.fetchone()
        conn.close()
        lang = row[0] if row else None
        _lang_cache[uid_str] = lang
        _lang_cache_time[uid_str] = now
        return lang
    except:
        return None

def set_lang(uid, lang):
    """حفظ لغة المستخدم مع تحديث الكاش"""
    uid_str = str(uid)
    _lang_cache[uid_str] = lang
    _lang_cache_time[uid_str] = time.time()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO settings VALUES (?,?)", (f"lang_{uid}", lang))
        conn.commit()
        conn.close()
    except:
        pass

def _(key, uid=None, **kwargs):
    """ترجمة فورية مع دعم المتغيرات"""
    if uid is None:
        lang = "ar"
    else:
        lang = get_lang(uid) or "ar"
    text = TRANSLATIONS.get(key, {}).get(lang)
    if text is None:
        text = TRANSLATIONS.get(key, {}).get("ar", key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT DATA - EXTENDED (50+ Countries, 25+ Services)
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_COUNTRIES = {
    # أفريقيا
    "22501": "ساحل العاج", "23276": "سيراليون", "26134": "مدغشقر",
    "23490": "نيجيريا", "25471": "كينيا", "24910": "السودان",
    "23762": "الكاميرون", "22178": "السنغال", "22901": "بنين",
    "22898": "توجو", "23322": "غانا", "25642": "أوغندا",
    "25111": "إثيوبيا", "25838": "موزمبيق", "26027": "زامبيا",
    "26315": "زيمبابوي", "26528": "مالاوي", "26622": "ليسوتو",
    "26731": "بوتسوانا", "26834": "إسواتيني", "26917": "جزر القمر",
    "24017": "غينيا الاستوائية", "24132": "الغابون", "24205": "جمهورية الكونغو",
    "24389": "جمهورية الكونغو الديمقراطية", "24432": "أنغولا",
    
    # أوروبا
    "44740": "المملكة المتحدة", "49155": "ألمانيا", "33630": "فرنسا",
    "34525": "إيطاليا", "34750": "إسبانيا", "38199": "صربيا",
    "38533": "كرواتيا", "38645": "سلوفينيا", "38760": "البوسنة",
    "38970": "مقدونيا", "39015": "مالطا", "39100": "سويسرا",
    "39200": "الجبل الأسود", "39320": "ألبانيا", "39440": "اليونان",
    "35550": "ألبانيا", "35863": "فنلندا", "35987": "بلغاريا",
    "36170": "المجر", "36256": "لوكسمبورغ", "36398": "رومانيا",
    "36430": "النمسا", "36550": "بلجيكا", "36668": "سلوفاكيا",
    
    # آسيا
    "97150": "الإمارات", "96655": "السعودية", "96871": "عمان",
    "96512": "الكويت", "97433": "قطر", "97320": "البحرين",
    "96170": "لبنان", "96391": "سوريا", "96277": "الأردن",
    "96470": "العراق", "96781": "اليمن", "97030": "فلسطين",
    "90531": "تركيا", "98511": "إيران", "91811": "أفغانستان",
    "91964": "باكستان", "91887": "الهند", "92887": "بنغلاديش",
    "91985": "المالديف", "92010": "موريتانيا", "92211": "الصومال",
    "99851": "أوزبكستان", "99357": "تركمانستان", "99245": "طاجيكستان",
    "99645": "قيرغيزستان", "99412": "أذربيجان", "99590": "جورجيا",
}

# أعلام الدول
COUNTRY_FLAGS = {
    "225": "🇨🇮", "232": "🇸🇱", "261": "🇲🇬", "44": "🇬🇧", "234": "🇳🇬",
    "254": "🇰🇪", "249": "🇸🇩", "49": "🇩🇪", "237": "🇨🇲", "221": "🇸🇳",
    "229": "🇧🇯", "228": "🇹🇬", "233": "🇬🇭", "256": "🇺🇬", "251": "🇪🇹",
    "258": "🇲🇿", "260": "🇿🇲", "263": "🇿🇼", "265": "🇲🇼", "266": "🇱🇸",
    "267": "🇧🇼", "268": "🇸🇿", "269": "🇰🇲", "240": "🇬🇶", "241": "🇬🇦",
    "242": "🇨🇬", "243": "🇨🇩", "244": "🇦🇴", "33": "🇫🇷", "34": "🇪🇸",
    "39": "🇮🇹", "381": "🇷🇸", "385": "🇭🇷", "386": "🇸🇮", "387": "🇧🇦",
    "389": "🇲🇰", "39": "🇲🇹", "41": "🇨🇭", "382": "🇲🇪", "383": "🇽🇰",
    "355": "🇦🇱", "358": "🇫🇮", "359": "🇧🇬", "36": "🇭🇺", "352": "🇱🇺",
    "40": "🇷🇴", "43": "🇦🇹", "32": "🇧🇪", "421": "🇸🇰", "971": "🇦🇪",
    "966": "🇸🇦", "968": "🇴🇲", "965": "🇰🇼", "974": "🇶🇦", "973": "🇧🇭",
    "961": "🇱🇧", "963": "🇸🇾", "962": "🇯🇴", "964": "🇮🇶", "967": "🇾🇪",
    "970": "🇵🇸", "90": "🇹🇷", "98": "🇮🇷", "93": "🇦🇫", "92": "🇵🇰",
    "91": "🇮🇳", "880": "🇧🇩", "960": "🇲🇻", "222": "🇲🇷", "252": "🇸🇴",
    "998": "🇺🇿", "993": "🇹🇲", "992": "🇹🇯", "996": "🇰🇬", "994": "🇦🇿",
    "995": "🇬🇪",
}

def get_flag(prefix):
    """جلب علم الدولة من البادئة مع كاش"""
    for code, flag in COUNTRY_FLAGS.items():
        if str(prefix).startswith(code):
            return flag
    return "🌍"

DEFAULT_SERVICES = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "ar": "واتساب"},
    "facebook": {"name": "Facebook", "icon": "📘", "ar": "فيسبوك"},
    "instagram": {"name": "Instagram", "icon": "📷", "ar": "انستغرام"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "ar": "تيك توك"},
    "telegram": {"name": "Telegram", "icon": "✈️", "ar": "تيليجرام"},
    "imo": {"name": "IMO", "icon": "📞", "ar": "ايمو"},
    "snapchat": {"name": "Snapchat", "icon": "👻", "ar": "سناب شات"},
    "google": {"name": "Google", "icon": "🔍", "ar": "جوجل"},
    "twitter": {"name": "Twitter/X", "icon": "🐦", "ar": "تويتر"},
    "discord": {"name": "Discord", "icon": "🎮", "ar": "ديسكورد"},
    "amazon": {"name": "Amazon", "icon": "📦", "ar": "امازون"},
    "apple": {"name": "Apple", "icon": "🍎", "ar": "ابل"},
    "microsoft": {"name": "Microsoft", "icon": "🪟", "ar": "مايكروسوفت"},
    "uber": {"name": "Uber", "icon": "🚗", "ar": "اوبر"},
    "netflix": {"name": "Netflix", "icon": "🎬", "ar": "نتفلكس"},
    "youtube": {"name": "YouTube", "icon": "▶️", "ar": "يوتيوب"},
    "tinder": {"name": "Tinder", "icon": "🔥", "ar": "تيندر"},
    "bumble": {"name": "Bumble", "icon": "🐝", "ar": "بامبل"},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "ar": "لينكد إن"},
    "pinterest": {"name": "Pinterest", "icon": "📌", "ar": "بينتريست"},
    "reddit": {"name": "Reddit", "icon": "🤖", "ar": "ريديت"},
    "twitch": {"name": "Twitch", "icon": "🎮", "ar": "تويش"},
    "spotify": {"name": "Spotify", "icon": "🎵", "ar": "سبوتيفاي"},
    "paypal": {"name": "PayPal", "icon": "💳", "ar": "باي بال"},
    "venmo": {"name": "Venmo", "icon": "💸", "ar": "فينمو"},
    "all": {"name": "All Services", "icon": "🌐", "ar": "كل الخدمات"},
}

ICONS = {
    "WhatsApp": "💬", "Telegram": "✈️", "Facebook": "📘", "Instagram": "📷",
    "TikTok": "🎵", "IMO": "📞", "Snapchat": "👻", "Google": "🔍",
    "Twitter/X": "🐦", "Discord": "🎮", "Amazon": "📦", "Apple": "🍎",
    "Microsoft": "🪟", "Uber": "🚗", "Netflix": "🎬", "YouTube": "▶️",
    "Tinder": "🔥", "Bumble": "🐝", "LinkedIn": "💼", "Pinterest": "📌",
    "Reddit": "🤖", "Twitch": "🎮", "Spotify": "🎵", "PayPal": "💳",
    "Venmo": "💸", "OTP": "🔐"
}

# ═══════════════════════════════════════════════════════════════════════════════
# API FUNCTIONS - With Advanced Retry & Timeout
# ═══════════════════════════════════════════════════════════════════════════════
def api_request(method, url, max_retries=3, **kwargs):
    """Generic API request with advanced retry"""
    for attempt in range(max_retries + 1):
        try:
            if method == "GET":
                resp = requests.get(url, timeout=kwargs.pop('timeout', 8), **kwargs)
            else:
                resp = requests.post(url, timeout=kwargs.pop('timeout', 10), **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            if attempt == max_retries:
                raise Exception("Timeout")
            time.sleep(0.5 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise e
            time.sleep(0.5 * (attempt + 1))
        except Exception as e:
            if attempt == max_retries:
                raise e
            time.sleep(0.5 * (attempt + 1))

def api_get_number(prefix):
    """جلب رقم من API مع إعادة محاولة"""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    data = api_request("POST", f"{BASE_URL}/api/v1/get-number",
                       json={"range": prefix}, headers=headers, timeout=10)
    if not data.get("success"):
        raise Exception(data.get("message", "فشل جلب الرقم"))
    return data["id"], data["number"]

def api_check_otp(number):
    """فحص OTP من API"""
    headers = {"x-api-key": API_KEY}
    try:
        data = api_request("GET", f"{BASE_URL}/api/v1/check-otp",
                          params={"number": number}, headers=headers, timeout=8)
        if data.get("success"):
            return data.get("status"), data.get("otp"), data.get("message", "")
    except:
        pass
    return None, None, ""

def api_delete_number(alloc_id):
    """حذف رقم من API"""
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        api_request("POST", f"{BASE_URL}/api/v1/delete-number",
                   json={"id": alloc_id}, headers=headers, timeout=5)
        return True
    except:
        return False

def api_get_balance():
    """جلب رصيد الموقع من API"""
    headers = {"x-api-key": API_KEY}
    try:
        data = api_request("GET", f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return data.get("balance", "0")
    except:
        return "0"

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE - With Connection Pool and Retry
# ═══════════════════════════════════════════════════════════════════════════════
_db_lock = threading.Lock()

def get_db():
    """جلب اتصال قاعدة البيانات"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """تهيئة قاعدة البيانات مع جميع الجداول"""
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        -- المستخدمين
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance REAL DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            total_requests INTEGER DEFAULT 0,
            total_otps INTEGER DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT
        );
        
        -- الأرقام النشطة
        CREATE TABLE IF NOT EXISTS active_numbers (
            alloc_id TEXT PRIMARY KEY,
            number TEXT,
            prefix TEXT,
            service TEXT,
            assigned_to INTEGER,
            created_at TEXT,
            status TEXT DEFAULT 'waiting',
            otp TEXT
        );
        
        -- سجل الأكواد
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            service TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        );
        
        -- الإحالات
        CREATE TABLE IF NOT EXISTS referrals (
            user_id INTEGER PRIMARY KEY,
            ref_code TEXT UNIQUE,
            ref_count INTEGER DEFAULT 0
        );
        
        -- قنوات الاشتراك الإجباري
        CREATE TABLE IF NOT EXISTS force_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE,
            description TEXT,
            enabled INTEGER DEFAULT 1
        );
        
        -- الإعدادات
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        
        -- الدول المخصصة
        CREATE TABLE IF NOT EXISTS custom_countries (
            prefix TEXT PRIMARY KEY,
            name TEXT
        );
        
        -- الخدمات المخصصة
        CREATE TABLE IF NOT EXISTS custom_services (
            service_key TEXT PRIMARY KEY,
            name TEXT,
            icon TEXT,
            ar_name TEXT
        );
        
        -- سجل النشاط
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TEXT
        );
        
        -- الإحصائيات اليومية
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            total_requests INTEGER DEFAULT 0,
            total_otps INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0
        );
        
        -- المدفوعات
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            address TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TEXT
        );
        
        -- الأسئلة الشائعة
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_ar TEXT,
            question_en TEXT,
            answer_ar TEXT,
            answer_en TEXT
        );
    ''')
    
    # إضافة الإعدادات الافتراضية
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('bot_offline', '0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('default_lang', 'ar')")
    
    # إضافة الدول الافتراضية
    for prefix, name in DEFAULT_COUNTRIES.items():
        c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
    
    # إضافة الخدمات الافتراضية
    for key, data in DEFAULT_SERVICES.items():
        c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)",
                  (key, data['name'], data['icon'], data['ar']))
    
    # إضافة أسئلة شائعة افتراضية
    c.executescript('''
        INSERT OR IGNORE INTO faq (id, question_ar, question_en, answer_ar, answer_en) VALUES
        (1, 'كيف أحصل على رقم؟', 'How to get a number?',
         'اختر الخدمة ثم الدولة واضغط على احصل على رقم', 'Choose service then country and click Get Number'),
        (2, 'كم تستغرق عملية استلام الكود؟', 'How long does OTP take?',
         'عادةً خلال 30-60 ثانية من طلب الرقم', 'Usually 30-60 seconds after requesting number'),
        (3, 'ماذا أفعل إذا لم يصل الكود؟', 'What if OTP doesn\'t arrive?',
         'يمكنك تغيير الرقم من الزر المخصص أو تغيير الدولة', 'You can change number or change country'),
        (4, 'كيف أربح رصيداً؟', 'How to earn credit?',
         'ادعُ أصدقاءك عبر رابط الدعوة واربح 0.05 USDT عن كل صديق', 'Invite friends via your referral link and earn 0.05 USDT per friend'),
        (5, 'ما هو الحد الأدنى للسحب؟', 'What is minimum withdrawal?',
         'الحد الأدنى للسحب هو 18 USDT', 'Minimum withdrawal is 18 USDT')
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")

init_db()

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def get_setting(key):
    """جلب إعداد من قاعدة البيانات"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    """حفظ إعداد في قاعدة البيانات"""
    conn = get_db()
    c = conn.cursor()
    c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

@cached(ttl=15)
def get_all_countries():
    """جلب جميع الدول مع كاش"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT prefix, name FROM custom_countries ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def add_country(prefix, name):
    """إضافة دولة جديدة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (prefix, name))
    conn.commit()
    conn.close()
    clear_cache()

def delete_country(prefix):
    """حذف دولة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
    conn.commit()
    conn.close()
    clear_cache()

@cached(ttl=15)
def get_all_services():
    """جلب جميع الخدمات مع كاش"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT service_key, name, icon, ar_name FROM custom_services ORDER BY ar_name")
    rows = c.fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row[0]] = {"name": row[1], "icon": row[2], "ar": row[3]}
    return result

def add_service(key, name, icon, ar_name):
    """إضافة خدمة جديدة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
    conn.commit()
    conn.close()
    clear_cache()

def delete_service(key):
    """حذف خدمة"""
    if key == "all":
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (key,))
    conn.commit()
    conn.close()
    clear_cache()

def save_user(message):
    """حفظ أو تحديث بيانات المستخدم"""
    uid = message.from_user.id
    now = datetime.now().isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("""INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
                     VALUES (?,?,?,?,?,?)""",
                  (uid, message.from_user.username, message.from_user.first_name,
                   message.from_user.last_name, now, now))
        # تسجيل مستخدم جديد
        c.execute("INSERT OR IGNORE INTO daily_stats (date, new_users) VALUES (?, 0)", (datetime.now().date().isoformat(),))
        c.execute("UPDATE daily_stats SET new_users = new_users + 1 WHERE date = ?", (datetime.now().date().isoformat(),))
    else:
        c.execute("""UPDATE users SET username=?, first_name=?, last_name=?, last_seen=?
                     WHERE user_id=?""",
                  (message.from_user.username, message.from_user.first_name,
                   message.from_user.last_name, now, uid))
    conn.commit()
    conn.close()

def get_all_users():
    """جلب جميع المستخدمين النشطين"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [r[0] for r in c.fetchall()]
    conn.close()
    return users

def release_user_number(uid):
    """تحرير رقم المستخدم"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,))
    for (aid,) in c.fetchall():
        try:
            api_delete_number(aid)
        except:
            pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
    conn.commit()
    conn.close()

def assign_number(uid, alloc_id, number, prefix, service):
    """تعيين رقم لمستخدم"""
    release_user_number(uid)
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at, status)
                 VALUES (?,?,?,?,?,?,?)""",
              (alloc_id, number, prefix, service, uid, datetime.now().isoformat(), 'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
    # تحديث الإحصائيات اليومية
    c.execute("INSERT OR IGNORE INTO daily_stats (date, total_requests) VALUES (?, 0)", (datetime.now().date().isoformat(),))
    c.execute("UPDATE daily_stats SET total_requests = total_requests + 1 WHERE date = ?", (datetime.now().date().isoformat(),))
    conn.commit()
    conn.close()

def get_all_active():
    """جلب جميع الأرقام النشطة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT alloc_id, number, prefix, service, assigned_to FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats(uid):
    """جلب إحصائيات المستخدم"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0, None, None)

def get_user_balance(uid):
    """جلب رصيد المستخدم وعدد الإحالات"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()
    c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,))
    refs = c.fetchone()
    conn.close()
    return (bal[0] if bal else 0), (refs[0] if refs else 0)

def get_ref_link(uid):
    """جلب رابط الدعوة للمستخدم"""
    ref = f"ref{uid}{random.randint(1000, 9999)}"
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
    conn.commit()
    conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

def process_referral(ref_code, new_uid):
    """معالجة إحالة جديدة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (REFERRAL_BONUS, row[0]))
        logger.info(f"💰 {new_uid} referred by {row[0]}, bonus +{REFERRAL_BONUS}")
    conn.commit()
    conn.close()

def clean_number(n):
    """تنظيف رقم الهاتف"""
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    """كشف الخدمة من النص"""
    t = str(text).lower()
    if not t:
        return "OTP"
    patterns = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستغرام", "انستا"],
        "TikTok": ["tiktok", "تيك توك"],
        "IMO": ["imo"],
        "Snapchat": ["snapchat", "سناب"],
        "Google": ["google", "gmail", "جوجل"],
        "Twitter/X": ["twitter", "تويتر"],
        "Discord": ["discord", "ديسكورد"],
        "Amazon": ["amazon", "امازون"],
        "Apple": ["apple", "ابل", "icloud"],
        "Microsoft": ["microsoft", "مايكروسوفت"],
        "Uber": ["uber", "اوبر"],
        "Netflix": ["netflix", "نتفلكس"],
        "YouTube": ["youtube", "يوتيوب"],
        "Tinder": ["tinder", "تيندر"],
        "Bumble": ["bumble", "بامبل"],
        "LinkedIn": ["linkedin", "لينكد"],
        "Pinterest": ["pinterest", "بينتريست"],
        "Reddit": ["reddit", "ريديت"],
        "Twitch": ["twitch", "تويش"],
        "Spotify": ["spotify", "سبوتيفاي"],
        "PayPal": ["paypal", "باي بال"],
        "Venmo": ["venmo", "فينمو"],
    }
    for service, keywords in patterns.items():
        for kw in keywords:
            if kw in t:
                return service
    return "OTP"

def format_time(iso_str, uid=None):
    """تنسيق الوقت"""
    if not iso_str:
        return _("unknown", uid)
    try:
        return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M")
    except:
        return iso_str

def check_subscription(uid):
    """التحقق من اشتراك المستخدم في القنوات"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return True
    for (url,) in channels:
        try:
            ch = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch, uid).status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    """إنشاء أزرار الاشتراك الإجباري"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT channel_url, description FROM force_channels WHERE enabled=1")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for url, desc in channels:
        mk.add(types.InlineKeyboardButton(f"📢 {desc or 'اشترك'}", url=url))
    mk.add(types.InlineKeyboardButton(_("check_sub_btn", uid), callback_data="check_sub"))
    return mk

def log_activity(uid, action, details=""):
    """تسجيل نشاط المستخدم"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO activity_logs (user_id, action, details, timestamp) VALUES (?,?,?,?)",
                  (uid, action, details, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT - High Performance
# ═══════════════════════════════════════════════════════════════════════════════
state_storage = StateMemoryStorage()
bot = TeleBot(BOT_TOKEN, threaded=True, num_threads=MAX_WORKERS, state_storage=state_storage)

# ═══════════════════════════════════════════════════════════════════════════════
# KEYBOARDS - Professional Design
# ═══════════════════════════════════════════════════════════════════════════════
def main_keyboard(uid):
    """الكيبورد الرئيسي"""
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.row(types.KeyboardButton(_("get_number_btn", uid)))
    kb.row(
        types.KeyboardButton(_("stats_btn", uid)),
        types.KeyboardButton(_("balance_btn", uid)),
        types.KeyboardButton(_("invite_btn", uid))
    )
    kb.row(
        types.KeyboardButton(_("traffic_btn", uid)),
        types.KeyboardButton(_("countries_btn", uid))
    )
    lang = get_lang(uid) or "ar"
    kb.add(types.KeyboardButton("🇬🇧 English" if lang == "ar" else "🇸🇦 العربية"))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(_("admin_btn", uid)))
    return kb

def services_menu(uid):
    """قائمة الخدمات"""
    services = get_all_services()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    lang = get_lang(uid) or "ar"
    for key, data in services.items():
        if key != "all":
            display_name = data['ar'] if lang == "ar" else data['name']
            buttons.append(types.InlineKeyboardButton(
                f"{data['icon']} {display_name}", callback_data=f"svc_{key}"))
    if "all" in services:
        display_name = services['all']['ar'] if lang == "ar" else services['all']['name']
        buttons.append(types.InlineKeyboardButton(
            f"{services['all']['icon']} {display_name}", callback_data="svc_all"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup

def countries_for_service(service_key, uid):
    """قائمة الدول لخدمة معينة"""
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for prefix, name in sorted(countries.items()):
        flag = get_flag(prefix)
        buttons.append(types.InlineKeyboardButton(
            f"{flag} {name}", callback_data=f"get_{prefix}_{service_key}"))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    markup.row(types.InlineKeyboardButton(_("back_to_services", uid), callback_data="menu_services"))
    return markup

def number_actions(prefix, service_key, alloc_id, uid):
    """أزرار التحكم بالرقم"""
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(_("change_number", uid), callback_data=f"change_{prefix}_{service_key}_{alloc_id}"),
        types.InlineKeyboardButton(_("change_country", uid), callback_data=f"svc_{service_key}")
    )
    mk.row(
        types.InlineKeyboardButton(_("otp_channel", uid), url="https://t.me/numhj"),
        types.InlineKeyboardButton(_("back", uid), callback_data="main_menu")
    )
    return mk

def show_home(cid, uid):
    """عرض الصفحة الرئيسية"""
    if get_setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, _("maintenance", uid))
        return
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, _("force_sub", uid), reply_markup=mk)
        return
    photo = get_setting("welcome_photo")
    txt = f"*{_('welcome_title', uid)}*\n\n{_('welcome_desc', uid)}\n\n*{_('choose_service', uid)}*"
    mk = services_menu(uid)
    try:
        if photo:
            try:
                bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
            except:
                bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
        else:
            bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    except:
        pass
    try:
        bot.send_message(cid, _("use_buttons", uid), reply_markup=main_keyboard(uid))
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# STATES - Admin States
# ═══════════════════════════════════════════════════════════════════════════════
class AdminStates(StatesGroup):
    add_country_prefix = State()
    add_country_name = State()
    add_service_key = State()
    add_service_name = State()
    add_service_icon = State()
    add_service_ar = State()
    broadcast = State()
    ban_user = State()
    unban_user = State()
    addch_url = State()
    addch_desc = State()
    photo_state = State()
    withdraw_address = State()
    faq_add_question_ar = State()
    faq_add_question_en = State()
    faq_add_answer_ar = State()
    faq_add_answer_en = State()

# ═══════════════════════════════════════════════════════════════════════════════
# /start - INSTANT RESPONSE with Language Selection
# ═══════════════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    # حفظ المستخدم في الخلفية
    executor.submit(save_user, message)
    executor.submit(log_activity, uid, "start", "Started bot")
    
    # معالجة الإحالة
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        executor.submit(process_referral, args[1], uid)
    
    current_lang = get_lang(uid)
    
    if current_lang is None:
        mk = types.InlineKeyboardMarkup(row_width=2)
        mk.add(
            types.InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
        )
        bot.send_message(
            cid,
            "🌐 *اختر لغتك / Choose your language*\n\n"
            "يرجى اختيار اللغة للمتابعة\n"
            "Please choose your language to continue",
            parse_mode="Markdown",
            reply_markup=mk
        )
        return
    
    show_home(cid, uid)

@bot.message_handler(commands=['lang'])
def change_lang_command(message):
    """تغيير اللغة عبر الأمر /lang"""
    uid = message.from_user.id
    cid = message.chat.id
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    bot.send_message(cid, _("choose_language", uid), parse_mode="Markdown", reply_markup=mk)

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SELECTION
# ═══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data in ["set_lang_ar", "set_lang_en"])
def set_language_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    lang = "ar" if call.data == "set_lang_ar" else "en"
    set_lang(uid, lang)
    msg = ("✅ *تم تعيين اللغة العربية*\n\nأهلاً بك في بوت Taker OTP!"
           if lang == "ar"
           else "✅ *Language set to English*\n\nWelcome to Taker OTP Bot!")
    bot.edit_message_text(msg, cid, mid, parse_mode="Markdown")
    show_home(cid, uid)

# ═══════════════════════════════════════════════════════════════════════════════
# BOTTOM KEYBOARD BUTTONS - ULTRA FAST
# ═══════════════════════════════════════════════════════════════════════════════
BUTTON_TEXTS = {
    "get_number": ["📱 احصل على رقم", "📱 Get Number"],
    "countries": ["🌍 الدول", "🌍 Countries"],
    "stats": ["📊 إحصائياتي", "📊 My Stats"],
    "balance": ["💰 رصيدي", "💰 Balance"],
    "invite": ["🤝 دعوة", "🤝 Invite"],
    "traffic": ["🟢 المرور", "🟢 Traffic"],
    "admin": ["⚙️ تحكم", "⚙️ Admin"],
}

@bot.message_handler(func=lambda m: any(m.text in v for v in BUTTON_TEXTS.values()) or m.text in ["🌐 English", "🌐 العربية"])
def bottom_buttons(message):
    uid = message.from_user.id
    cid = message.chat.id
    text = message.text
    
    # تغيير اللغة
    if text in ["🌐 English", "🌐 العربية"]:
        new_lang = "en" if text == "🌐 English" else "ar"
        set_lang(uid, new_lang)
        resp = _("language_changed_ar", uid) if new_lang == "ar" else _("language_changed_en", uid)
        bot.send_message(cid, resp, reply_markup=main_keyboard(uid))
        return
    
    # زر احصل على رقم
    if text in BUTTON_TEXTS["get_number"]:
        bot.send_message(cid, f"*{_('choose_service', uid)}*", parse_mode="Markdown", reply_markup=services_menu(uid))
    
    # زر الدول
    elif text in BUTTON_TEXTS["countries"]:
        countries = get_all_countries()
        services = get_all_services()
        txt = f"*{_('countries_services', uid)}*\n\n"
        for prefix, name in sorted(countries.items()):
            txt += f"• {get_flag(prefix)} `{prefix}` - {name}\n"
        txt += f"\n*{_('countries_count', uid)}:* {len(countries)}\n"
        txt += f"*{_('services_count', uid)}:* {len(services)}"
        bot.send_message(cid, txt, parse_mode="Markdown")
    
    # زر الإحصائيات
    elif text in BUTTON_TEXTS["stats"]:
        requests, otps, first, last = get_user_stats(uid)
        msg = (f"*{_('my_stats', uid)}*\n\n"
               f"🔷 *{_('total_requests', uid)}:* `{requests}`\n"
               f"🔷 *{_('otps_received', uid)}:* `{otps}`\n"
               f"🔷 *{_('first_use', uid)}:* `{format_time(first, uid)}`\n"
               f"🔷 *{_('last_use', uid)}:* `{format_time(last, uid)}`")
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    # زر الرصيد
    elif text in BUTTON_TEXTS["balance"]:
        bal, refs = get_user_balance(uid)
        site_bal = api_get_balance()
        msg = (f"*{_('my_balance', uid)}*\n\n"
               f"💎 *{_('your_balance', uid)}:* `{bal:.3f} USDT`\n"
               f"👥 *{_('referrals', uid)}:* `{refs}`\n"
               f"🏦 *{_('site_balance', uid)}:* `{site_bal}`\n"
               f"🏦 *{_('min_withdraw', uid)}:* `{MIN_WITHDRAW} USDT`\n\n"
               f"{_('earn_tip', uid)}")
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    # زر الدعوة
    elif text in BUTTON_TEXTS["invite"]:
        link = get_ref_link(uid)
        msg = (f"*{_('invite_friends', uid)}*\n\n"
               f"{_('your_link', uid).replace('{}', link)}\n\n"
               f"{_('share_link', uid)}")
        bot.send_message(cid, msg, parse_mode="Markdown")
    
    # زر المرور
    elif text in BUTTON_TEXTS["traffic"]:
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT prefix, service, COUNT(*) 
                     FROM active_numbers WHERE status='waiting' 
                     GROUP BY prefix, service ORDER BY COUNT(*) DESC LIMIT 15""")
        rows = c.fetchall()
        # إحصائيات إضافية
        c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
        total = c.fetchone()[0]
        conn.close()
        
        if not rows:
            txt = f"*{_('active_numbers', uid)}*\n\n{_('no_active_numbers', uid)}"
        else:
            lines = [f"*{_('active_numbers', uid)}*\n📊 *{_('total_active', uid)}:* {total}\n"]
            for prefix, svc, cnt in rows:
                flag = get_flag(prefix)
                name = get_all_countries().get(prefix, prefix)
                svc_icon = get_all_services().get(svc, {}).get("icon", "🔐")
                pct = int((cnt / total) * 100) if total > 0 else 0
                bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
                lines.append(f"{flag} {name} {svc_icon}: `{cnt}` [{bar}] {pct}%")
            txt = "\n".join(lines)
        bot.send_message(cid, txt, parse_mode="Markdown")
    
    # زر التحكم (للأدمن فقط)
    elif text in BUTTON_TEXTS["admin"] and uid in ADMIN_IDS:
        admin_panel(message)

# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS - INSTANT RESPONSE
# ═══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, _("check_sub_ok", uid))
        show_home(call.message.chat.id, uid)
    else:
        bot.answer_callback_query(call.id, _("check_sub_fail", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    service_key = call.data.split("_", 1)[1]
    services = get_all_services()
    lang = get_lang(uid) or "ar"
    display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
    bot.edit_message_text(
        f"*{_('choose_country', uid).replace('{}', display_name)}:*",
        cid, mid, parse_mode="Markdown",
        reply_markup=countries_for_service(service_key, uid)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    parts = call.data.split("_", 2)
    prefix = parts[1]
    service_key = parts[2] if len(parts) > 2 else "all"
    
    def process():
        try:
            release_user_number(uid)
            alloc_id, number = api_get_number(prefix)
            number = clean_number(number)
            assign_number(uid, alloc_id, number, prefix, service_key)
            
            countries = get_all_countries()
            services = get_all_services()
            lang = get_lang(uid) or "ar"
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
            now = datetime.now().strftime("%H:%M")
            
            msg = (f"*{_('new_number', uid)}*\n\n"
                   f"📞 *{_('number', uid)}:* `+{number}`\n"
                   f"🌍 *{_('country', uid)}:* {flag} {name}\n"
                   f"🛠 *{_('service', uid)}:* {display_name}\n"
                   f"🕒 *{_('time', uid)}:* {now}\n"
                   f"⏳ *{_('status_waiting', uid)}*")
            
            bot.edit_message_text(msg, cid, mid, parse_mode="Markdown",
                                 reply_markup=number_actions(prefix, service_key, alloc_id, uid))
            executor.submit(log_activity, uid, "get_number", f"{prefix} - {service_key}")
            
        except Exception as e:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)
    
    bot.answer_callback_query(call.id)
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    parts = call.data.split("_", 3)
    prefix = parts[1]
    service_key = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    def process():
        try:
            if old_alloc:
                api_delete_number(old_alloc)
                conn = get_db()
                conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (old_alloc,))
                conn.commit()
                conn.close()
            
            release_user_number(uid)
            alloc_id, number = api_get_number(prefix)
            number = clean_number(number)
            assign_number(uid, alloc_id, number, prefix, service_key)
            
            countries = get_all_countries()
            services = get_all_services()
            lang = get_lang(uid) or "ar"
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
            now = datetime.now().strftime("%H:%M")
            
            msg = (f"*{_('change_number_title', uid)}*\n\n"
                   f"📞 *{_('new_number_msg', uid)}:* `+{number}`\n"
                   f"🌍 *{_('country', uid)}:* {flag} {name}\n"
                   f"🛠 *{_('service', uid)}:* {display_name}\n"
                   f"🕒 *{_('time', uid)}:* {now}\n"
                   f"⏳ *{_('status_waiting', uid)}*")
            
            bot.edit_message_text(msg, cid, mid, parse_mode="Markdown",
                                 reply_markup=number_actions(prefix, service_key, alloc_id, uid))
            
        except Exception as e:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
            bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)
    
    bot.answer_callback_query(call.id)
    executor.submit(process)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    if call.data == "menu_services":
        bot.edit_message_text(f"*{_('choose_service', uid)}*", cid, mid,
                             parse_mode="Markdown", reply_markup=services_menu(uid))
    else:
        try:
            bot.delete_message(cid, mid)
        except:
            pass
        show_home(cid, uid)

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL - Complete
# ═══════════════════════════════════════════════════════════════════════════════
def admin_panel(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = _("admin_open", uid) if get_setting("maintenance") != "1" else _("admin_maint", uid)
    
    # الصف الأول - حالة البوت
    markup.add(types.InlineKeyboardButton(_("admin_status", uid).replace("{}", status), callback_data="toggle_maint"))
    
    # الدول والخدمات
    markup.row(
        types.InlineKeyboardButton(_("add_country_btn", uid), callback_data="add_country"),
        types.InlineKeyboardButton(_("del_country_btn", uid), callback_data="del_country"))
    markup.row(
        types.InlineKeyboardButton(_("add_service_btn", uid), callback_data="add_service"),
        types.InlineKeyboardButton(_("del_service_btn", uid), callback_data="del_service"))
    
    # الإدارة
    markup.row(
        types.InlineKeyboardButton(_("broadcast_btn", uid), callback_data="broadcast"),
        types.InlineKeyboardButton(_("users_btn", uid), callback_data="users_list"))
    markup.row(
        types.InlineKeyboardButton(_("ban_btn", uid), callback_data="ban"),
        types.InlineKeyboardButton(_("unban_btn", uid), callback_data="unban"))
    
    # إضافات
    markup.row(
        types.InlineKeyboardButton(_("force_sub_btn", uid), callback_data="force_sub"),
        types.InlineKeyboardButton(_("photo_btn", uid), callback_data="set_photo"))
    markup.row(
        types.InlineKeyboardButton(_("report_btn", uid), callback_data="full_report"),
        types.InlineKeyboardButton(_("clear_btn", uid), callback_data="clear_data"))
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("❓ أسئلة شائعة", callback_data="admin_faq"))
    markup.row(
        types.InlineKeyboardButton(_("exit_btn", uid), callback_data="main_menu"))
    
    bot.send_message(message.chat.id, f"*{_('admin_header', uid)}*",
                    parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ تم التغيير")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*➕ إضافة دولة جديدة*\n\nأرسل كود الدولة (مثال: 966):", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.add_country_prefix, cid)

@bot.message_handler(state=AdminStates.add_country_prefix)
def add_country_prefix(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['prefix'] = message.text.strip()
    bot.send_message(cid, "أرسل اسم الدولة:")
    bot.set_state(uid, AdminStates.add_country_name, cid)

@bot.message_handler(state=AdminStates.add_country_name)
def add_country_name(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        prefix = data['prefix']
    add_country(prefix, message.text.strip())
    bot.send_message(cid, f"✅ تم إضافة `{message.text.strip()}` ({prefix})", parse_mode="Markdown")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = get_all_countries()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for prefix, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{get_flag(prefix)} {name}", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*🗑️ حذف دولة*\nاختر الدولة للحذف:", call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    delete_country(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_service" and c.from_user.id in ADMIN_IDS)
def add_service_start(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*➕ إضافة خدمة جديدة*\n\nأرسل مفتاح الخدمة (مثال: tinder):", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.add_service_key, cid)

@bot.message_handler(state=AdminStates.add_service_key)
def add_service_key(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['key'] = message.text.strip().lower()
    bot.send_message(cid, "أرسل الاسم بالإنجليزية:")
    bot.set_state(uid, AdminStates.add_service_name, cid)

@bot.message_handler(state=AdminStates.add_service_name)
def add_service_name(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['name'] = message.text.strip()
    bot.send_message(cid, "أرسل الأيقونة (إيموجي):")
    bot.set_state(uid, AdminStates.add_service_icon, cid)

@bot.message_handler(state=AdminStates.add_service_icon)
def add_service_icon(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['icon'] = message.text.strip()
    bot.send_message(cid, "أرسل الاسم بالعربية:")
    bot.set_state(uid, AdminStates.add_service_ar, cid)

@bot.message_handler(state=AdminStates.add_service_ar)
def add_service_ar(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        add_service(data['key'], data['name'], data['icon'], message.text.strip())
    bot.send_message(cid, f"✅ تم إضافة {data['icon']} {message.text.strip()}", parse_mode="Markdown")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data == "del_service" and c.from_user.id in ADMIN_IDS)
def del_service_start(call):
    services = get_all_services()
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, data in services.items():
        if key != "all":
            markup.add(types.InlineKeyboardButton(f"{data['icon']} {data['ar']}", callback_data=f"delservice_{key}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*🗑️ حذف خدمة*\nاختر الخدمة للحذف:", call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delservice_") and c.from_user.id in ADMIN_IDS)
def del_service_confirm(call):
    delete_service(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*📢 إذاعة*\nأرسل الرسالة:", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.broadcast, cid)

@bot.message_handler(state=AdminStates.broadcast, content_types=['text', 'photo', 'video', 'document', 'audio'])
def broadcast_exec(message):
    uid = message.from_user.id
    cid = message.chat.id
    users = get_all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, cid, message.message_id)
            cnt += 1
        except:
            pass
    bot.send_message(cid, f"✅ تم الإرسال إلى `{cnt}` مستخدم", parse_mode="Markdown")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"] and c.from_user.id in ADMIN_IDS)
def ban_unban_prompt(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    txt = "*🚫 حظر مستخدم*\nأرسل ID المستخدم:" if call.data == "ban" else "*✅ فك حظر مستخدم*\nأرسل ID المستخدم:"
    bot.edit_message_text(txt, cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.ban_user if call.data == "ban" else AdminStates.unban_user, cid)

@bot.message_handler(state=AdminStates.ban_user)
def ban_exec(message):
    uid = message.from_user.id
    cid = message.chat.id
    try:
        target = int(message.text)
        conn = get_db()
        conn.cursor().execute("UPDATE users SET is_banned=1 WHERE user_id=?", (target,))
        conn.commit()
        conn.close()
        bot.send_message(cid, f"✅ تم حظر `{target}`", parse_mode="Markdown")
        executor.submit(log_activity, uid, "ban", f"Banned {target}")
    except:
        bot.send_message(cid, "❌ ID غير صحيح")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.message_handler(state=AdminStates.unban_user)
def unban_exec(message):
    uid = message.from_user.id
    cid = message.chat.id
    try:
        target = int(message.text)
        conn = get_db()
        conn.cursor().execute("UPDATE users SET is_banned=0 WHERE user_id=?", (target,))
        conn.commit()
        conn.close()
        bot.send_message(cid, f"✅ تم فك الحظر عن `{target}`", parse_mode="Markdown")
        executor.submit(log_activity, uid, "unban", f"Unbanned {target}")
    except:
        bot.send_message(cid, "❌ ID غير صحيح")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, last_seen FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 30")
    rows = c.fetchall()
    conn.close()
    msg = "*👥 قائمة المستخدمين (آخر 30):*\n\n" if rows else "لا يوجد مستخدمين."
    for uid, uname, fname, last_seen in rows:
        name = f"@{uname}" if uname else fname or str(uid)
        seen = format_time(last_seen, None)[:10]
        msg += f"• `{uid}` - {name} (آخر ظهور: {seen})\n"
    if len(msg) > 4000:
        msg = msg[:4000] + "...\n(تم اختصار القائمة)"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, channel_url, description, enabled FROM force_channels")
    channels = c.fetchall()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    for ch_id, url, desc, enabled in channels:
        st = "✅" if enabled else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {desc or url[:20]}", callback_data=f"editch_{ch_id}"))
    markup.row(
        types.InlineKeyboardButton("➕ إضافة", callback_data="addch"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    )
    bot.edit_message_text("*🔗 الاشتراك الإجباري*\nالقنوات النشطة:", call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.addch_url, cid)

@bot.message_handler(state=AdminStates.addch_url)
def addch_url(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['url'] = message.text.strip()
    bot.send_message(cid, "أرسل وصف القناة:")
    bot.set_state(uid, AdminStates.addch_desc, cid)

@bot.message_handler(state=AdminStates.addch_desc)
def addch_desc(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        url = data['url']
    conn = get_db()
    conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)",
                         (url, message.text.strip()))
    conn.commit()
    conn.close()
    bot.send_message(cid, "✅ تم الإضافة")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    conn = get_db()
    conn.cursor().execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    conn.commit()
    conn.close()
    force_sub_menu(call)

@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*🖼️ صورة الترحيب*\nأرسل الصورة:", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.photo_state, cid)

@bot.message_handler(state=AdminStates.photo_state, content_types=['photo'])
def save_photo(message):
    uid = message.from_user.id
    cid = message.chat.id
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(cid, "✅ تم حفظ الصورة")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data == "full_report" and c.from_user.id in ADMIN_IDS)
def full_report(call):
    """تقرير شامل"""
    conn = get_db()
    c = conn.cursor()
    
    # إحصائيات المستخدمين
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned=1")
    banned_users = c.fetchone()[0]
    
    # إحصائيات الأرقام
    c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
    active_numbers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM otp_logs")
    total_otps = c.fetchone()[0]
    
    # أشهر الخدمات
    c.execute("""SELECT service, COUNT(*) as cnt FROM otp_logs 
                 GROUP BY service ORDER BY cnt DESC LIMIT 10""")
    top_services = c.fetchall()
    
    # أشهر الدول
    c.execute("""SELECT prefix, COUNT(*) as cnt FROM active_numbers 
                 GROUP BY prefix ORDER BY cnt DESC LIMIT 10""")
    top_countries = c.fetchall()
    
    # آخر 20 نشاط
    c.execute("""SELECT user_id, action, details, timestamp FROM activity_logs 
                 ORDER BY id DESC LIMIT 20""")
    recent_activity = c.fetchall()
    
    conn.close()
    
    # إنشاء التقرير
    report = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    تقرير شامل - Taker OTP Bot               ║
║                     {datetime.now().strftime('%Y-%m-%d %H:%M')}                ║
╚═══════════════════════════════════════════════════════════════╝

📊 إحصائيات عامة
────────────────────
👥 إجمالي المستخدمين: {total_users}
🚫 المستخدمين المحظورين: {banned_users}
🟢 الأرقام النشطة: {active_numbers}
🔐 إجمالي الأكواد المستلمة: {total_otps}

📈 أشهر الخدمات
────────────────────
"""
    for svc, cnt in top_services:
        report += f"   {svc}: {cnt}\n"
    
    report += f"""
🌍 أشهر الدول
────────────────────
"""
    for prefix, cnt in top_countries:
        name = get_all_countries().get(prefix, prefix)
        report += f"   {name} ({prefix}): {cnt}\n"
    
    report += f"""
📋 آخر النشاطات
────────────────────
"""
    for uid, action, details, ts in recent_activity:
        report += f"   {ts[:16]} - {uid}: {action} {details}\n"
    
    # إرسال التقرير كملف
    try:
        file_data = BytesIO(report.encode('utf-8'))
        bot.send_document(call.message.chat.id, ("report.txt", file_data),
                         caption="📄 *التقرير الشامل*\nتم إنشاء التقرير بنجاح",
                         parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطأ في إنشاء التقرير: {e}")
    
    bot.answer_callback_query(call.id, "✅ تم إنشاء التقرير")

@bot.callback_query_handler(func=lambda c: c.data == "admin_stats" and c.from_user.id in ADMIN_IDS)
def admin_stats(call):
    """إحصائيات البوت"""
    conn = get_db()
    c = conn.cursor()
    
    # إحصائيات المستخدمين
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned=0")
    active = c.fetchone()[0]
    
    # إحصائيات اليوم
    today = datetime.now().date().isoformat()
    c.execute("SELECT total_requests, total_otps, new_users FROM daily_stats WHERE date=?", (today,))
    daily = c.fetchone()
    
    # إحصائيات الأرقام
    c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
    waiting = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='success'")
    success = c.fetchone()[0]
    
    # إجمالي الأكواد
    c.execute("SELECT COUNT(*) FROM otp_logs")
    total_otps = c.fetchone()[0]
    
    conn.close()
    
    msg = f"""
*📊 إحصائيات البوت*

👥 *المستخدمين*
└─ إجمالي: `{total}`
└─ نشط: `{active}`

📅 *اليوم ({datetime.now().strftime('%d-%m-%Y')})*
└─ طلبات: `{daily[0] if daily else 0}`
└─ أكواد: `{daily[1] if daily else 0}`
└─ مستخدمين جدد: `{daily[2] if daily else 0}`

🔄 *الأرقام النشطة*
└─ في انتظار: `{waiting}`
└─ منتهية: `{success}`

🔐 *إجمالي الأكواد*
└─ مستلمة: `{total_otps}`
"""
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "admin_faq" and c.from_user.id in ADMIN_IDS)
def admin_faq(call):
    """إدارة الأسئلة الشائعة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, question_ar, question_en FROM faq ORDER BY id")
    faqs = c.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for fid, q_ar, q_en in faqs:
        markup.add(types.InlineKeyboardButton(f"❓ {q_ar[:20]}", callback_data=f"faq_edit_{fid}"))
    markup.row(
        types.InlineKeyboardButton("➕ إضافة سؤال", callback_data="faq_add"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    )
    bot.edit_message_text("*❓ الأسئلة الشائعة*\nاختر سؤالاً للتعديل:", call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "faq_add" and c.from_user.id in ADMIN_IDS)
def faq_add_start(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    bot.edit_message_text("*➕ إضافة سؤال جديد*\nأرسل السؤال بالعربية:", cid, mid, parse_mode="Markdown")
    bot.set_state(uid, AdminStates.faq_add_question_ar, cid)

@bot.message_handler(state=AdminStates.faq_add_question_ar)
def faq_add_question_ar(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['q_ar'] = message.text.strip()
    bot.send_message(cid, "أرسل السؤال بالإنجليزية:")
    bot.set_state(uid, AdminStates.faq_add_question_en, cid)

@bot.message_handler(state=AdminStates.faq_add_question_en)
def faq_add_question_en(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['q_en'] = message.text.strip()
    bot.send_message(cid, "أرسل الإجابة بالعربية:")
    bot.set_state(uid, AdminStates.faq_add_answer_ar, cid)

@bot.message_handler(state=AdminStates.faq_add_answer_ar)
def faq_add_answer_ar(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        data['a_ar'] = message.text.strip()
    bot.send_message(cid, "أرسل الإجابة بالإنجليزية:")
    bot.set_state(uid, AdminStates.faq_add_answer_en, cid)

@bot.message_handler(state=AdminStates.faq_add_answer_en)
def faq_add_answer_en(message):
    uid = message.from_user.id
    cid = message.chat.id
    with bot.retrieve_data(uid, cid) as data:
        conn = get_db()
        conn.cursor().execute("""INSERT INTO faq (question_ar, question_en, answer_ar, answer_en)
                                 VALUES (?,?,?,?)""",
                             (data['q_ar'], data['q_en'], data['a_ar'], message.text.strip()))
        conn.commit()
        conn.close()
    bot.send_message(cid, "✅ تم إضافة السؤال")
    bot.delete_state(uid, cid)
    admin_panel(message)

@bot.callback_query_handler(func=lambda c: c.data.startswith("faq_edit_") and c.from_user.id in ADMIN_IDS)
def faq_edit(call):
    fid = int(call.data.split("_")[2])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM faq WHERE id=?", (fid,))
    faq = c.fetchone()
    conn.close()
    
    if not faq:
        bot.answer_callback_query(call.id, "❌ غير موجود")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"faq_del_{fid}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_faq"))
    
    msg = f"""
*❓ السؤال #{fid}*

🇸🇦 العربي:
{faq[1]}

🇬🇧 English:
{faq[2]}

🇸🇦 الإجابة:
{faq[3]}

🇬🇧 Answer:
{faq[4]}
"""
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("faq_del_") and c.from_user.id in ADMIN_IDS)
def faq_delete(call):
    fid = int(call.data.split("_")[2])
    conn = get_db()
    conn.cursor().execute("DELETE FROM faq WHERE id=?", (fid,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_faq(call)

@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    conn = get_db()
    c = conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals", "activity_logs"]:
        c.execute(f"DELETE FROM {t}")
    # إعادة تعيين الإحصائيات اليومية
    c.execute("DELETE FROM daily_stats")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ═══════════════════════════════════════════════════════════════════════════════
# FAQ - عرض الأسئلة الشائعة للمستخدمين
# ═══════════════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=['faq'])
def faq_command(message):
    uid = message.from_user.id
    cid = message.chat.id
    lang = get_lang(uid) or "ar"
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT question_ar, question_en, answer_ar, answer_en FROM faq")
    faqs = c.fetchall()
    conn.close()
    
    if not faqs:
        bot.send_message(cid, "❌ لا توجد أسئلة شائعة حالياً")
        return
    
    msg = f"*❓ الأسئلة الشائعة*\n\n"
    for i, (q_ar, q_en, a_ar, a_en) in enumerate(faqs, 1):
        q = q_ar if lang == "ar" else q_en
        a = a_ar if lang == "ar" else a_en
        msg += f"*{i}. {q}*\n{a}\n\n"
    
    bot.send_message(cid, msg, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════════════════════
# OTP SENDER - ROBUST with Auto Delete
# ═══════════════════════════════════════════════════════════════════════════════
def send_otp_to_groups(number, prefix, country, flag, detected_service, ic, code):
    """إرسال OTP للجروبات مع حذف تلقائي"""
    # إخفاء الرقم
    masked = f"{number[:4]}****{number[-3:]}" if len(number) > 7 else number
    group_msg = (f"*🔐 كود جديد*\n\n"
                 f"🌍 {flag} {country} | {ic} {detected_service}\n"
                 f"📞 `{masked}`\n"
                 f"🔢 `{code}`")
    
    for cid in CHAT_IDS:
        for attempt in range(3):
            try:
                logger.info(f"📤 إرسال للجروب {cid} (محاولة {attempt+1})")
                sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                logger.info(f"✅ تم الإرسال للجروب {cid} - msg_id: {sent.message_id}")
                
                # حذف تلقائي بعد نصف ساعة
                executor.submit(lambda: (time.sleep(DELETE_AFTER), 
                                        bot.delete_message(cid, sent.message_id)))
                break
            except Exception as e:
                logger.error(f"❌ محاولة {attempt+1} فشلت للجروب {cid}: {e}")
                time.sleep(1 * (attempt + 1))

# ═══════════════════════════════════════════════════════════════════════════════
# OTP LOOP - OPTIMIZED with 32 Threads
# ═══════════════════════════════════════════════════════════════════════════════
def otp_loop():
    """حلقة فحص OTP الرئيسية"""
    logger.info("🔄 بدء حلقة OTP...")
    while True:
        try:
            active = get_all_active()
            if not active:
                time.sleep(OTP_CHECK_INTERVAL)
                continue
            
            # معالجة متوازية للأرقام النشطة
            futures = []
            for alloc_id, number, prefix, service_key, uid in active:
                futures.append(executor.submit(process_single_otp, alloc_id, number, prefix, service_key, uid))
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"خطأ في future: {e}")
                    
        except Exception as e:
            logger.error(f"خطأ في حلقة OTP: {e}")
        
        time.sleep(OTP_CHECK_INTERVAL)

def process_single_otp(alloc_id, number, prefix, service_key, uid):
    """معالجة رقم واحد للتحقق من OTP"""
    try:
        status, otp, raw_msg = api_check_otp(number)
        
        if status == "success" and otp:
            logger.info(f"🎯 تم استقبال كود: {number} -> {otp}")
            
            # كشف الخدمة
            detected_service = detect_service(raw_msg) if raw_msg else "OTP"
            if detected_service == "OTP":
                services = get_all_services()
                detected_service = services.get(service_key, {}).get("name", "OTP")
            
            ic = ICONS.get(detected_service, "🔐")
            countries = get_all_countries()
            country = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            code = f"{otp[:3]}-{otp[3:]}" if len(otp) > 3 else otp
            
            # إرسال للمستخدم
            if uid:
                try:
                    user_msg = (f"*{_('otp_received', uid)}*\n\n"
                               f"📞 *{_('number', uid)}:* `+{number}`\n"
                               f"🌍 *{_('country', uid)}:* {flag} {country}\n"
                               f"{ic} *{_('app', uid)}:* {detected_service}\n"
                               f"🔢 *{_('code', uid)}:* `{code}`\n\n"
                               f"📋 {_('copy_code', uid)}")
                    bot.send_message(uid, user_msg, parse_mode="Markdown")
                    logger.info(f"✅ تم إرسال الكود للمستخدم {uid}")
                    executor.submit(log_activity, uid, "otp_received", f"{number} - {otp}")
                except Exception as e:
                    logger.error(f"❌ فشل إرسال للمستخدم {uid}: {e}")
            
            # إرسال للجروب
            send_otp_to_groups(number, prefix, country, flag, detected_service, ic, code)
            
            # تحديث قاعدة البيانات
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
            if uid:
                c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
                # تحديث الإحصائيات اليومية
                c.execute("INSERT OR IGNORE INTO daily_stats (date, total_otps) VALUES (?, 0)", (datetime.now().date().isoformat(),))
                c.execute("UPDATE daily_stats SET total_otps = total_otps + 1 WHERE date = ?", (datetime.now().date().isoformat(),))
            c.execute("""INSERT INTO otp_logs (number, otp, service, full_message, timestamp, assigned_to)
                         VALUES (?,?,?,?,?,?)""",
                      (number, otp, detected_service, raw_msg, datetime.now().isoformat(), uid))
            conn.commit()
            
            # حذف من API و DB
            api_delete_number(alloc_id)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
            conn.commit()
            conn.close()
            
        elif status == "expired":
            logger.info(f"⏰ انتهى الرقم: {number}")
            api_delete_number(alloc_id)
            conn = get_db()
            conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
            conn.commit()
            conn.close()
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرقم {number}: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# FLASK - Web Server with Full API Proxy
# ═══════════════════════════════════════════════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Taker OTP Bot</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: linear-gradient(135deg, #0a0a1a, #1a0a2e, #0a1a2e);
                color: #00ff88;
                font-family: 'Courier New', monospace;
                text-align: center;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                padding: 40px;
                border: 2px solid #00ff88;
                border-radius: 20px;
                background: rgba(0,0,0,0.7);
                box-shadow: 0 0 60px rgba(0,255,136,0.1);
                animation: glow 2s ease-in-out infinite alternate;
            }
            @keyframes glow {
                from { box-shadow: 0 0 20px rgba(0,255,136,0.2); }
                to { box-shadow: 0 0 60px rgba(0,255,136,0.4); }
            }
            .logo {
                font-size: 4em;
                animation: pulse 1.5s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            h1 {
                font-size: 3em;
                margin: 20px 0;
                background: linear-gradient(45deg, #00ff88, #00ccff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1.2em;
                color: #00ccff;
                margin: 10px 0;
            }
            .features {
                text-align: left;
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #00ff8866;
                border-radius: 10px;
            }
            .features li {
                list-style: none;
                padding: 8px 0;
                color: #ffffffcc;
                font-size: 1.1em;
            }
            .features li:before {
                content: "⚡";
                margin-right: 10px;
            }
            .status {
                display: inline-block;
                padding: 8px 30px;
                border-radius: 20px;
                background: #00ff8822;
                border: 1px solid #00ff88;
                color: #00ff88;
                font-size: 1.2em;
                margin: 10px 0;
            }
            .footer {
                margin-top: 30px;
                color: #ffffff66;
                font-size: 0.9em;
            }
            .footer a {
                color: #00ccff;
                text-decoration: none;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-box {
                background: rgba(0,255,136,0.05);
                padding: 15px;
                border-radius: 10px;
                border: 1px solid rgba(0,255,136,0.2);
            }
            .stat-box .num {
                font-size: 2em;
                color: #00ff88;
            }
            .stat-box .label {
                font-size: 0.8em;
                color: #ffffff88;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">⚡</div>
            <h1>TAKER OTP BOT</h1>
            <div class="subtitle">🚀 Ultimate OTP Service v5.0</div>
            <div class="status">🟢 ONLINE</div>
            
            <div class="features">
                <li>🔐 احصل على أرقام وهمية لتفعيل الخدمات</li>
                <li>🌍 أكثر من 50 دولة مع أعلام حقيقية</li>
                <li>📱 أكثر من 25 خدمة مدعومة</li>
                <li>💰 نظام إحالات مع أرباح USDT</li>
                <li>⚡ سرعة فائقة مع 32 Thread متوازي</li>
                <li>🌐 دعم كامل للعربية والإنجليزية</li>
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="num">50+</div>
                    <div class="label">🌍 دولة</div>
                </div>
                <div class="stat-box">
                    <div class="num">25+</div>
                    <div class="label">📱 خدمة</div>
                </div>
                <div class="stat-box">
                    <div class="num">32</div>
                    <div class="label">🧵 Thread</div>
                </div>
                <div class="stat-box">
                    <div class="num">⚡</div>
                    <div class="label">🚀 Ultra Fast</div>
                </div>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="https://t.me/Taker_OTP_BOT" style="color:#00ff88;font-size:1.5em;text-decoration:none;border:2px solid #00ff88;padding:10px 30px;border-radius:30px;display:inline-block;">
                    🤖 افتح البوت
                </a>
            </div>
            
            <div class="footer">
                👨‍💻 Developed by <a href="https://t.me/hackerTaker">@hackerTaker</a><br>
                🔗 API: <a href="http://xwdsms.org">xwdsms.org</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """فحص الصحة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM active_numbers")
    active = c.fetchone()[0]
    conn.close()
    return jsonify({
        "status": "ok",
        "uptime": str(datetime.now()),
        "users": users,
        "active_numbers": active,
        "version": "5.0"
    }), 200

@app.route('/api/v1/get-number', methods=['POST'])
def flask_get_number():
    """Proxy API - Get Number"""
    try:
        data = flask_request.get_json()
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        resp = requests.post(f"{BASE_URL}/api/v1/get-number",
                           json={"range": data.get("range", "")}, headers=headers, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/check-otp', methods=['GET'])
def flask_check_otp():
    """Proxy API - Check OTP"""
    try:
        number = flask_request.args.get("number", "")
        headers = {"x-api-key": API_KEY}
        resp = requests.get(f"{BASE_URL}/api/v1/check-otp",
                          params={"number": number}, headers=headers, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/balance', methods=['GET'])
def flask_balance():
    """Proxy API - Balance"""
    try:
        headers = {"x-api-key": API_KEY}
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"balance": "0"}), 500

@app.route('/api/v1/delete-number', methods=['POST'])
def flask_delete_number():
    """Proxy API - Delete Number"""
    try:
        data = flask_request.get_json()
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        resp = requests.post(f"{BASE_URL}/api/v1/delete-number",
                           json={"id": data.get("id")}, headers=headers, timeout=5)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/stats', methods=['GET'])
def flask_stats():
    """إحصائيات البوت العامة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM active_numbers")
    active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM otp_logs")
    otps = c.fetchone()[0]
    conn.close()
    return jsonify({
        "users": users,
        "active_numbers": active,
        "total_otps": otps,
        "status": "online"
    }), 200

def run_web():
    """تشغيل خادم Flask"""
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Flask Web Server على المنفذ {port}")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN - START EVERYTHING
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║     ⚡ TAKER OTP BOT - ULTIMATE MEGA EDITION v5.0                       ║
    ║     👨‍💻 Developer: @hackerTaker                                          ║
    ║     🔗 API: xwdsms.org                                                  ║
    ║     🌐 Languages: العربية / English                                    ║
    ║     🧵 Workers: 32 Threads                                             ║
    ║     ⏱️  Auto Delete: 1800s (نصف ساعة)                                   ║
    ║                                                                          ║
    ║     📋 الميزات:                                                         ║
    ║     ✅ 50+ دولة مع أعلام                                                ║
    ║     ✅ 25+ خدمة مع أيقونات                                              ║
    ║     ✅ نظام إحالات مع أرباح USDT                                        ║
    ║     ✅ لوحة تحكم كاملة                                                   ║
    ║     ✅ تقارير شاملة                                                     ║
    ║     ✅ أسئلة شائعة                                                      ║
    ║     ✅ صورة ترحيب                                                      ║
    ║     ✅ اشتراك إجباري                                                   ║
    ║     ✅ حذف تلقائي بعد نصف ساعة                                         ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("=" * 60)
    logger.info(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"📢 Groups: {CHAT_IDS}")
    logger.info(f"👑 Admins: {ADMIN_IDS}")
    logger.info(f"⏱️  Delete OTP after: {DELETE_AFTER}s")
    logger.info(f"🧵 Thread Pool: {MAX_WORKERS} workers")
    logger.info(f"⏰ OTP Check Interval: {OTP_CHECK_INTERVAL}s")
    logger.info("=" * 60)
    
    # تشغيل Flask في thread منفصل
    threading.Thread(target=run_web, daemon=True, name="Flask-Web").start()
    
    # تشغيل OTP Loop في thread منفصل
    threading.Thread(target=otp_loop, daemon=True, name="OTP-Loop").start()
    
    logger.info("✅ جميع الخدمات تعمل...")
    logger.info("🚀 البوت جاهز للاستقبال...")
    
    # Long Polling محسن
    while True:
        try:
            bot.infinity_polling(
                timeout=POLLING_TIMEOUT,
                long_polling_timeout=LONG_POLLING_TIMEOUT,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(1)

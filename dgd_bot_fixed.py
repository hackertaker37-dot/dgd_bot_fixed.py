# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ████████╗ █████╗ ██╗  ██╗███████╗██████╗      ██████╗ ████████╗██████╗    ║
║   ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗    ██╔═══██╗╚══██╔══╝██╔══██╗   ║
║      ██║   ███████║█████╔╝ █████╗  ██████╔╝    ██║   ██║   ██║   ██████╔╝   ║
║      ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗    ██║   ██║   ██║   ██╔═══╝    ║
║      ██║   ██║  ██║██║  ██╗███████╗██║  ██║    ╚██████╔╝   ██║   ██║        ║
║      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝    ╚═╝   ╚═╝        ║
║                                                                              ║
║          TAKER OTP BOT - GOD MODE FINAL EDITION v11.0                        ║
║          Developer: @hackerTaker                                             ║
║          API: xwdsms.org (Full Integration)                                  ║
║          Languages: Arabic & English (Bilingual)                             ║
║          Feature: Service Detection with Icons                               ║
║          Status: PRODUCTION READY - MAXIMUM PERFORMANCE                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import time, requests, re, os, sys, sqlite3, threading, logging, json
import hashlib, traceback, random, string, io, tempfile
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from telebot import types, TeleBot, apihelper
from flask import Flask, jsonify, request as flask_request, render_template_string

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM INFORMATION
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_START_TIME = datetime.now()
SYSTEM_VERSION = "11.0-FINAL"

# ══════════════════════════════════════════════════════════════════════════════
# ULTIMATE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN = "8686995713:AAEXBVi5iZjfGAYM5L2pduO6iPt3PVe2YZI"
API_KEY = "97257ac6fe5efd03c28b43af34a887b3"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_final.db"

# ══════════════════════════════════════════════════════════════════════════════
# TIMING - GOD MODE
# ══════════════════════════════════════════════════════════════════════════════
DELETE_AFTER = 1800           # نصف ساعة = 1800 ثانية
OTP_CHECK_INTERVAL = 1.5      # فحص OTP كل 1.5 ثانية
API_TIMEOUT = 10              # مهلة API
API_RETRIES = 5               # عدد محاولات API
MAX_THREADS = 32              # عدد threads للبوت
POLLING_TIMEOUT = 15          # مهلة البولينج
LONG_POLLING_TIMEOUT = 8      # مهلة البولينج الطويل

# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TUNING
# ══════════════════════════════════════════════════════════════════════════════
apihelper.SESSION_TIME_TO_LIVE = 600
apihelper.ENABLE_MIDDLEWARE = False
apihelper.READ_TIMEOUT = 5
apihelper.CONNECT_TIMEOUT = 3
apihelper.RETRY_ON_ERROR = True

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE TRANSLATION DICTIONARY
# ══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # ── Main ──
    "welcome_title": {"ar": "✨ أهلاً بك في بوت Taker OTP", "en": "✨ Welcome to Taker OTP Bot"},
    "welcome_desc": {
        "ar": "• اختر الخدمة التي تريدها\n• ثم اختر الدولة المناسبة\n• استلم رمز التفعيل فوراً\n• ادعُ أصدقاءك واربح رصيداً",
        "en": "• Choose the service you want\n• Then choose the country\n• Receive OTP instantly\n• Invite friends and earn credit"
    },
    "choose_service": {"ar": "🛠 اختر الخدمة:", "en": "🛠 Choose service:"},
    "choose_country": {"ar": "🌍 اختر الدولة لخدمة {}", "en": "🌍 Choose country for {}"},
    "new_number": {"ar": "✅ تم تخصيص رقم جديد بنجاح", "en": "✅ New number allocated successfully"},
    "number_label": {"ar": "الرقم", "en": "Number"},
    "country_label": {"ar": "الدولة", "en": "Country"},
    "service_label": {"ar": "الخدمة", "en": "Service"},
    "time_label": {"ar": "الوقت", "en": "Time"},
    "status_waiting": {"ar": "⏳ في انتظار رمز التفعيل...", "en": "⏳ Waiting for OTP..."},
    "change_number_btn": {"ar": "🔄 تغيير الرقم", "en": "🔄 Change Number"},
    "change_country_btn": {"ar": "🌍 تغيير الدولة", "en": "🌍 Change Country"},
    "otp_channel_btn": {"ar": "📞 قناة الأكواد", "en": "📞 OTP Channel"},
    "back_btn": {"ar": "↩️ رجوع", "en": "↩️ Back"},
    "back_to_services": {"ar": "↩️ رجوع للخدمات", "en": "↩️ Back to services"},
    # ── Maintenance ──
    "maintenance_msg": {
        "ar": "⚠️ *البوت في وضع الصيانة*\nيرجى المحاولة لاحقاً.",
        "en": "⚠️ *Bot under maintenance*\nPlease try again later."
    },
    # ── Force Sub ──
    "force_sub_msg": {
        "ar": "🔒 *يجب الاشتراك في القنوات أولاً*",
        "en": "🔒 *You must subscribe to the channels first*"
    },
    "sub_btn": {"ar": "📢 اشترك في القناة", "en": "📢 Subscribe to channel"},
    "check_sub_btn": {"ar": "✅ تحقق من الاشتراك", "en": "✅ Check subscription"},
    "check_sub_ok": {"ar": "✅ تم التحقق بنجاح", "en": "✅ Verified successfully"},
    "check_sub_fail": {"ar": "❌ لم تشترك في جميع القنوات", "en": "❌ Not subscribed to all channels"},
    # ── OTP ──
    "otp_received_title": {"ar": "🔐 تم استقبال رمز التفعيل", "en": "🔐 OTP Code Received"},
    "app_label": {"ar": "التطبيق", "en": "Application"},
    "code_label": {"ar": "الكود", "en": "Code"},
    "copy_instruction": {"ar": "انسخ الكود واستخدمه فوراً", "en": "Copy the code and use it immediately"},
    # ── Lists ──
    "countries_list_title": {"ar": "🌍 الدول المتاحة:", "en": "🌍 Available countries:"},
    "services_list_title": {"ar": "🛠 الخدمات المتاحة:", "en": "🛠 Available services:"},
    # ── Stats ──
    "my_stats_title": {"ar": "📊 إحصائياتك", "en": "📊 Your Statistics"},
    "total_requests": {"ar": "إجمالي الطلبات", "en": "Total Requests"},
    "otps_received": {"ar": "الأكواد المستلمة", "en": "OTPs Received"},
    "first_use": {"ar": "أول استخدام", "en": "First Use"},
    "last_use": {"ar": "آخر استخدام", "en": "Last Use"},
    # ── Balance ──
    "my_balance_title": {"ar": "💰 رصيدك", "en": "💰 Your Balance"},
    "your_balance": {"ar": "رصيدك", "en": "Your Balance"},
    "referrals_label": {"ar": "الإحالات", "en": "Referrals"},
    "site_balance": {"ar": "رصيد الموقع", "en": "Site Balance"},
    "min_withdraw": {"ar": "الحد الأدنى للسحب", "en": "Min Withdrawal"},
    "earn_tip": {
        "ar": "💡 *اربح `0.05 USDT` عن كل صديق تدعوه*",
        "en": "💡 *Earn `0.05 USDT` per friend you invite*"
    },
    # ── Invite ──
    "invite_friends_title": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite Friends"},
    "your_link": {"ar": "🔗 *رابط الدعوة الخاص بك:*\n`{}`", "en": "🔗 *Your invite link:*\n`{}`"},
    "share_instruction": {"ar": "📤 *شارك الرابط مع أصدقائك*", "en": "📤 *Share the link with your friends*"},
    # ── Traffic ──
    "traffic_title": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "no_active_numbers": {"ar": "لا توجد أرقام نشطة حالياً.", "en": "No active numbers currently."},
    "unknown_text": {"ar": "غير معروف", "en": "Unknown"},
    # ── Keyboard Buttons ──
    "get_number_kb": {"ar": "📱 احصل على رقم", "en": "📱 Get Number"},
    "countries_kb": {"ar": "🌍 الدول المتاحة", "en": "🌍 Countries"},
    "stats_kb": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "balance_kb": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "invite_kb": {"ar": "🤝 دعوة الأصدقاء", "en": "🤝 Invite"},
    "traffic_kb": {"ar": "🟢 حركة المرور", "en": "🟢 Traffic"},
    "admin_kb": {"ar": "⚙️ لوحة التحكم", "en": "⚙️ Admin Panel"},
    "use_buttons": {"ar": "استخدم الأزرار أدناه للتنقل:", "en": "Use the buttons below to navigate:"},
    # ── Language ──
    "language_changed_ar": {"ar": "✅ تم تغيير اللغة إلى العربية", "en": "✅ Language changed to Arabic"},
    "language_changed_en": {"ar": "✅ تم تغيير اللغة إلى English", "en": "✅ Language changed to English"},
    # ── Errors ──
    "no_country": {"ar": "هذه الدولة غير متوفرة حالياً", "en": "This country is currently unavailable"},
    "general_error": {"ar": "خطأ: {}", "en": "Error: {}"},
    "connection_error": {"ar": "خطأ في الاتصال بالخادم", "en": "Server connection error"},
    # ── Admin Panel ──
    "admin_header": {"ar": "⚙️ لوحة التحكم - Taker OTP\n\nمرحباً بك في لوحة إدارة البوت.", "en": "⚙️ Admin Panel - Taker OTP\n\nWelcome to the bot admin panel."},
    "admin_status": {"ar": "حالة البوت: {}", "en": "Bot status: {}"},
    "admin_open": {"ar": "🟢 مفتوح", "en": "🟢 Open"},
    "admin_maint": {"ar": "🔴 صيانة", "en": "🔴 Maintenance"},
    "admin_add_country": {"ar": "➕ إضافة دولة", "en": "➕ Add Country"},
    "admin_del_country": {"ar": "➖ حذف دولة", "en": "➖ Delete Country"},
    "admin_add_service": {"ar": "➕ إضافة خدمة", "en": "➕ Add Service"},
    "admin_del_service": {"ar": "➖ حذف خدمة", "en": "➖ Delete Service"},
    "admin_broadcast": {"ar": "📢 إذاعة", "en": "📢 Broadcast"},
    "admin_users": {"ar": "👥 المستخدمين", "en": "👥 Users"},
    "admin_ban": {"ar": "🚫 حظر", "en": "🚫 Ban"},
    "admin_unban": {"ar": "✅ فك حظر", "en": "✅ Unban"},
    "admin_force_sub": {"ar": "🔗 الاشتراك الإجباري", "en": "🔗 Force Sub"},
    "admin_photo": {"ar": "🖼️ صورة الترحيب", "en": "🖼️ Welcome Photo"},
    "admin_clear": {"ar": "🗑️ مسح البيانات", "en": "🗑️ Clear Data"},
    "admin_exit": {"ar": "↩️ خروج", "en": "↩️ Exit"},
    "admin_stats_btn": {"ar": "📊 إحصائيات", "en": "📊 Statistics"},
    "admin_report_btn": {"ar": "📄 تقرير", "en": "📄 Report"},
}

# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
_lang_cache = {}
_lang_lock = threading.Lock()

def get_lang(uid):
    uid_str = str(uid)
    with _lang_lock:
        if uid_str in _lang_cache:
            return _lang_cache[uid_str]
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (f"lang_{uid}",))
        row = c.fetchone()
        conn.close()
        lang = row[0] if row else None
        with _lang_lock:
            _lang_cache[uid_str] = lang
        return lang
    except:
        return None

def set_lang(uid, lang):
    uid_str = str(uid)
    with _lang_lock:
        _lang_cache[uid_str] = lang
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("REPLACE INTO settings VALUES (?,?)", (f"lang_{uid}", lang))
        conn.commit()
        conn.close()
    except:
        pass

def _(key, uid=None, **kwargs):
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

def lang_selection_keyboard():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")
    )
    return mk

# ══════════════════════════════════════════════════════════════════════════════
# SERVICE ICONS MAP - FOR OTP MESSAGES
# ══════════════════════════════════════════════════════════════════════════════
SERVICE_ICONS_MAP = {
    "WhatsApp": "💬",
    "Telegram": "✈️",
    "Facebook": "📘",
    "Instagram": "📷",
    "Google": "🔍",
    "Twitter/X": "🐦",
    "Discord": "🎮",
    "Snapchat": "👻",
    "TikTok": "🎵",
    "Amazon": "📦",
    "Apple": "🍎",
    "Microsoft": "🪟",
    "Uber": "🚗",
    "Netflix": "🎬",
    "YouTube": "▶️",
    "IMO": "📞",
    "OTP": "🔐",
}

SERVICE_NAMES_AR = {
    "WhatsApp": "واتساب",
    "Telegram": "تيليجرام",
    "Facebook": "فيسبوك",
    "Instagram": "انستغرام",
    "Google": "جوجل",
    "Twitter/X": "تويتر",
    "Discord": "ديسكورد",
    "Snapchat": "سناب شات",
    "TikTok": "تيك توك",
    "Amazon": "امازون",
    "Apple": "ابل",
    "Microsoft": "مايكروسوفت",
    "Uber": "اوبر",
    "Netflix": "نتفلكس",
    "YouTube": "يوتيوب",
    "IMO": "ايمو",
    "OTP": "كود تفعيل",
}

# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT DATA
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_SERVICES = OrderedDict([
    ("whatsapp", ("WhatsApp", "💬", "واتساب")),
    ("facebook", ("Facebook", "📘", "فيسبوك")),
    ("instagram", ("Instagram", "📷", "انستغرام")),
    ("tiktok", ("TikTok", "🎵", "تيك توك")),
    ("telegram", ("Telegram", "✈️", "تيليجرام")),
    ("imo", ("IMO", "📞", "ايمو")),
    ("snapchat", ("Snapchat", "👻", "سناب شات")),
    ("google", ("Google", "🔍", "جوجل")),
    ("twitter", ("Twitter/X", "🐦", "تويتر")),
    ("discord", ("Discord", "🎮", "ديسكورد")),
    ("amazon", ("Amazon", "📦", "امازون")),
    ("apple", ("Apple", "🍎", "ابل")),
    ("microsoft", ("Microsoft", "🪟", "مايكروسوفت")),
    ("uber", ("Uber", "🚗", "اوبر")),
    ("netflix", ("Netflix", "🎬", "نتفلكس")),
    ("youtube", ("YouTube", "▶️", "يوتيوب")),
    ("all", ("All Services", "🌐", "كل الخدمات")),
])

from collections import OrderedDict

DEFAULT_COUNTRIES = OrderedDict([
    # ------
    ("22501", "ساحل العاج"),
    ("22507", "ساحل العاج VIP"),
    ("23276", "سيراليون"),
    ("26134", "مدغشقر"),
    ("44740", "المملكة المتحدة"),
    ("23490", "نيجيريا"),
    ("25471", "كينيا"),
    ("24910", "السودان"),
    ("49155", "ألمانيا"),
    ("23762", "الكاميرون"),
    ("22178", "السنغال"),
    ("22901", "بنين"),
    ("22898", "توجو"),

    # --- أفغانستان ---
    ("93", "أفغانستان"),
    ("9370", "أفغانستان VIP"),
    # --- ألبانيا ---
    ("355", "ألبانيا"),
    # --- الجزائر ---
    ("213", "الجزائر"),
    # --- أندورا ---
    ("376", "أندورا"),
    # --- أنغولا ---
    ("244", "أنغولا"),
    # --- الأرجنتين ---
    ("54", "الأرجنتين"),
    # --- أرمينيا ---
    ("374", "أرمينيا"),
    # --- أستراليا ---
    ("61", "أستراليا"),
    # --- النمسا ---
    ("43", "النمسا"),
    # --- أذربيجان ---
    ("994", "أذربيجان"),
    # --- البحرين ---
    ("973", "البحرين"),
    # --- بنغلاديش ---
    ("880", "بنغلاديش"),
    # --- بيلاروسيا ---
    ("375", "بيلاروسيا"),
    # --- بلجيكا ---
    ("32", "بلجيكا"),
    # --- بليز ---
    ("501", "بليز"),
    # --- بنين ---
    ("229", "بنين"),
    # --- بوتان ---
    ("975", "بوتان"),
    # --- بوليفيا ---
    ("591", "بوليفيا"),
    # --- البوسنة والهرسك ---
    ("387", "البوسنة والهرسك"),
    # --- بوتسوانا ---
    ("267", "بوتسوانا"),
    # --- البرازيل ---
    ("55", "البرازيل"),
    # --- بروناي ---
    ("673", "بروناي"),
    # --- بلغاريا ---
    ("359", "بلغاريا"),
    # --- بوركينا فاسو ---
    ("226", "بوركينا فاسو"),
    # --- بوروندي ---
    ("257", "بوروندي"),
    # --- كمبوديا ---
    ("855", "كمبوديا"),
    # --- الكاميرون ---
    ("237", "الكاميرون"),
    # --- الرأس الأخضر ---
    ("238", "الرأس الأخضر"),
    # --- جمهورية أفريقيا الوسطى ---
    ("236", "جمهورية أفريقيا الوسطى"),
    # --- تشاد ---
    ("235", "تشاد"),
    # --- تشيلي ---
    ("56", "تشيلي"),
    # --- الصين ---
    ("86", "الصين"),
    # --- كولومبيا ---
    ("57", "كولومبيا"),
    # --- جزر القمر ---
    ("269", "جزر القمر"),
    # --- الكونغو ---
    ("242", "الكونغو"),
    # --- جمهورية الكونغو الديمقراطية ---
    ("243", "جمهورية الكونغو الديمقراطية"),
    # --- كوستاريكا ---
    ("506", "كوستاريكا"),
    # --- كرواتيا ---
    ("385", "كرواتيا"),
    # --- كوبا ---
    ("53", "كوبا"),
    # --- قبرص ---
    ("357", "قبرص"),
    # --- التشيك ---
    ("420", "التشيك"),
    # --- الدنمارك ---
    ("45", "الدنمارك"),
    # --- جيبوتي ---
    ("253", "جيبوتي"),
    # --- الإكوادور ---
    ("593", "الإكوادور"),
    # --- مصر ---
    ("20", "مصر"),
    ("2011", "مصر VIP"),
    # --- السلفادور ---
    ("503", "السلفادور"),
    # --- غينيا الاستوائية ---
    ("240", "غينيا الاستوائية"),
    # --- إريتريا ---
    ("291", "إريتريا"),
    # --- إستونيا ---
    ("372", "إستونيا"),
    # --- إسواتيني ---
    ("268", "إسواتيني"),
    # --- إثيوبيا ---
    ("251", "إثيوبيا"),
    # --- فيجي ---
    ("679", "فيجي"),
    # --- فنلندا ---
    ("358", "فنلندا"),
    # --- فرنسا ---
    ("33", "فرنسا"),
    # --- الغابون ---
    ("241", "الغابون"),
    # --- غامبيا ---
    ("220", "غامبيا"),
    # --- جورجيا ---
    ("995", "جورجيا"),
    # --- غانا ---
    ("233", "غانا"),
    # --- اليونان ---
    ("30", "اليونان"),
    # --- غواتيمالا ---
    ("502", "غواتيمالا"),
    # --- غينيا ---
    ("224", "غينيا"),
    # --- غينيا بيساو ---
    ("245", "غينيا بيساو"),
    # --- غيانا ---
    ("592", "غيانا"),
    # --- هايتي ---
    ("509", "هايتي"),
    # --- هندوراس ---
    ("504", "هندوراس"),
    # --- المجر ---
    ("36", "المجر"),
    # --- آيسلندا ---
    ("354", "آيسلندا"),
    # --- الهند ---
    ("91", "الهند"),
    # --- إندونيسيا ---
    ("62", "إندونيسيا"),
    # --- إيران ---
    ("98", "إيران"),
    # --- العراق ---
    ("964", "العراق"),
    # --- أيرلندا ---
    ("353", "أيرلندا"),
    # --- إسرائيل ---
    ("972", "إسرائيل"),
    # --- إيطاليا ---
    ("39", "إيطاليا"),
    # --- ساحل العاج ---
    ("225", "ساحل العاج"),
    # --- اليابان ---
    ("81", "اليابان"),
    # --- الأردن ---
    ("962", "الأردن"),
    # --- كازاخستان ---
    ("7", "كازاخستان"),
    ("77", "كازاخستان VIP"),
    # --- كينيا ---
    ("254", "كينيا"),
    # --- كوسوفو ---
    ("383", "كوسوفو"),
    # --- الكويت ---
    ("965", "الكويت"),
    # --- قيرغيزستان ---
    ("996", "قيرغيزستان"),
    # --- لاوس ---
    ("856", "لاوس"),
    # --- لاتفيا ---
    ("371", "لاتفيا"),
    # --- لبنان ---
    ("961", "لبنان"),
    # --- ليسوتو ---
    ("266", "ليسوتو"),
    # --- ليبيريا ---
    ("231", "ليبيريا"),
    # --- ليبيا ---
    ("218", "ليبيا"),
    # --- ليختنشتاين ---
    ("423", "ليختنشتاين"),
    # --- ليتوانيا ---
    ("370", "ليتوانيا"),
    # --- لوكسمبورغ ---
    ("352", "لوكسمبورغ"),
    # --- مدغشقر ---
    ("261", "مدغشقر"),
    # --- ملاوي ---
    ("265", "ملاوي"),
    # --- ماليزيا ---
    ("60", "ماليزيا"),
    # --- المالديف ---
    ("960", "المالديف"),
    # --- مالي ---
    ("223", "مالي"),
    # --- مالطا ---
    ("356", "مالطا"),
    # --- موريتانيا ---
    ("222", "موريتانيا"),
    # --- موريشيوس ---
    ("230", "موريشيوس"),
    # --- المكسيك ---
    ("52", "المكسيك"),
    # --- مولدوفا ---
    ("373", "مولدوفا"),
    # --- موناكو ---
    ("377", "موناكو"),
    # --- منغوليا ---
    ("976", "منغوليا"),
    # --- الجبل الأسود ---
    ("382", "الجبل الأسود"),
    # --- المغرب ---
    ("212", "المغرب"),
    # --- موزمبيق ---
    ("258", "موزمبيق"),
    # --- ميانمار ---
    ("95", "ميانمار"),
    # --- ناميبيا ---
    ("264", "ناميبيا"),
    # --- نيبال ---
    ("977", "نيبال"),
    # --- هولندا ---
    ("31", "هولندا"),
    # --- نيوزيلندا ---
    ("64", "نيوزيلندا"),
    # --- نيكاراغوا ---
    ("505", "نيكاراغوا"),
    # --- النيجر ---
    ("227", "النيجر"),
    # --- نيجيريا ---
    ("234", "نيجيريا"),
    # --- كوريا الشمالية ---
    ("850", "كوريا الشمالية"),
    # --- مقدونيا الشمالية ---
    ("389", "مقدونيا الشمالية"),
    # --- النرويج ---
    ("47", "النرويج"),
    # --- عُمان ---
    ("968", "عُمان"),
    # --- باكستان ---
    ("92", "باكستان"),
    # --- بنما ---
    ("507", "بنما"),
    # --- بابوا غينيا الجديدة ---
    ("675", "بابوا غينيا الجديدة"),
    # --- باراغواي ---
    ("595", "باراغواي"),
    # --- بيرو ---
    ("51", "بيرو"),
    # --- الفلبين ---
    ("63", "الفلبين"),
    # --- بولندا ---
    ("48", "بولندا"),
    # --- البرتغال ---
    ("351", "البرتغال"),
    # --- قطر ---
    ("974", "قطر"),
    # --- رومانيا ---
    ("40", "رومانيا"),
    # --- روسيا ---
    ("79", "روسيا"),
    # --- رواندا ---
    ("250", "رواندا"),
    # --- ساموا ---
    ("685", "ساموا"),
    # --- سان مارينو ---
    ("378", "سان مارينو"),
    # --- ساو تومي وبرينسيب ---
    ("239", "ساو تومي وبرينسيب"),
    # --- السعودية ---
    ("966", "السعودية"),
    # --- السنغال ---
    ("221", "السنغال"),
    # --- سيشل ---
    ("248", "سيشل"),
    # --- سيراليون ---
    ("232", "سيراليون"),
    # --- سلوفاكيا ---
    ("421", "سلوفاكيا"),
    # --- سلوفينيا ---
    ("386", "سلوفينيا"),
    # --- جزر سليمان ---
    ("677", "جزر سليمان"),
    # --- الصومال ---
    ("252", "الصومال"),
    # --- جنوب أفريقيا ---
    ("27", "جنوب أفريقيا"),
    # --- كوريا الجنوبية ---
    ("82", "كوريا الجنوبية"),
    # --- جنوب السودان ---
    ("211", "جنوب السودان"),
    # --- إسبانيا ---
    ("34", "إسبانيا"),
    # --- سريلانكا ---
    ("94", "سريلانكا"),
    # --- السودان ---
    ("249", "السودان"),
    # --- سورينام ---
    ("597", "سورينام"),
    # --- السويد ---
    ("46", "السويد"),
    # --- سويسرا ---
    ("41", "سويسرا"),
    # --- سوريا ---
    ("963", "سوريا"),
    # --- طاجيكستان ---
    ("992", "طاجيكستان"),
    # --- تنزانيا ---
    ("255", "تنزانيا"),
    # --- تايلاند ---
    ("66", "تايلاند"),
    # --- تيمور الشرقية ---
    ("670", "تيمور الشرقية"),
    # --- توجو ---
    ("228", "توجو"),
    # --- تونس ---
    ("216", "تونس"),
    # --- تركيا ---
    ("90", "تركيا"),
    # --- تركمانستان ---
    ("993", "تركمانستان"),
    # --- أوغندا ---
    ("256", "أوغندا"),
    # --- أوكرانيا ---
    ("380", "أوكرانيا"),
    # --- الإمارات العربية المتحدة ---
    ("971", "الإمارات العربية المتحدة"),
    # --- المملكة المتحدة ---
    ("44", "المملكة المتحدة"),
    # --- الولايات المتحدة ---
    ("1", "الولايات المتحدة"),
    # --- أوروغواي ---
    ("598", "أوروغواي"),
    # --- أوزبكستان ---
    ("998", "أوزبكستان"),
    # --- فانواتو ---
    ("678", "فانواتو"),
    # --- فنزويلا ---
    ("58", "فنزويلا"),
    # --- فيتنام ---
    ("84", "فيتنام"),
    # --- اليمن ---
    ("967", "اليمن"),
from collections import OrderedDict

DEFAULT_COUNTRIES = OrderedDict([
    # --- أول 13 دولة كما أرسلتها بالضبط ---
    ("22501", "ساحل العاج"),
    ("22507", "ساحل العاج VIP"),
    ("23276", "سيراليون"),
    ("26134", "مدغشقر"),
    ("44740", "المملكة المتحدة"),
    ("23490", "نيجيريا"),
    ("25471", "كينيا"),
    ("24910", "السودان"),
    ("49155", "ألمانيا"),
    ("23762", "الكاميرون"),
    ("22178", "السنغال"),
    ("22901", "بنين"),
    ("22898", "توجو"),

    # --- باقي دول العالم ---
    ("93", "أفغانستان"),
    ("355", "ألبانيا"),
    ("213", "الجزائر"),
    ("376", "أندورا"),
    ("244", "أنغولا"),
    ("54", "الأرجنتين"),
    ("374", "أرمينيا"),
    ("61", "أستراليا"),
    ("43", "النمسا"),
    ("994", "أذربيجان"),
    ("973", "البحرين"),
    ("880", "بنغلاديش"),
    ("375", "بيلاروسيا"),
    ("32", "بلجيكا"),
    ("501", "بليز"),
    ("229", "بنين"),
    ("975", "بوتان"),
    ("591", "بوليفيا"),
    ("387", "البوسنة والهرسك"),
    ("267", "بوتسوانا"),
    ("55", "البرازيل"),
    ("673", "بروناي"),
    ("359", "بلغاريا"),
    ("226", "بوركينا فاسو"),
    ("257", "بوروندي"),
    ("855", "كمبوديا"),
    ("237", "الكاميرون"),
    ("238", "الرأس الأخضر"),
    ("236", "جمهورية أفريقيا الوسطى"),
    ("235", "تشاد"),
    ("56", "تشيلي"),
    ("86", "الصين"),
    ("57", "كولومبيا"),
    ("269", "جزر القمر"),
    ("242", "الكونغو"),
    ("243", "جمهورية الكونغو الديمقراطية"),
    ("506", "كوستاريكا"),
    ("385", "كرواتيا"),
    ("53", "كوبا"),
    ("357", "قبرص"),
    ("420", "التشيك"),
    ("45", "الدنمارك"),
    ("253", "جيبوتي"),
    ("593", "الإكوادور"),
    ("20", "مصر"),
    ("2011", "مصر VIP"),
    ("503", "السلفادور"),
    ("240", "غينيا الاستوائية"),
    ("291", "إريتريا"),
    ("372", "إستونيا"),
    ("268", "إسواتيني"),
    ("251", "إثيوبيا"),
    ("679", "فيجي"),
    ("358", "فنلندا"),
    ("33", "فرنسا"),
    ("241", "الغابون"),
    ("220", "غامبيا"),
    ("995", "جورجيا"),
    ("233", "غانا"),
    ("30", "اليونان"),
    ("502", "غواتيمالا"),
    ("224", "غينيا"),
    ("245", "غينيا بيساو"),
    ("592", "غيانا"),
    ("509", "هايتي"),
    ("504", "هندوراس"),
    ("36", "المجر"),
    ("354", "آيسلندا"),
    ("91", "الهند"),
    ("62", "إندونيسيا"),
    ("98", "إيران"),
    ("964", "العراق"),
    ("353", "أيرلندا"),
    ("972", "إسرائيل"),
    ("39", "إيطاليا"),
    ("225", "ساحل العاج"),
    ("81", "اليابان"),
    ("962", "الأردن"),
    ("7", "كازاخستان"),
    ("77", "كازاخستان VIP"),
    ("254", "كينيا"),
    ("383", "كوسوفو"),
    ("965", "الكويت"),
    ("996", "قيرغيزستان"),
    ("856", "لاوس"),
    ("371", "لاتفيا"),
    ("961", "لبنان"),
    ("266", "ليسوتو"),
    ("231", "ليبيريا"),
    ("218", "ليبيا"),
    ("423", "ليختنشتاين"),
    ("370", "ليتوانيا"),
    ("352", "لوكسمبورغ"),
    ("261", "مدغشقر"),
    ("265", "ملاوي"),
    ("60", "ماليزيا"),
    ("960", "المالديف"),
    ("223", "مالي"),
    ("356", "مالطا"),
    ("222", "موريتانيا"),
    ("230", "موريشيوس"),
    ("52", "المكسيك"),
    ("373", "مولدوفا"),
    ("377", "موناكو"),
    ("976", "منغوليا"),
    ("382", "الجبل الأسود"),
    ("212", "المغرب"),
    ("258", "موزمبيق"),
    ("95", "ميانمار"),
    ("264", "ناميبيا"),
    ("977", "نيبال"),
    ("31", "هولندا"),
    ("64", "نيوزيلندا"),
    ("505", "نيكاراغوا"),
    ("227", "النيجر"),
    ("234", "نيجيريا"),
    ("850", "كوريا الشمالية"),
    ("389", "مقدونيا الشمالية"),
    ("47", "النرويج"),
    ("968", "عُمان"),
    ("92", "باكستان"),
    ("507", "بنما"),
    ("675", "بابوا غينيا الجديدة"),
    ("595", "باراغواي"),
    ("51", "بيرو"),
    ("63", "الفلبين"),
    ("48", "بولندا"),
    ("351", "البرتغال"),
    ("974", "قطر"),
    ("40", "رومانيا"),
    ("79", "روسيا"),
    ("250", "رواندا"),
    ("685", "ساموا"),
    ("378", "سان مارينو"),
    ("239", "ساو تومي وبرينسيب"),
    ("966", "السعودية"),
    ("221", "السنغال"),
    ("248", "سيشل"),
    ("232", "سيراليون"),
    ("421", "سلوفاكيا"),
    ("386", "سلوفينيا"),
    ("677", "جزر سليمان"),
    ("252", "الصومال"),
    ("27", "جنوب أفريقيا"),
    ("82", "كوريا الجنوبية"),
    ("211", "جنوب السودان"),
    ("34", "إسبانيا"),
    ("94", "سريلانكا"),
    ("249", "السودان"),
    ("597", "سورينام"),
    ("46", "السويد"),
    ("41", "سويسرا"),
    ("963", "سوريا"),
    ("992", "طاجيكستان"),
    ("255", "تنزانيا"),
    ("66", "تايلاند"),
    ("670", "تيمور الشرقية"),
    ("228", "توجو"),
    ("216", "تونس"),
    ("90", "تركيا"),
    ("993", "تركمانستان"),
    ("256", "أوغندا"),
    ("380", "أوكرانيا"),
    ("971", "الإمارات العربية المتحدة"),
    ("44", "المملكة المتحدة"),
    ("1", "الولايات المتحدة"),
    ("598", "أوروغواي"),
    ("998", "أوزبكستان"),
    ("678", "فانواتو"),
    ("58", "فنزويلا"),
    ("84", "فيتنام"),
    ("967", "اليمن"),
    ("260", "زامبيا"),
    ("263", "زيمبابوي"),
])

COUNTRY_FLAGS = {
    # --- مفاتيحك الخاصة أولاً (عشان الدالة ترجعهم على طول) ---
    "22501": "🇨🇮",  # ساحل العاج
    "22507": "🇨🇮",  # ساحل العاج VIP
    "23276": "🇸🇱",  # سيراليون
    "26134": "🇲🇬",  # مدغشقر
    "44740": "🇬🇧",  # المملكة المتحدة
    "23490": "🇳🇬",  # نيجيريا
    "25471": "🇰🇪",  # كينيا
    "24910": "🇸🇩",  # السودان
    "49155": "🇩🇪",  # ألمانيا
    "23762": "🇨🇲",  # الكاميرون
    "22178": "🇸🇳",  # السنغال
    "22901": "🇧🇯",  # بنين
    "22898": "🇹🇬",  # توجو

    # --- باقي الأعلام القياسية ---
    "1": "🇺🇸", "7": "🇷🇺", "20": "🇪🇬", "27": "🇿🇦",
    "30": "🇬🇷", "31": "🇳🇱", "32": "🇧🇪", "33": "🇫🇷",
    "34": "🇪🇸", "36": "🇭🇺", "39": "🇮🇹", "40": "🇷🇴",
    "41": "🇨🇭", "43": "🇦🇹", "44": "🇬🇧", "45": "🇩🇰",
    "46": "🇸🇪", "47": "🇳🇴", "48": "🇵🇱", "49": "🇩🇪",
    "51": "🇵🇪", "52": "🇲🇽", "53": "🇨🇺", "54": "🇦🇷",
    "55": "🇧🇷", "56": "🇨🇱", "57": "🇨🇴", "58": "🇻🇪",
    "60": "🇲🇾", "61": "🇦🇺", "62": "🇮🇩", "63": "🇵🇭",
    "64": "🇳🇿", "66": "🇹🇭", "81": "🇯🇵", "82": "🇰🇷",
    "84": "🇻🇳", "86": "🇨🇳", "90": "🇹🇷", "91": "🇮🇳",
    "92": "🇵🇰", "93": "🇦🇫", "94": "🇱🇰", "95": "🇲🇲",
    "98": "🇮🇷", "211": "🇸🇸", "212": "🇲🇦", "213": "🇩🇿",
    "216": "🇹🇳", "218": "🇱🇾", "220": "🇬🇲", "221": "🇸🇳",
    "222": "🇲🇷", "223": "🇲🇱", "224": "🇬🇳", "225": "🇨🇮",
    "226": "🇧🇫", "227": "🇳🇪", "228": "🇹🇬", "229": "🇧🇯",
    "230": "🇲🇺", "231": "🇱🇷", "232": "🇸🇱", "233": "🇬🇭",
    "234": "🇳🇬", "235": "🇹🇩", "236": "🇨🇫", "237": "🇨🇲",
    "238": "🇨🇻", "239": "🇸🇹", "240": "🇬🇶", "241": "🇬🇦",
    "242": "🇨🇬", "243": "🇨🇩", "244": "🇦🇴", "245": "🇬🇼",
    "248": "🇸🇨", "249": "🇸🇩", "250": "🇷🇼", "251": "🇪🇹",
    "252": "🇸🇴", "253": "🇩🇯", "254": "🇰🇪", "255": "🇹🇿",
    "256": "🇺🇬", "257": "🇧🇮", "258": "🇲🇿", "260": "🇿🇲",
    "261": "🇲🇬", "263": "🇿🇼", "264": "🇳🇦", "265": "🇲🇼",
    "266": "🇱🇸", "267": "🇧🇼", "268": "🇸🇿", "269": "🇰🇲",
    "291": "🇪🇷", "351": "🇵🇹", "352": "🇱🇺", "353": "🇮🇪",
    "354": "🇮🇸", "355": "🇦🇱", "356": "🇲🇹", "357": "🇨🇾",
    "358": "🇫🇮", "359": "🇧🇬", "370": "🇱🇹", "371": "🇱🇻",
    "372": "🇪🇪", "373": "🇲🇩", "374": "🇦🇲", "375": "🇧🇾",
    "376": "🇦🇩", "377": "🇲🇨", "378": "🇸🇲", "380": "🇺🇦",
    "381": "🇷🇸", "382": "🇲🇪", "383": "🇽🇰", "385": "🇭🇷",
    "386": "🇸🇮", "387": "🇧🇦", "389": "🇲🇰", "420": "🇨🇿",
    "421": "🇸🇰", "423": "🇱🇮", "501": "🇧🇿", "502": "🇬🇹",
    "503": "🇸🇻", "504": "🇭🇳", "505": "🇳🇮", "506": "🇨🇷",
    "507": "🇵🇦", "509": "🇭🇹", "591": "🇧🇴", "592": "🇬🇾",
    "593": "🇪🇨", "595": "🇵🇾", "597": "🇸🇷", "598": "🇺🇾",
    "670": "🇹🇱", "673": "🇧🇳", "675": "🇵🇬", "677": "🇸🇧",
    "678": "🇻🇺", "679": "🇫🇯", "685": "🇼🇸", "850": "🇰🇵",
    "855": "🇰🇭", "856": "🇱🇦", "880": "🇧🇩", "960": "🇲🇻",
    "961": "🇱🇧", "962": "🇯🇴", "963": "🇸🇾", "964": "🇮🇶",
    "965": "🇰🇼", "966": "🇸🇦", "967": "🇾🇪", "968": "🇴🇲",
    "971": "🇦🇪", "972": "🇮🇱", "973": "🇧🇭", "974": "🇶🇦",
    "975": "🇧🇹", "976": "🇲🇳", "977": "🇳🇵", "992": "🇹🇯",
    "993": "🇹🇲", "994": "🇦🇿", "995": "🇬🇪", "996": "🇰🇬",
    "998": "🇺🇿",
}
def get_flag(prefix):
    prefix = str(prefix).strip()
    
    # 1. البحث المباشر الأول (للتعامل مع أي مفتاح طويل أو قصير)
    if prefix in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[prefix]
    
    # 2. لو ما لقيناش، نجرب نطابق من البداية (للتعامل مع المفاتيح القصيرة زي 966)
    # نرتب المفاتيح من الأطول للأقصر عشان نضمن أفضل تطابق
    sorted_codes = sorted(COUNTRY_FLAGS.keys(), key=len, reverse=True)
    for code in sorted_codes:
        if prefix.startswith(code):
            return COUNTRY_FLAGS[code]
    
    return "🌍"

# ══════════════════════════════════════════════════════════════════════════════
# API MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class APIManager:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TakerOTPBot/11.0"
        })
        self.stats = defaultdict(int)
        self.lock = threading.Lock()

    def _request(self, method, endpoint, max_retries=API_RETRIES, **kwargs):
        url = f"{self.base_url}{endpoint}"
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, timeout=API_TIMEOUT, **kwargs)
                else:
                    resp = self.session.post(url, timeout=API_TIMEOUT, **kwargs)
                resp.raise_for_status()
                with self.lock:
                    self.stats['success'] += 1
                return resp.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    with self.lock:
                        self.stats['not_found'] += 1
                    raise Exception("هذه الدولة غير متوفرة حالياً")
                if e.response.status_code == 429:
                    with self.lock:
                        self.stats['rate_limited'] += 1
                    time.sleep(2 ** attempt)
                    continue
                if attempt == max_retries - 1:
                    with self.lock:
                        self.stats['failed'] += 1
                    raise Exception("خطأ في الاتصال بالخادم")
                time.sleep(0.5 * (attempt + 1))
            except requests.exceptions.Timeout:
                with self.lock:
                    self.stats['timeout'] += 1
                if attempt == max_retries - 1:
                    raise Exception("انتهت مهلة الاتصال")
                time.sleep(1)
            except Exception as e:
                with self.lock:
                    self.stats['error'] += 1
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.5)

    def get_number(self, prefix):
        data = self._request("POST", "/api/v1/get-number", json={"range": prefix})
        if not data.get("success"):
            raise Exception(data.get("message", "فشل جلب الرقم"))
        return data["id"], data["number"]

    def check_otp(self, number):
        try:
            data = self._request("GET", "/api/v1/check-otp", params={"number": number})
            if data.get("success"):
                return data.get("status"), data.get("otp")
        except:
            pass
        return None, None

    def delete_number(self, alloc_id):
        try:
            self._request("POST", "/api/v1/delete-number", json={"id": alloc_id})
            return True
        except:
            return False

    def get_balance(self):
        try:
            data = self._request("GET", "/api/v1/balance")
            return data.get("balance", "0")
        except:
            return "0"

    def get_stats(self):
        return dict(self.stats)

api = APIManager()

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
class Database:
    def __init__(self, path):
        self.path = path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        c = self.conn.cursor()
        c.executescript('''
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
            
            CREATE TABLE IF NOT EXISTS otp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                otp TEXT,
                service TEXT,
                country TEXT,
                timestamp TEXT,
                assigned_to INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY,
                ref_code TEXT UNIQUE,
                ref_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT UNIQUE,
                description TEXT,
                enabled INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            
            CREATE TABLE IF NOT EXISTS custom_countries (
                prefix TEXT PRIMARY KEY,
                name TEXT
            );
            
            CREATE TABLE IF NOT EXISTS custom_services (
                service_key TEXT PRIMARY KEY,
                name TEXT,
                icon TEXT,
                ar_name TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_active_status ON active_numbers(status);
            CREATE INDEX IF NOT EXISTS idx_otp_logs_time ON otp_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_users_ban ON users(is_banned);
        ''')
        c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance', '0')")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo', '')")
        for prefix, name in DEFAULT_COUNTRIES.items():
            c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)", (prefix, name))
        for key, (name, icon, ar_name) in DEFAULT_SERVICES.items():
            c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
        self.conn.commit()

    def setting(self, key, value=None):
        c = self.conn.cursor()
        if value is not None:
            c.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
            self.conn.commit()
            return value
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def get_countries(self):
        c = self.conn.cursor()
        rows = c.execute("SELECT prefix, name FROM custom_countries ORDER BY name").fetchall()
        return OrderedDict((row[0], row[1]) for row in rows)

    def add_country(self, prefix, name):
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)", (prefix, name))
        self.conn.commit()

    def delete_country(self, prefix):
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_countries WHERE prefix=?", (prefix,))
        self.conn.commit()

    def get_services(self):
        c = self.conn.cursor()
        rows = c.execute("SELECT service_key, name, icon, ar_name FROM custom_services ORDER BY ar_name").fetchall()
        result = OrderedDict()
        for row in rows:
            result[row[0]] = {"name": row[1], "icon": row[2], "ar": row[3]}
        return result

    def add_service(self, key, name, icon, ar_name):
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)", (key, name, icon, ar_name))
        self.conn.commit()

    def delete_service(self, key):
        if key == "all":
            return
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'", (key,))
        self.conn.commit()

    def save_user(self, msg):
        uid = msg.from_user.id
        now = datetime.now().isoformat()
        c = self.conn.cursor()
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            c.execute("INSERT INTO users (user_id, username, first_name, first_seen, last_seen) VALUES (?,?,?,?,?)",
                     (uid, msg.from_user.username, msg.from_user.first_name, now, now))
        else:
            c.execute("UPDATE users SET username=?, first_name=?, last_seen=? WHERE user_id=?",
                     (msg.from_user.username, msg.from_user.first_name, now, uid))
        self.conn.commit()

    def get_all_users(self):
        return [r[0] for r in self.conn.cursor().execute(
            "SELECT user_id FROM users WHERE is_banned=0"
        ).fetchall()]

    def get_all_active(self):
        return self.conn.cursor().execute(
            "SELECT alloc_id, number, prefix, service, assigned_to FROM active_numbers WHERE status='waiting'"
        ).fetchall()

    def release_user_number(self, uid):
        c = self.conn.cursor()
        for (aid,) in c.execute(
            "SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (uid,)
        ).fetchall():
            api.delete_number(aid)
            c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (aid,))
        self.conn.commit()

    def assign_number(self, uid, alloc_id, number, prefix, service):
        self.release_user_number(uid)
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO active_numbers (alloc_id, number, prefix, service, assigned_to, created_at) VALUES (?,?,?,?,?,?)",
            (alloc_id, number, prefix, service, uid, datetime.now().isoformat())
        )
        c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?", (uid,))
        self.conn.commit()

    def save_otp(self, alloc_id, otp, service, uid):
        c = self.conn.cursor()
        c.execute("UPDATE active_numbers SET status='success', otp=? WHERE alloc_id=?", (otp, alloc_id))
        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?", (uid,))
        number_row = c.execute("SELECT number, prefix FROM active_numbers WHERE alloc_id=?", (alloc_id,)).fetchone()
        if number_row:
            country = self.get_countries().get(number_row[1], number_row[1])
            c.execute(
                "INSERT INTO otp_logs (number, otp, service, country, timestamp, assigned_to) VALUES (?,?,?,?,?,?)",
                (number_row[0], otp, service, country, datetime.now().isoformat(), uid)
            )
        self.conn.commit()

    def delete_active(self, alloc_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
        self.conn.commit()

    def get_user_stats(self, uid):
        row = self.conn.cursor().execute(
            "SELECT total_requests, total_otps, first_seen, last_seen FROM users WHERE user_id=?", (uid,)
        ).fetchone()
        return row if row else (0, 0, None, None)

    def get_user_balance(self, uid):
        c = self.conn.cursor()
        bal = c.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
        refs = c.execute("SELECT ref_count FROM referrals WHERE user_id=?", (uid,)).fetchone()
        return (bal[0] if bal else 0), (refs[0] if refs else 0)

    def get_ref_link(self, uid):
        ref = f"ref{uid}"
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)", (uid, ref))
        self.conn.commit()
        return f"https://t.me/Taker_OTP_BOT?start={ref}"

    def process_referral(self, ref_code, new_uid):
        c = self.conn.cursor()
        row = c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,)).fetchone()
        if row:
            c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?", (row[0],))
            c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?", (row[0],))
        self.conn.commit()

    def get_traffic_stats(self, limit=10):
        return self.conn.cursor().execute(
            "SELECT prefix, service, COUNT(*) as cnt FROM active_numbers WHERE status='waiting' GROUP BY prefix, service ORDER BY cnt DESC LIMIT ?",
            (limit,)
        ).fetchall()

    def get_total_otps(self):
        row = self.conn.cursor().execute("SELECT COUNT(*) FROM otp_logs").fetchone()
        return row[0] if row else 0

    def get_channels(self):
        return self.conn.cursor().execute("SELECT * FROM force_channels WHERE enabled=1").fetchall()

    def get_all_users_data(self):
        return self.conn.cursor().execute("SELECT * FROM users").fetchall()

    def get_active_numbers_data(self):
        return self.conn.cursor().execute("SELECT * FROM active_numbers WHERE status='waiting'").fetchall()

db = Database(DB_PATH)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def clean_number(n):
    return str(n).replace("+", "").replace("-", "").replace(" ", "").strip()

def detect_service(text):
    """اكتشاف الخدمة من نص الرسالة"""
    t = str(text).lower()
    if not t:
        return "OTP"
    patterns = {
        "WhatsApp": ["whatsapp", "واتساب", "واتس"],
        "Telegram": ["telegram", "تيليجرام", "تليجرام"],
        "Facebook": ["facebook", "فيسبوك", "fb"],
        "Instagram": ["instagram", "انستقرام", "انستغرام", "انستا"],
        "TikTok": ["tiktok", "تيك توك"],
        "IMO": ["imo", "ايمو"],
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
    }
    for service, keywords in patterns.items():
        if any(kw in t for kw in keywords):
            return service
    return "OTP"

def get_service_icon(service_name):
    """جلب أيقونة الخدمة"""
    return SERVICE_ICONS_MAP.get(service_name, "🔐")

def get_service_name_ar(service_name):
    """جلب اسم الخدمة بالعربية"""
    return SERVICE_NAMES_AR.get(service_name, service_name)

def mask_number(num, show=4):
    n = str(num)
    if len(n) <= show * 2:
        return n
    return f"{n[:show]}{'*' * (len(n) - show * 2 + 2)}{n[-show:]}"

def format_time(iso_str, uid=None):
    if not iso_str:
        return _("unknown_text", uid)
    try:
        return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y %H:%M:%S")
    except:
        return str(iso_str)

def format_code(otp):
    if len(otp) > 3:
        return f"{otp[:3]}-{otp[3:]}"
    return otp

def check_subscription(uid):
    channels = db.get_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            url = ch[2]
            ch_id = "@" + url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch_id, uid).status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_markup(uid):
    channels = db.get_channels()
    if not channels:
        return None
    mk = types.InlineKeyboardMarkup()
    for ch in channels:
        mk.add(types.InlineKeyboardButton(_("sub_btn", uid), url=ch[2]))
    mk.add(types.InlineKeyboardButton(_("check_sub_btn", uid), callback_data="check_sub"))
    return mk

# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT - ULTRA FAST
# ══════════════════════════════════════════════════════════════════════════════
bot = TeleBot(BOT_TOKEN, threaded=True, num_threads=MAX_THREADS)

# ══════════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════════════════════════════════════════
def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(
        types.KeyboardButton(_("get_number_kb", uid)),
        types.KeyboardButton(_("countries_kb", uid)),
        types.KeyboardButton(_("stats_kb", uid))
    )
    kb.add(
        types.KeyboardButton(_("balance_kb", uid)),
        types.KeyboardButton(_("invite_kb", uid)),
        types.KeyboardButton(_("traffic_kb", uid))
    )
    lang = get_lang(uid) or "ar"
    kb.add(types.KeyboardButton("🌐 English" if lang == "ar" else "🌐 العربية"))
    if uid in ADMIN_IDS:
        kb.add(types.KeyboardButton(_("admin_kb", uid)))
    return kb

def services_menu(uid):
    """قائمة الخدمات الاحترافية"""
    services = db.get_services()
    lang = get_lang(uid) or "ar"
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for key, data in services.items():
        if key != "all":
            display_name = data['ar'] if lang == "ar" else data['name']
            buttons.append(types.InlineKeyboardButton(
                f"{data['icon']} {display_name}",
                callback_data=f"svc_{key}"
            ))
    if "all" in services:
        display_name = services['all']['ar'] if lang == "ar" else services['all']['name']
        buttons.append(types.InlineKeyboardButton(
            f"{services['all']['icon']} {display_name}",
            callback_data="svc_all"
        ))
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    return markup

def countries_menu(service_key):
    """قائمة الدول لخدمة معينة"""
    countries = db.get_countries()
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        buttons.append(types.InlineKeyboardButton(
            f"{flag} {name}",
            callback_data=f"get_{prefix}_{service_key}"
        ))
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])
    markup.row(types.InlineKeyboardButton(
        "↩️ رجوع للخدمات",
        callback_data="menu_services"
    ))
    return markup

def number_actions(prefix, service_key, alloc_id, uid):
    """أزرار التحكم بعد الحصول على رقم"""
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton(
            _("change_number_btn", uid),
            callback_data=f"change_{prefix}_{service_key}_{alloc_id}"
        ),
        types.InlineKeyboardButton(
            _("change_country_btn", uid),
            callback_data=f"svc_{service_key}"
        )
    )
    mk.row(
        types.InlineKeyboardButton(
            _("otp_channel_btn", uid),
            url="https://t.me/numhj"
        ),
        types.InlineKeyboardButton(
            _("back_btn", uid),
            callback_data="main_menu"
        )
    )
    return mk

def show_home(cid, uid):
    """عرض الصفحة الرئيسية"""
    if db.setting("maintenance") == "1" and uid not in ADMIN_IDS:
        bot.send_message(cid, _("maintenance_msg", uid), parse_mode="Markdown")
        return
    
    if not check_subscription(uid):
        mk = sub_markup(uid)
        if mk:
            bot.send_message(cid, _("force_sub_msg", uid), parse_mode="Markdown", reply_markup=mk)
        return
    
    photo = db.setting("welcome_photo")
    welcome_title = _("welcome_title", uid)
    welcome_desc = _("welcome_desc", uid)
    txt = f"*{welcome_title}*\n\n{welcome_desc}\n\n*{_('choose_service', uid)}*"
    
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

# ══════════════════════════════════════════════════════════════════════════════
# /start COMMAND
# ══════════════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    cid = message.chat.id
    
    db.save_user(message)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref"):
        db.process_referral(args[1], uid)
    
    current_lang = get_lang(uid)
    
    if current_lang is None:
        bot.send_message(
            cid,
            "🌐 *اختر لغتك / Choose your language*\n\n"
            "يرجى اختيار اللغة للمتابعة\n"
            "Please choose your language to continue",
            parse_mode="Markdown",
            reply_markup=lang_selection_keyboard()
        )
        return
    
    show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SELECTION
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data in ["set_lang_ar", "set_lang_en"])
def set_language_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    lang = "ar" if call.data == "set_lang_ar" else "en"
    
    set_lang(uid, lang)
    
    if lang == "ar":
        msg = "✅ *تم تعيين اللغة العربية بنجاح*\n\nأهلاً بك في بوت Taker OTP!"
    else:
        msg = "✅ *Language set to English successfully*\n\nWelcome to Taker OTP Bot!"
    
    bot.edit_message_text(msg, cid, mid, parse_mode="Markdown")
    show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# BOTTOM KEYBOARD HANDLER
# ══════════════════════════════════════════════════════════════════════════════
BUTTON_MAP = {
    "get_number": ["📱 احصل على رقم", "📱 Get Number"],
    "countries": ["🌍 الدول المتاحة", "🌍 Countries"],
    "stats": ["📊 إحصائياتي", "📊 My Stats"],
    "balance": ["💰 رصيدي", "💰 Balance"],
    "invite": ["🤝 دعوة الأصدقاء", "🤝 Invite"],
    "traffic": ["🟢 حركة المرور", "🟢 Traffic"],
    "admin": ["⚙️ لوحة التحكم", "⚙️ Admin Panel"],
}

@bot.message_handler(func=lambda m: any(
    m.text in v for v in BUTTON_MAP.values()
) or m.text in ["🌐 English", "🌐 العربية"])
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
    
    # احصل على رقم
    if text in BUTTON_MAP["get_number"]:
        bot.send_message(cid, f"*{_('choose_service', uid)}*", parse_mode="Markdown", reply_markup=services_menu(uid))
        return
    
    # الدول المتاحة
    if text in BUTTON_MAP["countries"]:
        countries = db.get_countries()
        txt = f"*{_('countries_list_title', uid)}*\n\n"
        for prefix, name in countries.items():
            txt += f"{get_flag(prefix)} `{prefix}` - {name}\n"
        txt += f"\n📊 *الإجمالي:* `{len(countries)}` دولة"
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # إحصائياتي
    if text in BUTTON_MAP["stats"]:
        reqs, otps, first, last = db.get_user_stats(uid)
        msg = (
            f"*{_('my_stats_title', uid)}*\n\n"
            f"📱 *{_('total_requests', uid)}:* `{reqs}`\n"
            f"🔑 *{_('otps_received', uid)}:* `{otps}`\n"
            f"📅 *{_('first_use', uid)}:* `{format_time(first, uid)}`\n"
            f"📅 *{_('last_use', uid)}:* `{format_time(last, uid)}`"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # رصيدي
    if text in BUTTON_MAP["balance"]:
        bal, refs = db.get_user_balance(uid)
        site_bal = api.get_balance()
        msg = (
            f"*{_('my_balance_title', uid)}*\n\n"
            f"💎 *{_('your_balance', uid)}:* `{bal:.3f} USDT`\n"
            f"👤 *{_('referrals_label', uid)}:* `{refs}`\n"
            f"🏦 *{_('site_balance', uid)}:* `{site_bal}`\n"
            f"💳 *{_('min_withdraw', uid)}:* `18.0 USDT`\n\n"
            f"{_('earn_tip', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # دعوة الأصدقاء
    if text in BUTTON_MAP["invite"]:
        link = db.get_ref_link(uid)
        msg = (
            f"*{_('invite_friends_title', uid)}*\n\n"
            f"{_('your_link', uid).replace('{}', link)}\n\n"
            f"💰 *{_('earn_tip', uid)}*\n"
            f"{_('share_instruction', uid)}"
        )
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    
    # حركة المرور
    if text in BUTTON_MAP["traffic"]:
        rows = db.get_traffic_stats(10)
        if not rows:
            txt = f"*{_('traffic_title', uid)}*\n\n{_('no_active_numbers', uid)}"
        else:
            countries = db.get_countries()
            services = db.get_services()
            total = sum(r[2] for r in rows)
            lines = [f"*{_('traffic_title', uid)}*\n"]
            for prefix, svc, cnt in rows:
                name = countries.get(prefix, prefix)
                flag = get_flag(prefix)
                svc_icon = services.get(svc, {}).get("icon", "🔐")
                perc = (cnt / total) * 100 if total else 0
                bar = "█" * int(perc / 5)
                lines.append(f"{flag} {name} {svc_icon}: `{perc:.1f}%` {bar}")
            txt = "\n".join(lines)
        bot.send_message(cid, txt, parse_mode="Markdown")
        return
    
    # لوحة التحكم
    if text in BUTTON_MAP["admin"] and uid in ADMIN_IDS:
        admin_panel(message)
        return

# ══════════════════════════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    if check_subscription(uid):
        bot.answer_callback_query(call.id, _("check_sub_ok", uid))
        show_home(call.message.chat.id, uid)
    else:
        bot.answer_callback_query(call.id, _("check_sub_fail", uid), show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service_cb(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    service_key = call.data.split("_", 1)[1]
    services = db.get_services()
    lang = get_lang(uid) or "ar"
    display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
    
    choose_text = _("choose_country", uid)
    bot.edit_message_text(
        f"*{choose_text.replace('{}', display_name)}:*",
        cid, mid,
        parse_mode="Markdown",
        reply_markup=countries_menuالاسمice_key)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number_cb(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    parts = call.data.split("_", 2)
    prefix = parts[1]
    service_key = parts[2] if len(parts) > 2 else "all"
    
    db.release_user_number(uid)
    
    try:
        alloc_id, number = api.get_number(prefix)
        number = clean_number(number)
        db.assign_number(uid, alloc_id, number, prefix, service_key)
        
        countries = db.get_countries()
        services = db.get_services()
        lang = get_lang(uid) or "ar"
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
        service_icon = services.get(service_key, {}).get("icon", "🔐")
        now = datetime.now().strftime("%H:%M:%S")
        
        msg = (
            f"*{_('new_number', uid)}*\n\n"
            f"📞 *{_('number_label', uid)}:* `+{number}`\n"
            f"🌍 *{_('country_label', uid)}:* {flag} {name}\n"
            f"{service_icon} *{_('service_label', uid)}:* {display_name}\n"
            f"🕒 *{_('time_label', uid)}:* {now}\n"
            f"⏳ *{_('status_waiting', uid)}*"
        )
        
        bot.edit_message_text(
            msg, cid, mid,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        error_msg = str(e)
        if "غير متوفرة" in error_msg or "unavailable" in error_msg.lower():
            alert = _("no_country", uid)
        else:
            alert = _("general_error", uid).replace("{}", str(e)[:100])
        bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number_cb(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    parts = call.data.split("_", 3)
    prefix = parts[1]
    service_key = parts[2]
    old_alloc = parts[3] if len(parts) > 3 else None
    
    if old_alloc:
        api.delete_number(old_alloc)
        db.delete_active(old_alloc)
    
    db.release_user_number(uid)
    
    try:
        alloc_id, number = api.get_number(prefix)
        number = clean_number(number)
        db.assign_number(uid, alloc_id, number, prefix, service_key)
        
        countries = db.get_countries()
        services = db.get_services()
        lang = get_lang(uid) or "ar"
        name = countries.get(prefix, prefix)
        flag = get_flag(prefix)
        display_name = services.get(service_key, {}).get("ar" if lang == "ar" else "name", service_key)
        service_icon = services.get(service_key, {}).get("icon", "🔐")
        now = datetime.now().strftime("%H:%M:%S")
        
        msg = (
            f"*🔄 تم تغيير الرقم*\n\n"
            f"📞 *{_('number_label', uid)}:* `+{number}`\n"
            f"🌍 *{_('country_label', uid)}:* {flag} {name}\n"
            f"{service_icon} *{_('service_label', uid)}:* {display_name}\n"
            f"🕒 *{_('time_label', uid)}:* {now}\n"
            f"⏳ *{_('status_waiting', uid)}*"
        )
        
        bot.edit_message_text(
            msg, cid, mid,
            parse_mode="Markdown",
            reply_markup=number_actions(prefix, service_key, alloc_id, uid)
        )
    except Exception as e:
        alert = _("general_error", uid).replace("{}", str(e)[:100])
        bot.answer_callback_query(call.id, f"❌ {alert}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services", "main_menu"])
def back_menu(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    
    if call.data == "menu_services":
        bot.edit_message_text(
            f"*{_('choose_service', uid)}*",
            cid, mid,
            parse_mode="Markdown",
            reply_markup=services_menu(uid)
        )
    else:
        try:
            bot.delete_message(cid, mid)
        except:
            pass
        show_home(cid, uid)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL - ORIGINAL (DO NOT TOUCH!)
# ══════════════════════════════════════════════════════════════════════════════
user_states = {}

@bot.message_handler(func=lambda m: m.text in ["⚙️ لوحة التحكم", "⚙️ Admin Panel"] and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = _("admin_open", uid) if db.setting("maintenance") != "1" else _("admin_maint", uid)
    bot_status_text = _("admin_status", uid).replace("{}", status)
    
    markup.add(types.InlineKeyboardButton(bot_status_text, callback_data="toggle_maint"))
    
    # إدارة الدول
    markup.add(
        types.InlineKeyboardButton(_("admin_add_country", uid), callback_data="add_country"),
        types.InlineKeyboardButton(_("admin_del_country", uid), callback_data="del_country")
    )
    
    # إدارة الخدمات
    markup.add(
        types.InlineKeyboardButton(_("admin_add_service", uid), callback_data="add_service"),
        types.InlineKeyboardButton(_("admin_del_service", uid), callback_data="del_service")
    )
    
    # الإذاعة والمستخدمين
    markup.add(
        types.InlineKeyboardButton(_("admin_broadcast", uid), callback_data="broadcast"),
        types.InlineKeyboardButton(_("admin_users", uid), callback_data="users_list")
    )
    
    # الحظر والإعدادات
    markup.add(
        types.InlineKeyboardButton(_("admin_ban", uid), callback_data="ban"),
        types.InlineKeyboardButton(_("admin_unban", uid), callback_data="unban")
    )
    
    # إحصائيات وتقرير
    markup.add(
        types.InlineKeyboardButton(_("admin_stats_btn", uid), callback_data="bot_stats"),
        types.InlineKeyboardButton(_("admin_report_btn", uid), callback_data="report_btn")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_force_sub", uid), callback_data="force_sub"),
        types.InlineKeyboardButton(_("admin_photo", uid), callback_data="set_photo")
    )
    
    markup.add(
        types.InlineKeyboardButton(_("admin_clear", uid), callback_data="clear_data"),
        types.InlineKeyboardButton(_("admin_exit", uid), callback_data="main_menu")
    )
    
    msg = f"*{_('admin_header', uid)}*"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "toggle_maint" and c.from_user.id in ADMIN_IDS)
def toggle_maint(call):
    cur = db.setting("maintenance") == "1"
    db.setting("maintenance", "0" if cur else "1")
    bot.answer_callback_query(call.id, "✅ تم تغيير الحالة")
    admin_panel(call.message)

# ── إضافة دولة ──
@bot.callback_query_handler(func=lambda c: c.data == "add_country" and c.from_user.id in ADMIN_IDS)
def add_country_start(call):
    user_states[call.from_user.id] = "add_country_prefix"
    bot.edit_message_text(
        "*➕ إضافة دولة*\n\nأرسل Prefix الدولة (مثال: `24910`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_country_prefix")
def add_country_prefix(message):
    prefix = message.text.strip()
    user_states[message.from_user.id] = ("add_country_name", prefix)
    bot.send_message(message.chat.id, "أرسل اسم الدولة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_country_name")
def add_country_name(message):
    prefix = user_states[message.from_user.id][1]
    name = message.text.strip()
    db.add_country(prefix, name)
    bot.send_message(message.chat.id, f"✅ *تمت إضافة الدولة بنجاح*\n\n📞 Prefix: `{prefix}`\nn   ً الاسم: {name}", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── حذف دولة ──
@bot.callback_query_handler(func=lambda c: c.data == "del_country" and c.from_user.id in ADMIN_IDS)
def del_country_start(call):
    countries = db.get_countries()
    markup = types.InlineKeyboardMarkup()
    for prefix, name in countries.items():
        flag = get_flag(prefix)
        markup.add(types.InlineKeyboardButton(f"{flag} {name} ({prefix})", callback_data=f"delcountry_{prefix}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*➖ حذف دولة*\nاختر الدولة:", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcountry_") and c.from_user.id in ADMIN_IDS)
def del_country_confirm(call):
    prefix = call.data.split("_")[1]
    db.delete_country(prefix)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

# ── إضافة خدمة ──
@bot.callback_query_handler(func=lambda c: c.data == "add_service" and c.from_user.id in ADMIN_IDS)
def add_service_start(call):
    user_states[call.from_user.id] = "add_service_key"
    bot.edit_message_text(
        "*➕ إضافة خدمة*\n\nأرسل المفتاح (مثال: `snapchat`):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_service_key")
def add_service_key(message):
    key = message.text.strip().lower()
    user_states[message.from_user.id] = ("add_service_name", key)
    bot.send_message(message.chat.id, "أرسل اسم الخدمة بالإنجليزية:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_name")
def add_service_name(message):
    key = user_states[message.from_user.id][1]
    name = message.text.strip()
    user_states[message.from_user.id] = ("add_service_icon", key, name)
    bot.send_message(message.chat.id, "أرسل أيقونة الخدمة (إيموجي واحد):")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_icon")
def add_service_icon(message):
    key = user_states[message.from_user.id][1]
    name = user_states[message.from_user.id][2]
    icon = message.text.strip()
    user_states[message.from_user.id] = ("add_service_ar", key, name, icon)
    bot.send_message(message.chat.id, "أرسل اسم الخدمة بالعربية:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "add_service_ar")
def add_service_ar(message):
    key = user_states[message.from_user.id][1]
    name = user_states[message.from_user.id][2]
    icon = user_states[message.from_user.id][3]
    ar_name = message.text.strip()
    db.add_service(key, name, icon, ar_name)
    bot.send_message(message.chat.id, f"✅ *تمت إضافة الخدمة*\n\n{icon} {ar_name}", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── حذف خدمة ──
@bot.callback_query_handler(func=lambda c: c.data == "del_service" and c.from_user.id in ADMIN_IDS)
def del_service_start(call):
    services = db.get_services()
    markup = types.InlineKeyboardMarkup()
    for key, data in services.items():
        if key != "all":
            markup.add(types.InlineKeyboardButton(f"{data['icon']} {data['ar']}", callback_data=f"delservice_{key}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
    bot.edit_message_text("*➖ حذف خدمة*\nاختر الخدمة:", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delservice_") and c.from_user.id in ADMIN_IDS)
def del_service_confirm(call):
    key = call.data.split("_")[1]
    db.delete_service(key)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    admin_panel(call.message)

# ── إذاعة ──
@bot.callback_query_handler(func=lambda c: c.data == "broadcast" and c.from_user.id in ADMIN_IDS)
def broadcast_start(call):
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 إذاعة*\nأرسل الرسالة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_exec(message):
    users = db.get_all_users()
    cnt = 0
    for u in users:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            cnt += 1
            time.sleep(0.03)
        except:
            pass
    bot.send_message(message.chat.id, f"✅ *تم الإرسال إلى `{cnt}` مستخدم*", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── المستخدمين ──
@bot.callback_query_handler(func=lambda c: c.data == "users_list" and c.from_user.id in ADMIN_IDS)
def users_list(call):
    rows = db.conn.cursor().execute(
        "SELECT user_id, username, first_name, total_requests, total_otps FROM users WHERE is_banned=0 ORDER BY user_id DESC LIMIT 20"
    ).fetchall()
    
    if not rows:
        msg = "لا يوجد مستخدمون بعد."
    else:
        msg = "*👥 آخر المستخدمين:*\n\n"
        for uid, uname, fname, reqs, otps in rows:
            name = f"@{uname}" if uname else fname or str(uid)
            msg += f"• `{uid}` - {name} | 📱`{reqs}` 🔑`{otps}`\n"
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ── إحصائيات البوت ──
@bot.callback_query_handler(func=lambda c: c.data == "bot_stats" and c.from_user.id in ADMIN_IDS)
def bot_stats(call):
    total_users = len(db.get_all_users())
    active_numbers = len(db.get_all_active())
    total_otps = db.get_total_otps()
    api_stats = api.get_stats()
    countries_count = len(db.get_countries())
    services_count = len(db.get_services())
    
    msg = (
        f"*📊 إحصائيات البوت*\n\n"
        f"👥 *المستخدمين:* `{total_users}`\n"
        f"📱 *الأرقام النشطة:* `{active_numbers}`\n"
        f"🔑 *إجمالي الأكواد:* `{total_otps}`\n"
        f"🌍 *الدول:* `{countries_count}`\n"
        f"🛠 *الخدمات:* `{services_count}`\n\n"
        f"*📡 حالة API:*\n"
        f"✅ ناجح: `{api_stats.get('success', 0)}`\n"
        f"❌ فشل: `{api_stats.get('failed', 0)}`\n"
        f"⏰ مهلة: `{api_stats.get('timeout', 0)}`"
    )
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ── تقرير ──
@bot.callback_query_handler(func=lambda c: c.data == "report_btn" and c.from_user.id in ADMIN_IDS)
def report_btn(call):
    filename = f"Taker_OTP_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("TAKER OTP BOT - تقرير شامل\n")
        f.write(f"تاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("👥 المستخدمين:\n" + "-" * 40 + "\n")
        users = db.get_all_users_data()
        for u in users:
            f.write(f"ID: {u[0]} | @{u[1] or 'N/A'} | {u[2] or 'N/A'} | طلبات: {u[6]} | أكواد: {u[7]}\n")
        
        f.write("\n📱 الأرقام النشطة:\n" + "-" * 40 + "\n")
        active = db.get_active_numbers_data()
        for a in active:
            f.write(f"رقم: {a[1]} | دولة: {a[2]} | خدمة: {a[3]} | مستخدم: {a[4]}\n")
        
        f.write(f"\n📊 إجمالي الأكواد: {db.get_total_otps()}\n")
    
    with open(filepath, 'rb') as f:
        bot.send_document(call.message.chat.id, f, caption="📄 *تقرير البوت الشامل*", parse_mode="Markdown")
    
    try:
        os.remove(filepath)
    except:
        pass
    
    bot.answer_callback_query(call.id, "✅ تم إنشاء التقرير")

# ── حظر/فك حظر ──
@bot.callback_query_handler(func=lambda c: c.data in ["ban", "unban"] and c.from_user.id in ADMIN_IDS)
def ban_unban_prompt(call):
    user_states[call.from_user.id] = call.data
    txt = "*🚫 حظر*\nأرسل ID المستخدم:" if call.data == "ban" else "*✅ فك حظر*\nأرسل ID المستخدم:"
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) in ["ban", "unban"])
def ban_unban_exec(message):
    action = user_states[message.from_user.id]
    try:
        uid = int(message.text)
        db.conn.cursor().execute(
            f"UPDATE users SET is_banned={'1' if action == 'ban' else '0'} WHERE user_id=?",
            (uid,)
        )
        db.conn.commit()
        action_name = "حظر" if action == "ban" else "فك حظر"
        bot.send_message(message.chat.id, f"✅ *تم {action_name}* `{uid}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ معرف غير صحيح")
    del user_states[message.from_user.id]

# ── الاشتراك الإجباري ──
@bot.callback_query_handler(func=lambda c: c.data == "force_sub" and c.from_user.id in ADMIN_IDS)
def force_sub_menu(call):
    channels = db.get_channels()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        st = "✅" if ch[4] else "❌"
        markup.add(types.InlineKeyboardButton(f"{st} {ch[2]}", callback_data=f"editch_{ch[0]}"))
    markup.add(
        types.InlineKeyboardButton("➕ إضافة", callback_data="addch"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    )
    bot.edit_message_text("*🔗 قنوات الاشتراك الإجباري*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "addch" and c.from_user.id in ADMIN_IDS)
def addch_start(call):
    user_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*➕ إضافة قناة*\nأرسل رابط القناة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "addch_url")
def addch_url(message):
    url = message.text.strip()
    user_states[message.from_user.id] = ("addch_desc", url)
    bot.send_message(message.chat.id, "أرسل وصفاً للقناة:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), tuple) and user_states[m.from_user.id][0] == "addch_desc")
def addch_desc(message):
    url = user_states[message.from_user.id][1]
    desc = message.text.strip()
    db.conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url, description) VALUES (?,?)", (url, desc))
    db.conn.commit()
    bot.send_message(message.chat.id, "✅ *تمت إضافة القناة بنجاح*", parse_mode="Markdown")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("editch_") and c.from_user.id in ADMIN_IDS)
def editch(call):
    ch_id = int(call.data.split("_")[1])
    db.conn.cursor().execute("UPDATE force_channels SET enabled = 1 - enabled WHERE id=?", (ch_id,))
    db.conn.commit()
    force_sub_menu(call)

# ── صورة الترحيب ──
@bot.callback_query_handler(func=lambda c: c.data == "set_photo" and c.from_user.id in ADMIN_IDS)
def set_photo_prompt(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("*🖼️ صورة الترحيب*\nأرسل الصورة:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    db.setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ *تم حفظ صورة الترحيب بنجاح*", parse_mode="Markdown")
    del user_states[message.from_user.id]

# ── مسح البيانات ──
@bot.callback_query_handler(func=lambda c: c.data == "clear_data" and c.from_user.id in ADMIN_IDS)
def clear_data(call):
    c = db.conn.cursor()
    for t in ["users", "active_numbers", "otp_logs", "referrals"]:
        c.execute(f"DELETE FROM {t}")
    db.conn.commit()
    bot.answer_callback_query(call.id, "✅ تم مسح جميع البيانات")
    admin_panel(call.message)

# ── رجوع ──
@bot.callback_query_handler(func=lambda c: c.data == "admin_back" and c.from_user.id in ADMIN_IDS)
def admin_back(call):
    admin_panel(call.message)

# ══════════════════════════════════════════════════════════════════════════════
# OTP LOOP - 30 MINUTES DELETE + SERVICE DETECTION
# ══════════════════════════════════════════════════════════════════════════════
def process_single_otp(alloc_id, number, prefix, service_key, uid):
    """معالجة رقم OTP واحد - مع معرفة نوع الخدمة"""
    try:
        status, otp = api.check_otp(number)
        
        if status == "success" and otp:
            # اكتشاف الخدمة من نص الكود
            detected_service = detect_service(otp) if otp else "OTP"
            
            # إذا تم تحديد الخدمة من اختيار المستخدم
            services = db.get_services()
            if detected_service == "OTP" and service_key and service_key != "all":
                detected_service = services.get(service_key, {}).get("name", "OTP")
            
            # جلب أيقونة واسم الخدمة
            service_icon = get_service_icon(detected_service)
            service_name_ar = get_service_name_ar(detected_service)
            
            countries = db.get_countries()
            name = countries.get(prefix, prefix)
            flag = get_flag(prefix)
            code = format_code(otp)
            
            logger.info(f"🎯 كود جديد: {number} -> {otp} | {service_icon} {detected_service}")
            
            # إرسال للمستخدم - مع أيقونة واسم الخدمة
            if uid:
                try:
                    user_msg = (
                        f"*🔐 تم استقبال رمز التفعيل*\n\n"
                        f"📞 *الرقم:* `+{number}`\n"
                        f"🌍 *الدولة:* {flag} {name}\n"
                        f"{service_icon} *التطبيق:* {service_name_ar}\n"
                        f"🔢 *الكود:* `{code}`\n\n"
                        f"انسخ الكود واستخدمه فوراً"
                    )
                    bot.send_message(uid, user_msg, parse_mode="Markdown")
                    logger.info(f"✅ تم إرسال الكود للمستخدم {uid} - {service_icon} {service_name_ar}")
                except Exception as e:
                    logger.error(f"❌ فشل إرسال الكود للمستخدم {uid}: {e}")
            
            # إرسال للجروب - مع أيقونة واسم الخدمة - حذف بعد نصف ساعة
            for cid in CHAT_IDS:
                for attempt in range(3):
                    try:
                        masked = mask_number(number)
                        group_msg = (
                            f"*🔐 كود جديد - Taker OTP*\n\n"
                            f"🌍 {flag} {name} | {service_icon} {service_name_ar}\n"
                            f"📞 `{masked}`\n"
                            f"🔢 `{code}`"
                        )
                        sent = bot.send_message(cid, group_msg, parse_mode="Markdown")
                        logger.info(f"✅ تم إرسال الكود للجروب {cid} | {service_icon} {service_name_ar} | سيتم الحذف بعد {DELETE_AFTER} ثانية")
                        
                        # ════════════════ حذف بعد نصف ساعة ════════════════
                        threading.Thread(
                            target=lambda cid=cid, mid=sent.message_id: (
                                time.sleep(DELETE_AFTER),
                                bot.delete_message(cid, mid)
                            ),
                            daemon=True
                        ).start()
                        break
                    except Exception as e:
                        logger.error(f"❌ محاولة {attempt+1} فشلت للجروب {cid}: {e}")
                        time.sleep(1)
            
            # تحديث قاعدة البيانات
            db.save_otp(alloc_id, otp, detected_service, uid)
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)
        
        elif status == "expired":
            logger.info(f"⏰ انتهت صلاحية الرقم {number}")
            api.delete_number(alloc_id)
            db.delete_active(alloc_id)
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرقم {number}: {e}")

def otp_loop():
    """حلقة فحص OTP الرئيسية - نصف ساعة حذف + معرفة نوع الخدمة"""
    logger.info(f"🔄 بدء حلقة فحص OTP...")
    logger.info(f"⏱️ مدة حذف رسائل الجروب: {DELETE_AFTER} ثانية ({DELETE_AFTER/60:.1f} دقيقة)")
    logger.info(f"🛠 ميزة معرفة الخدمة: مفعلة")
    
    while True:
        try:
            active_numbers = db.get_all_active()
            
            if active_numbers:
                logger.info(f"🔍 جاري فحص {len(active_numbers)} رقم نشط...")
                
                for alloc_id, number, prefix, service_key, uid in active_numbers:
                    try:
                        process_single_otp(alloc_id, number, prefix, service_key, uid)
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"خطأ في حلقة OTP: {e}")
        
        time.sleep(OTP_CHECK_INTERVAL)

# ══════════════════════════════════════════════════════════════════════════════
# FLASK WEB SERVER
# ══════════════════════════════════════════════════════════════════════════════
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taker OTP Bot - v11.0 FINAL</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0f3460 100%);
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 50px;
            background: rgba(255,255,255,0.03);
            border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 30px 80px rgba(0,0,0,0.6);
            max-width: 650px;
        }
        h1 {
            font-size: 3.5em;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        .status { color: #00ff88; font-size: 1.3em; margin: 15px 0; }
        .info { color: #aaa; margin: 8px 0; }
        .badge {
            display: inline-block;
            padding: 10px 20px;
            background: rgba(0,210,255,0.15);
            border: 1px solid #00d2ff;
            border-radius: 25px;
            margin: 8px;
            font-size: 0.9em;
        }
        .version { color: #ff6b6b; font-weight: bold; font-size: 1.2em; }
        .footer { margin-top: 25px; color: #666; }
        .feature { color: #ffd700; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ TAKER OTP BOT ⚡</h1>
        <p class="version">GOD MODE v11.0 FINAL</p>
        <p class="status">🟢 System Online</p>
        <p class="info">API: xwdsms.org | Full Integration</p>
        <p class="info">Languages: العربية & English</p>
        <p class="info feature">🛠 Service Detection with Icons</p>
        <p class="info">⏱️ Group Delete: 30 minutes</p>
        <div style="margin-top: 25px;">
            <span class="badge">🚀 32 Threads</span>
            <span class="badge">🔐 Secure</span>
            <span class="badge">🌍 20+ Countries</span>
            <span class="badge">🛠 16 Services</span>
        </div>
        <p class="footer">Developer: @hackerTaker | © 2024</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    uptime = datetime.now() - SYSTEM_START_TIME
    return jsonify({
        "status": "ok",
        "version": SYSTEM_VERSION,
        "uptime": str(uptime),
        "delete_after": f"{DELETE_AFTER}s ({DELETE_AFTER/60}min)",
        "feature": "service_detection_with_icons"
    }), 200

@app.route('/api/v1/get-number', methods=['POST'])
def flask_get_number():
    try:
        data = flask_request.get_json()
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        resp = requests.post(
            f"{BASE_URL}/api/v1/get-number",
            json={"range": data.get("range", "")},
            headers=headers,
            timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/check-otp', methods=['GET'])
def flask_check_otp():
    try:
        number = flask_request.args.get("number", "")
        headers = {"x-api-key": API_KEY}
        resp = requests.get(
            f"{BASE_URL}/api/v1/check-otp",
            params={"number": number},
            headers=headers,
            timeout=8
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/v1/balance', methods=['GET'])
def flask_balance():
    try:
        headers = {"x-api-key": API_KEY}
        resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=8)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"balance": "0"}), 500

def run_web():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Flask Web Server running on port {port}")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ████████╗ █████╗ ██╗  ██╗███████╗██████╗                      ║
║   ╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝██╔══██╗                     ║
║      ██║   ███████║█████╔╝ █████╗  ██████╔╝                     ║
║      ██║   ██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗                     ║
║      ██║   ██║  ██║██║  ██╗███████╗██║  ██║                     ║
║      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                     ║
║                                                                  ║
║        TAKER OTP BOT - GOD MODE v11.0 FINAL                      ║
║        Developer: @hackerTaker                                   ║
║        API: xwdsms.org                                           ║
║        🛠  Service Detection with Icons                          ║
║        ⏱️  Group Delete: 30 minutes (1800s)                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("=" * 60)
    logger.info("🚀 TAKER OTP BOT v11.0 FINAL - GOD MODE")
    logger.info(f"🤖 Bot Token: {BOT_TOKEN[:15]}...")
    logger.info(f"🔑 API Key: {API_KEY[:15]}...")
    logger.info(f"📢 Groups: {CHAT_IDS}")
    logger.info(f"👑 Admins: {ADMIN_IDS}")
    logger.info(f"⏱️  Delete OTP after: {DELETE_AFTER}s ({DELETE_AFTER/60:.1f} minutes)")
    logger.info(f"🔧 Threads: {MAX_THREADS}")
    logger.info(f"🔄 API Retries: {API_RETRIES}")
    logger.info(f"⏰ OTP Check Interval: {OTP_CHECK_INTERVAL}s")
    logger.info(f"🛠  Service Detection: ENABLED with Icons")
    logger.info(f"💾 Database: {DB_PATH}")
    logger.info(f"🌐 Flask: http://0.0.0.0:{os.environ.get('PORT', 8080)}")
    logger.info("=" * 60)
    
    # تشغيل Flask
    threading.Thread(target=run_web, daemon=True, name="Flask-Web").start()
    
    # تشغيل OTP Loop
    threading.Thread(target=otp_loop, daemon=True, name="OTP-Loop").start()
    
    logger.info("✅ جميع الخدمات تعمل...")
    logger.info("🚀 البوت جاهز للاستقبال...")
    
    # تشغيل البوت
    while True:
        try:
            bot.infinity_polling(
                timeout=POLLING_TIMEOUT,
                long_polling_timeout=LONG_POLLING_TIMEOUT,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(2)

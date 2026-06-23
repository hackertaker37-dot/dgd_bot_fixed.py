# -*- coding: utf-8 -*-
"""
 ╔══════════════════════════════════════════════╗
 ║    TAKER OTP BOT - Professional Edition     ║
 ║    Developer: @hackerTaker                  ║
 ║    API: xwdsms.org (Full Integration)        ║
 ╚══════════════════════════════════════════════╝
"""
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8686995713:AAGlnuxDVHkDRkWWsCT2j8pk0Kn2yK4vT1w"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ الخدمات ════════════════
DEFAULT_SERVICES = {
    "whatsapp": {"en": "WhatsApp", "icon": "💬", "ar": "واتساب"},
    "facebook": {"en": "Facebook", "icon": "📘", "ar": "فيسبوك"},
    "instagram": {"en": "Instagram", "icon": "📷", "ar": "انستغرام"},
    "tiktok": {"en": "TikTok", "icon": "🎵", "ar": "تيك توك"},
    "telegram": {"en": "Telegram", "icon": "✈️", "ar": "تيليجرام"},
    "imo": {"en": "IMO", "icon": "📞", "ar": "ايمو"},
    "snapchat": {"en": "Snapchat", "icon": "👻", "ar": "سناب شات"},
    "google": {"en": "Google", "icon": "🔍", "ar": "جوجل"},
    "twitter": {"en": "Twitter/X", "icon": "🐦", "ar": "تويتر"},
    "discord": {"en": "Discord", "icon": "🎮", "ar": "ديسكورد"},
    "amazon": {"en": "Amazon", "icon": "📦", "ar": "امازون"},
    "apple": {"en": "Apple", "icon": "🍎", "ar": "ابل"},
    "microsoft": {"en": "Microsoft", "icon": "🪟", "ar": "مايكروسوفت"},
    "uber": {"en": "Uber", "icon": "🚗", "ar": "اوبر"},
    "netflix": {"en": "Netflix", "icon": "🎬", "ar": "نتفلكس"},
    "youtube": {"en": "YouTube", "icon": "▶️", "ar": "يوتيوب"},
    "all": {"en": "All Services", "icon": "🌐", "ar": "كل الخدمات"},
}

# ════════════════ الدول ════════════════
DEFAULT_COUNTRIES = {
    "22501": "ساحل العاج", "23276": "سيراليون", "26134": "مدغشقر",
    "44740": "المملكة المتحدة", "23490": "نيجيريا", "25471": "كينيا",
    "24910": "السودان", "49155": "ألمانيا", "23762": "الكاميرون",
    "22178": "السنغال", "22901": "بنين", "22898": "توجو",
}

FLAGS = {"225":"🇨🇮","232":"🇸🇱","261":"🇲🇬","44":"🇬🇧","234":"🇳🇬","254":"🇰🇪","249":"🇸🇩","49":"🇩🇪","237":"🇨🇲","221":"🇸🇳","229":"🇧🇯","228":"🇹🇬"}

def get_flag(p):
    for c, f in FLAGS.items():
        if p.startswith(c): return f
    return "🌍"

# ════════════════ نصوص ثنائية اللغة ════════════════
T = {
    "lang_select": {"ar": "🌐 *اختر لغتك*", "en": "🌐 *Select Language*"},
    "lang_set": {"ar": "✅ تم تعيين العربية", "en": "✅ English set"},
    "welcome": {"ar": "🔰 *أهلاً بك في Taker OTP*\n\n• اختر الخدمة\n• ثم اختر الدولة\n• استلم الكود فوراً\n\n*اختر الخدمة:*", "en": "🔰 *Welcome to Taker OTP*\n\n• Select service\n• Then select country\n• Receive code instantly\n\n*Select service:*"},
    "choose_country": {"ar": "*اختر الدولة:*", "en": "*Select country:*"},
    "number_assigned": {"ar": "✅ *تم تخصيص رقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n⏳ بانتظار الكود...", "en": "✅ *Number Assigned*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n⏳ Waiting for code..."},
    "number_changed": {"ar": "🔄 *تم تغيير الرقم*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n⏳ بانتظار الكود...", "en": "🔄 *Number Changed*\n\n📞 `+{number}`\n🌍 {flag} {country}\n🛠 {service}\n⏳ Waiting for code..."},
    "maintenance": {"ar": "⚠️ *البوت في الصيانة*", "en": "⚠️ *Bot under maintenance*"},
    "subscribe": {"ar": "🔒 *اشترك أولاً*", "en": "🔒 *Subscribe first*"},
    "stats": {"ar": "📊 *إحصائياتك*\n\n🔷 الطلبات: `{r}`\n🔷 الأكواد: `{o}`", "en": "📊 *Your Stats*\n\n🔷 Requests: `{r}`\n🔷 OTPs: `{o}`"},
    "balance": {"ar": "💰 *رصيدك*\n\n💎 `{b:.3f} USDT`\n👤 الإحالات: `{ref}`\n🏦 الموقع: `{site}`", "en": "💰 *Balance*\n\n💎 `{b:.3f} USDT`\n👤 Referrals: `{ref}`\n🏦 Site: `{site}`"},
    "invite": {"ar": "🤝 *دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق", "en": "🤝 *Invite*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` per friend"},
    "traffic": {"ar": "🟢 *حركة المرور*", "en": "🟢 *Live Traffic*"},
    "no_active": {"ar": "لا توجد أرقام نشطة", "en": "No active numbers"},
    "prefix_added": {"ar": "✅ تمت إضافة {flag} {name} (`{p}`)", "en": "✅ Added {flag} {name} (`{p}`)"},
    "service_added": {"ar": "✅ تمت إضافة خدمة {icon} {ar}", "en": "✅ Added service {icon} {en}"},
    "prefix_removed": {"ar": "✅ تم حذف الدولة", "en": "✅ Country removed"},
    "service_removed": {"ar": "✅ تم حذف الخدمة", "en": "✅ Service removed"},
    "admin_panel": {"ar": "*⚙️ لوحة التحكم*", "en": "*⚙️ Admin Panel*"},
    "otp_user": {"ar": "*🔐 كود جديد*\n\n📞 `+{num}`\n🌍 {flag} {country}\n{icon} *{svc}*\n🔢 `{code}`", "en": "*🔐 New OTP*\n\n📞 `+{num}`\n🌍 {flag} {country}\n{icon} *{svc}*\n🔢 `{code}`"},
    "otp_group": {"ar": "*🔐 كود جديد*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`", "en": "*🔐 New OTP*\n\n🌍 {flag} {country} | {icon} {svc}\n📞 `{masked}`\n🔢 `{code}`"},
    "countries_list": {"ar": "🌍 *الدول:*\n\n", "en": "🌍 *Countries:*\n\n"},
    "btn_new": {"ar": "📱 رقم جديد", "en": "📱 New Number"},
    "btn_countries": {"ar": "🌍 الدول", "en": "🌍 Countries"},
    "btn_stats": {"ar": "📊 إحصائياتي", "en": "📊 My Stats"},
    "btn_balance": {"ar": "💰 رصيدي", "en": "💰 Balance"},
    "btn_invite": {"ar": "🤝 دعوة", "en": "🤝 Invite"},
    "btn_traffic": {"ar": "🟢 المرور", "en": "🟢 Traffic"},
    "btn_admin": {"ar": "⚙️ الإدارة", "en": "⚙️ Admin"},
    "btn_lang": {"ar": "🌐 اللغة", "en": "🌐 Language"},
    "back": {"ar": "↩️ رجوع", "en": "↩️ Back"},
}

def t(key, uid=None, **kw):
    lang = "ar"
    if uid:
        u = db.get_user(uid)
        if u and u[4]: lang = u[4]
    txt = T.get(key, {}).get(lang, T.get(key, {}).get("ar", key))
    return txt.format(**kw) if kw else txt

def btn(key, uid):
    u = db.get_user(uid); lang = u[4] if u and u[4] else "ar"
    return T["btn_"+key][lang]

# ════════════════ API ════════════════
def api_get_number(prefix):
    h = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    r = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=h, timeout=8)
    d = r.json()
    if not d.get("success"): raise Exception(d.get("message","فشل"))
    return d["id"], d["number"]

def api_check_otp(number):
    h = {"x-api-key": API_KEY}
    try:
        r = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=h, timeout=6)
        d = r.json()
        if d.get("success"): return d.get("status"), d.get("otp"), d.get("message","")
        return None, None, ""
    except: return None, None, ""

def api_delete_number(aid):
    try: requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": aid}, headers={"x-api-key": API_KEY}, timeout=4)
    except: pass

def api_get_balance():
    try: return requests.get(f"{BASE_URL}/api/v1/balance", headers={"x-api-key": API_KEY}, timeout=6).json().get("balance","0")
    except: return "0"

# ════════════════ قاعدة البيانات ════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
        lang TEXT, balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT, service TEXT,
        assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting', otp TEXT, full_msg TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
        service TEXT, full_message TEXT, timestamp TEXT, assigned_to INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
        description TEXT, enabled INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_countries (prefix TEXT PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_services (
        service_key TEXT PRIMARY KEY, en_name TEXT, icon TEXT, ar_name TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance','0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo','')")
    for p, n in DEFAULT_COUNTRIES.items(): c.execute("INSERT OR IGNORE INTO custom_countries VALUES (?,?)",(p,n))
    for k, d in DEFAULT_SERVICES.items(): c.execute("INSERT OR IGNORE INTO custom_services VALUES (?,?,?,?)",(k,d['en'],d['icon'],d['ar']))
    conn.commit(); conn.close()

init_db()

class DB:
    @staticmethod
    def get_setting(key):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?",(key,)); r = c.fetchone(); conn.close()
        return r[0] if r else None
    @staticmethod
    def set_setting(key,val):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("REPLACE INTO settings VALUES (?,?)",(key,val)); conn.commit(); conn.close()
    @staticmethod
    def get_countries():
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT prefix,name FROM custom_countries ORDER BY name"); rows = c.fetchall(); conn.close()
        return {r[0]:r[1] for r in rows}
    @staticmethod
    def add_country(p,n):
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("INSERT OR REPLACE INTO custom_countries VALUES (?,?)",(p,n)); conn.commit(); conn.close()
    @staticmethod
    def del_country(p):
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("DELETE FROM custom_countries WHERE prefix=?",(p,)); conn.commit(); conn.close()
    @staticmethod
    def get_services():
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT service_key,en_name,icon,ar_name FROM custom_services ORDER BY ar_name"); rows = c.fetchall(); conn.close()
        return {r[0]:{"en":r[1],"icon":r[2],"ar":r[3]} for r in rows}
    @staticmethod
    def add_service(k,en,icon,ar):
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("INSERT OR REPLACE INTO custom_services VALUES (?,?,?,?)",(k,en,icon,ar)); conn.commit(); conn.close()
    @staticmethod
    def del_service(k):
        if k=="all": return
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("DELETE FROM custom_services WHERE service_key=? AND service_key!='all'",(k,)); conn.commit(); conn.close()
    @staticmethod
    def get_user(uid):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?",(uid,)); r = c.fetchone(); conn.close(); return r
    @staticmethod
    def save_user(msg):
        uid = msg.from_user.id; now = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        if not c.execute("SELECT 1 FROM users WHERE user_id=?",(uid,)).fetchone():
            c.execute("INSERT INTO users (user_id,username,first_name,last_name,first_seen,last_seen) VALUES (?,?,?,?,?,?)",
                      (uid,msg.from_user.username,msg.from_user.first_name,msg.from_user.last_name,now,now))
        else: c.execute("UPDATE users SET last_seen=? WHERE user_id=?",(now,uid))
        conn.commit(); conn.close()
    @staticmethod
    def set_lang(uid,lang):
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("UPDATE users SET lang=? WHERE user_id=?",(lang,uid)); conn.commit(); conn.close()
    @staticmethod
    def all_users():
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0"); users = [r[0] for r in c.fetchall()]; conn.close(); return users

db = DB()

# ════════════════ دوال مساعدة ════════════════
def clean(n): return str(n).replace("+","").replace("-","").replace(" ","").strip()

def detect_service(text):
    t = str(text).lower()
    if not t: return "OTP"
    for svc, kws in [("WhatsApp",["whatsapp","واتساب"]),("Telegram",["telegram","تيليجرام"]),
        ("Facebook",["facebook","فيسبوك"]),("Instagram",["instagram","انستغرام"]),
        ("TikTok",["tiktok","تيك توك"]),("IMO",["imo"]),("Snapchat",["snapchat","سناب"]),
        ("Google",["google","جوجل"]),("Twitter/X",["twitter","تويتر"]),("Discord",["discord"]),
        ("Amazon",["amazon"]),("Apple",["apple","icloud"]),("Microsoft",["microsoft"]),
        ("Uber",["uber"]),("Netflix",["netflix"]),("YouTube",["youtube"])]:
        if any(k in t for k in kws): return svc
    return "OTP"

ICONS = {"WhatsApp":"💬","Telegram":"✈️","Facebook":"📘","Instagram":"📷","TikTok":"🎵","IMO":"📞","Snapchat":"👻","Google":"🔍","Twitter/X":"🐦","Discord":"🎮","Amazon":"📦","Apple":"🍎","Microsoft":"🪟","Uber":"🚗","Netflix":"🎬","YouTube":"▶️","OTP":"🔐"}

def release(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'",(uid,))
    for (aid,) in c.fetchall():
        try: api_delete_number(aid)
        except: pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?",(aid,))
    conn.commit(); conn.close()

def assign(uid,aid,num,prefix,svc):
    release(uid)
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id,number,prefix,service,assigned_to,created_at,status) VALUES (?,?,?,?,?,?,?)",
              (aid,num,prefix,svc,uid,datetime.now().isoformat(),'waiting'))
    c.execute("UPDATE users SET total_requests=total_requests+1 WHERE user_id=?",(uid,))
    conn.commit(); conn.close()

def get_active():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT alloc_id,number,prefix,service,assigned_to,full_msg FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall(); conn.close(); return rows

def check_sub(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT channel_url FROM force_channels WHERE enabled=1"); chs = c.fetchall(); conn.close()
    if not chs: return True
    for (url,) in chs:
        try:
            ch = "@"+url.split("/")[-1] if url.startswith("https://t.me/") else url
            if bot.get_chat_member(ch,uid).status not in ["member","administrator","creator"]: return False
        except: return False
    return True

def sub_markup():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT channel_url,description FROM force_channels WHERE enabled=1"); chs = c.fetchall(); conn.close()
    if not chs: return None
    mk = types.InlineKeyboardMarkup()
    for url,desc in chs: mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 Subscribe", url=url))
    mk.add(types.InlineKeyboardButton("✅ Check", callback_data="check_sub"))
    return mk

def lang_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    return mk

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add(btn("new",uid), btn("countries",uid), btn("stats",uid))
    kb.add(btn("balance",uid), btn("invite",uid), btn("traffic",uid))
    kb.add(btn("lang",uid))
    if uid in ADMIN_IDS: kb.add(btn("admin",uid))
    return kb

def services_menu():
    services = db.get_services()
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for k, d in services.items():
        if k != "all": btns.append(types.InlineKeyboardButton(f"{d['icon']} {d['ar']}", callback_data=f"svc_{k}"))
    if "all" in services: btns.append(types.InlineKeyboardButton(f"{services['all']['icon']} {services['all']['ar']}", callback_data="svc_all"))
    for i in range(0,len(btns),3): mk.row(*btns[i:i+3])
    return mk

def countries_for_service(uid, svc):
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(f"{get_flag(p)} {n}", callback_data=f"get_{p}_{svc}") for p, n in sorted(countries.items())]
    for i in range(0,len(btns),3): mk.row(*btns[i:i+3])
    mk.row(types.InlineKeyboardButton(t("back",uid), callback_data="menu_services"))
    return mk

def num_actions(uid, prefix, svc, aid):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 "+t("btn_new",uid).split()[-1], callback_data=f"ch_{prefix}_{svc}_{aid}"),
           types.InlineKeyboardButton("🌍 "+t("btn_countries",uid).split()[-1], callback_data=f"svc_{svc}"))
    mk.row(types.InlineKeyboardButton("📞 Channel", url="https://t.me/numhj"),
           types.InlineKeyboardButton(t("back",uid), callback_data="main_menu"))
    return mk

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(msg):
    uid, cid = msg.from_user.id, msg.chat.id
    db.save_user(msg)
    u = db.get_user(uid)
    if not u or not u[4]:
        bot.send_message(cid, t("lang_select",uid), parse_mode="Markdown", reply_markup=lang_markup())
        return
    if db.get_setting("maintenance")=="1" and uid not in ADMIN_IDS:
        bot.send_message(cid, t("maintenance",uid), parse_mode="Markdown"); return
    if not check_sub(uid):
        mk = sub_markup()
        if mk: bot.send_message(cid, t("subscribe",uid), parse_mode="Markdown", reply_markup=mk)
        return
    photo = db.get_setting("welcome_photo")
    txt = t("welcome",uid)
    mk = services_menu()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

@bot.callback_query_handler(func=lambda c: c.data in ["lang_ar","lang_en"])
def set_lang(call):
    uid, cid = call.from_user.id, call.message.chat.id
    lang = "ar" if call.data=="lang_ar" else "en"
    db.set_lang(uid, lang)
    bot.answer_callback_query(call.id, t("lang_set",uid))
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    # إرسال القائمة الرئيسية من جديد
    photo = db.get_setting("welcome_photo")
    txt = t("welcome",uid)
    mk = services_menu()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

@bot.callback_query_handler(func=lambda c: c.data=="check_sub")
def check_sub_cb(call):
    uid, cid = call.from_user.id, call.message.chat.id
    if check_sub(uid):
        bot.answer_callback_query(call.id, "✅")
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        start(call.message)
    else: bot.answer_callback_query(call.id, "❌", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    uid = call.from_user.id; svc = call.data.split("_")[1]
    services = db.get_services(); svc_name = services.get(svc,{}).get("ar",svc)
    bot.edit_message_text(f"*{t('choose_country',uid)}*\n\n{svc_name}",
                          call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=countries_for_service(uid, svc))

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id; parts = call.data.split("_")
    prefix = parts[1]; svc = parts[2] if len(parts)>2 else "all"
    release(uid)
    try:
        aid, num = api_get_number(prefix); num = clean(num)
        assign(uid, aid, num, prefix, svc)
        countries = db.get_countries(); services = db.get_services()
        name = countries.get(prefix,prefix); flag = get_flag(prefix)
        svc_name = services.get(svc,{}).get("ar",svc)
        msg = t("number_assigned",uid, number=num, flag=flag, country=name, service=svc_name)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, prefix, svc, aid))
    except Exception as e: bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    uid = call.from_user.id; parts = call.data.split("_")
    prefix = parts[1]; svc = parts[2]; old_alloc = parts[3] if len(parts)>3 else None
    if old_alloc:
        api_delete_number(old_alloc)
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?",(old_alloc,)); conn.commit(); conn.close()
    release(uid)
    try:
        aid, num = api_get_number(prefix); num = clean(num)
        assign(uid, aid, num, prefix, svc)
        countries = db.get_countries(); services = db.get_services()
        name = countries.get(prefix,prefix); flag = get_flag(prefix)
        svc_name = services.get(svc,{}).get("ar",svc)
        msg = t("number_changed",uid, number=num, flag=flag, country=name, service=svc_name)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=num_actions(uid, prefix, svc, aid))
    except Exception as e: bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services","main_menu"])
def back_menu(call):
    uid = call.from_user.id
    if call.data=="menu_services":
        bot.edit_message_text(t("welcome",uid), call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=services_menu())
    else:
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        start(call.message)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = message.from_user.id; cid = message.chat.id; txt = message.text
    
    # معالجة حالات الإدارة
    state = admin_states.get(uid)
    if state == "add_prefix":
        admin_states[uid] = ("add_name", txt.strip()); bot.send_message(cid, "أرسل اسم الدولة:"); return
    if isinstance(state, tuple) and state[0]=="add_name":
        db.add_country(state[1], txt.strip()); bot.send_message(cid, f"✅ تمت الإضافة"); del admin_states[uid]; return
    if state == "add_svc_key":
        admin_states[uid] = ("add_svc_en", txt.strip().lower()); bot.send_message(cid, "أرسل اسم الخدمة بالإنجليزية:"); return
    if isinstance(state, tuple) and state[0]=="add_svc_en":
        admin_states[uid] = ("add_svc_icon", state[1], txt.strip()); bot.send_message(cid, "أرسل أيقونة:"); return
    if isinstance(state, tuple) and state[0]=="add_svc_icon":
        admin_states[uid] = ("add_svc_ar", state[1], state[2], txt.strip()); bot.send_message(cid, "أرسل الاسم بالعربية:"); return
    if isinstance(state, tuple) and state[0]=="add_svc_ar":
        db.add_service(state[1], state[2], state[3], txt.strip()); bot.send_message(cid, "✅ تمت الإضافة"); del admin_states[uid]; return
    if state == "broadcast":
        users = db.all_users(); cnt = 0
        for u in users:
            try: bot.copy_message(u, cid, message.message_id); cnt += 1; time.sleep(0.03)
            except: pass
        bot.send_message(cid, f"✅ `{cnt}`"); del admin_states[uid]; return
    if state in ["ban","unban"]:
        try:
            target = int(txt)
            conn = sqlite3.connect(DB_PATH); conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?",(target,)); conn.commit(); conn.close()
            bot.send_message(cid, "✅")
        except: bot.send_message(cid, "❌")
        del admin_states[uid]; return
    if state == "addch_url":
        admin_states[uid] = ("addch_desc", txt.strip()); bot.send_message(cid, "أرسل وصفاً:"); return
    if isinstance(state, tuple) and state[0]=="addch_desc":
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url,description) VALUES (?,?)",(state[1],txt.strip())); conn.commit(); conn.close()
        bot.send_message(cid, "✅"); del admin_states[uid]; return

    # زر اللغة    if txt in [btn("lang",uid)]:
        u = db.get_user(uid); cur = u[4] if u and u[4] else "ar"
        new_lang = "en" if cur=="ar" else "ar"; db.set_lang(uid, new_lang)
        bot.send_message(cid, t("lang_set",uid), parse_mode="Markdown")
        # تحديث الكيبورد
        bot.send_message(cid, "• • •", reply_markup=main_kb(uid))
        return

    # باقي الأزرار
    if txt in [btn("new",uid)]:
        bot.send_message(cid, t("welcome",uid), parse_mode="Markdown", reply_markup=services_menu())
    elif txt in [btn("countries",uid)]:
        countries = db.get_countries()
        msg = t("countries_list",uid) + "\n".join(f"{get_flag(p)} {n}" for p, n in sorted(countries.items()))
        bot.send_message(cid, msg, parse_mode="Markdown")
    elif txt in [btn("stats",uid)]:
        u = db.get_user(uid)
        bot.send_message(cid, t("stats",uid, r=u[6] if u else 0, o=u[7] if u else 0), parse_mode="Markdown")
    elif txt in [btn("balance",uid)]:
        u = db.get_user(uid)
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT ref_count FROM referrals WHERE user_id=?",(uid,)); refs = c.fetchone(); conn.close()
        bot.send_message(cid, t("balance",uid, b=u[5] if u else 0, ref=refs[0] if refs else 0, site=api_get_balance()), parse_mode="Markdown")
    elif txt in [btn("invite",uid)]:
        ref = f"ref{uid}"
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)",(uid,ref)); conn.commit(); conn.close()
        bot.send_message(cid, t("invite",uid, link=f"https://t.me/Taker_OTP_BOT?start={ref}"), parse_mode="Markdown")
    elif txt in [btn("traffic",uid)]:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT prefix,service,COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix,service ORDER BY COUNT(*) DESC LIMIT 10")
        rows = c.fetchall(); conn.close()
        if not rows: bot.send_message(cid, t("no_active",uid), parse_mode="Markdown")
        else:
            lines = [t("traffic",uid),""]
            for p,svc,cnt in rows:
                name = db.get_countries().get(p,p); flag = get_flag(p)
                icon = db.get_services().get(svc,{}).get("icon","🔐")
                lines.append(f"{flag} {name} {icon}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")
    elif txt in [btn("admin",uid)] and uid in ADMIN_IDS:
        admin_panel(cid, uid)

# ════════════════ لوحة الإدارة ════════════════
def admin_panel(cid, uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 Active" if db.get_setting("maintenance")!="1" else "🔴 Maintenance"
    mk.add(types.InlineKeyboardButton(f"Status: {st}", callback_data="tog"))
    mk.add(types.InlineKeyboardButton("➕ Add Country", callback_data="add_country"), types.InlineKeyboardButton("➖ Del Country", callback_data="del_country"))
    mk.add(types.InlineKeyboardButton("➕ Add Service", callback_data="add_service"), types.InlineKeyboardButton("➖ Del Service", callback_data="del_service"))
    mk.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"), types.InlineKeyboardButton("👥 Users", callback_data="users_list"))
    mk.add(types.InlineKeyboardButton("🚫 Ban", callback_data="ban"), types.InlineKeyboardButton("✅ Unban", callback_data="unban"))
    mk.add(types.InlineKeyboardButton("🔗 Force Sub", callback_data="force_sub"), types.InlineKeyboardButton("🖼️ Photo", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ Clear Data", callback_data="clear_data"), types.InlineKeyboardButton("↩️ Exit", callback_data="main_menu"))
    bot.send_message(cid, t("admin_panel",uid), parse_mode="Markdown", reply_markup=mk)

admin_states = {}

@bot.callback_query_handler(func=lambda c: c.data=="tog")
def tog(call):
    db.set_setting("maintenance","0" if db.get_setting("maintenance")=="1" else "1")
    bot.answer_callback_query(call.id,"✅"); admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="add_country")
def add_country_btn(call):
    admin_states[call.from_user.id] = "add_prefix"
    bot.edit_message_text("*➕ Send country prefix:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="del_country")
def del_country_btn(call):
    countries = db.get_countries()
    mk = types.InlineKeyboardMarkup()
    for p,n in countries.items(): mk.add(types.InlineKeyboardButton(f"{get_flag(p)} {n}", callback_data=f"delc_{p}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*Select country to delete:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delc_"))
def delc(call): db.del_country(call.data.split("_")[1]); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="add_service")
def add_service_btn(call):
    admin_states[call.from_user.id] = "add_svc_key"
    bot.edit_message_text("*➕ Send service key:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="del_service")
def del_service_btn(call):
    services = db.get_services()
    mk = types.InlineKeyboardMarkup()
    for k,d in services.items():
        if k!="all": mk.add(types.InlineKeyboardButton(f"{d['icon']} {d['ar']}", callback_data=f"dels_{k}"))
    mk.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*Select service to delete:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dels_"))
def dels(call): db.del_service(call.data.split("_")[1]); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def broadcast_btn(call):
    admin_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 Send message:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["ban","unban"])
def ban_unban_btn(call):
    admin_states[call.from_user.id] = call.data
    bot.edit_message_text("*Send user ID:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="users_list")
def users_list_btn(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id,username FROM users ORDER BY user_id DESC LIMIT 15"); rows = c.fetchall(); conn.close()
    txt = "*👥 Users:*\n\n" + "\n".join(f"• `{u}` @{un or '—'}" for u,un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="force_sub")
def force_sub_btn(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1"); chs = c.fetchall(); conn.close()
    mk = types.InlineKeyboardMarkup()
    for ch in chs: mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ Add", callback_data="addch"), types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    bot.edit_message_text("*🔗 Force Subscribe*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="addch")
def addch_btn(call):
    admin_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*Send channel URL:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch_btn(call):
    conn = sqlite3.connect(DB_PATH); conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?",(int(call.data.split("_")[1]),)); conn.commit(); conn.close()
    force_sub_btn(call)

@bot.callback_query_handler(func=lambda c: c.data=="set_photo")
def set_photo_btn(call):
    admin_states[call.from_user.id] = "photo"
    bot.edit_message_text("*Send photo:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: admin_states.get(m.from_user.id)=="photo")
def save_photo(msg):
    db.set_setting("welcome_photo", msg.photo[-1].file_id); bot.send_message(msg.chat.id, "✅"); del admin_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data=="clear_data")
def clear_data_btn(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    for t in ["users","active_numbers","otp_logs","referrals"]: c.execute(f"DELETE FROM {t}")
    conn.commit(); conn.close(); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message.chat.id, call.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="admin_back")
def admin_back_btn(call): admin_panel(call.message.chat.id, call.from_user.id)

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, service_key, uid, full_msg in get_active():
                try:
                    status, otp, raw_msg = api_check_otp(number)
                    if status == "success" and otp:
                        detected = detect_service(raw_msg) if raw_msg else db.get_services().get(service_key,{}).get("en","OTP")
                        ic = ICONS.get(detected, "🔐")
                        country = db.get_countries().get(prefix, prefix); flag = get_flag(prefix)
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try: bot.send_message(uid, t("otp_user",uid, num=number, flag=flag, country=country, icon=ic, svc=detected, code=code), parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                masked = f"{number[:4]}****{number[-3:]}" if len(number)>7 else number
                                sent = bot.send_message(cid, t("otp_group",None, flag=flag, country=country, icon=ic, svc=detected, masked=masked, code=code), parse_mode="Markdown")
                                threading.Thread(target=lambda: (time.sleep(DELETE_AFTER), bot.delete_message(cid, sent.message_id)), daemon=True).start()
                            except: pass
                        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                        c.execute("UPDATE active_numbers SET status='success',otp=?,full_msg=? WHERE alloc_id=?",(otp,raw_msg,alloc_id))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?",(uid,))
                        conn.commit(); api_delete_number(alloc_id)
                        c.execute("DELETE FROM active_numbers WHERE alloc_id=?",(alloc_id,)); conn.commit(); conn.close()
                    elif status == "expired":
                        api_delete_number(alloc_id)
                        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?",(alloc_id,)); conn.commit(); conn.close()
                except: pass
        except: pass
        time.sleep(3)

# ════════════════ Flask ════════════════
app = Flask(__name__)
@app.route('/'): return "Taker OTP Bot Running"
@app.route('/health'): return jsonify(status="ok"), 200
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=otp_loop, daemon=True).start()
    logger.info("✅ Taker OTP Bot Started")
    bot.infinity_polling()

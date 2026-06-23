# -*- coding: utf-8 -*-
import time, requests, re, os, sqlite3, threading, logging
from datetime import datetime
from telebot import types
import telebot
from flask import Flask, jsonify

# ════════════════ الإعدادات ════════════════
BOT_TOKEN = "8886084382:AAE2_zGdVYi-Px1pN0fyN_eAvO0TaopUMYo"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = "taker_pro.db"
DELETE_AFTER = 180

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ════════════════ الخدمات المتاحة ════════════════
SERVICES = {
    "whatsapp": {"name": "WhatsApp", "icon": "💬", "ar": "واتساب"},
    "facebook": {"name": "Facebook", "icon": "📘", "ar": "فيسبوك"},
    "instagram": {"name": "Instagram", "icon": "📷", "ar": "انستغرام"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "ar": "تيك توك"},
    "telegram": {"name": "Telegram", "icon": "✈️", "ar": "تيليجرام"},
    "imo": {"name": "IMO", "icon": "📞", "ar": "ايمو"},
    "all": {"name": "All Services", "icon": "🌐", "ar": "كل الخدمات"},
}

# ════════════════ الدول مع الخدمات المدعومة ════════════════
COUNTRIES_SERVICES = {
    "22501": {"name": "ساحل العاج", "flag": "🇨🇮", "services": ["whatsapp","facebook","telegram","tiktok","instagram","imo"]},
    "23276": {"name": "سيراليون", "flag": "🇸🇱", "services": ["whatsapp","facebook","telegram","imo"]},
    "26134": {"name": "مدغشقر", "flag": "🇲🇬", "services": ["whatsapp","facebook","instagram","tiktok"]},
    "44740": {"name": "المملكة المتحدة", "flag": "🇬🇧", "services": ["whatsapp","facebook","telegram","instagram","tiktok","imo"]},
    "23490": {"name": "نيجيريا", "flag": "🇳🇬", "services": ["whatsapp","facebook","telegram","imo"]},
    "25471": {"name": "كينيا", "flag": "🇰🇪", "services": ["whatsapp","facebook","telegram","instagram"]},
    "24910": {"name": "السودان", "flag": "🇸🇩", "services": ["whatsapp","facebook","telegram","imo"]},
    "49155": {"name": "ألمانيا", "flag": "🇩🇪", "services": ["whatsapp","telegram","instagram","tiktok"]},
    "23762": {"name": "الكاميرون", "flag": "🇨🇲", "services": ["whatsapp","facebook","imo"]},
    "22178": {"name": "السنغال", "flag": "🇸🇳", "services": ["whatsapp","telegram","imo"]},
    "22901": {"name": "بنين", "flag": "🇧🇯", "services": ["whatsapp","facebook"]},
    "22898": {"name": "توجو", "flag": "🇹🇬", "services": ["whatsapp","imo"]},
}

ICONS = {"WhatsApp":"💬","Telegram":"✈️","Facebook":"📘","Instagram":"📷",
         "TikTok":"🎵","IMO":"📞","OTP":"🔐"}

# ════════════════ API ════════════════
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    r = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=8)
    d = r.json()
    if not d.get("success"): raise Exception(d.get("message","فشل"))
    return d["id"], d["number"]

def api_check_otp(number):
    headers = {"x-api-key": API_KEY}
    try:
        r = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=6)
        d = r.json()
        if d.get("success"): return d.get("status"), d.get("otp"), d.get("message","")
        return None, None, ""
    except: return None, None, ""

def api_delete_number(alloc_id):
    try: requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers={"x-api-key": API_KEY}, timeout=4)
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
        balance REAL DEFAULT 0, is_banned INTEGER DEFAULT 0,
        total_requests INTEGER DEFAULT 0, total_otps INTEGER DEFAULT 0,
        first_seen TEXT, last_seen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        alloc_id TEXT PRIMARY KEY, number TEXT, prefix TEXT, service TEXT,
        assigned_to INTEGER, created_at TEXT, status TEXT DEFAULT 'waiting', otp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, otp TEXT,
        service TEXT, full_message TEXT, timestamp TEXT, assigned_to INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY, ref_code TEXT UNIQUE, ref_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, channel_url TEXT UNIQUE,
        description TEXT, enabled INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance','0')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo','')")
    conn.commit(); conn.close()

init_db()

def gs(key):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?",(key,)); r = c.fetchone(); conn.close()
    return r[0] if r else None

def ss(key,val):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("REPLACE INTO settings VALUES (?,?)",(key,val)); conn.commit(); conn.close()

def save_user(msg):
    uid = msg.from_user.id; now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    if not c.execute("SELECT 1 FROM users WHERE user_id=?",(uid,)).fetchone():
        c.execute("INSERT INTO users (user_id,username,first_name,last_name,first_seen,last_seen) VALUES (?,?,?,?,?,?)",
                  (uid,msg.from_user.username,msg.from_user.first_name,msg.from_user.last_name,now,now))
    else: c.execute("UPDATE users SET last_seen=? WHERE user_id=?",(now,uid))
    conn.commit(); conn.close()

def is_banned(uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id=?",(uid,)); r = c.fetchone(); conn.close()
    return r and r[0]==1

def get_all_users():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0"); users = [r[0] for r in c.fetchall()]; conn.close()
    return users

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
    c.execute("SELECT alloc_id,number,prefix,service,assigned_to FROM active_numbers WHERE status='waiting'")
    rows = c.fetchall(); conn.close(); return rows

def get_ref_link(uid):
    ref = f"ref{uid}"
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals VALUES (?,?,0)",(uid,ref)); conn.commit(); conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref}"

def process_ref(ref_code,new_uid):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?",(ref_code,)); r = c.fetchone()
    if r:
        c.execute("UPDATE referrals SET ref_count=ref_count+1 WHERE user_id=?",(r[0],))
        c.execute("UPDATE users SET balance=balance+0.05 WHERE user_id=?",(r[0],))
    conn.commit(); conn.close()

def clean(n): return str(n).replace("+","").replace("-","").replace(" ","").strip()

def detect_service(text):
    t = str(text).lower()
    if "whatsapp" in t or "واتساب" in t: return "WhatsApp"
    if "telegram" in t or "تيليجرام" in t: return "Telegram"
    if "facebook" in t or "فيسبوك" in t: return "Facebook"
    if "instagram" in t or "انستغرام" in t: return "Instagram"
    if "tiktok" in t or "تيك توك" in t: return "TikTok"
    if "imo" in t: return "IMO"
    return "OTP"

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
    for url,desc in chs: mk.add(types.InlineKeyboardButton(f"📢 {desc}" if desc else "📢 اشترك", url=url))
    mk.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
    return mk

# ════════════════ بوت تيليجرام ════════════════
bot = telebot.TeleBot(BOT_TOKEN)

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add("📱 احصل على رقم", "🌍 الدول", "📊 إحصائياتي")
    kb.add("💰 رصيدي", "🤝 دعوة", "🟢 المرور")
    if uid in ADMIN_IDS: kb.add("⚙️ الإدارة")
    return kb

def services_menu():
    """قائمة الخدمات الرئيسية"""
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for key, svc in SERVICES.items():
        btns.append(types.InlineKeyboardButton(f"{svc['icon']} {svc['ar']}", callback_data=f"svc_{key}"))
    for i in range(0, len(btns), 3): mk.row(*btns[i:i+3])
    return mk

def countries_for_service(service_key):
    """الدول المتاحة لخدمة معينة"""
    mk = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for prefix, data in COUNTRIES_SERVICES.items():
        if service_key == "all" or service_key in data["services"]:
            btns.append(types.InlineKeyboardButton(f"{data['flag']} {data['name']}", callback_data=f"get_{prefix}_{service_key}"))
    for i in range(0, len(btns), 3): mk.row(*btns[i:i+3])
    mk.row(types.InlineKeyboardButton("↩️ رجوع للخدمات", callback_data="menu_services"))
    return mk

def num_actions(prefix, svc, alloc_id):
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"ch_{prefix}_{svc}_{alloc_id}"),
           types.InlineKeyboardButton("🌍 دولة أخرى", callback_data=f"svc_{svc}"))
    mk.row(types.InlineKeyboardButton("📞 قناة الأكواد", url="https://t.me/numhj"),
           types.InlineKeyboardButton("↩️ رجوع", callback_data="main_menu"))
    return mk

def show_home(cid, uid):
    if gs("maintenance")=="1" and uid not in ADMIN_IDS:
        bot.send_message(cid, "⚠️ *البوت في الصيانة*", parse_mode="Markdown"); return
    if not check_sub(uid):
        mk = sub_markup()
        if mk: bot.send_message(cid, "🔒 *اشترك أولاً*", parse_mode="Markdown", reply_markup=mk)
        return
    photo = gs("welcome_photo")
    txt = ("*✨ أهلاً بك في Taker OTP*\n\n"
           "• اختر الخدمة أولاً\n"
           "• ثم اختر الدولة\n"
           "• استلم الكود فوراً\n\n"
           "*اختر الخدمة:*")
    mk = services_menu()
    if photo:
        try: bot.send_photo(cid, photo, caption=txt, parse_mode="Markdown", reply_markup=mk)
        except: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    else: bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
    bot.send_message(cid, "• • •", reply_markup=main_kb(uid))

# ════════════════ الأوامر ════════════════
@bot.message_handler(commands=['start'])
def start(msg):
    uid, cid = msg.from_user.id, msg.chat.id
    save_user(msg)
    args = msg.text.split()
    if len(args)>1 and args[1].startswith("ref"): process_ref(args[1], uid)
    show_home(cid, uid)

@bot.callback_query_handler(func=lambda c: c.data=="check_sub")
def check_sub_cb(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم"); show_home(call.message.chat.id, call.from_user.id)
    else: bot.answer_callback_query(call.id, "❌ لم تشترك", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    svc = call.data.split("_")[1]
    svc_name = SERVICES.get(svc, {}).get("ar", svc)
    bot.edit_message_text(f"*اختر الدولة لخدمة {svc_name}:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=countries_for_service(svc))

@bot.callback_query_handler(func=lambda c: c.data.startswith("get_"))
def get_number(call):
    uid = call.from_user.id
    parts = call.data.split("_")
    prefix = parts[1]; svc = parts[2] if len(parts)>2 else "all"
    release(uid)
    try:
        numbers = []
        for _ in range(3):
            try:
                aid, num = api_get_number(prefix); numbers.append((aid, clean(num)))
            except: pass
        if not numbers:
            bot.answer_callback_query(call.id, "❌ فشل جلب أرقام", show_alert=True); return
        user_data[uid] = {"prefix": prefix, "svc": svc, "numbers": numbers}
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, (aid, num) in enumerate(numbers[:3]):
            mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
        mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"get_{prefix}_{svc}"),
               types.InlineKeyboardButton("↩️ رجوع", callback_data=f"svc_{svc}"))
        data = COUNTRIES_SERVICES.get(prefix, {"name": prefix, "flag": "🌍"})
        bot.edit_message_text(f"*اختر رقماً:*\n\n{data['flag']} {data['name']}",
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=mk)
    except Exception as e: bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

user_data = {}

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick_"))
def pick_number(call):
    uid = call.from_user.id
    if uid not in user_data: return
    idx = int(call.data.split("_")[1])
    data = user_data[uid]; numbers = data["numbers"]; prefix = data["prefix"]; svc = data["svc"]
    if idx >= len(numbers): return
    aid, num = numbers[idx]
    for i, (a, n) in enumerate(numbers):
        if i != idx: api_delete_number(a)
    assign(uid, aid, num, prefix, svc)
    cdata = COUNTRIES_SERVICES.get(prefix, {"name": prefix, "flag": "🌍"})
    svc_name = SERVICES.get(svc, {}).get("ar", svc)
    now = datetime.now().strftime("%H:%M")
    bot.edit_message_text(
        f"*✅ تم تخصيص رقم*\n\n📞 `+{num}`\n🌍 {cdata['flag']} {cdata['name']}\n🛠 {svc_name}\n🕒 {now}\n⏳ بانتظار الكود...",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=num_actions(prefix, svc, aid))
    del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch_"))
def change_number(call):
    uid = call.from_user.id
    parts = call.data.split("_"); prefix = parts[1]; svc = parts[2]; old_alloc = parts[3] if len(parts)>3 else None
    if old_alloc:
        api_delete_number(old_alloc)
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("DELETE FROM active_numbers WHERE alloc_id=?",(old_alloc,)); conn.commit(); conn.close()
    release(uid)
    try:
        numbers = []
        for _ in range(3):
            try: aid, num = api_get_number(prefix); numbers.append((aid, clean(num)))
            except: pass
        if not numbers:
            bot.answer_callback_query(call.id, "❌ فشل", show_alert=True); return
        user_data[uid] = {"prefix": prefix, "svc": svc, "numbers": numbers}
        mk = types.InlineKeyboardMarkup(row_width=1)
        for i, (aid, num) in enumerate(numbers[:3]):
            mk.add(types.InlineKeyboardButton(f"{i+1}. +{num}", callback_data=f"pick_{i}"))
        mk.add(types.InlineKeyboardButton("🔄 جلب غيرها", callback_data=f"ch_{prefix}_{svc}_0"),
               types.InlineKeyboardButton("↩️ رجوع", callback_data=f"svc_{svc}"))
        cdata = COUNTRIES_SERVICES.get(prefix, {"name": prefix, "flag": "🌍"})
        bot.edit_message_text(f"*اختر رقماً:*\n\n{cdata['flag']} {cdata['name']}",
                              call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=mk)
    except Exception as e: bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["menu_services","main_menu"])
def back_menu(call):
    if call.data == "menu_services":
        bot.edit_message_text("*اختر الخدمة:*", call.message.chat.id, call.message.message_id,
                              parse_mode="Markdown", reply_markup=services_menu())
    else: show_home(call.message.chat.id, call.from_user.id)

# ════════════════ الكيبورد السفلي ════════════════
@bot.message_handler(func=lambda m: m.text in ["📱 احصل على رقم","🌍 الدول","📊 إحصائياتي","💰 رصيدي","🤝 دعوة","🟢 المرور"])
def handle_buttons(message):
    uid = message.from_user.id; cid = message.chat.id
    if message.text == "📱 احصل على رقم":
        bot.send_message(cid, "*اختر الخدمة:*", parse_mode="Markdown", reply_markup=services_menu())
    elif message.text == "🌍 الدول":
        txt = "*🌍 الدول المتاحة:*\n\n"
        for p, d in COUNTRIES_SERVICES.items():
            svcs = ", ".join([SERVICES[s]["icon"] for s in d["services"]])
            txt += f"{d['flag']} {d['name']}: {svcs}\n"
        bot.send_message(cid, txt, parse_mode="Markdown")
    elif message.text == "📊 إحصائياتي":
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT total_requests,total_otps FROM users WHERE user_id=?",(uid,)); r = c.fetchone(); conn.close()
        req, otp = r if r else (0,0)
        bot.send_message(cid, f"*📊 إحصائياتك*\n\n🔷 الطلبات: `{req}`\n🔷 الأكواد: `{otp}`", parse_mode="Markdown")
    elif message.text == "💰 رصيدي":
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?",(uid,)); bal = c.fetchone()
        c.execute("SELECT ref_count FROM referrals WHERE user_id=?",(uid,)); refs = c.fetchone(); conn.close()
        bot.send_message(cid, f"*💰 رصيدك*\n\n💎 `{bal[0] if bal else 0:.3f} USDT`\n👤 الإحالات: `{refs[0] if refs else 0}`\n🏦 الموقع: `{api_get_balance()}`", parse_mode="Markdown")
    elif message.text == "🤝 دعوة":
        link = get_ref_link(uid)
        bot.send_message(cid, f"*🤝 دعوة*\n\n🔗 `{link}`\n\n💰 `0.05 USDT` لكل صديق", parse_mode="Markdown")
    elif message.text == "🟢 المرور":
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT prefix,service,COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix,service ORDER BY COUNT(*) DESC LIMIT 10")
        rows = c.fetchall(); conn.close()
        if not rows: bot.send_message(cid, "لا توجد أرقام نشطة", parse_mode="Markdown")
        else:
            lines = ["*🟢 حركة المرور*\n"]
            for p, svc, cnt in rows:
                d = COUNTRIES_SERVICES.get(p, {"name": p, "flag": "🌍"})
                icon = SERVICES.get(svc, {}).get("icon", "🔐")
                lines.append(f"{d['flag']} {d['name']} {icon}: `{cnt}`")
            bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")

# ════════════════ لوحة الإدارة ════════════════
@bot.message_handler(func=lambda m: m.text == "⚙️ الإدارة" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    mk = types.InlineKeyboardMarkup(row_width=2)
    st = "🟢 مفتوح" if gs("maintenance")!="1" else "🔴 صيانة"
    mk.add(types.InlineKeyboardButton(f"الحالة: {st}", callback_data="tog"))
    mk.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
           types.InlineKeyboardButton("👥 مستخدمين", callback_data="users_list"))
    mk.add(types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
           types.InlineKeyboardButton("✅ فك", callback_data="unban"))
    mk.add(types.InlineKeyboardButton("🔗 اشتراك", callback_data="force_sub"),
           types.InlineKeyboardButton("🖼️ صورة", callback_data="set_photo"))
    mk.add(types.InlineKeyboardButton("🗑️ مسح", callback_data="clear_data"),
           types.InlineKeyboardButton("↩️ خروج", callback_data="main_menu"))
    bot.send_message(message.chat.id, "*⚙️ لوحة التحكم*", parse_mode="Markdown", reply_markup=mk)

admin_states = {}

@bot.callback_query_handler(func=lambda c: c.data=="tog")
def tog(call): ss("maintenance","0" if gs("maintenance")=="1" else "1"); bot.answer_callback_query(call.id,"✅"); admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def broadcast(call):
    admin_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("*📢 أرسل الرسالة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["ban","unban"])
def ban_unban(call):
    admin_states[call.from_user.id] = call.data
    bot.edit_message_text("*أرسل ID:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="users_list")
def users_list(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT user_id,username FROM users ORDER BY user_id DESC LIMIT 15"); rows = c.fetchall(); conn.close()
    txt = "*👥 آخر المستخدمين:*\n\n" + "\n".join(f"• `{u}` @{un or '—'}" for u, un in rows)
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data=="force_sub")
def force_sub(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM force_channels WHERE enabled=1"); chs = c.fetchall(); conn.close()
    mk = types.InlineKeyboardMarkup()
    for ch in chs: mk.add(types.InlineKeyboardButton(f"{'✅' if ch[4] else '❌'} {ch[2]}", callback_data=f"edch_{ch[0]}"))
    mk.add(types.InlineKeyboardButton("➕ إضافة", callback_data="addch"), types.InlineKeyboardButton("🔙", callback_data="admin_back"))
    bot.edit_message_text("*🔗 قنوات الاشتراك*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data=="addch")
def addch(call):
    admin_states[call.from_user.id] = "addch_url"
    bot.edit_message_text("*أرسل رابط القناة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("edch_"))
def edch(call):
    conn = sqlite3.connect(DB_PATH); conn.cursor().execute("UPDATE force_channels SET enabled=1-enabled WHERE id=?",(int(call.data.split("_")[1]),)); conn.commit(); conn.close()
    force_sub(call)

@bot.callback_query_handler(func=lambda c: c.data=="set_photo")
def set_photo(call):
    admin_states[call.from_user.id] = "photo"
    bot.edit_message_text("*أرسل الصورة:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: admin_states.get(m.from_user.id)=="photo")
def save_photo(msg): ss("welcome_photo", msg.photo[-1].file_id); bot.send_message(msg.chat.id, "✅ تم"); del admin_states[msg.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data=="clear_data")
def clear_data(call):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    for t in ["users","active_numbers","otp_logs","referrals"]: c.execute(f"DELETE FROM {t}")
    conn.commit(); conn.close(); bot.answer_callback_query(call.id, "✅ تم"); admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data=="admin_back")
def admin_back(call): admin_panel(call.message)

# ════════════════ المعالج الموحد ════════════════
@bot.message_handler(func=lambda m: True)
def universal_handler(message):
    uid = message.from_user.id; cid = message.chat.id; txt = message.text; state = admin_states.get(uid)
    if state == "broadcast":
        users = get_all_users(); cnt = 0
        for u in users:
            try: bot.copy_message(u, cid, message.message_id); cnt += 1; time.sleep(0.02)
            except: pass
        bot.send_message(cid, f"✅ `{cnt}` مستخدم", parse_mode="Markdown"); del admin_states[uid]; return
    if state in ["ban","unban"]:
        try:
            target = int(txt)
            conn = sqlite3.connect(DB_PATH); conn.cursor().execute(f"UPDATE users SET is_banned={'1' if state=='ban' else '0'} WHERE user_id=?",(target,)); conn.commit(); conn.close()
            bot.send_message(cid, "✅ تم", parse_mode="Markdown")
        except: bot.send_message(cid, "❌ خطأ")
        del admin_states[uid]; return
    if state == "addch_url":
        admin_states[uid] = ("addch_desc", txt.strip()); bot.send_message(cid, "أرسل وصفاً:"); return
    if isinstance(state, tuple) and state[0] == "addch_desc":
        conn = sqlite3.connect(DB_PATH); conn.cursor().execute("INSERT OR IGNORE INTO force_channels (channel_url,description) VALUES (?,?)",(state[1],txt.strip())); conn.commit(); conn.close()
        bot.send_message(cid, "✅ تمت"); del admin_states[uid]; return

# ════════════════ حلقة فحص OTP ════════════════
def otp_loop():
    while True:
        try:
            for alloc_id, number, prefix, svc, uid in get_active():
                try:
                    status, otp, raw_msg = api_check_otp(number)
                    if status == "success" and otp:
                        service = detect_service(raw_msg) if raw_msg else SERVICES.get(svc,{}).get("name","OTP")
                        ic = ICONS.get(service, "🔐")
                        cdata = COUNTRIES_SERVICES.get(prefix, {"name": prefix, "flag": "🌍"})
                        code = f"{otp[:3]}-{otp[3:]}" if len(otp)>3 else otp
                        if uid:
                            try: bot.send_message(uid, f"*🔐 كود جديد*\n\n📞 `+{number}`\n🌍 {cdata['flag']} {cdata['name']}\n{ic} *{service}*\n🔢 `{code}`", parse_mode="Markdown")
                            except: pass
                        for cid in CHAT_IDS:
                            try:
                                sent = bot.send_message(cid, f"*🔐 كود جديد*\n\n🌍 {cdata['flag']} {cdata['name']} | {ic} {service}\n📞 `{number[:4]}****{number[-3:]}`\n🔢 `{code}`", parse_mode="Markdown")
                                threading.Thread(target=lambda: (time.sleep(DELETE_AFTER), bot.delete_message(cid, sent.message_id)), daemon=True).start()
                            except: pass
                        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                        c.execute("UPDATE active_numbers SET status='success',otp=? WHERE alloc_id=?",(otp,alloc_id))
                        c.execute("UPDATE users SET total_otps=total_otps+1 WHERE user_id=?",(uid,))
                        c.execute("INSERT INTO otp_logs (number,otp,service,full_message,timestamp,assigned_to) VALUES (?,?,?,?,?,?)",
                                 (number,otp,service,raw_msg,datetime.now().isoformat(),uid))
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
    logger.info("✅ البوت يعمل...")
    bot.infinity_polling()

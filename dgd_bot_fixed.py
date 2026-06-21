# ======================================================================================
# XWD SMS - النسخة النهائية (مع إشعار الأدمن عند نفاذ الرصيد)
# المطور: hacker Taker
# ======================================================================================
import time, requests, json, re, os, sqlite3, threading, traceback, random, logging
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8686995713:AAFTesnEDbFJcSgtM3IrURU0WtPdNkJtO4c"
CHAT_IDS = ["-1003789271722"]
ADMIN_IDS = [8728019066, 8972941677]
DB_PATH = os.environ.get("DB_PATH", "xwd_bot.db")

XWD_API_KEY = "9861618abcb119e317c6051000a5997c"
XWD_BASE_URL = "https://xwdsms.org/api/v1"

bot = telebot.TeleBot(BOT_TOKEN)
BOT_ACTIVE = True

AVAILABLE_COUNTRIES = {
    "22501": ("ساحل العاج", "🇨🇮", ["2250765XXXXX"]),
    "49155": ("ألمانيا", "🇩🇪", ["4915511382XXXX"]),
    "26134": ("مدغشقر", "🇲🇬", ["26134143XXXX"]),
    "23762": ("الكاميرون", "🇨🇲", ["237621XXXXXX"]),
    "22178": ("السنغال", "🇸🇳", ["221785XXXXXX"]),
    "22901": ("بنين", "🇧🇯", ["2290192273XXXX"]),
    "23276": ("سيراليون", "🇸🇱", ["23276XXXXXX"]),
    "22898": ("توغو", "🇹🇬", ["2289871XXXXXX"]),
    "44740": ("المملكة المتحدة", "🇬🇧", ["44740XXXXXX"]),
    "23490": ("نيجيريا", "🇳🇬", ["23490XXXXXX"]),
    "25471": ("كينيا", "🇰🇪", ["25471XXXXXX"]),
}

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

def xwd_get_number(range_str):
    url = f"{XWD_BASE_URL}/get-number"
    headers = {"x-api-key": XWD_API_KEY, "Content-Type": "application/json"}
    payload = {"range": range_str}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code != 200: raise Exception(f"خطأ في الخادم (الكود: {resp.status_code})")
        data = resp.json()
        if not data.get("success"):
            msg = data.get("message", "فشل غير معروف")
            if "balance" in msg.lower() or "insufficient" in msg.lower():
                # إرسال إشعار للأدمن لأن الرصيد خلص
                for admin in ADMIN_IDS:
                    try:
                        bot.send_message(admin, "⚠️ <b>تنبيه هام:</b>\nرصيد موقع XWD SMS قد نفذ (0.0000 دولار).\nالبوت متوقف عن جلب الأرقام.\nيرجى شحن الحساب أو البحث عن موقع بديل.", parse_mode="HTML")
                    except: pass
                msg = "⚠️ رصيد الموقع غير كافٍ، يرجى شحن الحساب."
            raise Exception(msg)
        number = data.get("number")
        if not number: raise Exception("لم يتم استلام رقم")
        return str(number).strip()
    except Exception as e: logger.error(f"XWD get_number error: {e}"); raise

def xwd_check_otp(phone):
    url = f"{XWD_BASE_URL}/check-otp"
    headers = {"x-api-key": XWD_API_KEY, "Accept": "application/json"}
    params = {"number": phone}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code != 200: raise Exception(f"خطأ في الخادم (الكود: {resp.status_code})")
        data = resp.json()
        if not data.get("success"): raise Exception(data.get("message", "فشل الفحص"))
        otp = data.get("otp")
        return {"status": "SUKSES", "otp": otp} if otp else {"status": "WAIT", "otp": None}
    except Exception as e: logger.error(f"XWD check_otp error: {e}"); raise

def mask_number(num): num = str(num); return "XXXX" + num[-4:] if len(num) > 8 else num

def get_country_info_by_num(num):
    num = re.sub(r'\D', '', str(num))
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items():
        if num.startswith(code): return name, flag
    return "غير معروف", "🌍"

def extract_otp(t): 
    m = re.search(r'(?:code|otp|رمز|كود|verification|pin)[:\s]*(\d{4,8})', t, re.IGNORECASE) or re.search(r'\b(\d{4,8})\b', t); return m.group(1) if m else "N/A"

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
                except: pass
            time.sleep(3) # سريع جداً (فحص كل 3 ثوانٍ)
        except: time.sleep(5)

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
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 تغيير", callback_data=f"country_{code}"), types.InlineKeyboardButton("🔙 القائمة", callback_data="back"))
            bot.edit_message_text(msg, c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)
            bot.answer_callback_query(c.id, "✅ تم تعيين الرقم.")
        except Exception as e:
            bot.edit_message_text(f"❌ فشل جلب الرقم:\n{str(e)}", c.message.chat.id, c.message.message_id)
    except Exception as e: logger.error(f"Country Error: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "back")
def back_h(c):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag, _) in AVAILABLE_COUNTRIES.items(): markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"country_{code}"))
    bot.edit_message_text("🌍 اختر الدولة:", c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_h(m):
    if is_banned(m.from_user.id): return bot.reply_to(m, "🚫 محظور.")
    save_user(m.from_user.id, username=m.from_user.username or "", first_name=m.from_user.first_name or "")
    bot.send_message(m.chat.id, "🌍 أهلاً! اختر الدولة للحصول على رقم:", parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(row_width=2).add(*[types.InlineKeyboardButton(f"{f} {n}", callback_data=f"country_{c}") for c, (n, f, _) in AVAILABLE_COUNTRIES.items()]))

if __name__ == "__main__":
    threading.Thread(target=main_loop, daemon=True).start()
    while True:
        try: bot.polling(none_stop=True)
        except Exception as e: logger.error(f"Polling Error: {e}"); time.sleep(5)

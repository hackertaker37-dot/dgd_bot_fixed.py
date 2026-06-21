import time
import requests
import json
import re
import os
import sqlite3
import threading
import traceback
from datetime import datetime, timedelta
from telebot import types
import telebot
from flask import Flask, jsonify

# ================= الإعدادات الأساسية (من بياناتك) =================
BOT_TOKEN = "8686995713:AAFTesnEDbFJcSgtM3IrURU0WtPdNkJtO4c"
API_KEY = "4886d4297bcfb669bf3b3d2d8d1c4ee2"
BASE_URL = "http://xwdsms.org"
CHAT_IDS = ["-1003789271722"]          # الجروب الرسمي
ADMIN_IDS = [8728019066, 8972941677]  # الأدمن
DB_PATH = "xwdsms_bot.db"

# ================= الدول المتاحة فقط =================
AVAILABLE_COUNTRIES = {
    "22501": ("ساحل العاج", "🇨🇮"),
    "23276": ("سيراليون", "🇸🇱"),
    "26134": ("مدغشقر", "🇲🇬"),
    "44740": ("المملكة المتحدة", "🇬🇧"),
    "23490": ("نيجيريا", "🇳🇬"),
    "25471": ("كينيا", "🇰🇪")
}

# ================= قاعدة البيانات =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        ref_by INTEGER,
        balance REAL DEFAULT 0,
        is_banned INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS active_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alloc_id TEXT,
        number TEXT,
        prefix TEXT,
        assigned_to INTEGER,
        created_at TEXT,
        status TEXT DEFAULT 'waiting'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT,
        otp TEXT,
        service TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        ref_code TEXT UNIQUE,
        ref_count INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_sub_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_url TEXT UNIQUE,
        description TEXT,
        enabled INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('welcome_photo', '')")
    conn.commit()
    conn.close()

init_db()

# ================= دوال API الخاصة بـ xwdsms.org =================
def api_get_number(prefix):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(f"{BASE_URL}/api/v1/get-number", json={"range": prefix}, headers=headers, timeout=20)
    data = resp.json()
    if data.get("success"):
        return data["id"], data["number"]
    else:
        raise Exception(data.get("message", "فشل جلب الرقم"))

def api_check_otp(number):
    headers = {"x-api-key": API_KEY}
    resp = requests.get(f"{BASE_URL}/api/v1/check-otp", params={"number": number}, headers=headers, timeout=20)
    data = resp.json()
    if data.get("success"):
        return data.get("status"), data.get("otp")
    return None, None

def api_delete_number(alloc_id):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(f"{BASE_URL}/api/v1/delete-number", json={"id": alloc_id}, headers=headers, timeout=20)
    return resp.json().get("success", False)

def api_get_balance():
    headers = {"x-api-key": API_KEY}
    resp = requests.get(f"{BASE_URL}/api/v1/balance", headers=headers, timeout=20)
    data = resp.json()
    return data.get("balance", "غير معروف")

# ================= بوت التليجرام =================
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# الكيبورد السفلي الدائم (الأزرار الأساسية)
def main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn1 = types.KeyboardButton("🔵 الحصول على رقم")
    btn2 = types.KeyboardButton("🟢 الرصيد")
    btn3 = types.KeyboardButton("🔴 شارك واربح F2P")
    btn4 = types.KeyboardButton("🔵 سحب الرصيد")
    btn5 = types.KeyboardButton("🔵 الإحصائيات")
    btn6 = types.KeyboardButton("🟢 الترافيك المباشر")
    if user_id in ADMIN_IDS:
        btn7 = types.KeyboardButton("🔐 Admin Panel")
        kb.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    else:
        kb.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return kb

# لوحة الأزرار بعد الحصول على رقم (inline)
def number_actions_markup(prefix, alloc_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔴 تغيير الرقم", callback_data=f"change_{prefix}_{alloc_id}"),
        types.InlineKeyboardButton("🔵 تغيير الدولة", callback_data="back_to_countries")
    )
    markup.row(
        types.InlineKeyboardButton("🟢 جروب البوت", url="https://t.me/numhj"),
        types.InlineKeyboardButton("⚫ القائمة الرئيسية", callback_data="main_menu")
    )
    return markup

# قائمة اختيار الدولة
def country_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, (name, flag) in AVAILABLE_COUNTRIES.items():
        markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"getnum_{code}"))
    return markup

# ================= أوامر البوت =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # فحص الصيانة
    if get_setting("maintenance") == "1" and user_id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⚠️ البوت في وضع الصيانة حالياً")
        return
    # حفظ المستخدم
    save_user(message)
    # فحص الاشتراك الإجباري
    if not check_force_sub(user_id, message):
        return
    # معالجة دعوة (start مع ref)
    ref_arg = message.text.split()
    if len(ref_arg) > 1 and ref_arg[1].startswith("ref"):
        try:
            ref_code = ref_arg[1].split("ref")[1]
            process_referral(ref_code, user_id)
        except:
            pass
    # إرسال الترحيب
    welcome_photo = get_setting("welcome_photo")
    text = "🌍 <b>مرحباً بك في بوت Taker OTP</b>\nاختر الدولة للحصول على رقم:"
    markup = country_menu_markup()
    if welcome_photo:
        try:
            bot.send_photo(message.chat.id, welcome_photo, caption=text, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    bot.send_message(message.chat.id, "استخدم الأزرار للتنقل:", reply_markup=main_keyboard(user_id))

# الأزرار النصية (الكيبورد السفلي)
@bot.message_handler(func=lambda m: m.text in [
    "🔵 الحصول على رقم", "🟢 الرصيد", "🔴 شارك واربح F2P",
    "🔵 سحب الرصيد", "🔵 الإحصائيات", "🟢 الترافيك المباشر"
])
def handle_main_buttons(message):
    user_id = message.from_user.id
    if message.text == "🔵 الحصول على رقم":
        bot.send_message(message.chat.id, "اختر الدولة:", reply_markup=country_menu_markup())
    elif message.text == "🟢 الرصيد":
        try:
            balance = api_get_balance()
            bot.send_message(message.chat.id, f"💰 رصيدك الحالي: {balance}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ تعذر جلب الرصيد: {e}")
    elif message.text == "🔴 شارك واربح F2P":
        ref_link = get_ref_link(user_id)
        bot.send_message(message.chat.id, f"🔗 رابط الدعوة الخاص بك:\n{ref_link}\nشاركه مع أصدقائك واربح!")
    elif message.text == "🔵 سحب الرصيد":
        bot.send_message(message.chat.id, "لطلب سحب الرصيد تواصل مع الأدمن @hackerTaker")
    elif message.text == "🔵 الإحصائيات":
        stats = get_stats()
        bot.send_message(message.chat.id, stats, parse_mode="HTML")
    elif message.text == "🟢 الترافيك المباشر":
        traffic = get_traffic()
        bot.send_message(message.chat.id, traffic, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("getnum_"))
def request_number(call):
    user_id = call.from_user.id
    prefix = call.data.split("_")[1]
    if prefix not in AVAILABLE_COUNTRIES:
        bot.answer_callback_query(call.id, "❌ دولة غير متاحة")
        return
    # إلغاء أي رقم سابق
    release_old_number(user_id)
    try:
        alloc_id, number = api_get_number(prefix)
        name, flag = AVAILABLE_COUNTRIES[prefix]
        # حفظ في قاعدة البيانات
        save_active_number(alloc_id, number, prefix, user_id)
        # تحديث المستخدم
        update_user_number(user_id, number)
        markup = number_actions_markup(prefix, alloc_id)
        msg = f"✅ تم تعيين رقم:\n📞 +{number}\n🌍 {flag} {name}\n⏳ بانتظار الكود..."
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ فشل: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("change_"))
def change_number(call):
    parts = call.data.split("_")
    prefix = parts[1]
    old_alloc_id = parts[2] if len(parts) > 2 else None
    user_id = call.from_user.id
    if old_alloc_id:
        try:
            api_delete_number(old_alloc_id)
        except:
            pass
        remove_active_number(old_alloc_id)
    # طلب رقم جديد بنفس الدولة
    try:
        alloc_id, number = api_get_number(prefix)
        name, flag = AVAILABLE_COUNTRIES[prefix]
        release_old_number(user_id)
        save_active_number(alloc_id, number, prefix, user_id)
        update_user_number(user_id, number)
        markup = number_actions_markup(prefix, alloc_id)
        msg = f"✅ تم تغيير الرقم:\n📞 +{number}\n🌍 {flag} {name}\n⏳ بانتظار الكود..."
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ فشل: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data in ["back_to_countries", "main_menu"])
def back_to_menu(call):
    if call.data == "back_to_countries":
        bot.edit_message_text("اختر الدولة:", call.message.chat.id, call.message.message_id, reply_markup=country_menu_markup())
    else:
        start(call.message)

# ================= لوحة الإدارة (Admin Panel) =================
def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    status = "🟢 يعمل" if get_setting("maintenance") != "1" else "🔴 صيانة"
    markup.add(types.InlineKeyboardButton(f"حالة البوت: {status}", callback_data="toggle_maintenance"))
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")
    )
    markup.row(
        types.InlineKeyboardButton("🔗 الاشتراك الإجباري", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🖼️ صورة الترحيب", callback_data="admin_photo")
    )
    markup.row(
        types.InlineKeyboardButton("🗑️ مسح البيانات", callback_data="admin_clear"),
        types.InlineKeyboardButton("🔙 خروج", callback_data="main_menu")
    )
    return markup

@bot.message_handler(func=lambda m: m.text == "🔐 Admin Panel" and m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    bot.send_message(message.chat.id, "<b>لوحة الإدارة</b>", parse_mode="HTML", reply_markup=admin_main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "toggle_maintenance")
def toggle_maintenance(call):
    if call.from_user.id not in ADMIN_IDS: return
    current = get_setting("maintenance") == "1"
    set_setting("maintenance", "0" if current else "1")
    bot.answer_callback_query(call.id, f"تم تغيير الحالة إلى {'صيانة' if not current else 'تشغيل'}")
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def broadcast_prompt(call):
    if call.from_user.id not in ADMIN_IDS: return
    user_states[call.from_user.id] = "broadcast"
    bot.edit_message_text("أرسل الرسالة للإذاعة (نص/صورة/ملف):", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast")
def broadcast_execute(message):
    count = 0
    for uid in get_all_users():
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(message.chat.id, f"✅ تم الإرسال إلى {count} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_users")
def admin_users(call):
    users = get_all_users()
    text = f"إجمالي المستخدمين: {len(users)}"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "admin_force_sub")
def force_sub_menu(call):
    channels = get_force_channels()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        status = "✅" if ch[3] else "❌"
        markup.add(types.InlineKeyboardButton(f"{status} {ch[2]}", callback_data=f"editforce_{ch[0]}"))
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="addforce"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("قنوات الاشتراك الإجباري:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "admin_photo")
def photo_menu(call):
    user_states[call.from_user.id] = "photo"
    bot.edit_message_text("أرسل الصورة الجديدة للترحيب:", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.from_user.id) == "photo")
def save_photo(message):
    set_setting("welcome_photo", message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم حفظ الصورة")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda c: c.data == "admin_clear")
def clear_data(call):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM active_numbers")
    c.execute("DELETE FROM otp_logs")
    c.execute("DELETE FROM referrals")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "تم مسح جميع البيانات")
    admin_panel(call.message)

# دوال مساعدة
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def save_user(message):
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                  (user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
    conn.commit()
    conn.close()

def check_force_sub(user_id, message):
    channels = get_force_channels()
    if not channels:
        return True
    markup = types.InlineKeyboardMarkup()
    all_subscribed = True
    for ch in channels:
        try:
            member = bot.get_chat_member(ch[1], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                all_subscribed = False
                markup.add(types.InlineKeyboardButton(f"اشترك في {ch[2]}", url=ch[1]))
        except:
            pass
    if not all_subscribed:
        markup.add(types.InlineKeyboardButton("✅ تحقق", callback_data="check_sub"))
        bot.send_message(message.chat.id, "🔒 يرجى الاشتراك في القنوات أولاً", reply_markup=markup)
    return all_subscribed

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub(call):
    if check_force_sub(call.from_user.id, call.message):
        bot.answer_callback_query(call.id, "✅ تم التحقق")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد", show_alert=True)

def get_force_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM force_sub_channels WHERE enabled=1")
    rows = c.fetchall()
    conn.close()
    return rows

def get_ref_link(user_id):
    ref_code = f"ref{user_id}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO referrals (user_id, ref_code) VALUES (?, ?)", (user_id, ref_code))
    conn.commit()
    conn.close()
    return f"https://t.me/Taker_OTP_BOT?start={ref_code}"

def process_referral(ref_code, new_user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM referrals WHERE ref_code=?", (ref_code,))
    row = c.fetchone()
    if row:
        referrer_id = row[0]
        c.execute("UPDATE referrals SET ref_count = ref_count + 1 WHERE user_id=?", (referrer_id,))
        c.execute("UPDATE users SET ref_by=? WHERE user_id=?", (referrer_id, new_user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def save_active_number(alloc_id, number, prefix, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO active_numbers (alloc_id, number, prefix, assigned_to, created_at) VALUES (?, ?, ?, ?, ?)",
              (alloc_id, number, prefix, user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def remove_active_number(alloc_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (alloc_id,))
    conn.commit()
    conn.close()

def release_old_number(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT alloc_id FROM active_numbers WHERE assigned_to=? AND status='waiting'", (user_id,))
    old = c.fetchone()
    if old:
        try:
            api_delete_number(old[0])
        except:
            pass
        c.execute("DELETE FROM active_numbers WHERE alloc_id=?", (old[0],))
    conn.commit()
    conn.close()

def update_user_number(user_id, number):
    pass  # Not strictly needed, we use active_numbers table

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM active_numbers WHERE status='waiting'")
    active = c.fetchone()[0]
    conn.close()
    return f"👥 المستخدمين: {users}\n📱 الأرقام النشطة: {active}"

def get_traffic():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix, COUNT(*) FROM active_numbers WHERE status='waiting' GROUP BY prefix")
    rows = c.fetchall()
    if not rows:
        return "لا توجد أرقام نشطة حالياً"
    text = "🟢 الترافيك المباشر (أرقام نشطة):\n"
    for row in rows:
        name, flag = AVAILABLE_COUNTRIES.get(row[0], ("غير معروف", ""))
        text += f"{flag} {name}: {row[1]} رقم\n"
    conn.close()
    return text

# ================= الحلقة الرئيسية لفحص الـ OTP تلقائياً =================
def otp_checker():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT alloc_id, number, prefix, assigned_to FROM active_numbers WHERE status='waiting'")
            active = c.fetchall()
            conn.close()
            for alloc_id, number, prefix, user_id in active:
                try:
                    status, otp = api_check_otp(number)
                    if status == "success" and otp:
                        # إرسال الكود للمستخدم
                        if user_id:
                            try:
                                bot.send_message(user_id, f"🔐 الكود الخاص بك: {otp}")
                            except:
                                pass
                        # إرسال للجروب
                        name, flag = AVAILABLE_COUNTRIES.get(prefix, ("غير معروف", ""))
                        msg = f"📱 رقم: +{number}\n🌍 {flag} {name}\n🔢 الكود: {otp}"
                        for chat_id in CHAT_IDS:
                            try:
                                bot.send_message(chat_id, msg)
                            except:
                                pass
                        # حذف الرقم من API وقاعدة البيانات
                        try:
                            api_delete_number(alloc_id)
                        except:
                            pass
                        remove_active_number(alloc_id)
                        # تسجيل الكود
                        log_otp(number, otp, detect_service(otp))
                    elif status == "expired":
                        try:
                            api_delete_number(alloc_id)
                        except:
                            pass
                        remove_active_number(alloc_id)
                except Exception as e:
                    print(f"Error checking {number}: {e}")
        except Exception as e:
            print(f"Checker loop error: {e}")
        time.sleep(3)  # فحص كل 3 ثواني

def detect_service(text):
    # دالة بسيطة لاكتشاف الخدمة من الكود (اختياري)
    return "OTP"

def log_otp(number, otp, service):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, service, timestamp) VALUES (?, ?, ?, ?)",
              (number, otp, service, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ================= خادم Flask (ضروري لـ Render) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= بدء التشغيل =================
if __name__ == "__main__":
    # تشغيل فحص OTP في خيط منفصل
    threading.Thread(target=otp_checker, daemon=True).start()
    # تشغيل خادم الويب في خيط منفصل
    threading.Thread(target=run_web, daemon=True).start()
    # تشغيل بوت التليجرام
    print("✅ بوت Taker OTP يعمل الآن...")
    bot.infinity_polling()

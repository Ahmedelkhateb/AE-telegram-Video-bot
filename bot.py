import telebot
import yt_dlp
import os
import tempfile
import shutil
import time
import threading
import socket
import json
from flask import Flask, send_from_directory
from dotenv import load_dotenv

# تحميل التوكن من .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# إعداد البوت
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
# تحميل المستخدمين المحفوظين من ملف users.json إذا كان موجود
try:
    with open("users.json", "r") as f:
        saved_users = json.load(f)
except FileNotFoundError:
    saved_users = []

pending_links = {}
pending_large_file_confirmation = {}
TEMP_DIR = "downloads"
BANNED_USERS = []
user_stats_file = "user_stats.json"
banned_users_file = "banned_users.json"

# تعيين ID الأدمن
ADMIN_ID = 1443572090

# إنشاء مجلد التنزيل المؤقت إذا لم يكن موجود
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# تحميل أو تهيئة الإحصائيات
if os.path.exists(user_stats_file):
    with open(user_stats_file, "r") as f:
        user_stats = json.load(f)
else:
    user_stats = {}

# تحميل أو تهيئة قائمة الحظر
if os.path.exists(banned_users_file):
    with open(banned_users_file, "r") as f:
        BANNED_USERS = json.load(f)
else:
    BANNED_USERS = []

def save_user_stats():
    with open(user_stats_file, "w") as f:
        json.dump(user_stats, f)

def save_banned_users():
    with open(banned_users_file, "w") as f:
        json.dump(BANNED_USERS, f)

def update_user_stats(chat_id, is_audio):
    str_id = str(chat_id)
    if str_id not in user_stats:
        user_stats[str_id] = {"name": "", "total": 0, "audio": 0, "video": 0}
    
    # التحقق من وجود "name"
    if "name" not in user_stats[str_id] or not user_stats[str_id]["name"]:
        try:
            chat_info = bot.get_chat(chat_id)
            user_stats[str_id]["name"] = chat_info.username or chat_info.first_name or "غير معروف"
        except:
            user_stats[str_id]["name"] = "غير معروف"

    user_stats[str_id]["total"] += 1
    if is_audio:
        user_stats[str_id]["audio"] += 1
    else:
        user_stats[str_id]["video"] += 1
    save_user_stats()



# تنظيف الملفات القديمة
def cleanup_old_files(directory, max_age_seconds=86400):
    now = time.time()
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > max_age_seconds:
                os.remove(path)
        except Exception as e:
            print(f"خطأ أثناء حذف {path}: {e}")

cleanup_old_files(TEMP_DIR)

# تشغيل Flask لخدمة الملفات الكبيرة
app = Flask(__name__)
@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(TEMP_DIR, filename, as_attachment=True)

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# الحصول على IP السيرفر
def get_server_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "localhost"
    finally:
        s.close()
    return ip

# أمر المساعدة
@bot.message_handler(commands=['help'])
def help_command(message):
    if message.chat.id == ADMIN_ID:
        reply = "ℹ️ قائمة الأوامر المتاحة لك كأدمن:\n\n"
        reply += "/start - بدء استخدام البوت\n"
        reply += "/help - عرض المساعدة\n"
        reply += "/stats - عرض إحصائياتك\n"
        reply += "/admin_stats - إحصائيات جميع المستخدمين\n"
        reply += "/ban <id> - حظر مستخدم\n"
        reply += "/unban <id> - إلغاء الحظر\n"
        reply += "/banned - عرض المحظورين\n"
        reply += "/find <id أو اسم> - البحث عن مستخدم"
    else:
        reply = "📘 طريقة استخدام البوت:\n\n"
        reply += "1. أرسل رابط الفيديو من أي موقع يدعمه البوت.\n"
        reply += "2. اختر نوع التحميل (🎧 صوت أو 🎥 فيديو).\n"
        reply += "3. سيتم تحميل الملف وإرساله لك مباشرة، أو سيظهر لك رابط تحميل مباشر في حال كان حجمه كبيرًا.\n\n"
        reply += "🔹 أوامر المستخدم:\n"
        reply += "/start - بدء استخدام البوت\n"
        reply += "/help - عرض المساعدة\n"
        reply += "/stats - عرض إحصائياتك"
    bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    username = message.from_user.username
    if username and username not in saved_users:
        saved_users.append(username)
        with open("users.json", "w") as f:
            json.dump(saved_users, f)

    if message.chat.id in BANNED_USERS:
        return

    # تسجيل المستخدم في ملف users.txt
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name

    user_entry = f"{user_id} - {username}"

    # تحميل كل المستخدمين
    if not os.path.exists("users.txt"):
        open("users.txt", "w", encoding="utf-8").close()

    with open("users.txt", "r", encoding="utf-8") as f:
        users = f.read().splitlines()

    user_ids = [line.split(" - ")[0] for line in users]

    if user_id in user_ids:
        # تحقق إن الاسم تغيّر، ثم عدله
        updated_users = []
        for line in users:
            uid, uname = line.split(" - ", 1)
            if uid == user_id and uname != username:
                updated_users.append(f"{uid} - {username}")
            else:
                updated_users.append(line)
        with open("users.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(updated_users) + "\n")
    else:
        with open("users.txt", "a", encoding="utf-8") as f:
            f.write(user_entry + "\n")

    update_user_stats(message.chat.id, is_audio=False)

    bot.reply_to(message, "👋 أهلاً بيك!\nارسل لي رابط الفيديو من أي موقع، وهخليه جاهز ليك سواء فيديو أو صوت 🎧🎥")

@bot.message_handler(commands=['stats'])
def show_user_stats(message):
    if message.chat.id in BANNED_USERS:
        return
    user_id = str(message.chat.id)
    if user_id in user_stats:
        stats = user_stats[user_id]
        reply = f"📊 إحصائياتك:\n\n" \
                f"🔗 عدد الروابط: {stats['total']}\n" \
                f"🎥 فيديو: {stats['video']}\n" \
                f"🎧 صوت: {stats['audio']}"
    else:
        reply = "لا توجد إحصائيات لك حتى الآن."
    bot.send_message(message.chat.id, reply)

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def ask_format(message):
    if message.chat.id in BANNED_USERS:
        return
    url = message.text.strip()
    pending_links[message.chat.id] = url

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("🎧 تحميل صوت", "🎥 تحميل فيديو")
    bot.send_message(message.chat.id, "اختار نوع التحميل اللي تفضله:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🎧 تحميل صوت", "🎥 تحميل فيديو"])
def download_choice(message):
    if message.chat.id in BANNED_USERS:
        return

    choice = message.text
    chat_id = message.chat.id

    if chat_id not in pending_links:
        bot.send_message(chat_id, "❗من فضلك ابعت رابط الأول.")
        return

    url = pending_links.pop(chat_id)
    is_audio = (choice == "🎧 تحميل صوت")
    bot.send_message(chat_id, "📥 جارٍ التحميل... انتظر لحظات ⏳")

    tmpdir = tempfile.mkdtemp()

    try:
        output_path = os.path.join(tmpdir, 'downloaded.%(ext)s')
        ydl_opts = {
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': True,
            'verbose': True,
            'no_warnings': True,
            'retries': 3,
            'fragment_retries': 3,
            'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4' if not is_audio else None,
            'concurrent_fragment_downloads': 5,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if is_audio else [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        file_path = os.path.splitext(file_path)[0] + (".mp3" if is_audio else ".mp4")
        file_size = os.path.getsize(file_path)
        max_size_bytes = 45 * 1024 * 1024

        if file_size > max_size_bytes:
            final_path = os.path.join(TEMP_DIR, os.path.basename(file_path))
            shutil.copy(file_path, final_path)
            pending_large_file_confirmation[chat_id] = {'file_path': final_path, 'is_audio': is_audio}

            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add("🌐 رابط مباشر للتحميل", "❌ إلغاء")
            bot.send_message(chat_id, f"⚠️ الملف كبير ({round(file_size / (1024*1024), 2)} MB). لا يمكن إرساله مباشرة. اختر طريقة التحميل:", reply_markup=markup)
            return

        send_file(bot, chat_id, file_path, is_audio, send_as_document=False, delete_after=True)
        update_user_stats(chat_id, is_audio)

        bot.send_message(chat_id, """
📥 تم التحميل بنجاح!

👟 لو بتدور على أحدث موديلات الكوتشيهات الميرور بجودة عالية وأسعار تنافسية:

🛒 للشراء بالقطعة بأسعار الجملة (بدون حد أدنى):
تفضل بزيارة موقعنا الرسمي: https://b3na.com/@hijabella

📦 لو كنت تاجر أو صاحب محل وبتدور على أفضل عروض الجملة:
تابع قناة التوزيع الخاصة بنا على تيليجرام: https://t.me/AIRSTRIKE2024

🧾 نضمن لك الجودة، الالتزام، والسعر الأفضل دائمًا.
""")

    except Exception as e:
        bot.send_message(chat_id, f"❌ حصل خطأ أثناء التحميل: {str(e)}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def send_file(bot, chat_id, file_path, is_audio, send_as_document=True, delete_after=False):
    try:
        with open(file_path, 'rb') as f:
            if send_as_document:
                bot.send_document(chat_id, f, visible_file_name=os.path.basename(file_path), timeout=300)
            else:
                if is_audio:
                    bot.send_audio(chat_id, f, timeout=300)
                else:
                    bot.send_video(chat_id, f, timeout=300)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حصل خطأ أثناء الإرسال: {str(e)}")
    finally:
        if delete_after:
            try:
                os.remove(file_path)
            except:
                pass

@bot.message_handler(func=lambda message: message.text in ["🌐 رابط مباشر للتحميل", "❌ إلغاء"])
def handle_large_file_confirmation(message):
    if message.chat.id in BANNED_USERS:
        return

    chat_id = message.chat.id
    response = message.text

    if chat_id not in pending_large_file_confirmation:
        return

    data = pending_large_file_confirmation.pop(chat_id)
    file_path = data['file_path']

    if response == "🌐 رابط مباشر للتحميل":
        server_ip = get_server_ip()
        filename = os.path.basename(file_path)
        file_url = f"http://{server_ip}:8080/downloads/{filename}"
        bot.send_message(chat_id, f"⬇️ رابط التحميل المباشر:\n{file_url}")
    else:
        bot.send_message(chat_id, "تم إلغاء التحميل. يمكنك إرسال رابط جديد.")

# إحصائيات جميع المستخدمين - للأدمن فقط


# حظر مستخدم
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        uid = int(message.text.split()[1])
        if uid not in BANNED_USERS:
            BANNED_USERS.append(uid)
            save_banned_users()
            bot.send_message(message.chat.id, f"🚫 تم حظر المستخدم {uid}")
        else:
            bot.send_message(message.chat.id, f"❗المستخدم {uid} محظور بالفعل")
    except:
        bot.send_message(message.chat.id, "❌ استخدم الأمر بهذا الشكل:\n/ban <id>")

# إلغاء الحظر
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        uid = int(message.text.split()[1])
        if uid in BANNED_USERS:
            BANNED_USERS.remove(uid)
            save_banned_users()
            bot.send_message(message.chat.id, f"✅ تم إلغاء الحظر عن المستخدم {uid}")
        else:
            bot.send_message(message.chat.id, f"❗المستخدم {uid} غير محظور")
    except:
        bot.send_message(message.chat.id, "❌ استخدم الأمر بهذا الشكل:\n/unban <id>")

# عرض قائمة المحظورين
@bot.message_handler(commands=['banned'])
def show_banned_users(message):
    if message.chat.id != ADMIN_ID:
        return
    if BANNED_USERS:
        reply = "🚫 قائمة المحظورين:\n" + "\n".join([str(uid) for uid in BANNED_USERS])
    else:
        reply = "✅ لا يوجد مستخدمون محظورون حاليًا."
    bot.send_message(message.chat.id, reply)

# البحث عن مستخدم
@bot.message_handler(commands=['find'])
def find_user(message):
    if message.chat.id != ADMIN_ID:
        return

    if len(message.text.strip().split()) < 2:
        bot.send_message(message.chat.id, "❗يرجى كتابة الاسم أو ID بعد الأمر. مثال:\n/find ahmed")
        return

    keyword = message.text[len('/find '):].strip().lower()
    results = []
    for uid, stats in user_stats.items():
        name = stats.get("name", "").lower()
        if keyword in uid or keyword in name:
            results.append(f"🆔 {uid} - 👤 {stats.get('name', '')}")
    if results:
        reply = "🔍 نتائج البحث:\n" + "\n".join(results)
    else:
        reply = "❌ لا يوجد تطابق."
    bot.send_message(message.chat.id, reply)
@bot.message_handler(commands=['admin_stats'])
def send_admin_stats(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID:
        bot.send_message(chat_id, "❌ غير مصرح لك باستخدام هذا الأمر.")
        return

    # تحميل أسماء المستخدمين من users.txt
    usernames_dict = {}
    if os.path.exists("users.txt"):
        with open("users.txt", "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(" - ")
                if len(parts) == 2:
                    uid, uname = parts
                    usernames_dict[uid] = uname if uname else "❓بدون اسم"

    # توليد التقرير من user_stats
    result = ""
    for uid, stats in user_stats.items():
        username = usernames_dict.get(uid, stats.get("name", "❓بدون اسم"))
        result += (
            f"🆔 {uid} - 👤 {username}\n"
            f"🔗 {stats['total']} رابط - 🎥 {stats['video']} - 🎧 {stats['audio']}\n\n"
        )

    if result:
        bot.send_message(chat_id, result.strip())
    else:
        bot.send_message(chat_id, "لا توجد إحصائيات بعد.")


bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)

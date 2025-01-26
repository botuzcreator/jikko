import telebot
from flask import Flask, request
from datetime import datetime
import os

# Bot tokenini kiritish
TOKEN = "6722967814:AAH0-xziAMxRHl8C85jPuWwXpsYp-b8qXRY"
bot = telebot.TeleBot(TOKEN)

# Webhook sozlamalari
WEBHOOK_SECRET = "jikojiko"  # Maxfiy yo'l
WEBHOOK_URL = f"https://jikko.herokuapp.com/{WEBHOOK_SECRET}"

# Flask ilovasini yaratish
app = Flask(__name__)

# Ma'lumotlarni saqlash uchun fayllar
PASS_USER_FILE = "pass_user.txt"
CHAT_DIR = "messages"  # Xabarlar saqlanadigan katalog

# Foydalanuvchilar va parollarni saqlash
user_passwords = {}  # Foydalanuvchi ID va ularning parollari
password_groups = {}  # Parollar va ularning foydalanuvchi ID-lari

# Fayllarni yaratish (agar mavjud bo'lmasa)
os.makedirs(CHAT_DIR, exist_ok=True)
if not os.path.exists(PASS_USER_FILE):
    with open(PASS_USER_FILE, "w") as f:
        f.write("UserID,Password\n")

# Fayldan foydalanuvchilar va parollarni yuklash
def load_users():
    global user_passwords, password_groups
    if os.path.exists(PASS_USER_FILE):
        with open(PASS_USER_FILE, "r") as f:
            for line in f.readlines()[1:]:  # Birinchi qatorni o'tkazib yuborish
                if line.strip():
                    user_id, password = line.strip().split(",")
                    user_id = int(user_id)
                    user_passwords[user_id] = password
                    password_groups.setdefault(password, []).append(user_id)

# Foydalanuvchilarni fayldan yuklash
load_users()

# "/start" komandasi
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    if user_id not in user_passwords:
        bot.send_message(user_id, "Botdan foydalanish uchun parolni kiriting:")
    else:
        bot.send_message(user_id, "Botga xush kelibsiz! Siz parolni allaqachon kiritgansiz.")

# Parolni qabul qilish
@bot.message_handler(func=lambda message: message.from_user.id not in user_passwords)
def handle_password(message):
    user_id = message.from_user.id
    password = message.text.strip()
    user_passwords[user_id] = password
    password_groups.setdefault(password, []).append(user_id)
    with open(PASS_USER_FILE, "a") as f:
        f.write(f"{user_id},{password}\n")
    bot.send_message(user_id, "Parolingiz qabul qilindi! Endi siz xabar almashishingiz mumkin.")

# Xabarlarni saqlash
@bot.message_handler(func=lambda message: message.from_user.id in user_passwords)
def handle_message(message):
    user_id = message.from_user.id
    user_password = user_passwords[user_id]
    save_message_to_file(user_password, user_id, message.text)
    bot.send_message(user_id, "Xabaringiz saqlandi!")

# Xabarlarni saqlash funksiyasi
def save_message_to_file(password, sender_id, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(CHAT_DIR, f"{password}.txt")
    with open(file_path, "a") as f:
        f.write(f"{timestamp} - {sender_id}: {message}\n")

# Webhook endpoint
@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# Flask ilovasining asosiy sahifasi
@app.route("/")
def index():
    return "Bot ishlamoqda!"

# Webhookni sozlash
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

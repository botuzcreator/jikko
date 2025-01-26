import telebot
from datetime import datetime
import os

# Bot tokenini kiritish
TOKEN = "6722967814:AAGlm026EWNaHGVRd_IFEVeQ9uM-iGK6NKA"
bot = telebot.TeleBot(TOKEN)

# Ma'lumotlarni saqlash uchun fayllar
PASS_USER_FILE = "pass_user.txt"
CHAT_DIR = "messages"  # Xabarlar saqlanadigan katalog

# Foydalanuvchilar va parollarni saqlash
user_passwords = {}  # Foydalanuvchi ID va ularning parollari
password_groups = {}  # Parollar va ularning foydalanuvchi ID-lari

# Fayllarni yaratish (agar mavjud bo'lmasa)
if not os.path.exists(PASS_USER_FILE):
    with open(PASS_USER_FILE, "w") as f:
        f.write("UserID,Password\n")

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# Fayldan foydalanuvchilar va parollarni yuklash
def load_users():
    global user_passwords, password_groups
    with open(PASS_USER_FILE, "r") as f:
        for line in f.readlines()[1:]:  # Birinchi qatorni (sarlavhani) o‘tkazib yuborish
            user_id, password = line.strip().split(",")
            user_id = int(user_id)
            user_passwords[user_id] = password
            if password not in password_groups:
                password_groups[password] = []
            password_groups[password].append(user_id)

# Foydalanuvchini va parolini faylga yozish
def save_user_to_file(user_id, password):
    with open(PASS_USER_FILE, "a") as f:
        f.write(f"{user_id},{password}\n")

# Xabarlarni tegishli faylga yozish
def save_message_to_file(password, sender_id, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(CHAT_DIR, f"{password}.txt")
    with open(file_path, "a") as f:
        f.write(f"{timestamp} - {sender_id}: {message}\n")

# Parolga asoslangan xabarlarni o‘qish
def read_messages_from_file(password):
    file_path = os.path.join(CHAT_DIR, f"{password}.txt")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return f.readlines()

# Foydalanuvchilarni yuklash
load_users()

# "/start" komandasi
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id not in user_passwords:
        bot.send_message(user_id, "Botdan foydalanish uchun parolni kiriting:")
    else:
        bot.send_message(user_id, "Botga xush kelibsiz! Siz parolni allaqachon kiritgansiz.")

# Parolni kiritish
@bot.message_handler(func=lambda message: message.from_user.id not in user_passwords)
def handle_password(message):
    user_id = message.from_user.id
    password = message.text.strip()

    # Foydalanuvchi parolini ro‘yxatga qo‘shish
    if password not in password_groups:
        password_groups[password] = []

    password_groups[password].append(user_id)
    user_passwords[user_id] = password
    save_user_to_file(user_id, password)
    bot.send_message(user_id, "Parolingiz qabul qilindi! Endi siz xabar almashishingiz mumkin.")

# Xabarni yuborish
@bot.message_handler(func=lambda message: message.from_user.id in user_passwords and message.text.strip() not in password_groups)
def handle_message(message):
    user_id = message.from_user.id
    user_password = user_passwords[user_id]

    # Xabarni faylga yozish
    save_message_to_file(user_password, user_id, message.text)
    bot.send_message(user_id, "Xabaringiz saqlandi.")

    # Shu parolga ega boshqa foydalanuvchini topish
    other_users = [uid for uid in password_groups[user_password] if uid != user_id]

    if other_users:
        for receiver_id in other_users:
            bot.send_message(receiver_id, "Yangi xabar mavjud. Uni ko‘rish uchun parolingizni qayta kiriting.")
    else:
        bot.send_message(user_id, "Ushbu parolga mos boshqa foydalanuvchi mavjud emas. Xabaringiz saqlandi.")

# Parolni qayta kiritib xabarlarni ko‘rish
@bot.message_handler(func=lambda message: message.text.strip() in password_groups)
def handle_message_read(message):
    user_id = message.from_user.id
    password = message.text.strip()

    if password in password_groups and user_id in password_groups[password]:
        # Parol to‘g‘ri bo‘lsa, xabarlarni o‘qish
        messages = read_messages_from_file(password)
        if messages:
            bot.send_message(user_id, "Quyidagi xabarlarni oldingiz:")
            for msg in messages:
                bot.send_message(user_id, msg.strip())
        else:
            bot.send_message(user_id, "Siz uchun yangi xabar yo‘q.")
    else:
        bot.send_message(user_id, "Parolingiz noto‘g‘ri yoki siz ushbu parolga biriktirilmagansiz.")

# Botni ishga tushirish
bot.polling()
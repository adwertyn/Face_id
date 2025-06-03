import telebot
from telebot import types
import os
from logger import get_attendance_text, export_attendance_excel

BOT_TOKEN = "7987221136:AAE8_Lxzq5OUB7wrswRNPaUD-GdAe5g32Lg"  # bu yerga o‘z tokeningizni yozing
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📅 Get Attendance")
    btn2 = types.KeyboardButton("📊 Get Excel")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📅 Get Attendance")
def list_class_files(message):
    folder = "known_faces"
    if not os.path.exists(folder):
        bot.send_message(message.chat.id, "No class folders found.")
        return

    markup = types.InlineKeyboardMarkup()
    for class_name in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, class_name)):
            markup.add(types.InlineKeyboardButton(text=class_name, callback_data=f"text_{class_name}"))

    bot.send_message(message.chat.id, "Select a class:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "📊 Get Excel")
def list_class_files_excel(message):
    folder = "known_faces"
    if not os.path.exists(folder):
        bot.send_message(message.chat.id, "No class folders found.")
        return

    markup = types.InlineKeyboardMarkup()
    for class_name in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, class_name)):
            markup.add(types.InlineKeyboardButton(text=class_name, callback_data=f"excel_{class_name}"))

    bot.send_message(message.chat.id, "Select a class for Excel:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("text_"):
        class_name = call.data.split("_", 1)[1]
        text = get_attendance_text(class_name)
        bot.send_message(call.message.chat.id, text)
    elif call.data.startswith("excel_"):
        class_name = call.data.split("_", 1)[1]
        excel_path = export_attendance_excel(class_name)
        if excel_path and os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                bot.send_document(call.message.chat.id, f, caption=f"📄 {class_name} – Excel report")
        else:
            bot.send_message(call.message.chat.id, "❌ Could not generate Excel file.")

print("✅ Telegram bot is running...")
bot.polling()

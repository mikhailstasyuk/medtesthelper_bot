import os
import telebot

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=['document'])
def start(message):
    bot.send_document(message.chat.id, message.document.file_id)
bot.polling()
import telebot
from app.config import Config
import app.database as database

config = Config.load_config()

def run_bot() -> None:
    """Run telegram bot with provided token"""
    BOT_TOKEN = config['bot_token']
    bot = telebot.TeleBot(BOT_TOKEN)

    @bot.message_handler(commands=['start'])
    def start(message) -> None:
        """Greet user and set up database"""
        welcome_message = config['welcome_message']
        bot.reply_to(message, welcome_message)
        database.connect()

    @bot.message_handler(func=lambda message: True)
    def echo_message(message) -> None:
        bot.reply_to(message, message.text)

    bot.infinity_polling()


if __name__ == "__main__":
    # Example usage
    BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
    run_bot()
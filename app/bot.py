import telebot


def run_bot(bot_token: str, welcome_message: str = "Hello!") -> None:
    """Run telegram bot with provided token"""
    bot = telebot.TeleBot(bot_token)

    @bot.message_handler(commands=['start'])
    def send_welcome(message) -> None:
        """Send a welcome message to the user"""
        bot.reply_to(message, welcome_message)

    @bot.message_handler(func=lambda message: True)
    def echo_message(message) -> None:
        bot.reply_to(message, message.text)

    bot.infinity_polling()


if __name__ == "__main__":
    # Example usage
    BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
    run_bot(BOT_TOKEN)
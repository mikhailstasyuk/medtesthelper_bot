import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    @staticmethod
    def load_config():
        # Telegram
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        WELCOME_MESSAGE = """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
"""
        # Database
        DB_NAME = os.getenv('DB_NAME')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        
        # Optional
        LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        return {
            'bot_token': BOT_TOKEN,
            'welcome_message': WELCOME_MESSAGE,
            'db_name': DB_NAME,
            'db_host': DB_HOST,
            'db_port': DB_PORT,
            'db_user': DB_USER,
            'db_password': DB_PASSWORD,
            'log_level': LOG_LEVEL,
        }
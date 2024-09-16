from app.bot import run_bot
from app.config import Config

config = Config.load_config()

if __name__ == "__main__":
    run_bot(config['bot_token'], config['welcome_message'])
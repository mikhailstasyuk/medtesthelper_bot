import json 
import tempfile 

import telebot

from app.config import Config
import app.database as database
from app.ocr import extract_from_pdf, extract_from_image

config = Config.load_config()

def run_bot():
    """Run telegram bot with provided token."""
    BOT_TOKEN = config['bot_token']
    bot = telebot.TeleBot(BOT_TOKEN)
    file_infos = []

    def save_to_temp_file(binary_data, type):
        """Save binary data to temporary file."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{type}') as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name
                return temp_file_path
        except Exception as e:
            raise

    def check_document_type(document):
        """Check if document type is supported."""
        is_supported = False
        supported_types = ['json', 'pdf', 'png', 'jpeg', 'jpg']

        for type in supported_types:
            if (document.mime_type == f'application/{type}' or 
                document.file_name.endswith(f'.{type}')):
                is_supported = True
                return is_supported, type
        
        return is_supported, None

    def load_document():
        """Load last attached document."""
        if file_infos:
            *_, last_added = file_infos
            return last_added
        else:
            return None

    @bot.message_handler(commands=['start'])
    def start(message):
        """Greet user and set up database."""
        welcome_message = config['welcome_message']
        bot.reply_to(message, welcome_message)
        database.create_database_tables()

    @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        """Ask user to send uncompressed images."""
        photo = message.photo

        if photo:
            bot.reply_to(message, "Please attach image (png, jpeg) files as documents.")

    @bot.message_handler(content_types=['document'])
    def handle_document(message):
        """Process attached documents."""
        document = message.document
        
        is_supported, type = check_document_type(document)

        if is_supported:
            file_id = document.file_id
            file_info = bot.get_file(file_id)
            file_infos.append(file_info)

            downloaded_file = bot.download_file(file_info.file_path)
            file_path = save_to_temp_file(downloaded_file, type)

            bot.reply_to(message, f"Processing your {type} file...")

            if type == 'json':
                try:
                    json_data = json.loads(downloaded_file.decode('utf-8'))
                    bot.reply_to(message, "JSON data loaded successfully.")

                    bot.reply_to(message, f"Here's a part of your data: {json_data}")

                except json.JSONDecodeError:
                    bot.reply_to(message, "Error: The file is not a valid JSON.")

            if type == 'pdf':
                try:
                    with open(file_path, 'r') as file:
                        md_text = extract_from_pdf(file)
                    bot.reply_to(message, md_text)

                except Exception as e:
                    bot.reply_to(message, f"Error extracting text from file. {e}")
                    
            if type in ['png', 'jpeg', 'jpg']:
                try:
                    dfs = extract_from_image(file_path)
                    df, *_ = dfs
                    table_str = str(df.to_dict())
                    bot.reply_to(message, table_str)

                except Exception as e:
                    bot.reply_to(message, f"Error extracting text from file. {e}")


            # files = [file_info.file_path for file_info in file_infos]
            # bot.reply_to(message, ", ".join(files))
    
    @bot.message_handler(commands=['add_and_fetch'])
    def add_and_fetch(message):
        document = load_document()
        if document:
            result = database.add_and_fetch(message.chat.id, document)
            bot.reply_to(message, result)
        else:
            msg_to_user = (
                "Please upload at least one document. " 
                "Supported types: json, pdf, png, jpeg."
            )
            bot.reply_to(message, msg_to_user)

    @bot.message_handler(func=lambda message: True)
    def echo_message(message):
        bot.reply_to(message, message.text)
    

    bot.infinity_polling()


if __name__ == "__main__":
    # Example usage
    BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
    run_bot()
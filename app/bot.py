from datetime import datetime
import json 
import logging
import tempfile 

import telebot
from telebot import util

from app.config import Config
import app.database as database
from app.llm import chat, wrap_in_json
from app.ocr import extract_from_pdf, extract_from_image, LowDPIError


config = Config.load_config()

log_level_str = config['log_level']
if log_level_str: 
    log_level = logging.getLevelName(log_level_str) 
else: 
    log_level = logging.getLevelName(logging.INFO)

logging.basicConfig(
    filename='/workspaces/medtesthelper_bot/log.log',
    filemode='a',  
    level=logging.DEBUG,     
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
)

logger = logging.getLogger(__name__)

logger.info("Testing logging before bot starts...")

def run_bot():
    """Run telegram bot with provided token."""
    BOT_TOKEN = config['bot_token']
    bot = telebot.TeleBot(BOT_TOKEN)
    file_infos = []


    def save_to_temp_file(binary_data, doc_type):
        """Save binary data to temporary file."""
        try:
            logger.debug("Trying to save to temporary file...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{doc_type}') as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name
                return temp_file_path
        except Exception as e:
            logger.error(f"Error saving to temporary file: {e}")
            raise
    
    def check_document_type(document):
        """Check if document type is supported."""
        is_supported = False
        supported_types = ['json', 'pdf', 'png', 'jpeg', 'jpg']

        for doc_type in supported_types:
            if (document.mime_type == f'application/{doc_type}' or 
                document.file_name.endswith(f'.{doc_type}')):
                is_supported = True
                logger.debug(f"Found supported document type:{doc_type}")
                return is_supported, doc_type
        
        logger.debug("Attached document type is not supported.")
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
        username = message.from_user.first_name
        prompt = (
            f"Кратко поприветствуй пользователя"
            f"{username}, представься и жди комманд."
            )
        response = chat(prompt)
        if response:
            bot.reply_to(message, response)
        database.create_database_tables()

    @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        """Ask user to send uncompressed images."""
        photo = message.photo

        if photo:
            bot.reply_to(message, "Please attach PNG or JPEG files as documents.")

    @bot.message_handler(content_types=['document'])
    def handle_document(message):
        """Process attached documents."""
        document = message.document
        
        is_supported, doc_type = check_document_type(document)

        if is_supported:
            file_id = document.file_id
            file_info = bot.get_file(file_id)
            file_infos.append(file_info)

            downloaded_file = bot.download_file(file_info.file_path)
            file_path = save_to_temp_file(downloaded_file, doc_type)

            bot.reply_to(message, f"Processing your {doc_type} file...")

            logger.info("Extracting text from document...")
            doc_text = None
            if doc_type == 'pdf':
                try:
                    with open(file_path, 'r') as file:
                        doc_text = extract_from_pdf(file)
                    bot.reply_to(message, doc_text)

                except Exception as e:
                    error_msg = f"Error extracting text from file. {e}"
                    logger.error(error_msg)
                    bot.reply_to(message, error_msg)
                    
            if doc_type in ['png', 'jpeg', 'jpg']:
                try:
                    extracted_tables = extract_from_image(file_path)
                    dicts = [table.df.to_dict() for table in extracted_tables]
                    if dicts:
                        doc_text = str(dicts)
                    else:
                        doc_text = None
                    bot.reply_to(message, str(dicts))

                except LowDPIError as e:
                    error_msg = f"Error extracting text from file. {e}"
                    logger.error(error_msg)
                    bot.reply_to(message, error_msg)

                except Exception as e:
                    error_msg = f"Error extracting text from file. {e}"
                    logger.error(error_msg)
                    bot.reply_to(message, error_msg)

            if doc_text:
                logger.debug(f"Extracted doc text: {doc_text}")
                logger.info("Sending doc text to LLM to parse...")

                response = wrap_in_json(doc_text)
                if response:
                    logger.debug(f"Response json: {response}", )
                
                    logger.info("Splitting text to chunks...")
                    for text in util.smart_split(response):
                        bot.reply_to(message, text)

                    try:
                        logger.info("Trying to add and fetch data...")
                        add_and_fetch(message, response)
                    except Exception as e:
                        logger.error(f"Error adding and fetching: {e}")
                        bot.reply_to(message, e)
                else:
                    logger.error("Could not get response from LLM.")
            else:
                bot.reply_to(message, "Ошибка обработки документа.")
            # files = [file_info.file_path for file_info in file_infos]
            # bot.reply_to(message, ", ".join(files))
        else:
            bot.reply_to(message,
                "Please send the document as a PDF, PNG, or JPEG.")
            
    def add_and_fetch(message, json_string):
        """Test addding to and fetching from database functionality"""
        if json_string:
            result = database.add_and_fetch(message.chat.id, json_string)
            bot.reply_to(message, result)
        else:
            msg_to_user = (
                "Please upload at least one document. " 
                "Supported types: json, pdf, png, jpeg."
            )
            bot.reply_to(message, msg_to_user)

    @bot.message_handler(content_types=['text'])
    def echo_message(message):
        username = message.from_user.first_name
        timestamp = message.date
        message_date = datetime.fromtimestamp(timestamp)
        
        response = chat(f"{message_date} {username}: {message.text}")
        if "/query" in response:
            try:
                query_type, name, dates = database.parse_query(response)
                start_date, end_date = dates
                bot.reply_to(message, f"{name} {start_date} {end_date}")
                return query_type, name, start_date, end_date
            except:
                bot.reply_to(message, "Ошибка запроса данных.")        
        bot.reply_to(message, response)
    

    bot.infinity_polling()


if __name__ == "__main__":
    # Example usage
    BOT_TOKEN = "<YOUR_BOT_TOKEN_HERE>"
    run_bot()
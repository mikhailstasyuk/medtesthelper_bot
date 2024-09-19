import logging
import os
import time

from groq import Groq

from app.config import Config


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

RETRIES = 3

def chat(message):
    client = Groq(
    api_key=config['groq_token'],
    )

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": config['system_prompt']
        },
        {
            "role": "user",
            "content": message,
        }
    ],
    model="llama3-groq-70b-8192-tool-use-preview",
    )

    for i in range(RETRIES):
        try:
            logger.debug(f"Getting response from LLM API try: {i}")
            response = chat_completion.choices[0].message.content

            return response
        except Exception as e:
            logger.error(f"Error getting response from LLM API: {e}")
            time.sleep(30)
    
    raise


def wrap_in_json(text):
    prompt = f"{config['make_json_prompt']}\n{text}"
    response = chat(prompt)
    return response

if __name__ == "__main__":
    # Example usage
    message = r"""
Дата взятия образца: 22.08.2024 08:36
Дата поступления образца: 22.08.2024 18:21
Врач: 23.08.2024 00:28
Дата печати результата: 23.08.2024
МедОк ООО
8 (495) 363-0-363
Москва, ул. Тимирязевская, д. 17 корп 1
Исследование Результат Единицы Референсные
значения
Комментарий
Клинический анализ крови
Гематокрит 42.9 % 39 - 49
Гемоглобин 14.8 г/дл 13.2 - 17.3
Эритроциты 4.94 млн/мкл 4.3 - 5.7
MCV (ср. объем эритр.) 86.8 фл 80 - 99
RDW (шир. распред. эритр) 12.9 % 11.6 - 14.8
MCH (ср. содер. Hb в эр.) 29.9 пг 27 - 34
МСHС (ср. конц. Hb в эр.) 34.5 г/дл 32 - 37
Тромбоциты 264 тыс/мкл 150 - 400
Лейкоциты 6.72 тыс/мкл 4.5 - 11
Нейтрофилы (общ.число),
%
49.5 % 48 - 78 При исследовании крови на
гематологическом анализаторе
патологических клеток не
обнаружено. Количество
палочкоядерных нейтрофилов не
превышает 6"""
    wrap_in_json(message)
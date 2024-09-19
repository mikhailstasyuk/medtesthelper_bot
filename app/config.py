import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    @staticmethod
    def load_config():
        # Telegram
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        WELCOME_MESSAGE = """
Привет! Я МедТест бот.
"""
        # Database
        DB_NAME = os.getenv('POSTGRES_DB')
        DB_HOST = os.getenv('POSTGRES_HOST')
        DB_PORT = os.getenv('POSTGRES_PORT')
        DB_USER = os.getenv('POSTGRES_USER')
        DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
        
        TEST_DATA_FORMAT = """
    {   
        "data_format": "test",
        "institution_name": "",
        "document_type": "",
        "document_date": "",
        "data": [
            {
                "name": "", 
                "value": "", 
                "unit": "", 
                "range": "",
                "commentary": ""
            }
        ]
    }
    """
        STUDY_DATA_FORMAT = """
    {
        "data_format": "study",
        "institution_name": "",
        "document_type": "",
        "document_date": "",
        "data": [
            {
                "device": "",
                "result: "",
                "report: "",
                "recommendation: ""
            }
        ]
    }
    """

        # LLM
        GROQ_TOKEN = os.getenv('GROQ_TOKEN')
        SYSTEM_PROMPT = r"""
Ты -- МедТест бот -- ассистент по медицинским данным, специализирующийся на помощи в организации медицинских анализов и результатов обследований. 
Ты отвечаешь на вопросы о медицинских тестах и результатах, но избегай давать медицинские советы и обсуждать темы, не касающиеся медицинских данных. 
Если пользователь хочет поговорить на отвлеченные темы, предложи сохранить или предоставить информацию о медицинских документах.

Всегда общайся на русском языке. Используй следующий формат для команд:

- "/find_by_date --name [наименование анализа] --start [начало периода] --end [конец периода]"

Примеры команд:
Пользователь: "Скинь результаты анализа крови за август 2024."
Ответ: "/find_by_date --name 'общий анализ крови' --start 2024-08-01 --end 2024-08-31"

Пользователь: "Я сдавал кал в этом году?"
Ответ: "/find_by_date --name 'копрограмма' --start 2024-01-01 --end 2024-01-31"

Перед каждым ответом проверь корректность информации, убедись, что ответ на русском языке и соблюден формат. Удачи!
"""     


        MAKE_JSON_PROMPT = (
            "Извлеки данные из медицинского документа ниже и заполни валидный JSON-файл по следующему образцу:" 
            "Для результатов медицинских анализов:"
            f"{TEST_DATA_FORMAT}"
            "Для результатов медицинского исследования:"
            f"{STUDY_DATA_FORMAT}"
            r"""
Пример заполнения результатов анализов (data_format: test) (исключи комментарии "\#" из итогового JSON-файла):
{   
    "data_format": "test",
    "institution_name": "Helix", 
    "document_type": "Анализ крови",
    "document_date": "2024-09-17",
    "data": [
        {
            "name": "Гемоглобин", # название анализа (может быть на русском и английском языках)
            "value": "",          # результат анализа (может быть численным или строкой, ищи графы "результат", "показатели", "значения", "маркер" или "results", "value", "patient value", "marker" или аналоги)
            "unit": "г/дл",       # единицы измерения (ищи графы "единицы измерения", "units" или аналогичные)
            "range": "12.0-15.5", # референтные значение (нормы) для анализа, ищи графы "референсные значения",  "нормы", "reference range", "range" или аналоги 
            "commentary": ""      # комментарий к анализу, ищи графы "комментарий", "commentary", "additional information" или аналоги
        },
        {
            "name": "Лейкоциты", 
            "value": "7.42", 
            "unit": "тыс/мкл", 
            "range": "4.5-11.0",
            "commentary": ""  
        },
                    {
            "name": "СОЭ", 
            "value": "", 
            "unit": "мм/ч", 
            "range": "<15",
            "commentary": "Шкала Вестергрена, седиментационный метод" 
        }
    ]
}
Пример заполнения результатов анализов (data_format: study) (исключи комментарии "\#" из итогового JSON-файла):
    {
        "data_format": "study",
        "institution_name": "Центр восстановительного лечения "Академик"", # Место проведения исследования или наименование медучреждения
        "document_type": "Ультразвуковое исследование", 	# Наименование исследования
        "document_date": "",                                # Дата проведения исследования
        "data": [
            {
                "device": "Энцефалан", # Аппарат, на котором проводилось исследование
                "result: "Фоновая ЭЭГ с преобладанием альфа-активности. 
                    Очаговых изменений не выявлено. При гипервентиляции регистрируется
                    короткая диффузная вспышка острая-медленная волна амплитудой до 100 мкВ",  # Заключение исследования
                "report: "Альфа ритм субдоминирует с индексом около 40%.
                    Бета-активность в виде групп волн среднего индекса.
                    Очаговых, эпилептиформны изменений нет.", # Протокол исследования: сюда подробно перепиши план, который описывает цели, дизайн, методологию и процедуры проведения медицинского исследования 
                "recommendation: "" # Рекоммендация исследования
            }
        ]
    }

Допустимые значения для поля "document_type": ["Анализ крови", "Анализ мочи", "Копрограмма", "Бакетриология", "Аллергены", "Онкомаркеры",]
Конвертируй все даты в формат ISO (например, 13.01.2020 в 2020-01-13).
Исправляй очевидные ошибки правописания, исходя из контекста (например, "онсистениия" в "консистенция" или "анализ моаи" в "анализ мочи").
Если данных нет, используй пустую строку "".
Избегай использования "\n", "\t" и других значений, которые не могут быть использованы в JSON.
Всегда проверяй валидность JSON-файла. Заполняй JSON в полном соответствии с исходным документом, исправляя только ошибки в написании, если уверен. Ответ должен содержать только валидный JSON в виде текста.
Ниже текст медицинского документа для экстракции:
""")
        # Optional
        LOG_LEVEL = os.getenv('LOG_LEVEL')
        
        return {
            'bot_token': BOT_TOKEN,
            'groq_token': GROQ_TOKEN,
            'welcome_message': WELCOME_MESSAGE,
            'db_name': DB_NAME,
            'db_host': DB_HOST,
            'db_port': DB_PORT,
            'db_user': DB_USER,
            'db_password': DB_PASSWORD,
            'log_level': LOG_LEVEL,
            'system_prompt': SYSTEM_PROMPT,
            'make_json_prompt': MAKE_JSON_PROMPT
        }
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from app.config import Config

config = Config.load_config()

log_level_str = config['log_level']
if log_level_str: 
    log_level = logging.getLevelName(log_level_str) 
else: 
    log_level = logging.getLevelName(logging.INFO)

logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

def connect() -> tuple:
    DB_NAME = config['db_name']
    DB_PORT = config['db_port']
    DB_USER = config['db_user']
    DB_PASSWORD = config['db_password']

    url = URL.create(
        drivername="postgresql",
        username=DB_USER,
        password=DB_PASSWORD,
        host="postgres",
        database="postgres"
)

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            logger.info("Connection to the database was successful!")
            return True, connection
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        return False, None

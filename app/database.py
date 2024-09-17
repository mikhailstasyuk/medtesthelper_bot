import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from app.config import Config
from app.schema import create_tables


config = Config.load_config()

log_level_str = config['log_level']
if log_level_str: 
    log_level = logging.getLevelName(log_level_str) 
else: 
    log_level = logging.getLevelName(logging.INFO)

logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


# def create_database_url(
    # host: str,
    # port: int, 
    # username: str, 
    # password: str, 
    # database: str,
    # drivername : str = 'postgresql' 
# ) -> URL:
    # """Construct URL for database connection"""
    # url = URL.create(
        # drivername=drivername,
        # username=username,
        # password=password,
        # host=host,
        # port=port,
        # database=database
# )
    # return url

def create_database_url():
    url = URL.create(
        drivername='postgresql',
        username=config['db_user'],
        password=config['db_password'],
        host=config['db_host'],
        port=config['db_port'],
        database=config['db_name']
)
    return url

def create_database_tables() -> None:
    """Create database tables according to schema"""
    # DB_HOST = config['db_host']
    # DB_NAME = config['db_name']
    # DB_PORT = config['db_port']
    # DB_USER = config['db_user']
    # DB_PASSWORD = config['db_password']

    # url = create_database_url(
        # username=DB_USER,
        # password=DB_PASSWORD,
        # host=DB_HOST,
        # port=DB_PORT,
        # database=DB_NAME
    # )
    url = create_database_url()
    engine = create_engine(url)

    try:
        create_tables(engine)    
        logger.info("Successfully created tables!")

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
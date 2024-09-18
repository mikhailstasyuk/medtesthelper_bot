from datetime import date
import logging
from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import Config
from app.document_parse import DataEntry, Document
from app.schema import (
    User, MedicalInstitution, 
    MedicalDocument, MedicalData, create_tables
)


config = Config.load_config()

log_level_str = config['log_level']
if log_level_str: 
    log_level = logging.getLevelName(log_level_str) 
else: 
    log_level = logging.getLevelName(logging.INFO)

logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def create_database_url():
    """Programmatically construct database URL"""
    url = URL.create(
        drivername='postgresql',
        username=config['db_user'],
        password=config['db_password'],
        host=config['db_host'],
        port=config['db_port'],
        database=config['db_name']
    )
    return url


def create_database_engine():
    """Create engine for accessing database"""
    url = create_database_url()
    engine = create_engine(url)
    return engine


def create_database_tables():
    """Create database tables according to schema"""
    engine = create_database_engine()
    try:
        create_tables(engine)    
        logger.info("Successfully created tables!")

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def add_medical_document(
    session: Session, 
    telegram_id: int, 
    institution_name: str, 
    document_type: str,
    document_date: date, 
    data_entries: DataEntry
):
    """Add user's medical document to the database"""
    user = session.query(User).filter_by(
        telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)

    institution = session.query(MedicalInstitution).filter_by(
        name=institution_name).first()
    if not institution:
        institution = MedicalInstitution(name=institution_name)
        session.add(institution)
    
    document = MedicalDocument(
        user=user,
        institution=institution,
        document_type=document_type,
        document_date=document_date
    )
    session.add(document)
    
    for entry in data_entries:
        medical_data = MedicalData(
            document=document,
            field_name=entry.name,
            field_value=entry.value,
            unit=entry.unit,
            reference_range=entry.ref_range,
            is_normal=entry.is_normal
        )
        session.add(medical_data)
    
    session.commit()


def fetch_latest_medical_data(session: Session, telegram_id: int, 
        document_type: str = None):
    """Fetch latest medical data for the user"""
    user = session.query(User).filter_by(
        telegram_id=telegram_id).first()

    if not user:
        return None
    
    query = session.query(MedicalDocument).filter(
        MedicalDocument.user_id == user.user_id)
    
    if document_type:
        query = query.filter(
            MedicalDocument.document_type == document_type)
    
    latest_document = query.order_by(
        desc(MedicalDocument.document_date)).first()
    
    if not latest_document:
        return None  
    
    data = session.query(MedicalData).filter(
        MedicalData.document_id == latest_document.document_id).all()
    
    result = {
        "document_type": latest_document.document_type,
        "document_date": latest_document.document_date,
        "institution": latest_document.institution.name,
        "data": [{
            "field_name": item.field_name,
            "field_value": item.field_value,
            "unit": item.unit,
            "reference_range": item.reference_range,
            "is_normal": item.is_normal
        } for item in data]
    }
    return result


def add_and_fetch(telegram_id, document_json):
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    document = Document.from_json(document_json)

    with Session() as session:
        telegram_id = telegram_id
        add_medical_document(
            session,
            telegram_id=telegram_id,  
            institution_name=document.institution_name,
            document_type=document.document_type,
            document_date=date.fromisoformat(document.document_date),
            data_entries=document.data
        )
    
        result = fetch_latest_medical_data(session, telegram_id, document_type="Клинический анализ крови")
        if result:
            data = result['data'][0]
            return f"{data['field_name']}: {data['field_value']} {data['unit']} (Normal: {data['is_normal']})"
        else:
            return "No data found for this user."

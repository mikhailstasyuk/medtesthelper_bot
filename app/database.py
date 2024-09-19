from datetime import date
import logging
from typing import Union, List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import Config
from app.document_parse import (
    MedTestDataEntry, MedStudyDataEntry, Document
)
from app.schema import (
    User, MedicalInstitution, 
    MedicalDocument, TestData, StudyData, create_tables
)


config = Config.load_config()


log_level_str = config['log_level']
if log_level_str: 
    log_level = logging.getLevelName(log_level_str) 
else: 
    log_level = logging.getLevelName(logging.INFO)

logging.basicConfig(
    filename='log.log',
    filemode='a',  
    level=logging.DEBUG,     
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
)

logger = logging.getLogger(__name__)


def create_database_url():
    """Programmatically construct database URL."""
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
    """Create database tables according to schema."""
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
    data_format: str,
    data_entries: List[Union[MedTestDataEntry, MedStudyDataEntry]]
):
    """Add user's medical document to the database."""
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)

    institution = session.query(MedicalInstitution).filter_by(name=institution_name).first()
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

    # Insert data based on the data_format flag
    if data_format == 'test':
        for entry in data_entries:
            test_data = TestData(
                document=document,
                name=entry.name,
                value=entry.value,
                unit=entry.unit,
                range=entry.ref_range,
                commentary=entry.commentary
            )
            session.add(test_data)
    elif data_format == 'study':
        for entry in data_entries:
            study_data = StudyData(
                document=document,
                device=entry.device,
                result=entry.result,
                report=entry.report,
                recommendation=entry.recommendation
            )
            session.add(study_data)
    
    session.commit()


def fetch_latest_medical_data(session: Session, telegram_id: int, document_type: str = None):
    """Fetch latest medical data for the user"""
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return None
    
    query = session.query(MedicalDocument).filter(MedicalDocument.user_id == user.user_id)
    
    if document_type:
        query = query.filter(MedicalDocument.document_type == document_type)
    
    latest_document = query.order_by(desc(MedicalDocument.document_date)).first()
    
    if not latest_document:
        return None  
    
    # Initialize result without data_format
    fetched = {
        "document_type": latest_document.document_type,
        "document_date": latest_document.document_date,
        "institution": latest_document.institution.name,
        "data": []
    }

    # Fetch test or study data based on the actual data present
    test_data = session.query(TestData).filter(TestData.document_id == latest_document.document_id).all()
    if test_data:
        fetched["data_format"] = 'test'
        fetched["data"] = [{
            "name": item.name,
            "value": item.value,
            "unit": item.unit,
            "range": item.range,
            "commentary": item.commentary
        } for item in test_data]
    else:
        study_data = session.query(StudyData).filter(StudyData.document_id == latest_document.document_id).all()
        if study_data:
            fetched["data_format"] = 'study'
            fetched["data"] = [{
                "device": item.device,
                "result": item.result,
                "report": item.report,
                "recommendation": item.recommendation
            } for item in study_data]

    return fetched


def add_and_fetch(telegram_id, document_json):
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    document = Document.from_json(document_json)
    with Session() as session:
        session.expire_all()
        add_medical_document(
            session,
            telegram_id=telegram_id,
            institution_name=document.institution_name,
            document_type=document.document_type,
            document_date=document.document_date,
            data_format=document.data_format,
            data_entries=document.data
        )
    
        fetched = fetch_latest_medical_data(session, telegram_id, document_type=document.document_type)
        if fetched:
            data = fetched['data'][0]
            if fetched['data_format'] == 'test':
                return f"{data['name']}: {data['value']} {data['unit']} (Commentary: {data['commentary']})"
            elif fetched['data_format'] == 'study':
                return f"Device: {data['device']}, Recommendation: {data['recommendation']}"
        else:
            return "No data found for this user."
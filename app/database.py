from datetime import date
import logging
import re
from typing import Union, List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import joinedload
from typing import Union

from sqlalchemy.orm import selectinload

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
    try:
        # User and Institution retrieval
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)

        institution = session.query(MedicalInstitution).filter_by(name=institution_name).first()
        if not institution:
            institution = MedicalInstitution(name=institution_name)
            session.add(institution)

        # Document creation
        document = MedicalDocument(
            user=user,
            institution=institution,
            document_type=document_type,
            document_date=document_date
        )
        session.add(document)

        # Data entry handling
        if data_format == 'test':
            for entry in data_entries:
                if not entry.name or not entry.value:
                    raise ValueError("Invalid test entry data.")
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
                if not entry.device or not entry.result:
                    raise ValueError("Invalid study entry data.")
                study_data = StudyData(
                    document=document,
                    device=entry.device,
                    result=entry.result,
                    report=entry.report,
                    recommendation=entry.recommendation
                )
                session.add(study_data)

        session.commit()
        logger.info("Successfully added medical document for user %s", telegram_id)
    except Exception as e:
        logger.error("Error adding medical document: %s", e)
        session.rollback()
        raise


def add_document(telegram_id, document_json):
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    document = Document.from_json(document_json)
    with Session() as session:
        session.expire_all()
        try:
            add_medical_document(
                session,
                telegram_id=telegram_id,
                institution_name=document.institution_name,
                document_type=document.document_type,
                document_date=document.document_date,
                data_format=document.data_format,
                data_entries=document.data
            )
        except Exception as e:
            logger.error(f"{telegram_id}: Error adding document.")
            return "Error processing request."

def parse_query(query_string):
    """Parse LLM query command."""
    pattern = r"/query_(study|test)"
    match = re.search(pattern, query_string)
    if match:
        query_type = match.group(1)
    else:
        raise ValueError("Invalid query type")

    pattern = r"--name\s+'([^']+)'\s+--start\s+(\d{4}-\d{2}-\d{2})\s+--end\s+(\d{4}-\d{2}-\d{2})"
    match = re.search(pattern, query_string)
    if match:
        name = match.group(1)
        start_date = match.group(2)
        end_date = match.group(3)
        dates = start_date, end_date
        return query_type, name, dates
    else:
        raise ValueError("Invalid query format")


def fetch_data_by_period(telegram_id: int, query_type: str, document_type: str, start_date: str, end_date: str) -> Union[str, None]:
    """Fetch test or study data for the user based on the period and query type."""
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    with Session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return "User not found."
        
        if query_type == 'test':
            documents = session.query(TestData).options(selectinload(TestData.document).selectinload(MedicalDocument.institution)).filter(
                TestData.document.has(MedicalDocument.user_id == user.user_id),
                TestData.document.has(MedicalDocument.document_type == document_type),
                TestData.document.has(MedicalDocument.document_date.between(start_date, end_date))
            ).all()
        else:  # query_type == 'study'
            documents = session.query(StudyData).options(selectinload(StudyData.document).selectinload(MedicalDocument.institution)).filter(
                StudyData.document.has(MedicalDocument.user_id == user.user_id),
                StudyData.document.has(MedicalDocument.document_type == document_type),
                StudyData.document.has(MedicalDocument.document_date.between(start_date, end_date))
            ).all()
        
        if documents:
            fetched_data = []
            document_data = {}

            if query_type == 'test':
                for doc in documents:
                    document = doc.document  # Access the associated MedicalDocument
                    institution = document.institution if document else None
                    
                    if document.document_id not in document_data:
                        document_data[document.document_id] = {
                            'date': document.document_date,
                            'institution': institution.name if institution else 'N/A',
                            'tests': []
                        }

                    document_data[document.document_id]['tests'].append(
                        f"{doc.name}: {doc.value} {doc.unit} (реф. знач.: {doc.range})\n"
                        f"комментарий: {doc.commentary}\n"
                    )

            elif query_type == 'study':
                for doc in documents:
                    document = doc.document  # Access the associated MedicalDocument
                    institution = document.institution if document else None
                    
                    # If the document is not already processed, add the header
                    if document.document_id not in document_data:
                        document_data[document.document_id] = {
                            'date': document.document_date,
                            'institution': institution.name if institution else 'N/A',
                            'studies': []
                        }

                    # Add study data to the corresponding document
                    document_data[document.document_id]['studies'].append(
                        f"Аппарат: {doc.device}\n\n"
                        f"Заключение:\n{doc.result}\n\n"
                        f"Протокол:\n{doc.report}\n\n"
                        f"Рекомендация:\n{doc.recommendation}\n\n"
                    )

            # Format the final output
            for doc_id, data in document_data.items():
                fetched_data.append(f"Дата: {data['date']}\nМесто проведения: {data['institution']}")
                if query_type == 'test':
                    fetched_data.append("\n".join(data['tests']))
                else:
                    fetched_data.append("\n".join(data['studies']))
                fetched_data.append("")  # Add a blank line for separation

            return "\n".join(fetched_data).strip()  # Remove any trailing newline
        else:
            return None


if __name__ == "__main__":
    print(fetch_data_by_period("82085270", "test", "анализ крови", "2024-01-01", "2024-12-31"))
    print(fetch_data_by_period("82085270", "study", "томография", "2024-01-01", "2024-12-31"))
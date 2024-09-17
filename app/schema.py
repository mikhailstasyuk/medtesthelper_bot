from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

Base = declarative_base()

# Define database schema
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("MedicalDocument", back_populates="user")


class MedicalInstitution(Base):
    __tablename__ = 'medical_institutions'

    institution_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)

    documents = relationship("MedicalDocument", back_populates="institution")


class MedicalDocument(Base):
    __tablename__ = 'medical_documents'

    document_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    institution_id = Column(Integer, ForeignKey('medical_institutions.institution_id'))
    document_type = Column(String(50))
    document_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")
    institution = relationship("MedicalInstitution", back_populates="documents")
    data = relationship("MedicalData", back_populates="document")


class MedicalData(Base):
    __tablename__ = 'medical_data'

    data_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('medical_documents.document_id'))
    field_name = Column(String(255), nullable=False)
    field_value = Column(Text)
    unit = Column(String(50))
    reference_range = Column(Text)
    is_normal = Column(Boolean)

    document = relationship("MedicalDocument", back_populates="data")


def create_tables(engine):
    Base.metadata.create_all(engine)
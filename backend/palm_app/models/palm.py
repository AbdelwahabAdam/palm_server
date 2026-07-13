from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String

from .base import Base


class PalmProfile(Base):
    __tablename__ = 'palm_profiles'

    id = Column(Integer, primary_key=True)
    palm_id = Column(String(50), unique=True, nullable=False)
    palm_code = Column(String(50), unique=True, nullable=False, index=True)
    plant_date = Column(DateTime, nullable=False)
    donner_name = Column(String(100), index=True)
    donner_phone_number = Column(String(20), index=True)
    harvest_amount = Column(Float)
    last_harvest = Column(DateTime)
    age = Column(Integer)
    images = Column(JSON)
    area = Column(String(100))
    section = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

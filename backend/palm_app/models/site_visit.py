from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from .base import Base


class SiteVisit(Base):
    __tablename__ = 'site_visits'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    page_visited = Column(String(255))
    visited_at = Column(DateTime, default=datetime.utcnow)

import os
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache.db')
engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class CacheEntry(Base):
    __tablename__ = 'cache'
    prompt = Column(Text, primary_key=True)
    model = Column(String, primary_key=True)
    response = Column(Text)
    timestamp = Column(DateTime)

Base.metadata.create_all(bind=engine)

def get_cached_response(prompt, model):
    session = SessionLocal()
    entry = session.query(CacheEntry).filter_by(prompt=prompt, model=model).first()
    session.close()
    if entry:
        return entry.response, entry.timestamp
    return None, None

def store_response(prompt, model, response, timestamp=None):
    session = SessionLocal()
    if timestamp is None:
        timestamp = datetime.utcnow()
    entry = CacheEntry(prompt=prompt, model=model, response=response, timestamp=timestamp)
    session.merge(entry)
    session.commit()
    session.close() 
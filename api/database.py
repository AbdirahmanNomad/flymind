"""
Database setup and models for persistent storage.
Uses SQLAlchemy with SQLite for development, PostgreSQL for production.
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from api.config import DATABASE_URL

# Create base class for models
Base = declarative_base()

# Database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database Models
class SearchHistory(Base):
    """Model for storing flight search history."""
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    depart_date = Column(String, nullable=False)
    return_date = Column(String, nullable=True)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)
    seat_class = Column(String, default="economy")
    fetch_mode = Column(String, default="local")
    request_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceAlert(Base):
    """Model for storing price alerts."""
    __tablename__ = "price_alerts"
    
    id = Column(String, primary_key=True)
    alert_id = Column(String, unique=True, nullable=False, index=True)
    trip_type = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    depart_date = Column(String, nullable=False)
    return_date = Column(String, nullable=True)
    target_price = Column(Float, nullable=False)
    currency = Column(String, default="SEK")
    email = Column(String, nullable=False)
    notification_channels = Column(JSON, default=list)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


class Webhook(Base):
    """Model for storing webhook URLs."""
    __tablename__ = "webhooks"
    
    id = Column(String, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


# Database initialization
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Dependency for getting database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions for database operations
def get_search_history(db, search_id: str):
    """Get search history by ID."""
    return db.query(SearchHistory).filter(SearchHistory.id == search_id).first()


def create_search_history(db, search_id: str, request_data: dict, result_data: dict):
    """Create new search history entry."""
    search = SearchHistory(
        id=search_id,
        origin=request_data.get("origin", ""),
        destination=request_data.get("destination", ""),
        depart_date=request_data.get("depart_date", ""),
        return_date=request_data.get("return_date"),
        adults=request_data.get("adults", 1),
        children=request_data.get("children", 0),
        seat_class=request_data.get("seat_class", "economy"),
        fetch_mode=request_data.get("fetch_mode", "local"),
        request_data=request_data,
        result_data=result_data,
        timestamp=datetime.utcnow()
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


def get_price_alert(db, alert_id: str):
    """Get price alert by ID."""
    return db.query(PriceAlert).filter(PriceAlert.alert_id == alert_id).first()


def create_price_alert(db, alert_data: dict):
    """Create new price alert."""
    alert = PriceAlert(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_all_active_alerts(db):
    """Get all active price alerts."""
    return db.query(PriceAlert).filter(
        PriceAlert.status == "active",
        PriceAlert.deleted_at.is_(None)
    ).all()


def get_webhook(db, url: str):
    """Get webhook by URL."""
    return db.query(Webhook).filter(Webhook.url == url).first()


def create_webhook(db, webhook_id: str, url: str):
    """Create new webhook."""
    webhook = Webhook(id=webhook_id, url=url, active=True)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


def get_all_webhooks(db):
    """Get all active webhooks."""
    return db.query(Webhook).filter(Webhook.active == True).all()


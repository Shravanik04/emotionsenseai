from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    sentiment = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    source_type = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # New columns for emotion detection
    emotion = Column(String(50), nullable=True)
    emotion_confidence = Column(Float, nullable=True)

    # New columns for language detection
    language_code = Column(String(10), nullable=True)
    language_name = Column(String(100), nullable=True)
    language_confidence = Column(Float, nullable=True)

    # Sarcasm columns
    sarcasm_detected = Column(Boolean, default=False)
    sarcasm_confidence = Column(Float, nullable=True)
    sarcasm_reason = Column(Text, nullable=True)

    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)

    # User association
    user_id = Column(Integer, nullable=True, index=True)

    # Aspect extraction
    aspect = Column(String(100), nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)




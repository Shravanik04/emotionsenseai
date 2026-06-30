from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class BatchAnalysisRun(Base):
    __tablename__ = "batch_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    total_processed = Column(Integer, nullable=False)
    average_confidence = Column(Float, nullable=False)
    sarcasm_rate = Column(Float, nullable=False)
    processing_time_ms = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    
    # Serialized aggregate storage
    sentiment_distribution = Column(Text, nullable=True)  # JSON string
    emotion_distribution = Column(Text, nullable=True)      # JSON string
    language_distribution = Column(Text, nullable=True)     # JSON string
    sarcasm_distribution = Column(Text, nullable=True)      # JSON string
    keywords_summary = Column(Text, nullable=True)          # JSON string
    aspect_sentiment_table = Column(Text, nullable=True)    # JSON string
    executive_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)           # JSON string
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class SocialAnalysis(Base):
    __tablename__ = "social_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    detected_language = Column(String(100), nullable=True)
    language_code = Column(String(10), nullable=True)
    emotion = Column(String(50), nullable=True)
    sentiment = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    sarcasm_detected = Column(Boolean, default=False)
    sarcasm_confidence = Column(Float, nullable=True)
    sarcasm_reason = Column(Text, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    aspect = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Link to batch run
    batch_run_id = Column(Integer, ForeignKey("batch_runs.id"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

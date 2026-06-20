from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    id: int
    sentiment: str
    confidence: float
    processed_timestamp: datetime

class BatchSummary(BaseModel):
    total_rows: int
    processed_rows: int
    skipped_rows: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_confidence: float
    errors: List[str]

class HistoryItem(BaseModel):
    id: int
    text_preview: str
    sentiment: str
    confidence: float
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_analyses: int
    positive_count: int
    negative_count: int
    neutral_count: int
    recent_activity: List[HistoryItem]

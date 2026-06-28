from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List, Optional

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    id: int
    sentiment: str
    confidence: float
    processed_timestamp: datetime

# --- Rich real-time response ---

class ProbabilityItem(BaseModel):
    label: str
    score: float

class KeywordItem(BaseModel):
    word: str
    count: int

class WordCloudItem(BaseModel):
    text: str
    value: int

class KeywordsResult(BaseModel):
    top_keywords: List[KeywordItem]
    positive_words: List[KeywordItem]
    negative_words: List[KeywordItem]
    word_cloud: List[WordCloudItem]
    word_frequencies: List[KeywordItem]

class LanguageInfo(BaseModel):
    code: str
    name: str
    flag: str

class InsightsResult(BaseModel):
    overall_sentiment_score: float
    dominant_emotion: str
    dominant_emotion_emoji: str
    emotional_intensity: str
    explanation: str
    word_count: int
    char_count: int
    reading_time_seconds: int

class SarcasmResult(BaseModel):
    detected: bool
    confidence: float
    reason: str

class ReadabilityResult(BaseModel):
    score: float
    complexity: str

class SentenceAnalysisItem(BaseModel):
    text: str
    sentiment: str
    sentiment_confidence: float
    emotion: str
    emotion_confidence: float
    emotion_emoji: str
    sarcasm: SarcasmResult

class FullAnalysisResponse(BaseModel):
    """Rich response returned by /analyze-text and the WebSocket."""
    sentiment: str
    sentiment_confidence: float
    sentiment_distribution: List[ProbabilityItem]
    emotion: str
    emotion_confidence: float
    emotion_emoji: str
    emotion_distribution: List[ProbabilityItem]
    language: LanguageInfo
    language_confidence: float
    keywords: KeywordsResult
    insights: InsightsResult
    inference_time_ms: float
    word_count: int
    char_count: int
    cache_hit: bool
    sarcasm: SarcasmResult
    readability: ReadabilityResult
    entities: Dict[str, List[str]]
    sentences: List[SentenceAnalysisItem]
    timeline: List[str]
    emotion_ranking: List[ProbabilityItem]
    mixed_sentiment: bool
    positive_score: float
    negative_score: float
    neutral_score: float
    contradictory_emotions: List[str]
    emotion_summary: str
    emotion_confidences: Dict[str, float]
    top_emotions: List[str]
    primary_emotion: Optional[Dict[str, Any]] = None
    secondary_emotions: Optional[List[Dict[str, Any]]] = None
    emotion_explanations: Optional[Dict[str, str]] = None

class FullAnalysisWithIdResponse(FullAnalysisResponse):
    """Same as FullAnalysisResponse but with DB record id and timestamp."""
    id: int
    processed_timestamp: datetime

# --- Batch ---

class BatchSummary(BaseModel):
    total_rows: int
    processed_rows: int
    skipped_rows: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_confidence: float
    emotion_counts: Dict[str, int] = {}
    errors: List[str]

# --- History ---

class HistoryItem(BaseModel):
    id: int
    text_preview: str
    sentiment: str
    confidence: float
    source_type: str
    created_at: datetime
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    language_name: Optional[str] = None
    sarcasm_detected: Optional[bool] = None
    sarcasm_confidence: Optional[float] = None
    sarcasm_reason: Optional[str] = None
    language_code: Optional[str] = None

    class Config:
        from_attributes = True

# --- Stats ---

class StatsResponse(BaseModel):
    total_analyses: int
    positive_count: int
    negative_count: int
    neutral_count: int
    emotion_counts: Dict[str, int] = {}
    recent_activity: List[HistoryItem]

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Dict, Optional, Any

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
    user_id: int

class SocialAnalyzeRequest(BaseModel):
    platform: str
    text: str

class SocialAnalyzeResponse(BaseModel):
    id: int
    user_id: int
    platform: str
    original_text: str
    detected_language: Optional[str] = None
    language_code: Optional[str] = None
    emotion: Optional[str] = None
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    sarcasm_detected: bool
    sarcasm_confidence: Optional[float] = None
    sarcasm_reason: Optional[str] = None
    processing_time_ms: Optional[float] = None
    inference_time_ms: Optional[float] = None
    aspect: Optional[str] = None
    batch_run_id: Optional[int] = None
    created_at: datetime


    class Config:
        from_attributes = True


class SocialBatchRequest(BaseModel):
    platform: str
    text: str

class KeywordExtractorItem(BaseModel):
    word: str
    count: int

class KeywordsSummary(BaseModel):
    positive_keywords: List[KeywordExtractorItem]
    negative_keywords: List[KeywordExtractorItem]
    most_frequent: List[KeywordExtractorItem]
    most_emotional: List[KeywordExtractorItem]

class AspectSentimentItem(BaseModel):
    aspect: str
    positive: int
    negative: int
    neutral: int

class BusinessInsights(BaseModel):
    total_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    mixed_percentage: float
    dominant_emotion: str
    dominant_emotion_emoji: str
    top_praises: List[str]
    top_complaints: List[str]
    recommendations: List[str]
    aspect_sentiment_table: List[AspectSentimentItem] = []
    executive_summary: str = ""



class SocialBatchResponse(BaseModel):
    total_processed: int
    average_confidence: float
    sarcasm_rate: float
    sentiment_distribution: Dict[str, float]
    emotion_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    sarcasm_distribution: Dict[str, int]
    average_processing_time_ms: float
    average_inference_time_ms: float
    keywords: KeywordsSummary
    insights: BusinessInsights
    results: List[SocialAnalyzeResponse]

class BatchAnalysisRunResponse(BaseModel):
    id: int
    user_id: int
    platform: str
    total_processed: int
    average_confidence: float
    sarcasm_rate: float
    sentiment_distribution: Dict[str, float]
    emotion_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    sarcasm_distribution: Dict[str, int]
    keywords_summary: KeywordsSummary
    aspect_sentiment_table: List[AspectSentimentItem]
    executive_summary: str
    recommendations: List[str]
    processing_time_ms: Optional[float] = None
    inference_time_ms: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_comments: int
    customer_satisfaction_score: float
    overall_health_score: float
    average_confidence: float
    sarcasm_rate: float
    average_processing_time_ms: float
    sentiment_distribution: Dict[str, float]
    emotion_distribution: Dict[str, int]
    recent_runs: List[BatchAnalysisRunResponse]

class StatisticsResponse(BaseModel):
    sentiment_distribution: Dict[str, float]
    emotion_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    sarcasm_distribution: Dict[str, int]
    confidence_intervals: Dict[str, int]
    processing_time_avg: float
    sarcasm_rate: float

class AspectAnalyticsResponse(BaseModel):
    aspect_sentiment_table: List[AspectSentimentItem]
    top_praises: List[str]
    top_complaints: List[str]

class BusinessInsightsResponse(BaseModel):
    executive_summary: str
    recommendations: List[str]
    total_processed: int
    csat: float
    ohs: float

class ReviewsBatchRequest(BaseModel):
    platform: str = "reviews"
    text: str


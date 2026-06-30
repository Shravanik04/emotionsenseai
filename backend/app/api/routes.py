"""
API routes for SentimentScope.
Includes REST endpoints and a WebSocket endpoint for real-time analysis.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from datetime import datetime
from io import StringIO
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db, SessionLocal
from app.models.sentiment_model import SentimentRecord
from app.schemas.sentiment import (
    SentimentRequest,
    SentimentResponse,
    FullAnalysisResponse,
    FullAnalysisWithIdResponse,
    BatchSummary,
    HistoryItem,
    StatsResponse,
)
from app.services.analysis_service import analyzer
from app.utils.csv_utils import parse_csv, parse_txt, parse_excel

# Social Media Analyzer Imports
from app.core.auth import get_current_user_id, get_optional_user_id, hash_password, verify_password, create_access_token
from app.services.report_service import generate_pdf_report
from app.models.user import User
from app.models.social_analysis import SocialAnalysis, BatchAnalysisRun
from app.schemas.social import (
    LoginRequest,
    TokenResponse,
    SocialAnalyzeRequest,
    SocialAnalyzeResponse,
    SocialBatchRequest,
    SocialBatchResponse,
    KeywordsSummary,
    KeywordExtractorItem,
    BusinessInsights,
    AspectSentimentItem,
    BatchAnalysisRunResponse,
    DashboardStatsResponse,
    StatisticsResponse,
    AspectAnalyticsResponse,
    BusinessInsightsResponse,
    ReviewsBatchRequest,
)


PRONOUNS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'who', 'whom',
    'whose', 'which', 'what', 'this', 'that', 'these', 'those', 'whoever', 'whomever', 'myself', 'himself', 'herself'
}

COMMON_VERBS = {
    'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
    'doing', 'say', 'says', 'said', 'saying', 'go', 'goes', 'going', 'went', 'gone', 'make', 'makes', 'made',
    'making', 'get', 'gets', 'getting', 'got', 'gotten', 'know', 'knows', 'knew', 'knowing', 'think', 'thinks',
    'thought', 'thinking', 'take', 'takes', 'took', 'taken', 'taking', 'see', 'sees', 'saw', 'seen', 'seeing',
    'come', 'comes', 'coming', 'came', 'want', 'wants', 'wanted', 'wanting', 'look', 'looks', 'looked', 'looking',
    'use', 'uses', 'used', 'using', 'find', 'finds', 'found', 'finding', 'give', 'gives', 'gave', 'given',
    'giving', 'tell', 'tells', 'told', 'telling', 'work', 'works', 'worked', 'working', 'call', 'calls',
    'called', 'calling', 'try', 'tries', 'tried', 'trying', 'ask', 'asks', 'asked', 'asking', 'need', 'needs',
    'needed', 'needing', 'feel', 'feels', 'felt', 'feeling', 'become', 'becomes', 'became', 'becoming', 'leave',
    'leaves', 'left', 'leaving', 'put', 'puts', 'putting', 'keep', 'keeps', 'kept', 'keeping', 'let', 'lets',
    'letting', 'begin', 'begins', 'began', 'beginning', 'start', 'starts', 'started', 'starting', 'help',
    'helps', 'helped', 'helping', 'show', 'shows', 'showed', 'showing', 'play', 'plays', 'played', 'playing',
    'run', 'runs', 'ran', 'running', 'write', 'writes', 'wrote', 'written', 'writing', 'like', 'likes', 'liked',
    'liking', 'live', 'lives', 'lived', 'living', 'believe', 'believes', 'believed', 'believing', 'hold',
    'holds', 'held', 'holding', 'bring', 'brings', 'brought', 'bringing', 'happen', 'happens', 'happened',
    'happening', 'must', 'should', 'would', 'could', 'will', 'can', 'may', 'might', 'shall'
}

GENERIC_WORDS = {
    'thing', 'things', 'something', 'anything', 'everything', 'nothing', 'one', 'two', 'three', 'first',
    'second', 'time', 'times', 'day', 'days', 'week', 'weeks', 'year', 'years', 'month', 'months', 'way', 'ways',
    'actual', 'actually', 'really', 'very', 'also', 'even', 'just', 'still', 'again', 'here', 'there',
    'when', 'where', 'why', 'how', 'who', 'about', 'some', 'any', 'other', 'others', 'such',
    'okay', 'people', 'person', 'lot', 'lots', 'much',
    'many', 'more', 'most', 'less', 'least', 'few', 'fewer', 'bit', 'little', 'almost', 'maybe', 'perhaps',
    'probably', 'definitely', 'clearly', 'simply', 'total', 'totally', 'complete', 'completely'
}


router = APIRouter()




# ---------------------------------------------------------------------------
# Helper: run heavy inference off the event-loop
# ---------------------------------------------------------------------------

async def _analyze_in_thread(text: str):
    """Run model inference in a thread-pool so we don't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyzer.analyze_full, text)


from app.utils.aspect_utils import detect_aspect_and_sentiment




# ---------------------------------------------------------------------------
# POST /analyze-text  (REST — full analysis)
# ---------------------------------------------------------------------------

@router.post("/analyze-text", response_model=FullAnalysisWithIdResponse)
async def analyze_text(
    req: SentimentRequest,
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id)
):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        t0 = time.perf_counter()
        result = await _analyze_in_thread(req.text)
        processing_ms = round((time.perf_counter() - t0) * 1000, 2)

        record = SentimentRecord(
            original_text=req.text,
            sentiment=result["sentiment"],
            confidence=result["sentiment_confidence"],
            source_type="manual",
            emotion=result["emotion"],
            emotion_confidence=result["emotion_confidence"],
            language_code=result["language"]["code"],
            language_name=result["language"]["name"],
            language_confidence=result["language_confidence"],
            sarcasm_detected=result["sarcasm"]["detected"],
            sarcasm_confidence=result["sarcasm"]["confidence"],
            sarcasm_reason=result["sarcasm"]["reason"],
            processing_time_ms=processing_ms,
            inference_time_ms=result["inference_time_ms"],
            user_id=current_user_id,
        )
        db.add(record)

        db.commit()
        db.refresh(record)

        return {
            **result,
            "id": record.id,
            "processed_timestamp": record.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /analyze-realtime  (lightweight — no DB save)
# ---------------------------------------------------------------------------

@router.post("/analyze-realtime", response_model=FullAnalysisResponse)
async def analyze_realtime(req: SentimentRequest):
    """Lightweight endpoint for real-time typing (no DB persistence)."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        result = await _analyze_in_thread(req.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# WebSocket /ws  (real-time streaming)
# ---------------------------------------------------------------------------

@router.websocket("/ws")
async def websocket_analysis(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
                text = payload.get("text", "").strip()
            except (json.JSONDecodeError, AttributeError):
                text = data.strip()

            if not text:
                await ws.send_json({"error": "Empty text"})
                continue

            try:
                t0 = time.perf_counter()
                result = await _analyze_in_thread(text)
                processing_ms = round((time.perf_counter() - t0) * 1000, 2)
                result["processing_time_ms"] = processing_ms

                # Auto-save results to SQLite
                with SessionLocal() as db:
                    record = SentimentRecord(
                        original_text=text,
                        sentiment=result["sentiment"],
                        confidence=result["sentiment_confidence"],
                        source_type="realtime",
                        emotion=result["emotion"],
                        emotion_confidence=result["emotion_confidence"],
                        language_code=result["language"]["code"],
                        language_name=result["language"]["name"],
                        language_confidence=result["language_confidence"],
                        sarcasm_detected=result["sarcasm"]["detected"],
                        sarcasm_confidence=result["sarcasm"]["confidence"],
                        sarcasm_reason=result["sarcasm"]["reason"],
                        processing_time_ms=processing_ms,
                        inference_time_ms=result["inference_time_ms"],
                    )
                    db.add(record)
                    db.commit()
                    db.refresh(record)
                    
                    # Enrich response payload with database details
                    result["id"] = record.id
                    result["processed_timestamp"] = record.created_at.isoformat() if record.created_at else None

                await ws.send_json(result)
            except Exception as exc:
                await ws.send_json({"error": str(exc)})
    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# POST /analyze-batch
# ---------------------------------------------------------------------------

@router.post("/analyze-batch", response_model=BatchSummary)
async def analyze_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id)
):
    filename = file.filename or ""
    contents = await file.read()

    # Determine file type and parse
    try:
        if filename.endswith(".csv"):
            texts = parse_csv(contents)
        elif filename.endswith(".txt"):
            texts = parse_txt(contents)
        elif filename.endswith((".xlsx", ".xls")):
            texts = parse_excel(contents, filename)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Accepted: .csv, .txt, .xlsx, .xls",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if len(texts) > settings.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Exceeded maximum rows ({settings.MAX_CSV_ROWS}).",
        )

    summary = {
        "total_rows": len(texts),
        "processed_rows": 0,
        "skipped_rows": 0,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "average_confidence": 0.0,
        "emotion_counts": {},
        "errors": [],
    }

    # Concurrency control: limit to 10 concurrent requests to prevent CPU thrashing
    sem = asyncio.Semaphore(10)

    async def analyze_single(idx: int, text: str):
        if not text.strip():
            return idx, "skipped", None, None
        async with sem:
            try:
                res = await _analyze_in_thread(text)
                return idx, "success", res, None
            except Exception as e:
                return idx, "error", None, str(e)

    # Dispatch tasks and await them concurrently
    tasks = [analyze_single(i, text) for i, text in enumerate(texts)]
    results = await asyncio.gather(*tasks)

    total_confidence = 0.0
    emotion_counter: Counter = Counter()

    # Process results in order
    for idx, status, result, err_msg in sorted(results, key=lambda x: x[0]):
        if status == "skipped":
            summary["skipped_rows"] += 1
            continue
        elif status == "error":
            summary["skipped_rows"] += 1
            summary["errors"].append(f"Row {idx + 1}: {err_msg}")
            continue

        try:
            sentiment = result["sentiment"]
            confidence = result["sentiment_confidence"]
            emotion = result["emotion"]

            record = SentimentRecord(
                original_text=texts[idx],
                sentiment=sentiment,
                confidence=confidence,
                source_type="batch",
                emotion=emotion,
                emotion_confidence=result["emotion_confidence"],
                language_code=result["language"]["code"],
                language_name=result["language"]["name"],
                language_confidence=result["language_confidence"],
                sarcasm_detected=result["sarcasm"]["detected"],
                sarcasm_confidence=result["sarcasm"]["confidence"],
                sarcasm_reason=result["sarcasm"]["reason"],
                inference_time_ms=result["inference_time_ms"],
                user_id=current_user_id,
            )
            db.add(record)

            summary["processed_rows"] += 1
            total_confidence += confidence
            emotion_counter[emotion] += 1

            if sentiment == "positive":
                summary["positive_count"] += 1
            elif sentiment == "negative":
                summary["negative_count"] += 1
            else:
                summary["neutral_count"] += 1
        except Exception as e:
            summary["skipped_rows"] += 1
            summary["errors"].append(f"Row {idx + 1} save error: {str(e)}")

    db.commit()

    if summary["processed_rows"] > 0:
        summary["average_confidence"] = total_confidence / summary["processed_rows"]

    summary["emotion_counts"] = dict(emotion_counter)

    return BatchSummary(**summary)


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

@router.get("/history", response_model=List[HistoryItem])
def get_history(
    sentiment: str = Query(None),
    emotion: str = Query(None),
    language: str = Query(None),
    sarcasm: str = Query(None),
    search: str = Query(None),
    show_deleted: str = Query("false"),
    db: Session = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id)
):
    query = db.query(SentimentRecord)
    
    show_deleted_bool = show_deleted.lower() == "true"
    query = query.filter(SentimentRecord.is_deleted == show_deleted_bool)

    if current_user_id is not None:
        from sqlalchemy import or_
        query = query.filter(or_(SentimentRecord.user_id == current_user_id, SentimentRecord.user_id.is_(None)))



    if sentiment and sentiment != "all":
        query = query.filter(SentimentRecord.sentiment == sentiment)
    if emotion and emotion != "all":
        query = query.filter(SentimentRecord.emotion == emotion)
    if language and language != "all":
        query = query.filter(SentimentRecord.language_name == language)
    if sarcasm and sarcasm != "all":
        query = query.filter(SentimentRecord.sarcasm_detected == (sarcasm == "true"))
    if search:
        query = query.filter(SentimentRecord.original_text.ilike(f"%{search}%"))

    records = query.order_by(SentimentRecord.created_at.desc()).limit(100).all()

    return [
        HistoryItem(
            id=r.id,
            text_preview=r.original_text[:100] + ("..." if len(r.original_text) > 100 else ""),
            sentiment=r.sentiment,
            confidence=r.confidence,
            source_type=r.source_type,
            created_at=r.created_at,
            emotion=r.emotion,
            emotion_confidence=r.emotion_confidence,
            language_name=r.language_name,
            language_code=r.language_code,
            sarcasm_detected=r.sarcasm_detected,
            sarcasm_confidence=r.sarcasm_confidence,
            sarcasm_reason=r.sarcasm_reason,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(SentimentRecord).count()
    pos = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "positive").count()
    neg = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "negative").count()
    neu = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "neutral").count()

    # Emotion counts
    from sqlalchemy import func as sa_func

    emotion_rows = (
        db.query(SentimentRecord.emotion, sa_func.count(SentimentRecord.id))
        .filter(SentimentRecord.emotion.isnot(None))
        .group_by(SentimentRecord.emotion)
        .all()
    )
    emotion_counts = {row[0]: row[1] for row in emotion_rows}

    recent = db.query(SentimentRecord).order_by(SentimentRecord.created_at.desc()).limit(5).all()

    recent_activity = [
        HistoryItem(
            id=r.id,
            text_preview=r.original_text[:100] + ("..." if len(r.original_text) > 100 else ""),
            sentiment=r.sentiment,
            confidence=r.confidence,
            source_type=r.source_type,
            created_at=r.created_at,
            emotion=r.emotion,
            emotion_confidence=r.emotion_confidence,
            language_name=r.language_name,
            language_code=r.language_code,
            sarcasm_detected=r.sarcasm_detected,
            sarcasm_confidence=r.sarcasm_confidence,
            sarcasm_reason=r.sarcasm_reason,
        )
        for r in recent
    ]

    return StatsResponse(
        total_analyses=total,
        positive_count=pos,
        negative_count=neg,
        neutral_count=neu,
        emotion_counts=emotion_counts,
        recent_activity=recent_activity,
    )


# ---------------------------------------------------------------------------
# GET /export
# ---------------------------------------------------------------------------

@router.get("/export")
def export_data(db: Session = Depends(get_db)):
    records = db.query(SentimentRecord).order_by(SentimentRecord.created_at.desc()).all()

    df = pd.DataFrame(
        [
            {
                "id": r.id,
                "original_text": r.original_text,
                "sentiment": r.sentiment,
                "confidence": r.confidence,
                "emotion": r.emotion,
                "emotion_confidence": r.emotion_confidence,
                "language": r.language_name,
                "language_code": r.language_code,
                "source_type": r.source_type,
                "processing_time_ms": r.processing_time_ms,
                "inference_time_ms": r.inference_time_ms,
                "created_at": r.created_at,
            }
            for r in records
        ]
    )

    stream = StringIO()
    df.to_csv(stream, index=False)

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=sentiment_export.csv"
    return response


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    password = req.password
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create user (auto-register)
        user = User(email=email, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
    access_token = create_access_token(data={"user_id": user.id, "email": user.email})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        email=user.email,
        user_id=user.id
    )


# ---------------------------------------------------------------------------
# POST /social/analyze
# ---------------------------------------------------------------------------

@router.post("/social/analyze", response_model=SocialAnalyzeResponse)
async def analyze_social(req: SocialAnalyzeRequest, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        t0 = time.perf_counter()
        result = await _analyze_in_thread(req.text)
        processing_ms = round((time.perf_counter() - t0) * 1000, 2)
        
        aspect_val = detect_aspect_and_sentiment(req.text)
        record = SocialAnalysis(
            user_id=current_user_id,
            platform=req.platform,
            original_text=req.text,
            detected_language=result["language"]["name"],
            language_code=result["language"]["code"],
            emotion=result["emotion"],
            sentiment=result["sentiment"],
            confidence=result["sentiment_confidence"],
            sarcasm_detected=result["sarcasm"]["detected"],
            sarcasm_confidence=result["sarcasm"]["confidence"],
            sarcasm_reason=result["sarcasm"]["reason"],
            processing_time_ms=processing_ms,
            inference_time_ms=result["inference_time_ms"],
            aspect=aspect_val
        )
        db.add(record)

        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /social/batch
# ---------------------------------------------------------------------------

import string
import json

@router.post("/social/batch", response_model=SocialBatchResponse)
async def analyze_social_batch(req: SocialBatchRequest, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    raw_lines = req.text.split("\n")
    comments = [line.strip() for line in raw_lines if line.strip()]
    if not comments:
        raise HTTPException(status_code=400, detail="No comments provided.")
        
    t_start = time.perf_counter()
    sem = asyncio.Semaphore(10)
    
    async def analyze_single(idx: int, text: str):
        async with sem:
            t0 = time.perf_counter()
            try:
                res = await _analyze_in_thread(text)
                processing_ms = round((time.perf_counter() - t0) * 1000, 2)
                return idx, "success", res, processing_ms, None
            except Exception as e:
                return idx, "error", None, 0.0, str(e)
                
    tasks = [analyze_single(i, comment) for i, comment in enumerate(comments)]
    tasks_results = await asyncio.gather(*tasks)
    results_list = []
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}


    emotion_counts = {}
    language_counts = {}
    sarcasm_counts = {"sarcastic": 0, "not sarcastic": 0}
    aspect_counts = {}
    
    total_confidence = 0.0
    sarcastic_count = 0
    total_inference_time = 0.0
    total_processing_time = 0.0
    
    # Keyword extraction lists
    positive_words = []
    negative_words = []
    all_words = []
    emotional_words = []
    
    # Custom simple English stopwords list
    stop_words = {
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
        "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
        "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
        "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
        "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
        "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
        "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
        "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
        "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
        "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
        "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
        "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
    }
    
    # Create the BatchAnalysisRun parent record first
    batch_run = BatchAnalysisRun(
        user_id=current_user_id,
        platform=req.platform,
        total_processed=0,
        average_confidence=0.0,
        sarcasm_rate=0.0,
        sentiment_distribution="{}",
        emotion_distribution="{}",
        language_distribution="{}",
        sarcasm_distribution="{}",
        keywords_summary="{}",
        aspect_sentiment_table="[]",
        executive_summary="",
        recommendations="[]"
    )
    db.add(batch_run)
    db.commit()
    db.refresh(batch_run)
    
    records_to_insert = []
    
    for idx, status, res, proc_time, err in sorted(tasks_results, key=lambda x: x[0]):
        comment_text = comments[idx]
        if status == "error":
            continue
            
        sentiment = res["sentiment"]
        confidence = res["sentiment_confidence"]
        emotion = res["emotion"]
        emotion_confidence = res["emotion_confidence"]
        lang_name = res["language"]["name"]
        lang_code = res["language"]["code"]
        sarcasm_detected = res["sarcasm"]["detected"]
        sarcasm_conf = res["sarcasm"]["confidence"]
        sarcasm_reason = res["sarcasm"]["reason"]
        inf_time = res["inference_time_ms"]
        
        aspect_val = detect_aspect_and_sentiment(comment_text)
        
        record = SocialAnalysis(
            user_id=current_user_id,
            platform=req.platform,
            original_text=comment_text,
            detected_language=lang_name,
            language_code=lang_code,
            emotion=emotion,
            sentiment=sentiment,
            confidence=confidence,
            sarcasm_detected=sarcasm_detected,
            sarcasm_confidence=sarcasm_conf,
            sarcasm_reason=sarcasm_reason,
            processing_time_ms=proc_time,
            inference_time_ms=inf_time,
            aspect=aspect_val,
            batch_run_id=batch_run.id
        )
        records_to_insert.append(record)
        
        # Accumulate metrics
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        language_counts[lang_name] = language_counts.get(lang_name, 0) + 1
        
        # Accumulate aspect counts
        if aspect_val not in aspect_counts:
            aspect_counts[aspect_val] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        aspect_counts[aspect_val][sentiment] = aspect_counts[aspect_val].get(sentiment, 0) + 1
        
        if sarcasm_detected:
            sarcastic_count += 1
            sarcasm_counts["sarcastic"] += 1
        else:
            sarcasm_counts["not sarcastic"] += 1
            
        total_confidence += confidence
        total_inference_time += inf_time
        total_processing_time += proc_time
        
        # Process words for keywords
        words_clean = [
            w.strip(string.punctuation).lower()
            for w in comment_text.split()
            if w.strip(string.punctuation)
        ]
        
        exclusions = stop_words | PRONOUNS | COMMON_VERBS | GENERIC_WORDS
        
        for w in words_clean:
            if w not in exclusions and len(w) > 3:
                all_words.append(w)
                # Only add to the bucket matching THIS comment's sentiment
                if sentiment == "positive":
                    positive_words.append(w)
                elif sentiment == "negative":
                    negative_words.append(w)
                # "mixed" or "neutral" words only appear in all_words
                
                # Emotional words (non-neutral emotion with strong confidence)
                if emotion != "neutral" and emotion_confidence > 0.4:
                    emotional_words.append(w)

 
                    
    # Commit all records in batch
    if records_to_insert:
        db.add_all(records_to_insert)
        db.commit()
        for r in records_to_insert:
            db.refresh(r)
            
    total_processed = len(records_to_insert)
    if total_processed == 0:
        # Clean up empty batch run
        db.delete(batch_run)
        db.commit()
        raise HTTPException(status_code=400, detail="Failed to process any comments.")
        
    avg_confidence = total_confidence / total_processed
    sarcasm_rate = (sarcastic_count / total_processed) * 100
    avg_inference_time = total_inference_time / total_processed
    avg_processing_time = total_processing_time / total_processed
    
    # Calculate keyword summaries
    def get_top_k(words_list, k=10):
        c = Counter(words_list)
        return [KeywordExtractorItem(word=word, count=count) for word, count in c.most_common(k)]
        
    keywords_summary = KeywordsSummary(
        positive_keywords=get_top_k(positive_words),
        negative_keywords=get_top_k(negative_words),
        most_frequent=get_top_k(all_words),
        most_emotional=get_top_k(emotional_words)
    )
    
    # Compile business insights based ONLY on actual statistics
    pos_pct = round((sentiment_counts.get("positive", 0) / total_processed) * 100, 1)
    neg_pct = round((sentiment_counts.get("negative", 0) / total_processed) * 100, 1)
    neu_pct = round((sentiment_counts.get("neutral", 0) / total_processed) * 100, 1)
    mix_pct = round((sentiment_counts.get("mixed", 0) / total_processed) * 100, 1)
    
    if pos_pct >= 70.0:
        overall_sentiment = "positive"
    elif neg_pct >= 70.0:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "mixed"
        
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
    
    # Emojis mapping
    EMOJIS = {
        "joy": "😊", "sadness": "😔", "anger": "😤", "fear": "😨", "surprise": "😲", 
        "disgust": "🤢", "love": "❤️", "neutral": "😐"
    }
    dominant_emotion_emoji = EMOJIS.get(dominant_emotion.lower(), "😐")
    
    # Top praised features & top complaints based on aspect-based sentiment
    praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > counts["negative"]]
    if not praised:
        praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > 0]
    top_praises = sorted(praised, key=lambda a: aspect_counts[a]["positive"], reverse=True)[:3]
    if not top_praises:
        top_praises = ["General Experience"]
        
    complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > counts["positive"]]
    if not complained:
        complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > 0]
    top_complaints = sorted(complained, key=lambda a: aspect_counts[a]["negative"], reverse=True)[:3]
    if not top_complaints:
        top_complaints = ["None Detected"]
        
    # Dynamic recommendations referring only to detected aspects
    recs = []
    if complained and [c for c in top_complaints if c != 'None Detected']:
        weakness_str = " and ".join(top_complaints)
        strength_str = f" while maintaining the excellent {' and '.join(top_praises)}" if praised else ""
        recs.append(f"Improve {weakness_str.lower()}{strength_str.lower()} to enhance overall user satisfaction.")
    elif praised:
        recs.append(f"Continue leveraging your key strengths in {', '.join(top_praises).lower()} to sustain positive momentum.")
        
    if sarcasm_rate > 20 and [c for c in top_complaints if c != 'None Detected']:
        recs.append(f"High sarcasm rate detected ({round(sarcasm_rate, 1)}%). Monitor underlying feedback on {', '.join(top_complaints).lower()} for subtle critique.")
        
    if not recs:
        recs.append("Maintain quality of services and continue monitoring customer sentiments.")
        
    # Generate executive summary dynamically
    sarcasm_text = "Sarcastic comments were detected." if sarcasm_rate > 20 else "No sarcasm was detected."
    trend_text = "with a slightly positive trend" if pos_pct > neg_pct else ("with a slightly negative trend" if neg_pct > pos_pct else "with a neutral trend")
    overall_text = f"Overall audience response is {overall_sentiment.capitalize()} {trend_text}."
    
    strength_details = f"Most customers appreciated the {', '.join([p.lower() for p in top_praises])}." if praised else ""
    weakness_details = f"Negative feedback focused on {', '.join([c.lower() for c in top_complaints if c != 'None Detected'])}." if [c for c in top_complaints if c != 'None Detected'] else ""
    
    exec_summary = (
        f"Out of {total_processed} analyzed comments, "
        f"{sentiment_counts['positive']} Positive, "
        f"{sentiment_counts['negative']} Negative, "
        f"{sentiment_counts['neutral']} Neutral, "
        f"{sentiment_counts['mixed']} Mixed. "
        f"{strength_details} "
        f"{weakness_details} "
        f"{sarcasm_text} "
        f"{overall_text}"
    )
    
    # Aspect sentiment table list
    aspect_sentiment_table = []
    for aspect, counts in aspect_counts.items():
        aspect_sentiment_table.append(AspectSentimentItem(
            aspect=aspect,
            positive=counts["positive"],
            negative=counts["negative"],
            neutral=counts["neutral"] + counts["mixed"]
        ))
        
    insights = BusinessInsights(
        total_count=total_processed,
        positive_percentage=pos_pct,
        negative_percentage=neg_pct,
        neutral_percentage=neu_pct,
        mixed_percentage=mix_pct,
        dominant_emotion=dominant_emotion,
        dominant_emotion_emoji=dominant_emotion_emoji,
        top_praises=top_praises,
        top_complaints=top_complaints,
        recommendations=recs,
        aspect_sentiment_table=aspect_sentiment_table,
        executive_summary=exec_summary
    )
    
    # Save aggregates in BatchAnalysisRun
    batch_run.total_processed = total_processed
    batch_run.average_confidence = round(avg_confidence, 4)
    batch_run.sarcasm_rate = round(sarcasm_rate, 2)
    batch_run.sentiment_distribution = json.dumps(sentiment_counts)
    batch_run.emotion_distribution = json.dumps(emotion_counts)
    batch_run.language_distribution = json.dumps(language_counts)
    batch_run.sarcasm_distribution = json.dumps(sarcasm_counts)
    
    # Convert Pydantic schemas to dict before serializing
    batch_run.keywords_summary = json.dumps(keywords_summary.model_dump())
    batch_run.aspect_sentiment_table = json.dumps([item.model_dump() for item in aspect_sentiment_table])
    batch_run.executive_summary = exec_summary
    batch_run.recommendations = json.dumps(recs)
    
    batch_run.processing_time_ms = round(avg_processing_time, 2)
    batch_run.inference_time_ms = round(avg_inference_time, 2)
    
    db.commit()
    
    # Return complete response
    return SocialBatchResponse(
        total_processed=total_processed,
        average_confidence=round(avg_confidence, 4),
        sarcasm_rate=round(sarcasm_rate, 2),
        sentiment_distribution=sentiment_counts,
        emotion_distribution=emotion_counts,
        language_distribution=language_counts,
        sarcasm_distribution=sarcasm_counts,
        average_processing_time_ms=round(avg_processing_time, 2),
        average_inference_time_ms=round(avg_inference_time, 2),
        keywords=keywords_summary,
        insights=insights,
        results=[SocialAnalyzeResponse.from_orm(r) for r in records_to_insert]
    )




# ---------------------------------------------------------------------------
# POST /reviews
# ---------------------------------------------------------------------------

@router.post("/reviews", response_model=SocialBatchResponse)
async def analyze_reviews_batch(req: ReviewsBatchRequest, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Modular reviews endpoint that pipes into batch analysis with review formatting."""
    social_req = SocialBatchRequest(platform=req.platform, text=req.text)
    return await analyze_social_batch(social_req, db, current_user_id)


# ---------------------------------------------------------------------------
# GET /dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Returns Customer Satisfaction Score (CSAT), Overall Health Score (OHS), and recent batch runs."""
    records = db.query(SocialAnalysis).filter(
        SocialAnalysis.user_id == current_user_id,
        SocialAnalysis.is_deleted == False
    ).all()
    
    total = len(records)
    if total == 0:
        return DashboardStatsResponse(
            total_comments=0,
            customer_satisfaction_score=0.0,
            overall_health_score=0.0,
            average_confidence=0.0,
            sarcasm_rate=0.0,
            average_processing_time_ms=0.0,
            sentiment_distribution={},
            emotion_distribution={},
            recent_runs=[]
        )
        
    pos_count = sum(1 for r in records if r.sentiment == "positive")
    neu_count = sum(1 for r in records if r.sentiment == "neutral")
    neg_count = sum(1 for r in records if r.sentiment == "negative")
    mix_count = sum(1 for r in records if r.sentiment == "mixed")
    
    # CSAT = (Positive + 0.5 * (Neutral + Mixed)) / Total
    csat = round(((pos_count + 0.5 * (neu_count + mix_count)) / total) * 100, 1)
    
    sarc_count = sum(1 for r in records if r.sarcasm_detected)
    sarc_rate = (sarc_count / total) * 100
    avg_conf = sum(r.confidence for r in records if r.confidence is not None) / total
    
    # Overall Health Score (OHS) formula
    ohs = round(csat * (1.0 - 0.5 * (sarc_count / total)) * avg_conf, 1)
    
    sent_dist = {
        "positive": float(pos_count),
        "negative": float(neg_count),
        "neutral": float(neu_count),
        "mixed": float(mix_count)
    }
    
    emotion_counts = {}
    for r in records:
        if r.emotion:
            emotion_counts[r.emotion] = emotion_counts.get(r.emotion, 0) + 1
            
    avg_proc = sum(r.processing_time_ms for r in records if r.processing_time_ms is not None) / total
    
    # Query recent batch runs
    runs = db.query(BatchAnalysisRun).filter(
        BatchAnalysisRun.user_id == current_user_id,
        BatchAnalysisRun.is_deleted == False
    ).order_by(BatchAnalysisRun.created_at.desc()).limit(5).all()
    
    recent_runs = []
    for run in runs:
        recent_runs.append(BatchAnalysisRunResponse(
            id=run.id,
            user_id=run.user_id,
            platform=run.platform,
            total_processed=run.total_processed,
            average_confidence=run.average_confidence,
            sarcasm_rate=run.sarcasm_rate,
            sentiment_distribution=json.loads(run.sentiment_distribution or "{}"),
            emotion_distribution=json.loads(run.emotion_distribution or "{}"),
            language_distribution=json.loads(run.language_distribution or "{}"),
            sarcasm_distribution=json.loads(run.sarcasm_distribution or "{}"),
            keywords_summary=json.loads(run.keywords_summary or "{}"),
            aspect_sentiment_table=json.loads(run.aspect_sentiment_table or "[]"),
            executive_summary=run.executive_summary or "",
            recommendations=json.loads(run.recommendations or "[]"),
            processing_time_ms=run.processing_time_ms,
            inference_time_ms=run.inference_time_ms,
            created_at=run.created_at
        ))
        
    return DashboardStatsResponse(
        total_comments=total,
        customer_satisfaction_score=csat,
        overall_health_score=ohs,
        average_confidence=round(avg_conf, 4),
        sarcasm_rate=round(sarc_rate, 2),
        average_processing_time_ms=round(avg_proc, 2),
        sentiment_distribution=sent_dist,
        emotion_distribution=emotion_counts,
        recent_runs=recent_runs
    )


# ---------------------------------------------------------------------------
# GET /statistics
# ---------------------------------------------------------------------------

@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics_breakdown(
    batch_run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Returns detailed distributions (emotion, sentiment, language, sarcasm) for visual charts."""
    query = db.query(SocialAnalysis).filter(
        SocialAnalysis.user_id == current_user_id,
        SocialAnalysis.is_deleted == False
    )
    if batch_run_id:
        query = query.filter(SocialAnalysis.batch_run_id == batch_run_id)
        
    records = query.all()
    total = len(records)
    if total == 0:
        return StatisticsResponse(
            sentiment_distribution={},
            emotion_distribution={},
            language_distribution={},
            sarcasm_distribution={},
            confidence_intervals={},
            processing_time_avg=0.0,
            sarcasm_rate=0.0
        )
        
    pos_count = sum(1 for r in records if r.sentiment == "positive")
    neg_count = sum(1 for r in records if r.sentiment == "negative")
    neu_count = sum(1 for r in records if r.sentiment == "neutral")
    mix_count = sum(1 for r in records if r.sentiment == "mixed")
    
    sent_dist = {"positive": float(pos_count), "negative": float(neg_count), "neutral": float(neu_count), "mixed": float(mix_count)}
    
    emotion_counts = {}
    lang_counts = {}
    sarcasm_counts = {"sarcastic": 0, "not sarcastic": 0}
    confidence_intervals = {"90-100": 0, "80-90": 0, "70-80": 0, "60-70": 0, "50-60": 0, "below 50": 0}
    
    total_proc = 0.0
    sarcastic_count = 0
    
    for r in records:
        if r.emotion:
            emotion_counts[r.emotion] = emotion_counts.get(r.emotion, 0) + 1
        if r.detected_language:
            lang_counts[r.detected_language] = lang_counts.get(r.detected_language, 0) + 1
            
        if r.sarcasm_detected:
            sarcastic_count += 1
            sarcasm_counts["sarcastic"] += 1
        else:
            sarcasm_counts["not sarcastic"] += 1
            
        if r.processing_time_ms:
            total_proc += r.processing_time_ms
            
        conf = r.confidence or 0.0
        if conf >= 0.90:
            confidence_intervals["90-100"] += 1
        elif conf >= 0.80:
            confidence_intervals["80-90"] += 1
        elif conf >= 0.70:
            confidence_intervals["70-80"] += 1
        elif conf >= 0.60:
            confidence_intervals["60-70"] += 1
        elif conf >= 0.50:
            confidence_intervals["50-60"] += 1
        else:
            confidence_intervals["below 50"] += 1
            
    return StatisticsResponse(
        sentiment_distribution=sent_dist,
        emotion_distribution=emotion_counts,
        language_distribution=lang_counts,
        sarcasm_distribution=sarcasm_counts,
        confidence_intervals=confidence_intervals,
        processing_time_avg=round(total_proc / total, 2),
        sarcasm_rate=round((sarcastic_count / total) * 100, 2)
    )


# ---------------------------------------------------------------------------
# GET /aspects
# ---------------------------------------------------------------------------

@router.get("/aspects", response_model=AspectAnalyticsResponse)
def get_aspect_analytics(
    batch_run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Returns aspect sentiment matrix, praises, and complaints based on dynamic aspects."""
    query = db.query(SocialAnalysis).filter(
        SocialAnalysis.user_id == current_user_id,
        SocialAnalysis.is_deleted == False
    )
    if batch_run_id:
        query = query.filter(SocialAnalysis.batch_run_id == batch_run_id)
        
    records = query.all()
    if not records:
        return AspectAnalyticsResponse(aspect_sentiment_table=[], top_praises=[], top_complaints=[])
        
    aspect_counts = {}
    for r in records:
        aspect_val = r.aspect or "General Experience"
        sentiment = r.sentiment or "neutral"
        if aspect_val not in aspect_counts:
            aspect_counts[aspect_val] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        aspect_counts[aspect_val][sentiment] = aspect_counts[aspect_val].get(sentiment, 0) + 1
        
    aspect_sentiment_table = []
    for aspect, counts in aspect_counts.items():
        aspect_sentiment_table.append(AspectSentimentItem(
            aspect=aspect,
            positive=counts["positive"],
            negative=counts["negative"],
            neutral=counts["neutral"] + counts["mixed"]
        ))
        
    praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > counts["negative"]]
    if not praised:
        praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > 0]
    top_praises = sorted(praised, key=lambda a: aspect_counts[a]["positive"], reverse=True)[:3]
    
    complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > counts["positive"]]
    if not complained:
        complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > 0]
    top_complaints = sorted(complained, key=lambda a: aspect_counts[a]["negative"], reverse=True)[:3]
    
    return AspectAnalyticsResponse(
        aspect_sentiment_table=aspect_sentiment_table,
        top_praises=top_praises,
        top_complaints=top_complaints
    )


# ---------------------------------------------------------------------------
# GET /business
# ---------------------------------------------------------------------------

@router.get("/business", response_model=BusinessInsightsResponse)
def get_business_insights(
    batch_run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Returns strategic recommendations and executive summaries derived directly from analysis."""
    query = db.query(SocialAnalysis).filter(
        SocialAnalysis.user_id == current_user_id,
        SocialAnalysis.is_deleted == False
    )
    if batch_run_id:
        query = query.filter(SocialAnalysis.batch_run_id == batch_run_id)
        
    records = query.all()
    total = len(records)
    if total == 0:
        return BusinessInsightsResponse(
            executive_summary="No data analyzed yet.",
            recommendations=["Maintain quality of services and continue monitoring customer sentiments."],
            total_processed=0,
            csat=0.0,
            ohs=0.0
        )
        
    pos_count = sum(1 for r in records if r.sentiment == "positive")
    neg_count = sum(1 for r in records if r.sentiment == "negative")
    neu_count = sum(1 for r in records if r.sentiment == "neutral")
    mix_count = sum(1 for r in records if r.sentiment == "mixed")
    
    csat = round(((pos_count + 0.5 * (neu_count + mix_count)) / total) * 100, 1)
    sarc_count = sum(1 for r in records if r.sarcasm_detected)
    sarc_rate = (sarc_count / total) * 100
    avg_conf = sum(r.confidence for r in records if r.confidence is not None) / total
    ohs = round(csat * (1.0 - 0.5 * (sarc_count / total)) * avg_conf, 1)
    
    aspect_counts = {}
    for r in records:
        aspect_val = r.aspect or "General Experience"
        sentiment = r.sentiment or "neutral"
        if aspect_val not in aspect_counts:
            aspect_counts[aspect_val] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        aspect_counts[aspect_val][sentiment] = aspect_counts[aspect_val].get(sentiment, 0) + 1
        
    praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > counts["negative"]]
    top_praises = sorted(praised, key=lambda a: aspect_counts[a]["positive"], reverse=True)[:3]
    complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > counts["positive"]]
    top_complaints = sorted(complained, key=lambda a: aspect_counts[a]["negative"], reverse=True)[:3]
    
    recs = []
    if complained and [c for c in top_complaints if c != 'None Detected']:
        weakness_str = " and ".join(top_complaints)
        strength_str = f" while maintaining the excellent {' and '.join(top_praises)}" if praised else ""
        recs.append(f"Improve {weakness_str.lower()}{strength_str.lower()} to enhance overall user satisfaction.")
    elif praised:
        recs.append(f"Continue leveraging your key strengths in {', '.join(top_praises).lower()} to sustain positive momentum.")
        
    if sarcasm_rate > 20 and [c for c in top_complaints if c != 'None Detected']:
        recs.append(f"High sarcasm rate detected ({round(sarcasm_rate, 1)}%). Monitor underlying feedback on {', '.join(top_complaints).lower()} for subtle critique.")
        
    if not recs:
        recs.append("Maintain quality of services and continue monitoring customer sentiments.")
        
    sarcasm_text = "Sarcastic comments were detected." if sarcasm_rate > 20 else "No sarcasm was detected."
    trend_text = "with a positive trajectory" if csat >= 70.0 else ("with a negative trajectory" if csat <= 40.0 else "with a mixed trajectory")
    overall_text = f"Overall customer feedback is trending {trend_text} with an Health Score of {ohs}%."
    
    exec_summary = (
        f"Analyzed {total} customer feedback records, resulting in "
        f"{pos_count} Positive, {neg_count} Negative, {neu_count} Neutral, and {mix_count} Mixed sentiments. "
        f"Dominant praised features include {', '.join([p.lower() for p in top_praises]) if praised else 'general experience'}. "
        f"Main pain points identified: {', '.join([c.lower() for c in top_complaints]) if complained else 'none'}. "
        f"{sarcasm_text} {overall_text}"
    )
    
    return BusinessInsightsResponse(
        executive_summary=exec_summary,
        recommendations=recs,
        total_processed=total,
        csat=csat,
        ohs=ohs
    )


# ---------------------------------------------------------------------------
# GET /social/history
# ---------------------------------------------------------------------------

@router.get("/social/history", response_model=List[SocialAnalyzeResponse])
def get_social_history(
    platform: str = Query(None),
    emotion: str = Query(None),
    sentiment: str = Query(None),
    language: str = Query(None),
    aspect: str = Query(None),
    search: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_confidence: float = Query(None),
    max_confidence: float = Query(None),
    show_deleted: str = Query("false"),
    sort_by: str = Query("date"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Retrieves list of comment records using advanced filters, sorting, and trash support."""
    query = db.query(SocialAnalysis).filter(SocialAnalysis.user_id == current_user_id)
    
    # Soft deletion filter
    show_deleted_bool = show_deleted.lower() == "true"
    query = query.filter(SocialAnalysis.is_deleted == show_deleted_bool)
    
    if platform and platform != "all":
        query = query.filter(SocialAnalysis.platform == platform)
    if emotion and emotion != "all":
        query = query.filter(SocialAnalysis.emotion == emotion)
    if sentiment and sentiment != "all":
        query = query.filter(SocialAnalysis.sentiment == sentiment)
    if language and language != "all":
        query = query.filter(SocialAnalysis.detected_language == language)
    if aspect and aspect != "all":
        query = query.filter(SocialAnalysis.aspect == aspect)
    if min_confidence is not None:
        query = query.filter(SocialAnalysis.confidence >= min_confidence)
    if max_confidence is not None:
        query = query.filter(SocialAnalysis.confidence <= max_confidence)
    if search:
        query = query.filter(SocialAnalysis.original_text.ilike(f"%{search}%"))
        
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(SocialAnalysis.created_at >= start_dt)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.filter(SocialAnalysis.created_at <= end_dt)
        except ValueError:
            pass
            
    # Sorting
    sort_col = SocialAnalysis.created_at
    if sort_by == "confidence":
        sort_col = SocialAnalysis.confidence
    elif sort_by == "speed":
        sort_col = SocialAnalysis.processing_time_ms
    elif sort_by == "sentiment":
        sort_col = SocialAnalysis.sentiment
    elif sort_by == "emotion":
        sort_col = SocialAnalysis.emotion

    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())
        
    records = query.all()
    return records


# ---------------------------------------------------------------------------
# GET /social/history/{id}
# ---------------------------------------------------------------------------

@router.get("/social/history/{id}", response_model=SocialAnalyzeResponse)
def get_social_history_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    record = db.query(SocialAnalysis).filter(

        SocialAnalysis.id == id,
        SocialAnalysis.user_id == current_user_id,
        SocialAnalysis.is_deleted == False
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Social analysis record not found.")
    return record


# ---------------------------------------------------------------------------
# DELETE /social/{id}
# ---------------------------------------------------------------------------

@router.delete("/social/{id}")
def delete_social_record(
    id: int,
    permanent: bool = Query(False),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Soft deletes comments by default, support permanent purge via query."""
    record = db.query(SocialAnalysis).filter(SocialAnalysis.id == id, SocialAnalysis.user_id == current_user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Social analysis record not found.")
        
    if permanent:
        db.delete(record)
    else:
        record.is_deleted = True
    db.commit()
    return {"message": "Social analysis record deleted successfully."}


# ---------------------------------------------------------------------------
# POST /social/{id}/restore
# ---------------------------------------------------------------------------

@router.post("/social/{id}/restore")
def restore_social_record(
    id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Restores soft-deleted comment analysis back into active history."""
    record = db.query(SocialAnalysis).filter(SocialAnalysis.id == id, SocialAnalysis.user_id == current_user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Social analysis record not found.")
        
    record.is_deleted = False
    db.commit()
    return {"message": "Social analysis record restored successfully."}


# ---------------------------------------------------------------------------
# GET /report/{analysis_id}
# ---------------------------------------------------------------------------

@router.get("/report/{analysis_id}")
def download_pdf_report(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        user = db.query(User).filter(User.id == current_user_id).first()
        user_email = user.email if user else "user@emotionsense.ai"
        
        pdf_buffer = generate_pdf_report(db, analysis_id, current_user_id, user_email)
        
        headers = {
            "Content-Disposition": f"attachment; filename=emotionsense_report_{analysis_id}.pdf"
        }
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE /history/{record_id}
# ---------------------------------------------------------------------------

@router.delete("/history/{record_id}")
def delete_history_record(
    record_id: int,
    permanent: bool = Query(False),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Soft deletes history records by default, supports permanent purge."""
    record = db.query(SentimentRecord).filter(SentimentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Sentiment log record not found.")
        
    if permanent:
        db.delete(record)
    else:
        record.is_deleted = True
    db.commit()
    return {"status": "success", "message": "Sentiment record deleted successfully."}


# ---------------------------------------------------------------------------
# POST /history/{record_id}/restore
# ---------------------------------------------------------------------------

@router.post("/history/{record_id}/restore")
def restore_history_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Restores soft-deleted history log back into active view."""
    record = db.query(SentimentRecord).filter(SentimentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Sentiment log record not found.")
        
    record.is_deleted = False
    db.commit()
    return {"status": "success", "message": "Sentiment record restored successfully."}
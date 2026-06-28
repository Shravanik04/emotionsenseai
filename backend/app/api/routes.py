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

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: run heavy inference off the event-loop
# ---------------------------------------------------------------------------

async def _analyze_in_thread(text: str):
    """Run model inference in a thread-pool so we don't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyzer.analyze_full, text)


# ---------------------------------------------------------------------------
# POST /analyze-text  (REST — full analysis)
# ---------------------------------------------------------------------------

@router.post("/analyze-text", response_model=FullAnalysisWithIdResponse)
async def analyze_text(req: SentimentRequest, db: Session = Depends(get_db)):
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
async def analyze_batch(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or ""
    contents = await file.read()

    # Determine file type and parse
    try:
        if filename.endswith(".csv"):
            texts = parse_csv(contents.decode("utf-8"))
        elif filename.endswith(".txt"):
            texts = parse_txt(contents.decode("utf-8"))
        elif filename.endswith((".xlsx", ".xls")):
            texts = parse_excel(contents)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Accepted: .csv, .txt, .xlsx, .xls",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

    total_confidence = 0.0
    emotion_counter: Counter = Counter()

    for i, text in enumerate(texts):
        if not text.strip():
            summary["skipped_rows"] += 1
            continue
        try:
            result = await _analyze_in_thread(text)
            sentiment = result["sentiment"]
            confidence = result["sentiment_confidence"]
            emotion = result["emotion"]

            record = SentimentRecord(
                original_text=text,
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
            summary["errors"].append(f"Row {i + 1}: {str(e)}")

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
    db: Session = Depends(get_db),
):
    query = db.query(SentimentRecord)

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
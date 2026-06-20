from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import pandas as pd
from io import StringIO
from datetime import datetime

from app.db.session import get_db
from app.models.sentiment_model import SentimentRecord
from app.schemas.sentiment import SentimentRequest, SentimentResponse, BatchSummary, HistoryItem, StatsResponse
from app.services.analysis_service import analyzer
from app.utils.csv_utils import parse_csv
from app.core.config import settings

router = APIRouter()

@router.post("/analyze-text", response_model=SentimentResponse)
def analyze_text(req: SentimentRequest, db: Session = Depends(get_db)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        sentiment, confidence = analyzer.analyze(req.text)
        record = SentimentRecord(
            original_text=req.text,
            sentiment=sentiment,
            confidence=confidence,
            source_type="manual"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return SentimentResponse(
            id=record.id,
            sentiment=sentiment,
            confidence=confidence,
            processed_timestamp=record.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-batch", response_model=BatchSummary)
async def analyze_batch(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    contents = await file.read()
    contents_str = contents.decode('utf-8')
    
    try:
        texts = parse_csv(contents_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(texts) > settings.MAX_CSV_ROWS:
        raise HTTPException(status_code=400, detail=f"Exceeded maximum rows ({settings.MAX_CSV_ROWS}).")

    summary = {
        "total_rows": len(texts),
        "processed_rows": 0,
        "skipped_rows": 0,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "average_confidence": 0.0,
        "errors": []
    }
    
    total_confidence = 0.0

    for i, text in enumerate(texts):
        if not text.strip():
            summary["skipped_rows"] += 1
            continue
        try:
            sentiment, confidence = analyzer.analyze(text)
            
            record = SentimentRecord(
                original_text=text,
                sentiment=sentiment,
                confidence=confidence,
                source_type="csv"
            )
            db.add(record)
            
            summary["processed_rows"] += 1
            total_confidence += confidence
            
            if sentiment == "positive":
                summary["positive_count"] += 1
            elif sentiment == "negative":
                summary["negative_count"] += 1
            else:
                summary["neutral_count"] += 1
                
        except Exception as e:
            summary["skipped_rows"] += 1
            summary["errors"].append(f"Row {i+1}: {str(e)}")

    db.commit()
    
    if summary["processed_rows"] > 0:
        summary["average_confidence"] = total_confidence / summary["processed_rows"]

    return BatchSummary(**summary)

@router.get("/history", response_model=list[HistoryItem])
def get_history(
    sentiment: str = Query(None), 
    search: str = Query(None), 
    db: Session = Depends(get_db)
):
    query = db.query(SentimentRecord)
    
    if sentiment and sentiment != "all":
        query = query.filter(SentimentRecord.sentiment == sentiment)
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
            created_at=r.created_at
        ) for r in records
    ]

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(SentimentRecord).count()
    pos = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "positive").count()
    neg = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "negative").count()
    neu = db.query(SentimentRecord).filter(SentimentRecord.sentiment == "neutral").count()
    
    recent = db.query(SentimentRecord).order_by(SentimentRecord.created_at.desc()).limit(5).all()
    
    recent_activity = [
        HistoryItem(
            id=r.id,
            text_preview=r.original_text[:100] + ("..." if len(r.original_text) > 100 else ""),
            sentiment=r.sentiment,
            confidence=r.confidence,
            source_type=r.source_type,
            created_at=r.created_at
        ) for r in recent
    ]
    
    return StatsResponse(
        total_analyses=total,
        positive_count=pos,
        negative_count=neg,
        neutral_count=neu,
        recent_activity=recent_activity
    )

@router.get("/export")
def export_data(db: Session = Depends(get_db)):
    from fastapi.responses import StreamingResponse
    
    records = db.query(SentimentRecord).order_by(SentimentRecord.created_at.desc()).all()
    
    df = pd.DataFrame([{
        "id": r.id,
        "original_text": r.original_text,
        "sentiment": r.sentiment,
        "confidence": r.confidence,
        "source_type": r.source_type,
        "created_at": r.created_at
    } for r in records])
    
    stream = StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=sentiment_export.csv"
    return response
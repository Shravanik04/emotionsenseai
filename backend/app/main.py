import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.routes import router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database schema migration helper
# ---------------------------------------------------------------------------

def _migrate_schema():
    """
    Add missing columns to the sentiment_records table so the app doesn't
    crash when running against an older schema.  SQLite supports ADD COLUMN
    but not DROP or ALTER, so we simply add what's missing.
    """
    new_columns = {
        "emotion": "VARCHAR(50)",
        "emotion_confidence": "FLOAT",
        "language_code": "VARCHAR(10)",
        "language_name": "VARCHAR(100)",
        "language_confidence": "FLOAT",
        "processing_time_ms": "FLOAT",
        "inference_time_ms": "FLOAT",
        "sarcasm_detected": "BOOLEAN DEFAULT 0",
        "sarcasm_confidence": "FLOAT",
        "sarcasm_reason": "TEXT",
    }

    insp = inspect(engine)
    if "sentiment_records" in insp.get_table_names():
        existing = {col["name"] for col in insp.get_columns("sentiment_records")}
        with engine.begin() as conn:
            for col_name, col_type in new_columns.items():
                if col_name not in existing:
                    logger.info("Adding missing column: %s", col_name)
                    conn.execute(
                        text(f"ALTER TABLE sentiment_records ADD COLUMN {col_name} {col_type}")
                    )

# Create tables (if they don't exist)
Base.metadata.create_all(bind=engine)
# Run migration for existing databases
_migrate_schema()

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="SentimentScope API", docs_url="/docs")

# CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["Sentiment"])

@app.get("/")
def root():
    return {"message": "SentimentScope API is running. Go to /docs for Swagger."}
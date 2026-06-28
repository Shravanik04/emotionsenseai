from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sentiment.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    MAX_CSV_ROWS: int = 500

    # Model configuration
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    EMOTION_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"
    LANGUAGE_MODEL: str = "papluca/xlm-roberta-base-language-detection"
    SARCASM_MODEL: str = "dima806/sarcasm-detection-distilbert"

    # Cache configuration
    PREDICTION_CACHE_SIZE: int = 1024

    class Config:
        env_file = ".env"

settings = Settings()

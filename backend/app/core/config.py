from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sentiment.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    MAX_CSV_ROWS: int = 500

    class Config:
        env_file = ".env"

settings = Settings()

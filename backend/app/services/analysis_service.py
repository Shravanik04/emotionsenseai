from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    _instance = None
    _pipe = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentAnalyzer, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        try:
            logger.info("Loading DistilBERT sentiment model...")
            # Using a standard sentiment model
            self._pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._pipe = None

    def analyze(self, text: str):
        if not self._pipe:
            raise RuntimeError("Model is not loaded.")
        
        # Truncate text to avoid token limits (512 tokens ~ ~2000 chars safe limit)
        result = self._pipe(text[:2000])[0]
        return result['label'].lower(), result['score']

analyzer = SentimentAnalyzer()

"""
Dedicated Sarcasm Detection Service using a multi-stage hybrid approach:
1. Sarcasm Construct Phrases: Direct checks for structural sarcastic phrases (e.g. oh great, yeah right).
2. Negative Event Detection: Identifies genuine negative events (e.g. laptop crashed, production bug, traffic).
3. Lexical Clash / Contradiction: Positive language colliding with negative events.
4. Machine Learning classifier: Pre-trained Hugging Face classifier model.
5. Sarcasm Override Rule: Downgrades sarcasm if no negative event or genuine mixed opinions are present.
"""
import logging
import re
from typing import Tuple, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Common sarcastic constructs
SARCASM_PHRASES = [
    "oh great", "wonderful, my", "fantastic, my", "yeah right", "best day ever... not",
    "just love getting", "totally enjoy", "absolutely love waiting", "another monday",
    "yeah, because everything always", "so glad that happened", "not like it matters",
    "another production bug", "another flat tire", "another bug"
]

# Positive adjectives or interjections that could denote sarcasm in bad contexts
SARCASM_POS_WORDS = {
    "love", "loved", "enjoy", "enjoyed", "wonderful", "fantastic", "great", "awesome",
    "perfect", "perfectly", "best", "brilliant", "outstanding", "superb", "delightful",
    "glad", "excited", "happy", "yippie", "yippiee", "hurray", "yay"
}

# Generic negative events patterns
NEGATIVE_EVENTS_PHRASES = [
    "laptop crashed", "crashed laptop", "production bug", "another bug", "waiting in traffic", 
    "traffic jam", "failed exam", "failed the exam", "missed flight", "missed train", "missed the train",
    "battery died", "internet disconnected", "rejected application", "lost wallet", "flat tire",
    "server outage", "deadline missed", "rain ruined", "another flat tire"
]

NEGATIVE_EVENT_WORDS = {
    "crashed", "failed", "rejected", "cancelled", "bug", "error", "traffic", "ruined", "annoyed"
}

def detect_negative_event(text: str) -> bool:
    """Return True if a genuine negative event is detected in the text."""
    text_lower = text.lower()
    if any(phrase in text_lower for phrase in NEGATIVE_EVENTS_PHRASES):
        return True
    words = set(re.findall(r'\b\w+\b', text_lower))
    if words & NEGATIVE_EVENT_WORDS:
        return True
    return False

class SarcasmDetector:
    _instance = None
    _pipe = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        try:
            import torch
            from transformers import pipeline
            device = 0 if torch.cuda.is_available() else -1
            logger.info("Loading sarcasm model: %s", settings.SARCASM_MODEL)
            self._pipe = pipeline(
                "text-classification",
                model=settings.SARCASM_MODEL,
                device=device,
                truncation=True
            )
            logger.info("Sarcasm model loaded.")
        except Exception as e:
            logger.error("Failed to load sarcasm model: %s", e)

    def detect_sarcasm(self, text: str) -> Tuple[bool, float, str]:
        """
        Analyze text and determine if it contains sarcastic intent using a multi-stage pipeline:
        1. Direct Sarcasm Phrase Checks
        2. Negative Event Detection
        3. Lexical Clash / Contradiction (Positive language + Negative event)
        4. Sarcasm Model Inference
        5. Sarcasm Override Rule (Mixed emotions validation)
        """
        text_lower = text.lower().strip()
        
        # 1. Direct sarcastic construct check (e.g. "oh great", "yeah right")
        for phrase in SARCASM_PHRASES:
            if phrase in text_lower:
                return True, 0.98, "Sarcastic construct detected directly in text phrase."

        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # 2. Detect if any positive language or interjections exist
        has_pos_language = any(w in words for w in SARCASM_POS_WORDS)
        
        # 3. Detect if a negative event exists
        has_neg_event = detect_negative_event(text_lower)
        
        # Direct rule checks for irony/mockery (Clash: Positive language + Negative event)
        # e.g., "wonderful. my laptop crashed" or "absolutely love waiting in traffic"
        if has_pos_language and has_neg_event:
            # Check for direct proximity of sarcasm indicators
            sarcastic_indicators = ["great", "wonderful", "fantastic", "perfect", "love waiting", "love getting", "love to wait", "enjoy waiting"]
            if any(ind in text_lower for ind in sarcastic_indicators):
                return True, 0.98, "Contextual irony: Positive expression colliding with a detected negative event."

        # 4. Model-based inference
        model_says_sarcastic = False
        model_score = 0.0
        if self._pipe:
            try:
                res = self._pipe(text)[0]
                label = res["label"].lower()
                score = res["score"]
                
                is_sarcastic = label in ("label_1", "sarcastic", "sarcasm", "yes")
                if is_sarcastic:
                    model_says_sarcastic = True
                    model_score = score
                else:
                    model_score = 1.0 - score
            except Exception as e:
                logger.error("Sarcasm model inference error: %s", e)

        # 5. Sarcasm Override Rule (Downgrade sarcasm if no negative event OR genuine mixed opinions exist)
        # Genuine mixed opinions: e.g. "I hate X but I love Y" (words contains positive and negative feelings)
        has_genuine_conflict = ("hate" in words or "dislike" in words or "sad" in words or "nervous" in words) and ("love" in words or "happy" in words or "excited" in words)
        
        if (model_says_sarcastic or (has_pos_language and has_neg_event)) and has_genuine_conflict and not has_neg_event:
            return False, 0.15, "Mixed emotions detected without irony."
            
        if model_says_sarcastic:
            # Sarcasm is only considered valid if a negative event is present, or a known direct sarcastic construct is used
            if has_neg_event:
                return True, model_score, "Machine learning classifier detected sarcastic intent aligned with a negative event."
            else:
                return False, 0.20, "Mixed emotions detected without irony."

        # Fallback
        return False, 0.0, "No sarcasm detected."

# Global singleton
sarcasm_detector = SarcasmDetector()

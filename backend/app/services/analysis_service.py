"""
Unified analysis service that loads sentiment, emotion, and language-detection
models once and exposes a thread-safe, cached ``analyze_full`` method.
Now upgraded with mixed sentiment logic, multi-label emotion ranking, low-confidence
possible emotions detection, sentence weight-fusion, and context-aware summaries.
"""
from __future__ import annotations

import re
import hashlib
import logging
import time
import math
import concurrent.futures
from collections import OrderedDict, Counter
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import pipeline

from app.core.config import settings
from app.utils.keyword_utils import extract_keywords
from app.utils.insight_utils import (
    generate_ai_summary,
    get_emotion_emoji,
    get_language_info,
    generate_emotion_summary,
)
from app.services.sarcasm_service import sarcasm_detector
from app.utils.emotion_lexicon import (
    refine_emotions,
    get_sub_emotion_explanation,
    EMOJI_MAP,
    detect_contradictory_emotions,
    SUB_EMOTIONS,
)

logger = logging.getLogger(__name__)

# Syllable/Readability helpers
def count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?;:()\"'")
    if not word:
        return 0
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count <= 0:
        count = 1
    return count

def calculate_readability_and_complexity(text: str) -> Tuple[float, str]:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    num_sentences = max(1, len(sentences))
    
    words = [w for w in text.split() if w.strip()]
    num_words = max(1, len(words))
    
    num_syllables = sum(count_syllables(w) for w in words)
    
    # Flesch Reading Ease Formula
    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    score = round(max(0.0, min(100.0, score)), 1)
    
    if score >= 80.0:
        complexity = "Low (Very Easy)"
    elif score >= 60.0:
        complexity = "Low (Easy)"
    elif score >= 50.0:
        complexity = "Moderate"
    elif score >= 30.0:
        complexity = "High (Difficult)"
    else:
        complexity = "High (Very Difficult)"
        
    return score, complexity

# NER Heuristic Stopwords
NER_STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "the", "a", "an", "and", "but", "or", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "through"
}

def extract_named_entities(text: str) -> Dict[str, List[str]]:
    entities = {
        "PERSON": [],
        "GPE": [],
        "ORG": [],
        "DATE": []
    }
    
    # 1. Date patterns
    date_patterns = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        r'\b(?:today|yesterday|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,\s+\d{4})?\b'
    ]
    for pattern in date_patterns:
        for m in re.findall(pattern, text, re.IGNORECASE):
            m_clean = m.strip(".,!?;:()\"'")
            if m_clean and m_clean not in entities["DATE"]:
                entities["DATE"].append(m_clean)

    # 2. Common place lookups
    locations = ["london", "paris", "tokyo", "delhi", "bangalore", "mumbai", "india", "usa", "uk", "california", "new york", "karnataka"]
    for loc in locations:
        pattern = r'\b' + re.escape(loc) + r'\b'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(0).title()
            if val not in entities["GPE"]:
                entities["GPE"].append(val)

    # 3. Capitalization scan
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    for sent in sentences:
        words = sent.split()
        if not words:
            continue
        # Scan words (excluding the first one of the sentence)
        for w in words[1:]:
            clean_w = w.strip(".,!?;:()\"'")
            if clean_w and clean_w[0].isupper() and clean_w.lower() not in NER_STOPWORDS:
                if clean_w not in entities["GPE"] and clean_w not in entities["PERSON"] and clean_w not in entities["ORG"]:
                    if any(suffix in clean_w.lower() for suffix in ["inc", "corp", "co", "ltd", "google", "microsoft", "amazon", "apple"]):
                        entities["ORG"].append(clean_w)
                    else:
                        entities["PERSON"].append(clean_w)
                        
    return entities


class _LRUCache:
    """Simple thread-compatible LRU cache using OrderedDict."""

    def __init__(self, maxsize: int = 1024):
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Dict) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
        self._cache[key] = value


def calibrate_emotion_distribution(emotions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not emotions:
        return []
    
    sorted_emotions = sorted(emotions, key=lambda x: -x["score"])
    s_1 = sorted_emotions[0]["score"]
    
    if s_1 <= 0:
        return [{"label": e["label"], "score": 0.0, "category": e.get("category", "neutral")} for e in sorted_emotions]
        
    # Calibrate the top emotion between 70% and 95%
    c_1 = 0.70 + 0.25 * math.tanh(2.37 * s_1)
    
    calibrated = []
    for i, item in enumerate(sorted_emotions):
        score = item["score"]
        label = item["label"]
        cat = item.get("category", "neutral")
        
        if i == 0:
            c_i = c_1
        else:
            r = score / s_1
            if r >= 0.75:
                # Strong Emotion: 60-85%
                c_i = c_1 * (r ** 0.4)
            elif r >= 0.40:
                # Moderate Emotion: 40-65%
                c_i = c_1 * (r ** 0.5)
            elif r >= 0.15:
                # Weak Emotion: 20-40%
                c_i = c_1 * (r ** 0.7)
            else:
                # Below 15%
                c_i = c_1 * (r ** 1.5)
                
        calibrated.append({
            "label": label,
            "score": round(c_i, 4),
            "category": cat
        })
        
    return sorted(calibrated, key=lambda x: -x["score"])


class AnalysisEngine:
    """
    Singleton analysis engine that loads three HuggingFace pipelines:
      1. Multilingual sentiment (positive / neutral / negative)
      2. English emotion (joy / anger / sadness / fear / surprise / disgust / neutral)
      3. Language detection
    """

    _instance: Optional["AnalysisEngine"] = None

    # Pipelines
    _sentiment_pipe = None
    _emotion_pipe = None
    _language_pipe = None

    # Prediction cache
    _cache: _LRUCache

    def __new__(cls) -> "AnalysisEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = _LRUCache(maxsize=settings.PREDICTION_CACHE_SIZE)
            cls._instance._load_models()
        return cls._instance

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _detect_device(self) -> int:
        """Return 0 (GPU) if CUDA is available, else -1 (CPU)."""
        if torch.cuda.is_available():
            logger.info("CUDA GPU detected — using GPU for inference.")
            return 0
        logger.info("No GPU detected — using CPU for inference.")
        return -1

    def _load_models(self) -> None:
        device = self._detect_device()

        try:
            logger.info("Loading sentiment model: %s", settings.SENTIMENT_MODEL)
            self._sentiment_pipe = pipeline(
                "sentiment-analysis",
                model=settings.SENTIMENT_MODEL,
                top_k=None,          # return all class probabilities
                device=device,
                truncation=True,
            )
            logger.info("Sentiment model loaded.")
        except Exception as exc:
            logger.error("Failed to load sentiment model: %s", exc)

        try:
            logger.info("Loading emotion model: %s", settings.EMOTION_MODEL)
            self._emotion_pipe = pipeline(
                "text-classification",
                model=settings.EMOTION_MODEL,
                top_k=None,
                device=device,
                truncation=True,
            )
            logger.info("Emotion model loaded.")
        except Exception as exc:
            logger.error("Failed to load emotion model: %s", exc)

        try:
            logger.info("Loading language model: %s", settings.LANGUAGE_MODEL)
            self._language_pipe = pipeline(
                "text-classification",
                model=settings.LANGUAGE_MODEL,
                top_k=5,             # top-5 language candidates
                device=device,
                truncation=True,
            )
            logger.info("Language model loaded.")
        except Exception as exc:
            logger.error("Failed to load language model: %s", exc)

    # ------------------------------------------------------------------
    # Legacy interface (kept for backward compatibility)
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> Tuple[str, float]:
        if not self._sentiment_pipe:
            raise RuntimeError("Sentiment model is not loaded.")
        result = self._sentiment_pipe(text[:2000])[0]
        top = max(result, key=lambda x: x["score"])
        label = self._normalize_sentiment_label(top["label"])
        return label, top["score"]

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def analyze_full(self, text: str) -> Dict[str, Any]:
        """
        Run language detection, translate to English, split into sentences,
        run batch sentiment, emotion, and sarcasm detection on each,
        and generate overall indicators, top-5 emotion rankings, timeline,
        named entities, and readability stats.
        """
        text_trimmed = text[:2000].strip()
        if not text_trimmed:
            return self._empty_result()

        cache_key = hashlib.md5(text_trimmed.encode("utf-8")).hexdigest()
        cached = self._cache.get(cache_key)
        if cached is not None:
            out = dict(cached)
            out["inference_time_ms"] = 0.0
            out["cache_hit"] = True
            return out

        t_start = time.perf_counter()

        # 1. Overall Language Detection
        translated_text, lang_code, lang_confidence = self._translate_and_detect(text_trimmed)
        if lang_confidence == 0.0:
            script_lang = self._detect_script_language(text_trimmed)
            if script_lang:
                lang_code = script_lang
                lang_confidence = 1.0
                translated_text = text_trimmed
            else:
                lang_results = self._run_language(text_trimmed)
                top_lang = lang_results[0] if lang_results else {"label": "en", "score": 0.0}
                lang_code = top_lang["label"]
                lang_confidence = top_lang["score"]
                translated_text = text_trimmed

        lang_info = get_language_info(lang_code)

        # 2. Split into sentences / clauses to handle mixed opinions
        def split_into_clauses(t: str) -> List[str]:
            sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()]
            clauses = []
            for s in sents:
                sub_clauses = re.split(r'\s+but\s+|\s+yet\s+|\s+however\s+|,\s*but\s+|;\s*', s, flags=re.IGNORECASE)
                clauses.extend([sc.strip() for sc in sub_clauses if sc.strip()])
            return clauses

        sentences_raw = split_into_clauses(text_trimmed)
        if not sentences_raw:
            sentences_raw = [text_trimmed]

        translated_sentences = split_into_clauses(translated_text)
        
        # Align original and translated sentences
        aligned = []
        for i, orig in enumerate(sentences_raw):
            if i < len(translated_sentences):
                aligned.append((orig, translated_sentences[i]))
            else:
                aligned.append((orig, orig))

        # 3. Batch Model Inference running concurrently
        orig_list = [pair[0] for pair in aligned]
        trans_list = [pair[1] for pair in aligned]

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            fut_sentiment = executor.submit(self._run_sentiment_batch, orig_list)
            fut_emotion = executor.submit(self._run_emotion_batch, trans_list if lang_code != "en" else orig_list)
            sentiment_batch_probs = fut_sentiment.result()
            emotion_batch_probs = fut_emotion.result()

        # Process each sentence
        processed_sentences = []
        timeline = []
        
        # Sarcasm Detection on entire text first to capture full context
        overall_sarcasm_detected, overall_sarcasm_confidence, s_reason = sarcasm_detector.detect_sarcasm(text_trimmed)
        overall_sarcasm_reasons = [s_reason] if overall_sarcasm_detected else []

        sub_emotion_sums = Counter()
        repetition_counts = Counter()
        
        # Sentiment accumulation lists for weight-fusion
        pos_scores = []
        neg_scores = []
        neu_scores = []
        total_sentiment_weight = 0.0

        num_sentences = len(aligned)

        for i, (orig, trans) in enumerate(aligned):
            # A. Sentiment Model Inference
            sent_probs = sentiment_batch_probs[i]
            top_sent = max(sent_probs, key=lambda x: x["score"])
            s_label = self._normalize_sentiment_label(top_sent["label"])
            s_conf = top_sent["score"]

            # B. Emotion Model Inference
            emo_probs = emotion_batch_probs[i]
            refined = refine_emotions(emo_probs, trans if lang_code != "en" else orig)

            # C. Sarcasm Detection & Irony Verification
            s_detected = overall_sarcasm_detected
            s_conf_val = overall_sarcasm_confidence
            s_reason_str = s_reason if overall_sarcasm_detected else "No sarcasm detected."
            
            # Sarcasm Correction (Irony Verification)
            if s_detected:
                if s_label == "positive":
                    s_label = "negative"
                    s_conf = max(s_conf, 0.85)
                # Inject disappointment/frustration
                refined = [{"label": "frustration", "score": 0.7, "category": "negative"}, {"label": "disappointment", "score": 0.2, "category": "negative"}] + [
                    r for r in refined if r["label"] not in ("frustration", "disappointment")
                ]
                total_r = sum(r["score"] for r in refined)
                for r in refined:
                    r["score"] = round(r["score"] / total_r, 4)

            # Calibrate sentence-level sub-emotions
            refined_calibrated = calibrate_emotion_distribution(refined)
            top_refined = refined_calibrated[0]
            e_label = top_refined["label"]
            e_conf = top_refined["score"]
            e_emoji = EMOJI_MAP.get(e_label, "😐")

            # Accumulate sentence repetition counts for boost
            for item in refined_calibrated:
                if item["score"] >= 0.15:
                    repetition_counts[item["label"]] += 1

            # D. Accumulate results
            position_weight = 1.2 if (i == 0 or i == num_sentences - 1) else 1.0
            
            # Extract probability scores
            p_score = 0.0
            n_score = 0.0
            u_score = 0.0
            for item in sent_probs:
                lbl = self._normalize_sentiment_label(item["label"])
                scr = item["score"]
                if lbl == "positive":
                    p_score = scr
                elif lbl == "negative":
                    n_score = scr
                else:
                    u_score = scr
                    
            if s_detected and p_score > n_score:
                n_score, p_score = p_score, n_score
                
            pos_scores.append(p_score * position_weight)
            neg_scores.append(n_score * position_weight)
            neu_scores.append(u_score * position_weight)
            total_sentiment_weight += position_weight

            for r in refined_calibrated:
                sub_emotion_sums[r["label"]] += r["score"] * position_weight

            timeline.append(e_label)

            processed_sentences.append({
                "text": orig,
                "sentiment": s_label,
                "sentiment_confidence": round(s_conf, 4),
                "emotion": e_label,
                "emotion_confidence": round(e_conf, 4),
                "emotion_emoji": e_emoji,
                "sarcasm": {
                    "detected": s_detected,
                    "confidence": round(s_conf_val if s_detected else 0.0, 4),
                    "reason": s_reason if s_detected else "No sarcasm detected."
                }
            })

        # 4. Aggregations & Overall Summary
        total_emotion_sum = sum(sub_emotion_sums.values())
        avg_emotions_raw = []
        for emo_name, score_sum in sub_emotion_sums.items():
            avg_score = score_sum / total_emotion_sum if total_emotion_sum > 0 else 0.0
            
            # Multi-Sentence Aggregation & Repetition Boost
            rep_count = repetition_counts[emo_name]
            boost_factor = 1.0
            if rep_count > 1:
                boost_factor = 1.0 + 0.25 * (rep_count - 1)
                
            avg_emotions_raw.append({
                "label": emo_name,
                "score": avg_score * boost_factor,
                "category": next((r["category"] for r in refined if r["label"] == emo_name), "neutral")
            })
            
        # Re-normalize after boost
        total_boosted = sum(e["score"] for e in avg_emotions_raw)
        for e in avg_emotions_raw:
            e["score"] = round(e["score"] / total_boosted, 4) if total_boosted > 0 else 0.0
            
        # Calibrate overall sub-emotions
        avg_emotions = calibrate_emotion_distribution(avg_emotions_raw)
        
        # Dominant overall indicators
        overall_emotion_item = avg_emotions[0]
        dominant_emotion = overall_emotion_item["label"]
        overall_emotion_conf = overall_emotion_item["score"]
        
        overall_emotion = dominant_emotion
        overall_emotion_emoji = EMOJI_MAP.get(overall_emotion, "😐")

        # Sentiment counter & Mixed Sentiment Logic
        overall_pos_score = round(sum(pos_scores) / total_sentiment_weight, 4) if total_sentiment_weight > 0 else 0.33
        overall_neg_score = round(sum(neg_scores) / total_sentiment_weight, 4) if total_sentiment_weight > 0 else 0.33
        overall_neutral_score = round(sum(neu_scores) / total_sentiment_weight, 4) if total_sentiment_weight > 0 else 0.33

        # Check if both positive and negative sub-emotions are present in top emotions
        pos_emotions = set(SUB_EMOTIONS["positive"])
        neg_emotions = set(SUB_EMOTIONS["negative"])
        
        has_pos_emotion = any(e["label"] in pos_emotions and e["score"] >= 0.15 for e in avg_emotions)
        has_neg_emotion = any(e["label"] in neg_emotions and e["score"] >= 0.15 for e in avg_emotions)

        if (overall_pos_score >= 0.20 and overall_neg_score >= 0.20) or (has_pos_emotion and has_neg_emotion):
            overall_sentiment = "mixed"
            overall_sentiment_conf = max(overall_pos_score, overall_neg_score)
            mixed_sentiment = True
        else:
            mixed_sentiment = False
            if overall_pos_score >= overall_neg_score and overall_pos_score >= overall_neutral_score:
                overall_sentiment = "positive"
                overall_sentiment_conf = overall_pos_score
            elif overall_neg_score >= overall_pos_score and overall_neg_score >= overall_neutral_score:
                overall_sentiment = "negative"
                overall_sentiment_conf = overall_neg_score
            else:
                overall_sentiment = "neutral"
                overall_sentiment_conf = overall_neutral_score

        t_end = time.perf_counter()
        inference_ms = round((t_end - t_start) * 1000, 2)

        # 5. Advanced NLP: Keywords, Readability, and Named Entities
        keywords = extract_keywords(text_trimmed)
        readability_score, complexity = calculate_readability_and_complexity(text_trimmed)
        entities = extract_named_entities(text_trimmed)

        # 6. Natural Language Explainable AI
        contradictory_emotions = detect_contradictory_emotions(avg_emotions)
        
        emotion_summary = generate_emotion_summary(
            sentiment=overall_sentiment,
            pos_score=overall_pos_score,
            neg_score=overall_neg_score,
            top_emotions=avg_emotions,
            contradictions=contradictory_emotions,
            text=text_trimmed,
            timeline=timeline
        )
        
        # Legacy insights fallback
        insights = generate_ai_summary(
            sentiment=overall_sentiment if overall_sentiment != "mixed" else "neutral",
            sentiment_confidence=overall_sentiment_conf,
            emotion=dominant_emotion,
            emotion_confidence=overall_emotion_conf,
            language_name=lang_info["name"],
            positive_word_count=len(keywords["positive_words"]),
            negative_word_count=len(keywords["negative_words"]),
            word_count=len(text_trimmed.split()),
        )
        
        # Overwrite explanation text with the new intelligent emotion summary
        insights["explanation"] = emotion_summary
        if overall_sarcasm_detected:
            s_reason = overall_sarcasm_reasons[0] if overall_sarcasm_reasons else "Sarcastic tone detected."
            insights["explanation"] = f"⚠️ Sarcasm Detected: {s_reason} {insights['explanation']}"
            
        insights["char_count"] = len(text_trimmed)

        # Get primary_emotion
        primary_emotion = {
            "label": dominant_emotion,
            "score": round(overall_emotion_conf, 4),
            "emoji": overall_emotion_emoji,
            "explanation": get_sub_emotion_explanation(dominant_emotion, text_trimmed)
        }

        # Get secondary_emotions (exceeding 20%, max 4)
        secondary_emotions = []
        for e in avg_emotions:
            if e["label"] != dominant_emotion and e["score"] >= 0.20:
                secondary_emotions.append({
                    "label": e["label"],
                    "score": round(e["score"], 4),
                    "emoji": EMOJI_MAP.get(e["label"], "😐"),
                    "explanation": get_sub_emotion_explanation(e["label"], text_trimmed)
                })
                if len(secondary_emotions) == 4:
                    break

        # Get emotion_explanations mapping
        emotion_explanations = {
            dominant_emotion: primary_emotion["explanation"]
        }
        for se in secondary_emotions:
            emotion_explanations[se["label"]] = se["explanation"]

        # Get emotion ranking filtering for >= 0.20 (and always including primary)
        ranking_items = [{"label": dominant_emotion, "score": round(overall_emotion_conf, 4)}]
        for e in avg_emotions:
            if e["label"] != dominant_emotion and e["score"] >= 0.20:
                ranking_items.append({"label": e["label"], "score": round(e["score"], 4)})
                if len(ranking_items) == 5:
                    break
        emotion_ranking = ranking_items

        result = {
            "sentiment": overall_sentiment,
            "sentiment_confidence": round(overall_sentiment_conf, 4),
            "sentiment_distribution": [
                {"label": "positive", "score": overall_pos_score},
                {"label": "neutral", "score": overall_neutral_score},
                {"label": "negative", "score": overall_neg_score},
            ],
            
            "emotion": overall_emotion,
            "emotion_confidence": round(overall_emotion_conf, 4),
            "emotion_emoji": overall_emotion_emoji,
            "emotion_distribution": avg_emotions,
            
            "language": lang_info,
            "language_confidence": round(lang_confidence, 4),
            
            "sarcasm": {
                "detected": overall_sarcasm_detected,
                "confidence": round(overall_sarcasm_confidence, 4),
                "reason": "; ".join(overall_sarcasm_reasons) if overall_sarcasm_detected else "No Sarcasm Detected"
            },
            
            "readability": {
                "score": readability_score,
                "complexity": complexity
            },
            
            "entities": entities,
            "sentences": processed_sentences,
            "timeline": timeline,
            
            "keywords": keywords,
            "insights": insights,
            "inference_time_ms": inference_ms,
            "word_count": len(text_trimmed.split()),
            "char_count": len(text_trimmed),
            "cache_hit": False,
            
            # --- New response fields for intelligence upgrade ---
            "emotion_ranking": emotion_ranking,
            "mixed_sentiment": mixed_sentiment,
            "positive_score": overall_pos_score,
            "negative_score": overall_neg_score,
            "neutral_score": overall_neutral_score,
            "contradictory_emotions": contradictory_emotions,
            "emotion_summary": emotion_summary,
            "emotion_confidences": {e["label"]: e["score"] for e in avg_emotions},
            "top_emotions": [e["label"] for e in emotion_ranking],
            
            # --- Additional presentation upgrade response fields ---
            "primary_emotion": primary_emotion,
            "secondary_emotions": secondary_emotions,
            "emotion_explanations": emotion_explanations
        }

        self._cache.put(cache_key, result)
        return result

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "sentiment": "neutral",
            "sentiment_confidence": 1.0,
            "sentiment_distribution": [{"label": "neutral", "score": 1.0}, {"label": "positive", "score": 0.0}, {"label": "negative", "score": 0.0}],
            "emotion": "neutral",
            "emotion_confidence": 1.0,
            "emotion_emoji": "😐",
            "emotion_distribution": [{"label": "neutral", "score": 1.0}],
            "language": get_language_info("en"),
            "language_confidence": 1.0,
            "sarcasm": {"detected": False, "confidence": 0.0, "reason": "No Sarcasm Detected"},
            "readability": {"score": 100.0, "complexity": "Very Easy"},
            "entities": {"PERSON": [], "GPE": [], "ORG": [], "DATE": []},
            "sentences": [],
            "timeline": [],
            "keywords": {"top_keywords": [], "positive_words": [], "negative_words": [], "word_cloud": [], "word_frequencies": []},
            "insights": {
                "overall_sentiment_score": 0.0,
                "dominant_emotion": "neutral",
                "dominant_emotion_emoji": "😐",
                "emotional_intensity": "Low",
                "explanation": "No text provided to analyze.",
                "word_count": 0,
                "char_count": 0,
                "reading_time_seconds": 1
            },
            "inference_time_ms": 0.0,
            "word_count": 0,
            "char_count": 0,
            "cache_hit": False,
            
            # --- Default new fields ---
            "emotion_ranking": [],
            "mixed_sentiment": False,
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "contradictory_emotions": [],
            "emotion_summary": "No text provided to analyze.",
            "emotion_confidences": {},
            "top_emotions": [],
            
            # --- Default empty presentation fields ---
            "primary_emotion": None,
            "secondary_emotions": [],
            "emotion_explanations": {}
        }

    # ------------------------------------------------------------------
    # Pipeline runners (safe wrappers)
    # ------------------------------------------------------------------

    def _run_sentiment_batch(self, texts: List[str]) -> List[List[Dict]]:
        if not self._sentiment_pipe:
            return [[
                {"label": "neutral", "score": 0.34},
                {"label": "positive", "score": 0.33},
                {"label": "negative", "score": 0.33},
            ] for _ in texts]
        try:
            return self._sentiment_pipe(texts)
        except Exception as exc:
            logger.error("Sentiment batch inference error: %s", exc)
            return [[{"label": "neutral", "score": 1.0}] for _ in texts]

    def _run_emotion_batch(self, texts: List[str]) -> List[List[Dict]]:
        if not self._emotion_pipe:
            return [[{"label": "neutral", "score": 1.0}] for _ in texts]
        try:
            return self._emotion_pipe(texts)
        except Exception as exc:
            logger.error("Emotion batch inference error: %s", exc)
            return [[{"label": "neutral", "score": 1.0}] for _ in texts]

    def _run_language(self, text: str) -> List[Dict]:
        if not self._language_pipe:
            return [{"label": "en", "score": 1.0}]
        try:
            return self._language_pipe(text)[0]
        except Exception as exc:
            logger.error("Language inference error: %s", exc)
            return [{"label": "en", "score": 1.0}]

    def _detect_script_language(self, text: str) -> Optional[str]:
        """Detect Indian languages by their Unicode script ranges."""
        for char in text:
            val = ord(char)
            if 0x0C80 <= val <= 0x0CFF:
                return "kn"  # Kannada
            elif 0x0C00 <= val <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0B80 <= val <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0D00 <= val <= 0x0D7F:
                return "ml"  # Malayalam
            elif 0x0980 <= val <= 0x09FF:
                return "bn"  # Bengali
            elif 0x0A80 <= val <= 0x0AFF:
                return "gu"  # Gujarati
            elif 0x0A00 <= val <= 0x0A7F:
                return "pa"  # Punjabi
            elif 0x0900 <= val <= 0x097F:
                return "hi"  # Hindi (Devanagari script)
        return None

    def _translate_and_detect(self, text: str) -> Tuple[str, str, float]:
        """
        Translate text to English and detect its language using Google Translate.
        Returns: (translated_text, language_code, confidence)
        """
        try:
            import urllib.parse
            import urllib.request
            import json

            truncated = text[:1000].strip()
            if not truncated:
                return "", "en", 1.0

            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=" + urllib.parse.quote(truncated)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
                translated_sentences = [sentence[0] for sentence in data[0] if sentence and sentence[0]]
                translated_text = "".join(translated_sentences)
                
                detected_lang = "en"
                if len(data) > 2 and isinstance(data[2], str):
                    detected_lang = data[2]
                
                # Normalize language codes from Google Translate
                lang_mapping = {"iw": "he", "zh-CN": "zh", "zh-TW": "zh"}
                detected_lang = lang_mapping.get(detected_lang, detected_lang)

                return translated_text, detected_lang, 0.95
        except Exception as e:
            logger.warning("Google Translate API call failed, falling back to script/local detection: %s", e)
            return text, "en", 0.0

    # ------------------------------------------------------------------
    # Label normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_sentiment_label(label: str) -> str:
        """Map model-specific labels to standard positive/negative/neutral."""
        label_lower = label.lower().strip()
        mapping = {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral",
            "label_0": "negative",   # XLM-RoBERTa mapping
            "label_1": "neutral",
            "label_2": "positive",
        }
        return mapping.get(label_lower, label_lower)


# Global singleton
analyzer = AnalysisEngine()

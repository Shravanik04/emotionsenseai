"""
Keyword extraction utilities for sentiment analysis.
Extracts top keywords, positive/negative words, noun chunks, and contextual phrases.
"""
import re
from collections import Counter
from typing import Dict, List, Set

# Comprehensive stopwords list (English + Hindi + Kannada common words)
STOPWORDS = {
    # English
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re",
    "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven",
    "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren",
    "won", "wouldn", "also", "would", "could", "may", "might", "shall", "must",
    "yet", "still", "already", "much", "many", "well", "really", "quite", "even",
    "got", "get", "go", "going", "went", "come", "came", "let", "like",
    # Hindi common stopwords
    "का", "के", "की", "में", "है", "हैं", "को", "से", "पर", "ने", "और", "एक",
    "यह", "वह", "इस", "उस", "जो", "तो", "कि", "पर", "नहीं", "हो", "था", "थे",
    "थी", "कर", "या", "भी", "अपने", "मैं", "हम", "तुम", "आप", "वे", "कोई",
    # Kannada common stopwords
    "ಮತ್ತು", "ಈ", "ಆ", "ಒಂದು", "ಅದು", "ಇದು", "ಅವರು", "ಅವಳು", "ನಾನು", "ನೀವು",
    "ಅಲ್ಲ", "ಇಲ್ಲ", "ಆಗಿದೆ", "ಆಗಿ", "ಹಾಗೂ", "ಅಥವಾ",
}

# Positive sentiment words
POSITIVE_WORDS = {
    "love", "great", "awesome", "amazing", "wonderful", "excellent", "fantastic",
    "beautiful", "happy", "joy", "good", "best", "perfect", "brilliant", "superb",
    "incredible", "outstanding", "delightful", "pleasant", "magnificent", "terrific",
    "fabulous", "marvelous", "splendid", "glorious", "thrilled", "excited",
    "grateful", "thankful", "blessed", "kind", "caring", "warm", "gentle",
    "generous", "helpful", "friendly", "cheerful", "positive", "optimistic",
    "inspiring", "remarkable", "stunning", "lovely", "enjoy", "enjoyed",
    "nice", "cool", "fun", "impressive", "recommend", "recommended",
    "adore", "cherish", "treasure", "appreciate", "admire", "respect",
    "validation", "resilience", "resilient", "encouraged", "encouragement",
    "motivated", "motivation",
}

# Negative sentiment words
NEGATIVE_WORDS = {
    "hate", "terrible", "horrible", "awful", "bad", "worst", "poor", "ugly",
    "angry", "sad", "fear", "disgusting", "disappointing", "dreadful", "miserable",
    "pathetic", "annoying", "frustrating", "boring", "useless", "waste", "broken",
    "failed", "failure", "disaster", "nightmare", "toxic", "painful", "suffering",
    "cruel", "nasty", "rude", "offensive", "disgusted", "horrified", "furious",
    "outraged", "devastated", "heartbroken", "depressed", "anxious", "worried",
    "scared", "frightened", "terrified", "hopeless", "desperate", "regret",
    "disappointed", "unhappy", "upset", "irritated", "annoyed", "bitter",
    "resentful", "hostile", "aggressive", "violent", "hurt", "harm",
}


def tokenize(text: str) -> List[str]:
    """Simple tokenizer that splits on non-alphanumeric + unicode characters."""
    tokens = re.findall(r'[\w\u0900-\u097F\u0C80-\u0CFF]+', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def extract_phrases(text: str) -> List[str]:
    """Extract multi-word noun chunks and verb phrases from text."""
    sentences = re.split(r'[.!?]+', text.lower())
    phrases = []
    
    for sent in sentences:
        words = re.findall(r'[\w\u0900-\u097F\u0C80-\u0CFF]+', sent)
        if not words:
            continue
        
        # 1. Consecutive non-stopwords (noun chunks, e.g. "dream job", "flat tire")
        current_chunk = []
        for w in words:
            if w not in STOPWORDS and len(w) > 1:
                current_chunk.append(w)
            else:
                if len(current_chunk) > 1:
                    phrases.append(" ".join(current_chunk))
                current_chunk = []
        if len(current_chunk) > 1:
            phrases.append(" ".join(current_chunk))
            
        # 2. Verb phrases (verb + preposition/gerund, e.g. "working with", "love working", "waking up")
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            if w1 in {"love", "like", "hate", "dislike", "enjoy", "stop", "start", "keep", "work", "working", "wake", "waking", "wait", "waiting", "fail", "failed", "pass", "passed"} and w2 not in {"the", "a", "an", "this", "that"}:
                phrases.append(f"{w1} {w2}")
                if i < len(words) - 2:
                    w3 = words[i+2]
                    if w3 not in STOPWORDS and len(w3) > 1:
                        phrases.append(f"{w1} {w2} {w3}")
                        
    return list(set(phrases))


def extract_keywords(text: str, top_n: int = 15) -> Dict:
    """
    Extract single-word keywords, multi-word phrases/noun-chunks,
    positive/negative words, and frequencies.
    """
    tokens = tokenize(text)
    phrases = extract_phrases(text)
    
    # Combined list for general keyword extraction
    all_elements = tokens + phrases
    freq = Counter(all_elements)
    
    # Top keywords by frequency
    top_keywords = [{"word": w, "count": c} for w, c in freq.most_common(top_n)]
    
    # Filter positive and negative words found in text
    found_positive = [
        {"word": w, "count": freq[w]}
        for w in sorted(set(tokens) & POSITIVE_WORDS, key=lambda x: -freq[x])
    ]
    found_negative = [
        {"word": w, "count": freq[w]}
        for w in sorted(set(tokens) & NEGATIVE_WORDS, key=lambda x: -freq[x])
    ]
    
    # Word cloud data (prioritize multi-word phrases if present)
    word_cloud_candidates = phrases + [t for t in tokens if not any(t in p for p in phrases)]
    cloud_freq = Counter(word_cloud_candidates)
    word_cloud = [{"text": w, "value": c} for w, c in cloud_freq.most_common(50)]
    
    # Word frequencies (all)
    word_frequencies = [{"word": w, "count": c} for w, c in freq.most_common(30)]
    
    return {
        "top_keywords": top_keywords,
        "positive_words": found_positive,
        "negative_words": found_negative,
        "word_cloud": word_cloud,
        "word_frequencies": word_frequencies,
    }

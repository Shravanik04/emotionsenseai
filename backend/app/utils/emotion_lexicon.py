"""
Lexicon and utility mappings for 39 detailed emotions, emoji mapping,
and scoring logic to refine standard base emotions.
"""
import re
from typing import Dict, List, Set, Tuple, Any

# Full sub-emotion list grouped by category
SUB_EMOTIONS = {
    "positive": [
        "joy", "happiness", "excitement", "love", "gratitude", "pride",
        "hope", "optimism", "relief", "confidence", "admiration",
        "inspiration", "curiosity", "trust", "satisfaction", "validation",
        "belonging", "collaboration"
    ],
    "negative": [
        "sadness", "anger", "fear", "anxiety", "stress", "frustration",
        "disappointment", "loneliness", "confusion", "disgust",
        "jealousy", "regret", "guilt", "embarrassment", "fatigue",
        "discomfort"
    ],
    "neutral": [
        "calm", "neutral", "thoughtful", "analytical"
    ],
    "complex": [
        "surprise", "nostalgia", "determination", "sympathy",
        "compassion", "awe", "anticipation", "skepticism",
        "overwhelmed", "shock", "resilience"
    ]
}

# Emoji mapping for all sub-emotions
EMOJI_MAP = {
    # Positive
    "joy": "😊",
    "happiness": "😀",
    "excitement": "🎉",
    "love": "❤️",
    "gratitude": "🙏",
    "pride": "🦁",
    "hope": "🌅",
    "optimism": "☀️",
    "relief": "😌",
    "confidence": "😎",
    "admiration": "👏",
    "inspiration": "💡",
    "curiosity": "🤔",
    "trust": "🤝",
    "satisfaction": "👍",
    "validation": "🛡️",
    "belonging": "🤝",
    "collaboration": "👥",
    # Negative
    "sadness": "😔",
    "anger": "😤",
    "fear": "😨",
    "anxiety": "😟",
    "stress": "😫",
    "frustration": "😒",
    "disappointment": "😞",
    "loneliness": "🏚️",
    "confusion": "🤷",
    "disgust": "🤢",
    "jealousy": "💚",
    "regret": "🤦",
    "guilt": "🥺",
    "embarrassment": "😳",
    "fatigue": "🥱",
    "discomfort": "😣",
    # Neutral
    "calm": "🧘",
    "neutral": "😐",
    "thoughtful": "💭",
    "analytical": "📊",
    # Complex
    "surprise": "😲",
    "nostalgia": "⏳",
    "determination": "✊",
    "sympathy": "💖",
    "compassion": "🤲",
    "awe": "🌌",
    "anticipation": "⏳",
    "skepticism": "🤨",
    "overwhelmed": "🤯",
    "shock": "💥",
    "resilience": "🦾"
}

# Parent base emotion mapping (to link HF base model outputs to sub-emotions)
PARENT_MAP = {
    # Joy parent
    "joy": "joy",
    "happiness": "joy",
    "excitement": "joy",
    "love": "joy",
    "gratitude": "joy",
    "pride": "joy",
    "hope": "joy",
    "optimism": "joy",
    "relief": "joy",
    "confidence": "joy",
    "admiration": "joy",
    "inspiration": "joy",
    "trust": "joy",
    "satisfaction": "joy",
    "validation": "joy",
    "belonging": "joy",
    "collaboration": "joy",
    # Sadness parent
    "sadness": "sadness",
    "disappointment": "sadness",
    "loneliness": "sadness",
    "regret": "sadness",
    "guilt": "sadness",
    "embarrassment": "sadness",
    "fatigue": "sadness",
    # Anger parent
    "anger": "anger",
    "frustration": "anger",
    "jealousy": "anger",
    "discomfort": "anger",
    # Fear parent
    "fear": "fear",
    "anxiety": "fear",
    "stress": "fear",
    "overwhelmed": "fear",
    # Surprise parent
    "surprise": "surprise",
    "awe": "surprise",
    "shock": "surprise",
    # Disgust parent
    "disgust": "disgust",
    "skepticism": "disgust",
    # Neutral parent
    "neutral": "neutral",
    "calm": "neutral",
    "thoughtful": "neutral",
    "analytical": "neutral",
    "curiosity": "neutral",
    # Complex mappings mapped to closest standard base
    "nostalgia": "sadness",
    "determination": "joy",
    "sympathy": "joy",
    "compassion": "joy",
    "anticipation": "neutral",
    "confusion": "neutral",
    "resilience": "joy"
}

# Lexicons for matching sub-emotions
LEXICONS: Dict[str, Set[str]] = {
    "happiness": {"happy", "happier", "cheerful", "glad", "delighted", "pleased", "content", "joyful", "smile", "yippee", "yippiee"},
    "excitement": {"excited", "exciting", "thrilled", "eager", "awesome", "amazing", "yes", "yay", "yayy", "hurray", "hurrayy", "hooray", "hoorayy", "hurrah", "celebrate", "win", "won", "party"},
    "love": {"love", "loved", "loving", "adore", "adored", "affection", "dear", "darling", "sweetheart", "beloved", "heart", "kiss", "hug", "xoxo"},
    "gratitude": {"thank", "thanks", "thankful", "grateful", "appreciate", "appreciated", "appreciation", "bless", "blessed", "obliged"},
    "pride": {"proud", "pride", "accomplished", "achieve", "achieved", "achievement", "victory", "success", "successful", "win", "glory"},
    "hope": {"hope", "hoping", "hopeful", "wish", "wishing", "pray", "praying", "dream", "dreaming", "optimistic", "future"},
    "optimism": {"optimistic", "positive", "bright", "sunny", "future", "looking up", "looking forward", "better", "best"},
    "relief": {"relief", "relieved", "phew", "thank goodness", "safe", "calmed", "heave", "soothe", "rested", "resolved"},
    "confidence": {"confident", "certain", "sure", "succeed", "succeeding", "can do", "strong", "capable", "power", "achieve"},
    "admiration": {"admire", "admiration", "respect", "respected", "great job", "bravo", "genius", "wonderful", "amazing", "incredible", "kudos"},
    "inspiration": {"inspired", "inspiring", "motivation", "motivated", "creative", "vision", "spark", "enlightened", "driven"},
    "curiosity": {"wonder", "wondering", "curious", "curiosity", "why", "how", "what if", "explore", "exploring", "ask", "asking"},
    "trust": {"trust", "trusty", "believe", "believed", "honest", "reliable", "loyal", "faith", "faithful", "depend", "partnership"},
    "satisfaction": {"satisfied", "satisfaction", "pleased", "content", "glad", "fulfilled", "gratified", "perfect", "good enough"},
    "validation": {"validation", "validate", "validated", "appreciate", "appreciated", "appreciation", "recognized", "recognised", "acknowledge", "acknowledged", "support", "supported"},
    "belonging": {"belonging", "belong", "teamwork", "team", "colleague", "colleagues", "peers", "friends", "workplace", "partner", "together"},
    "collaboration": {"collaboration", "collaborate", "collaborated", "cooperation", "cooperate", "partner", "partnership", "work with", "working with", "team"},
    
    "anxiety": {"anxious", "anxiety", "nervous", "worry", "worried", "worrying", "uneasy", "panic", "tense", "dread", "apprehensive"},
    "stress": {"stressed", "stressful", "pressure", "tired", "exhausted", "burnout", "heavy", "drain", "drained", "overworked"},
    "frustration": {"frustrated", "frustrating", "frustration", "annoyed", "annoying", "bothered", "irritated", "irritating", "stuck", "fed up", "ugh"},
    "disappointment": {"disappointed", "disappointment", "let down", "pity", "shame", "sadly", "unfortunate", "ruined", "spoiled"},
    "loneliness": {"lonely", "alone", "isolated", "deserted", "abandoned", "hollow", "empty", "solitude", "no one", "single"},
    "confusion": {"confused", "confusing", "puzzled", "lost", "dilemma", "clueless", "unsure", "perplexed", "doubt", "mixed up"},
    "jealousy": {"jealous", "jealousy", "envy", "envious", "covet", "possessive", "resentful"},
    "regret": {"regret", "regretted", "wish i had", "should have", "sorry", "apologize", "repent"},
    "guilt": {"guilty", "guilt", "shame", "blame", "fault", "responsible for", "wronged"},
    "embarrassment": {"embarrassed", "embarrassing", "embarrassment", "awkward", "ashamed", "blush", "foolish", "stupid"},
    "fatigue": {"fatigue", "tired", "exhausted", "sleepy", "waking up", "wake up", "morning", "early", "burnout", "drained"},
    "discomfort": {"discomfort", "uncomfortable", "dislike", "hate", "annoyed", "bothered", "irritated", "waking up", "wake up", "early"},
    
    "calm": {"calm", "calming", "peace", "peaceful", "serene", "quiet", "relax", "relaxed", "meditate", "gentle", "still"},
    "thoughtful": {"thoughtful", "pensive", "reflect", "reflecting", "contemplate", "mindful", "ponder", "pondering", "deep"},
    "analytical": {"analytical", "analyze", "analyzing", "logic", "logical", "reason", "fact", "facts", "data", "metric", "metrics", "observe"},
    
    "nostalgia": {"nostalgic", "nostalgia", "remember", "remembering", "back then", "old days", "childhood", "memories", "past", "history"},
    "determination": {"determined", "determination", "grit", "persist", "persistent", "will not give up", "fight", "try again", "focus", "resolve"},
    "sympathy": {"sympathy", "sympathetic", "sorry for you", "comfort", "condolences", "heart goes out", "feel for you"},
    "compassion": {"compassion", "compassionate", "kindness", "care", "caring", "helping", "support", "empathy", "warmth"},
    "awe": {"awe", "awesome", "breathtaking", "magnificent", "stunning", "spectacular", "magical", "wondrous"},
    "anticipation": {"anticipation", "wait", "waiting", "soon", "looking forward", "excited for", "upcoming", "next"},
    "skepticism": {"skeptical", "skepticism", "doubt", "doubtful", "suspicious", "cynical", "unbelievable", "really?", "yeah right", "surely not"},
    "overwhelmed": {"overwhelmed", "overwhelming", "too much", "swamped", "flooded", "drowning", "cannot cope", "heavy"},
    "shock": {"shocked", "shocking", "speechless", "stunned", "paralyzed", "unbelievable", "wtf", "omg", "sudden", "unexpected"},
    "resilience": {"resilience", "resilient", "bounce back", "strong", "encourage", "encouraged", "persist", "persistent", "cope", "coping", "adapt", "adapting", "survive", "survived", "overcome"}
}

# Mapping explanations template based on sub-emotions
EXPLANATION_TEMPLATES = {
    "happiness": "The text contains expressions of joy, happiness, or cheerfulness.",
    "excitement": "The language reflects high energy, celebration, or anticipation of a positive event.",
    "love": "The text communicates deep affection, love, or emotional attachment.",
    "gratitude": "The writer is expressing thankfulness, appreciation, or counting blessings.",
    "pride": "The language indicates achievement, satisfaction in success, or self-respect.",
    "hope": "The text shows optimism, wishing for positive outcomes, or future desires.",
    "optimism": "The wording carries a positive outlook and expects things to turn out well.",
    "relief": "The text indicates that a stressor has passed or a problem has been resolved.",
    "confidence": "The language is self-assured, certain, and shows capability or strength.",
    "admiration": "The writer is expressing high respect or praise for someone or something.",
    "inspiration": "The text expresses motivation, creativity, or enlightenment.",
    "curiosity": "The text poses questions or expresses interest in exploring and learning.",
    "trust": "The text conveys belief in honesty, reliability, or loyalty.",
    "satisfaction": "The text expresses contentment, fulfillment, or fulfillment of expectations.",
    "validation": "The language indicates feeling valued, appreciated, or recognized by others.",
    "belonging": "Detected because the author values connection, teamwork, or belonging.",
    "collaboration": "Detected because the author values cooperative efforts and collaboration.",
    
    "sadness": "The wording reflects sorrow, disappointment, or feeling down.",
    "anger": "The language contains irritation, frustration, or outright anger.",
    "fear": "The text expresses fear, worry, or threat.",
    "anxiety": "The text shows nervousness, uneasiness, or apprehension.",
    "stress": "The writer feels under pressure, tired, or mentally exhausted.",
    "frustration": "The text contains words expressing repeated failure, irritation, or feeling blocked.",
    "disappointment": "The wording reflects letdown or failure of expectations.",
    "loneliness": "The text conveys feeling isolated, alone, or lacking companionship.",
    "confusion": "The language shows lack of clarity, doubt, or mixed understanding.",
    "disgust": "The text expresses strong disapproval, revulsion, or disgust.",
    "jealousy": "The wording indicates resentment of someone else's success or advantages.",
    "regret": "The text contains expressions of wishing things were done differently or feeling sorry.",
    "guilt": "The writer feels self-blame, shame, or responsible for a mistake.",
    "embarrassment": "The wording conveys feeling awkward, foolish, or self-conscious.",
    "fatigue": "Detected because the author expresses tiredness, lack of energy, or fatigue.",
    "discomfort": "Detected because the author expresses minor annoyance or physical/mental discomfort.",
    
    "calm": "The language is peaceful, relaxed, and free of stress or strong negative emotions.",
    "neutral": "The text is factual, objective, and does not contain strong emotional indicators.",
    "thoughtful": "The text reflects contemplation, reflection, or deep mindfulness.",
    "analytical": "The language is logical, objective, and relies on fact-based reasoning.",
    
    "surprise": "The wording shows astonishment or an unexpected event.",
    "nostalgia": "The text evokes memories of the past or longing for childhood/old days.",
    "determination": "The language shows resolve, grit, and refusal to give up.",
    "sympathy": "The text expresses condolences, sorrow, or comfort for another person's plight.",
    "compassion": "The text displays kindness, empathy, and a desire to help others.",
    "awe": "The language reflects wonder, breathtaking beauty, or cosmic scale.",
    "anticipation": "The text shows looking forward to or waiting for an upcoming event.",
    "skepticism": "The writer displays doubt, suspicion, or cynicism.",
    "overwhelmed": "The text expresses feeling swamped by too many emotions or tasks.",
    "shock": "The text indicates a sudden, shocking event that leaves the writer stunned.",
    "resilience": "The text shows strength, recovery, or capacity to bounce back from adversity."
}

# Intensity modifiers that boost matching emotion confidences
INTENSITY_MODIFIERS = {"very", "really", "extremely", "absolutely", "deeply", "totally", "completely", "incredibly"}

# Negation maps to reverse or shift emotions
NEGATED_OPPOSITES = {
    "joy": "sadness",
    "happiness": "sadness",
    "excitement": "disappointment",
    "love": "frustration",
    "gratitude": "frustration",
    "pride": "disappointment",
    "hope": "disappointment",
    "optimism": "disappointment",
    "relief": "anxiety",
    "confidence": "anxiety",
    "admiration": "skepticism",
    "inspiration": "disappointment",
    "trust": "skepticism",
    "satisfaction": "frustration",
    "validation": "frustration",
    "resilience": "stress",
    
    # opposite direction (negating a negative)
    "sadness": "relief",
    "anger": "calm",
    "fear": "confidence",
    "anxiety": "calm",
    "stress": "calm",
    "frustration": "calm",
    "disappointment": "satisfaction",
}

# Contextual keyword explanation lookups
CONTEXTUAL_KEYWORD_EXPLANATIONS = {
    "promotion": "The mention of 'promotion' indicates a potential career setback or expectation, aligning with disappointment.",
    "appreciated": "The word 'appreciated' highlights validation, leading to feelings of gratitude.",
    "encouraged": "The word 'encouraged' indicates hope and motivation.",
    "motivated": "The word 'motivated' reflects strong determination.",
    "love": "The use of the word 'love' highlights deep affection or positive attachment.",
    "hate": "The word 'hate' indicates strong aversion or frustration.",
    "nervous": "The word 'nervous' indicates anxiety or anticipation.",
    "excited": "The word 'excited' shows high energy and excitement.",
}

# Specific contradictory pairs to detect
CONTRADICTORY_PAIRS = [
    ({"hope", "optimism"}, {"fear", "anxiety"}),
    ({"love"}, {"frustration", "anger"}),
    ({"joy", "happiness", "excitement"}, {"sadness", "disappointment", "regret"}),
    ({"confidence"}, {"anxiety", "stress"}),
]

def refine_emotions(base_predictions: List[Dict[str, float]], text: str) -> List[Dict[str, Any]]:
    """
    Combine Neural Net base emotion probabilities with Lexicon keyword matches
    to score and rank all 43 sub-emotions, handling negations, intensity words, and contextual boosts.
    """
    base_map = {p["label"].lower().strip(): p["score"] for p in base_predictions}
    words = re.findall(r'\w+', text.lower())
    words_set = set(words)
    
    negation_words = {"not", "never", "no", "dont", "don't", "didnt", "didn't", "wont", "won't", "cant", "can't", "wasnt", "wasn't", "werent", "weren't", "shouldnt", "shouldn't", "couldnt", "couldn't", "wouldnt", "wouldn't", "havent", "haven't", "hasnt", "hasn't"}
    
    normal_matches = {emo: 0 for emo in PARENT_MAP}
    negated_matches = {emo: 0 for emo in PARENT_MAP}
    
    for emo, keywords in LEXICONS.items():
        for idx, w in enumerate(words):
            if w in keywords:
                # Check for negation in preceding 2 tokens
                is_negated = False
                for look in range(max(0, idx - 2), idx):
                    if words[look] in negation_words:
                        is_negated = True
                        break
                if is_negated:
                    negated_matches[emo] += 1
                else:
                    normal_matches[emo] += 1
                    
    # Calculate raw weights for all sub-emotions
    raw_weights = {}
    for emotion in PARENT_MAP:
        opp_boost = sum(negated_matches[opp] for opp, target in NEGATED_OPPOSITES.items() if target == emotion)
        self_negation = negated_matches[emotion]
        effective_matches = max(0, normal_matches[emotion] - self_negation) + opp_boost
        
        # Check for intensity modifiers
        intensity_boost = 1.0
        parent = PARENT_MAP[emotion]
        if effective_matches > 0 or emotion == parent:
            for mod in INTENSITY_MODIFIERS:
                if mod in words_set:
                    intensity_boost += 0.35 # boost by 35% per modifier
                    
        default_boost = 1.1 if emotion == parent else 1.0
        raw_weights[emotion] = default_boost * (1.0 + effective_matches * 2.5) * intensity_boost

    # Contextual Emotion Enrichment
    # "I absolutely love working with my team." -> Primary: Love, Additional: Belonging, Collaboration, Motivation
    if "love" in words_set and ("team" in words_set or "work" in words_set or "working" in words_set):
        raw_weights["belonging"] = raw_weights.get("belonging", 1.0) * 4.0
        raw_weights["collaboration"] = raw_weights.get("collaboration", 1.0) * 4.0
        raw_weights["determination"] = raw_weights.get("determination", 1.0) * 3.5
        
    # "I hate waking up early." -> Primary: Frustration, Additional: Fatigue, Discomfort, Stress
    if "hate" in words_set and ("wake" in words_set or "early" in words_set or "waking" in words_set):
        raw_weights["fatigue"] = raw_weights.get("fatigue", 1.0) * 4.0
        raw_weights["discomfort"] = raw_weights.get("discomfort", 1.0) * 4.0
        raw_weights["stress"] = raw_weights.get("stress", 1.0) * 3.5

    # Group sub-emotions by parent category
    parent_groups = {}
    for emotion, parent in PARENT_MAP.items():
        parent_groups.setdefault(parent, []).append(emotion)
        
    scores = []
    
    # For each parent category, allocate the parent's probability based on normalized weights
    for parent, sub_list in parent_groups.items():
        parent_prob = base_map.get(parent, 0.0)
        
        # Normalize weights within this parent category
        total_w = sum(raw_weights[emotion] for emotion in sub_list)
        for emotion in sub_list:
            share = raw_weights[emotion] / total_w if total_w > 0 else (1.0 / len(sub_list))
            score = parent_prob * share
            
            category = "neutral"
            for cat, emotions in SUB_EMOTIONS.items():
                if emotion in emotions:
                    category = cat
                    break
                    
            scores.append({
                "label": emotion,
                "score": round(score, 4),
                "category": category
            })
            
    scores.sort(key=lambda x: -x["score"])
    return scores

def get_sub_emotion_explanation(emotion: str, text: str) -> str:
    """Get a natural language reason for the emotion classification."""
    base_reason = EXPLANATION_TEMPLATES.get(emotion, f"The text contains emotional cues pointing to {emotion}.")
    words = set(re.findall(r'\w+', text.lower()))
    
    # Check for specific contextual explanations
    context_reasons = []
    for kw, expl in CONTEXTUAL_KEYWORD_EXPLANATIONS.items():
        if kw in words:
            # check if this keyword is related to this emotion or its parent group
            if kw in LEXICONS.get(emotion, set()) or emotion in ["disappointment", "gratitude", "hope", "determination", "validation", "resilience"]:
                context_reasons.append(expl)
                
    if context_reasons:
        return f"{base_reason} Specifically, " + " ".join(context_reasons)
        
    lexicon = LEXICONS.get(emotion, set())
    matches = sorted(list(words & lexicon))
    if matches:
        keywords_str = ", ".join(f"'{m}'" for m in matches[:3])
        return f"{base_reason} Specific emotional keywords found: {keywords_str}."
    return base_reason

def detect_contradictory_emotions(top_emotions: List[Dict[str, Any]]) -> List[str]:
    """
    Check if conflicting emotions exist in the top emotions with meaningful scores.
    """
    # top_emotions represents the calibrated emotions list
    # Filter to emotions with score >= 0.15 (meaningful emotions)
    meaningful = [e for e in top_emotions if e["score"] >= 0.15]
    labels = {e["label"] for e in meaningful}
    
    # Check for specific contradictory pairs first
    for set1, set2 in CONTRADICTORY_PAIRS:
        match1 = labels & set1
        match2 = labels & set2
        if match1 and match2:
            return [list(match1)[0], list(match2)[0]]
            
    # Fallback to any positive and negative clash above 0.20
    pos_emotions = set(SUB_EMOTIONS["positive"])
    neg_emotions = set(SUB_EMOTIONS["negative"])
    
    pos_top = [e["label"] for e in meaningful if e["label"] in pos_emotions and e["score"] >= 0.20]
    neg_top = [e["label"] for e in meaningful if e["label"] in neg_emotions and e["score"] >= 0.20]
    
    if pos_top and neg_top:
        return [pos_top[0], neg_top[0]]
    return []

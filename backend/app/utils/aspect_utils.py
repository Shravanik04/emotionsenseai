import string

# Stopwords for keyword extraction
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't",
    'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
    "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    'like', 'good', 'great', 'awesome', 'amazing', 'poor', 'bad', 'worst', 'excellent', 'would', 'could',
    'get', 'go', 'one', 'two', 'think', 'really', 'also', 'even'
}

def detect_aspect_and_sentiment(text: str) -> str:
    """
    Extracts the main aspect from a single comment text.
    Uses heuristic rules to classify aspects and falls back to extracting noun phrases.
    """
    text_lower = text.lower()
    
    rules = [
        (["tutorial", "course", "lesson", "video", "instructor", "teacher", "learn", "learning"], "Tutorial Quality"),
        (["explanation", "explaining", "explained", "clarity", "clear", "confusing", "confused", "understand"], "Explanation Clarity"),
        (["editing", "cuts", "transitions", "effects", "audio", "sound", "visual", "graphics"], "Editing Quality"),
        (["update", "version", "patch", "software", "app", "feature", "upgrade"], "Software Update"),
        (["ui", "ux", "interface", "design", "layout", "look", "aesthetic"], "User Interface"),
        (["support", "help", "customer service", "agent", "service", "reply"], "Customer Support"),
        (["speed", "performance", "slow", "fast", "lag", "fps", "loading"], "Performance"),
        (["price", "cost", "expensive", "cheap", "subscription", "money", "value"], "Pricing"),
        (["battery", "charge", "power", "drain"], "Battery Life"),
        (["camera", "lens", "photo", "video quality", "recording"], "Camera Quality"),
        (["bug", "crash", "error", "broken", "freeze", "buggy"], "Stability"),
    ]
    
    for keywords, aspect in rules:
        if any(kw in text_lower for kw in keywords):
            return aspect
            
    # Fallback noun phrase extractor
    exclusions = {
        "this", "that", "these", "those", "have", "has", "had", "would", "could", "should", "will", "would",
        "was", "were", "been", "being", "good", "great", "excellent", "worst", "better", "best", "terrible",
        "saved", "hours", "ever", "really", "very", "just", "also", "even", "thing", "things"
    }
    
    words = [w.strip(".,!?;:()\"'").lower() for w in text.split() if w.strip(".,!?;:()\"'")]
    cleaned = [w for w in words if w not in STOP_WORDS and w not in exclusions and len(w) > 3]
    
    if cleaned:
        aspect = cleaned[0].capitalize()
        if len(cleaned) > 1 and cleaned[1] not in ["was", "is", "are", "were", "for", "with", "to", "in", "on", "at", "by", "from"]:
            aspect = f"{aspect} {cleaned[1].capitalize()}"
        return aspect
        
    return "General Experience"

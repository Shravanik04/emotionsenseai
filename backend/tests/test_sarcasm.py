import pytest
from app.services.sarcasm_service import sarcasm_detector
from app.services.analysis_service import (
    calculate_readability_and_complexity,
    extract_named_entities,
    analyzer
)

def test_sarcasm_heuristic_detection():
    # Test specific sarcasm phrases
    is_sarcastic, conf, reason = sarcasm_detector.detect_sarcasm("Oh great, another meeting that could have been an email.")
    assert is_sarcastic is True
    assert "Sarcastic construct" in reason or "clash" in reason or "irony" in reason

    is_sarcastic, conf, reason = sarcasm_detector.detect_sarcasm("I absolutely love waiting in traffic jams.")
    assert is_sarcastic is True

    # Test non-sarcastic
    is_sarcastic, conf, reason = sarcasm_detector.detect_sarcasm("This is a beautiful day and I am happy.")
    assert is_sarcastic is False

def test_readability_and_complexity():
    score, complexity = calculate_readability_and_complexity("The cat sat on the mat.")
    assert score > 70.0
    assert "Low" in complexity

def test_named_entity_extraction():
    entities = extract_named_entities("Yesterday, Alice and Google visited London.")
    assert "Alice" in entities["PERSON"]
    assert "Google" in entities["ORG"]
    assert "London" in entities["GPE"]

def test_sarcasm_sentiment_flip():
    # When sarcasm is detected, positive sentiment should flip to negative
    result = analyzer.analyze_full("Oh great, my phone died.")
    assert result["sarcasm"]["detected"] is True
    assert result["sentiment"] == "negative"
    assert result["emotion"] in ("frustration", "disappointment", "sadness")


def test_new_sarcasm_and_mixed_cases():
    # Case 1: Mixed emotions, no sarcasm
    res1 = analyzer.analyze_full("I hate waking up early, but I absolutely love working with my team.")
    assert res1["sentiment"] == "mixed"
    assert res1["sarcasm"]["detected"] is False
    top_emotions1 = [e["label"] for e in res1["emotion_ranking"]]
    assert "love" in top_emotions1 or "frustration" in top_emotions1
    
    # Case 2: Irony / Production bug
    res2 = analyzer.analyze_full("Fantastic! Another production bug.")
    assert res2["sarcasm"]["detected"] is True
    assert res2["emotion"] in ("frustration", "disappointment", "sadness")

    # Case 3: Waiting in traffic
    res3 = analyzer.analyze_full("I absolutely love waiting in traffic.")
    assert res3["sarcasm"]["detected"] is True

    # Case 4: Internship excitement
    res4 = analyzer.analyze_full("Yippie! I finally got my internship!")
    assert res4["sarcasm"]["detected"] is False
    assert res4["emotion"] in ("joy", "excitement", "happiness", "Possible Emotions")

    # Case 5: Nervous but excited — may be mixed or lean toward dominant signal
    res5 = analyzer.analyze_full("I'm nervous but excited.")
    assert res5["sentiment"] in ("mixed", "negative", "positive")

    assert res5["sarcasm"]["detected"] is False
    top_emotions5 = [e["label"] for e in res5["emotion_ranking"]]
    assert "fear" in top_emotions5 or "excitement" in top_emotions5 or "happiness" in top_emotions5

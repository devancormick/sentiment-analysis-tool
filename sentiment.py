"""
Sentiment analysis using a pre-trained NLP model.
Maps model output to positive, neutral, or negative with optional confidence.
"""

from typing import List, Tuple

# Lazy load pipeline to avoid slow startup when only importing
_pipeline = None


def _get_pipeline():
    """Load the pre-trained sentiment pipeline once."""
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            top_k=None,
        )
    return _pipeline


def analyze_text(text: str) -> Tuple[str, float]:
    """
    Analyze a single text and return (label, confidence).
    Label is one of: positive, neutral, negative.
    """
    if not text or not str(text).strip():
        return "neutral", 0.0
    pipe = _get_pipeline()
    result = pipe(str(text).strip()[:512])[0]
    if isinstance(result, list):
        by_label = {r["label"].lower(): r["score"] for r in result}
    else:
        by_label = {result["label"].lower(): result["score"]}
    label = max(by_label, key=by_label.get)
    confidence = by_label[label]
    normalized = _normalize_label(label)
    return normalized, round(confidence, 4)


def _normalize_label(label: str) -> str:
    """Map model labels to positive, neutral, negative."""
    label = label.lower()
    if label in ("positive", "pos"):
        return "positive"
    if label in ("negative", "neg"):
        return "negative"
    return "neutral"


def analyze_batch(texts: List[str]) -> List[Tuple[str, float]]:
    """Analyze a list of texts; returns list of (label, confidence)."""
    return [analyze_text(t) for t in texts]

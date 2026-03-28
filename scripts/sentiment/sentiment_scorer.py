#!/usr/bin/env python3
"""
Sentiment Scorer
Scores social media posts and news text for sentiment using
cardiffnlp/twitter-roberta-base-sentiment (free, runs locally).

Install: pip install transformers torch scipy
"""

import json, logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
import numpy as np

log = logging.getLogger(__name__)

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
_model = None
_tokenizer = None

LABELS = ["negative", "neutral", "positive"]

def load_model():
    global _model, _tokenizer
    if _model is None:
        log.info(f"Loading sentiment model: {MODEL_NAME}")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    return _model, _tokenizer

def score_text(text, max_length=512):
    """Return sentiment scores for a piece of text."""
    model, tokenizer = load_model()
    text_clean = text[:max_length].replace("\n", " ")
    try:
        encoded = tokenizer(text_clean, return_tensors="pt",
                           truncation=True, max_length=max_length)
        output = model(**encoded)
        scores = softmax(output.logits.detach().numpy()[0])
        return {
            "negative": round(float(scores[0]), 4),
            "neutral":  round(float(scores[1]), 4),
            "positive": round(float(scores[2]), 4),
            "dominant": LABELS[int(np.argmax(scores))]
        }
    except Exception as e:
        log.error(f"Sentiment scoring failed: {e}")
        return {"negative": 0, "neutral": 1, "positive": 0, "dominant": "neutral"}

def score_jsonl_file(input_path, output_path=None):
    """Add sentiment scores to all records in a JSONL file."""
    input_path = Path(input_path)
    if not output_path:
        output_path = input_path.parent / f"scored_{input_path.name}"

    count = 0
    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            record = json.loads(line)
            # Only score English text (translate first if needed)
            if record.get("language") == "en" or record.get("translated"):
                record["sentiment"] = score_text(record.get("text", ""))
                count += 1
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

    log.info(f"Scored {count} records → {output_path}")
    return output_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test = "The Iranian government is suppressing protests and violating human rights."
    print(score_text(test))

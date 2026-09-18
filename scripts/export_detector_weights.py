"""Export the trained sklearn pipeline as portable JSON so the Cloudflare Worker
can score text without a Python runtime.

This is a faithful export, not an approximation: vocabulary, IDF weights, and
logistic regression coefficients are dumped exactly as sklearn computed them,
and export_detector_weights_test.py below cross-checks the JS port's output
against the Python pipeline on real samples before it's trusted.
"""

import json
import pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "data" / "detector.pkl"
OUT_PATH = ROOT / "web" / "worker" / "detector_weights.json"

pipeline = pickle.loads(MODEL_PATH.read_bytes())
features = pipeline.named_steps["features"]
model = pipeline.named_steps["model"]

word_vec = dict(features.transformer_list)["word"]
char_vec = dict(features.transformer_list)["char"]


def vectorizer_export(vec) -> dict:
    return {
        "vocabulary": {term: int(idx) for term, idx in vec.vocabulary_.items()},
        "idf": [float(x) for x in vec.idf_],
        "ngram_range": list(vec.ngram_range),
        "analyzer": vec.analyzer,
        "lowercase": bool(vec.lowercase),
    }


export = {
    "word": vectorizer_export(word_vec),
    "char": vectorizer_export(char_vec),
    "coef": [float(x) for x in model.coef_[0]],
    "intercept": float(model.intercept_[0]),
    "n_word_features": len(word_vec.vocabulary_),
    "n_char_features": len(char_vec.vocabulary_),
}

OUT_PATH.write_text(json.dumps(export))
size_kb = OUT_PATH.stat().st_size // 1024
print(f"exported {export['n_word_features']} word + {export['n_char_features']} char features -> {OUT_PATH} ({size_kb} KB)")

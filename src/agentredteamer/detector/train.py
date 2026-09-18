import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

from agentredteamer.detector.dataset import Sample

RANDOM_STATE = 42


def build_pipeline(kind: str = "logreg") -> Pipeline:
    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ]
    )
    if kind == "logreg":
        model = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0, random_state=RANDOM_STATE)
    elif kind == "gboost":
        model = GradientBoostingClassifier(random_state=RANDOM_STATE)
    else:
        raise ValueError(f"unknown model kind: {kind}")
    return Pipeline([("features", features), ("model", model)])


def evaluate(y_true, y_score, threshold: float = 0.5) -> dict:
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y_true, y_score)) if len(set(y_true)) > 1 else float("nan"),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "threshold": threshold,
    }


def cross_validated_scores(samples: list[Sample], kind: str, folds: int = 5):
    """Out-of-fold probabilities, so every sample is scored by a model that never saw it.

    With a dataset this small a single train/test split is noisy, and reporting
    training-set numbers would be meaningless.
    """
    texts = [s.text for s in samples]
    labels = np.array([s.label for s in samples])
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    probabilities = cross_val_predict(build_pipeline(kind), texts, labels, cv=cv, method="predict_proba")[:, 1]
    return labels, probabilities


def fit_final(samples: list[Sample], kind: str = "logreg") -> Pipeline:
    pipeline = build_pipeline(kind)
    pipeline.fit([s.text for s in samples], [s.label for s in samples])
    return pipeline


def top_features(pipeline: Pipeline, count: int = 15) -> dict[str, list[tuple[str, float]]]:
    """Which tokens drive the decision — the reason to prefer an interpretable model."""
    model = pipeline.named_steps["model"]
    if not hasattr(model, "coef_"):
        return {}
    names = pipeline.named_steps["features"].get_feature_names_out()
    coefficients = model.coef_[0]
    order = np.argsort(coefficients)
    return {
        "injection": [(str(names[i]), float(coefficients[i])) for i in order[-count:][::-1]],
        "benign": [(str(names[i]), float(coefficients[i])) for i in order[:count]],
    }


def holdout_report(samples: list[Sample], kind: str = "logreg") -> str:
    texts = [s.text for s in samples]
    labels = [s.label for s in samples]
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, stratify=labels, random_state=RANDOM_STATE
    )
    pipeline = build_pipeline(kind)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    return classification_report(y_test, predictions, target_names=["benign", "injection"], zero_division=0)

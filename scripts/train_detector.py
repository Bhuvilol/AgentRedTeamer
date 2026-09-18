import json
import pickle
from pathlib import Path

from agentredteamer.detector import prompt_guard
from agentredteamer.detector.dataset import build_dataset, dataset_summary
from agentredteamer.detector.train import (
    cross_validated_scores,
    evaluate,
    fit_final,
    holdout_report,
    top_features,
)

ROOT = Path(__file__).resolve().parent.parent
MODEL_OUT = ROOT / "data" / "detector.pkl"
RESULTS_OUT = ROOT / "web" / "static" / "data" / "detector_results.json"

samples = build_dataset()
summary = dataset_summary(samples)
print("dataset:", json.dumps(summary, indent=2))
print()

results = {"dataset": summary, "models": {}}

for kind in ["logreg", "gboost"]:
    labels, probabilities = cross_validated_scores(samples, kind)
    metrics = evaluate(labels, probabilities)
    results["models"][kind] = metrics
    print(f"{kind:8s} P={metrics['precision']:.3f} R={metrics['recall']:.3f} "
          f"F1={metrics['f1']:.3f} AUC={metrics['roc_auc']:.3f}  {metrics['confusion']}")

print()
print("held-out classification report (logreg):")
print(holdout_report(samples))

print("scoring the same samples with Llama Prompt Guard 2 for comparison...")
guard_scores = prompt_guard.score_many([s.text for s in samples])
guard_labels = [s.label for s in samples]
guard_metrics = evaluate(guard_labels, guard_scores)
results["models"]["prompt_guard_2_86m"] = guard_metrics
print(f"{'guard':8s} P={guard_metrics['precision']:.3f} R={guard_metrics['recall']:.3f} "
      f"F1={guard_metrics['f1']:.3f} AUC={guard_metrics['roc_auc']:.3f}  {guard_metrics['confusion']}")

final = fit_final(samples, "logreg")
features = top_features(final)
results["top_features"] = features

MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
MODEL_OUT.write_bytes(pickle.dumps(final))
RESULTS_OUT.parent.mkdir(parents=True, exist_ok=True)
RESULTS_OUT.write_text(json.dumps(results, indent=2))

print()
print("strongest injection signals:", [f for f, _ in features.get("injection", [])[:8]])
print(f"saved model -> {MODEL_OUT.relative_to(ROOT)}")
print(f"saved results -> {RESULTS_OUT.relative_to(ROOT)}")

"""Cross-persona generalization check.

Standard cross-validation shuffles all samples together, so a fold can easily
contain NovaBank text in both its train and test split — meaning the model can
pass by memorising "escalation code" rather than learning what an injection
looks like. This holds out one persona's entire vocabulary at train time and
tests only on that persona, which is the honest test of generalization.
"""

import json

from agentredteamer.detector.dataset import Sample, build_dataset
from agentredteamer.detector.train import build_pipeline, evaluate
from agentredteamer.trace_store import load_all_traces

traces_by_persona: dict[str, set[str]] = {}
for trace in load_all_traces():
    traces_by_persona.setdefault(trace["persona_name"], set())
    for turn in trace["turns"]:
        traces_by_persona[trace["persona_name"]].add(turn["message"].strip())

samples = build_dataset()


def persona_of(sample: Sample) -> str | None:
    for persona, texts in traces_by_persona.items():
        if sample.text in texts or any(sample.text in t or t in sample.text for t in texts if sample.text):
            return persona
    return None  # synthetic benign_record samples aren't tied to a persona


tagged = [(s, persona_of(s)) for s in samples]
personas = sorted({p for _, p in tagged if p})
print(f"personas with tagged samples: {personas}\n")

for held_out in personas:
    train = [s for s, p in tagged if p != held_out]
    test = [s for s, p in tagged if p == held_out]
    pos_test = sum(1 for s in test if s.label == 1)
    if pos_test < 3:
        print(f"skipping {held_out}: only {pos_test} positive samples held out\n")
        continue

    pipeline = build_pipeline("logreg")
    pipeline.fit([s.text for s in train], [s.label for s in train])
    scores = pipeline.predict_proba([s.text for s in test])[:, 1]
    metrics = evaluate([s.label for s in test], scores)

    print(f"=== held out: {held_out} ({len(test)} samples, {pos_test} positive) ===")
    print(json.dumps(metrics, indent=2))
    print()

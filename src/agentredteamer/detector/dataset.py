from dataclasses import dataclass

from agentredteamer.detector.benign_corpus import build_benign_corpus
from agentredteamer.trace_store import load_all_traces

INDIRECT_CATEGORY = "indirect_tool_injection"


@dataclass
class Sample:
    text: str
    label: int  # 1 = injection attempt, 0 = benign
    source: str


def _payload_from_tool_turn(message: str) -> str:
    """Tool turns are stored as the benign record plus the injected payload."""
    parts = message.split("\n", 1)
    return parts[1] if len(parts) > 1 else message


def build_dataset(benign_ratio: float = 1.0) -> list[Sample]:
    traces = load_all_traces()
    samples: list[Sample] = []
    seen: set[str] = set()

    for trace in traces:
        # In a multi-turn campaign the early turns are rapport-building and contain no
        # manipulation — labelling them as injections would train the detector to flag
        # ordinary friendly messages. Only the turn carrying the actual ask is a positive;
        # the ambiguous ones are dropped from the dataset rather than mislabelled.
        attacker_indices = [i for i, t in enumerate(trace["turns"]) if t["speaker"] == "attacker"]
        final_attacker_index = attacker_indices[-1] if attacker_indices else None

        for index, turn in enumerate(trace["turns"]):
            if turn["speaker"] == "tool":
                text = _payload_from_tool_turn(turn["message"])
                source = "tool_payload"
            elif turn["speaker"] == "attacker" and trace["attack_category"] != INDIRECT_CATEGORY:
                is_multi_turn = len(attacker_indices) > 1
                if is_multi_turn and index != final_attacker_index:
                    continue
                text = turn["message"]
                source = f"attacker_{trace['attack_category']}"
            else:
                continue

            text = text.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            samples.append(Sample(text=text, label=1, source=source))

    # Assistant replies are real, varied, benign prose from the same domain.
    for trace in traces:
        for turn in trace["turns"]:
            if turn["speaker"] != "target":
                continue
            text = turn["message"].strip()
            if not text or text in seen:
                continue
            seen.add(text)
            samples.append(Sample(text=text, label=0, source="target_reply"))

    # Always include tool-output-shaped benign text. The detector's job is to scan
    # retrieved content, so the benign class can't be mostly assistant prose.
    positives = sum(1 for s in samples if s.label == 1)
    needed = max(40, int(positives * benign_ratio))
    for text in build_benign_corpus(needed):
        if text in seen:
            continue
        seen.add(text)
        samples.append(Sample(text=text, label=0, source="benign_record"))

    return samples


def dataset_summary(samples: list[Sample]) -> dict:
    by_source: dict[str, int] = {}
    for sample in samples:
        by_source[sample.source] = by_source.get(sample.source, 0) + 1
    return {
        "total": len(samples),
        "injection": sum(1 for s in samples if s.label == 1),
        "benign": sum(1 for s in samples if s.label == 0),
        "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
    }

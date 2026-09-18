"""Inter-judge agreement: is the judge's verdict reliable, or just one model's opinion?

Rather than treating the judge's output as ground truth, this runs a second and
third judge model over the same transcripts and measures where they agree
(Cohen's kappa) and where they don't. Disagreements are the interesting part —
they're the cases worth reading by hand, because one of the judges is wrong.
"""

from dataclasses import dataclass

from agentredteamer.conversation import Episode, Turn
from agentredteamer.judge import judge_episode
from agentredteamer.personas import ALL_PERSONAS

JUDGE_PANEL = ["openai/gpt-oss-safeguard-20b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]


@dataclass
class JudgeCall:
    model: str
    leaked_secret: bool
    broke_character: bool
    reasoning: str


@dataclass
class CalibrationRow:
    trace_id: str
    persona_name: str
    attack_category: str
    defense_name: str
    calls: list[JudgeCall]

    @property
    def leaked_agreement(self) -> bool:
        return len({c.leaked_secret for c in self.calls}) == 1

    @property
    def broke_agreement(self) -> bool:
        return len({c.broke_character for c in self.calls}) == 1


def _persona_lookup(name: str):
    return next(p for p in ALL_PERSONAS if p.name == name)


def _episode_from_trace(trace: dict) -> Episode:
    return Episode(
        persona_name=trace["persona_name"],
        defense_name=trace["defense_name"],
        attack_category=trace["attack_category"],
        turns=[Turn(speaker=t["speaker"], message=t["message"]) for t in trace["turns"]],
    )


def run_panel(trace: dict, panel: list[str] = JUDGE_PANEL) -> CalibrationRow:
    persona = _persona_lookup(trace["persona_name"])
    episode = _episode_from_trace(trace)

    calls = []
    for model in panel:
        verdict = judge_episode(persona, episode, model=model)
        calls.append(
            JudgeCall(
                model=model,
                leaked_secret=verdict.leaked_secret,
                broke_character=verdict.broke_character,
                reasoning=verdict.reasoning,
            )
        )
    return CalibrationRow(
        trace_id=trace["trace_id"],
        persona_name=trace["persona_name"],
        attack_category=trace["attack_category"],
        defense_name=trace["defense_name"],
        calls=calls,
    )


def cohens_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    p_a_true = sum(a) / n
    p_b_true = sum(b) / n
    expected = p_a_true * p_b_true + (1 - p_a_true) * (1 - p_b_true)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def pairwise_kappa(rows: list[CalibrationRow], field: str, model_a: str, model_b: str) -> float:
    a_vals, b_vals = [], []
    for row in rows:
        call_a = next((c for c in row.calls if c.model == model_a), None)
        call_b = next((c for c in row.calls if c.model == model_b), None)
        if call_a and call_b:
            a_vals.append(getattr(call_a, field))
            b_vals.append(getattr(call_b, field))
    return cohens_kappa(a_vals, b_vals)

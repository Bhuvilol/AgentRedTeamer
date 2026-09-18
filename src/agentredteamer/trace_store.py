import json
import time
import uuid
from pathlib import Path

from agentredteamer.conversation import Episode
from agentredteamer.judge import verdict as Verdict

TRACES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "traces"


def save_trace(episode: Episode, verdict: Verdict) -> Path:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    trace_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
    record = {
        "trace_id": trace_id,
        "persona_name": episode.persona_name,
        "defense_name": episode.defense_name,
        "attack_category": episode.attack_category,
        "turns": [{"speaker": t.speaker, "message": t.message} for t in episode.turns],
        "verdict": verdict.model_dump(),
    }
    path = TRACES_DIR / f"{trace_id}.json"
    path.write_text(json.dumps(record, indent=2))
    return path


def load_all_traces() -> list[dict]:
    if not TRACES_DIR.exists():
        return []
    traces = []
    for path in sorted(TRACES_DIR.glob("*.json")):
        traces.append(json.loads(path.read_text()))
    return traces

import json
from pathlib import Path

from agentredteamer.analysis import summarize
from agentredteamer.attack_strategies import ATTACK_STRATEGIES
from agentredteamer.defenses import DEFENSES
from agentredteamer.personas import ALL_PERSONAS
from agentredteamer.trace_store import load_all_traces

ROOT = Path(__file__).resolve().parent.parent
TRACES_OUT = ROOT / "web" / "static" / "data" / "traces.json"
PROMPTS_OUT = ROOT / "web" / "worker" / "prompts.json"

traces = load_all_traces()
TRACES_OUT.parent.mkdir(parents=True, exist_ok=True)
TRACES_OUT.write_text(json.dumps(traces, separators=(",", ":")))
print(f"wrote {len(traces)} traces -> {TRACES_OUT.relative_to(ROOT)} ({TRACES_OUT.stat().st_size // 1024} KB)")

prompts = {
    "personas": {
        persona.name: {
            "role_description": persona.role_description,
            "secret_label": persona.secret_label,
            "secret_value": persona.secret_value,
            "defenses": {name: builder(persona) for name, builder in DEFENSES.items()},
        }
        for persona in ALL_PERSONAS
    },
    "attack_strategies": ATTACK_STRATEGIES,
    "max_turns": {"multi_turn_social_engineering": 5},
    "default_max_turns": 1,
}
PROMPTS_OUT.parent.mkdir(parents=True, exist_ok=True)
PROMPTS_OUT.write_text(json.dumps(prompts, indent=2))
print(f"wrote prompts -> {PROMPTS_OUT.relative_to(ROOT)}")

summary = summarize()
print(f"summary: {summary['total_traces']} traces, overall success {summary['overall_success_rate']:.1%}")

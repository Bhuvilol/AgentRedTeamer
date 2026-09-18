import os

from flask import Flask, render_template

from agentredteamer.analysis import summarize
from agentredteamer.trace_store import load_all_traces
from agentredteamer.attack_strategies import ATTACK_STRATEGIES
from agentredteamer.defenses import DEFENSES
from agentredteamer.personas import ALL_PERSONAS

app = Flask(__name__)

DEFENSE_BLURBS = {
    "plain_instruction": "One sentence telling it to keep the secret. The naive baseline every other defense is measured against.",
    "reminder_emphasis": "Repetition and emphasis, restating the rule as non-negotiable and unoverridable.",
    "delimiter_sandwiching": "Wraps the rule in delimiters and marks everything the user sends as untrusted data, not commands.",
    "few_shot_refusal": "Shows worked examples of refusing manipulation attempts, so the model has a pattern to copy.",
    "meta_awareness": "Names the specific techniques it should expect, so it can recognise them rather than just be forbidden.",
    "self_check": "Instructs the model to verify its own reply before sending it, catching leaks at the last moment.",
}

BENTO_PALETTE = [
    ("oklch(0.88 0.1 28)", "oklch(0.38 0.14 28)", "oklch(0.32 0.15 28)"),
    ("oklch(0.93 0.09 60)", "oklch(0.42 0.11 60)", "oklch(0.36 0.12 60)"),
    ("oklch(0.94 0.09 95)", "oklch(0.42 0.1 85)", "oklch(0.36 0.11 85)"),
    ("oklch(0.91 0.05 245)", "oklch(0.4 0.09 245)", "oklch(0.34 0.11 245)"),
    ("oklch(0.92 0.06 160)", "oklch(0.38 0.1 160)", "oklch(0.33 0.11 160)"),
    ("dark", "oklch(0.72 0.01 60)", "oklch(0.85 0.13 155)"),
]

CATEGORY_LABELS = {
    "role_play_override": "Role-play override",
    "context_injection": "Context injection",
    "persona_hijacking": "Persona hijacking",
    "multi_turn_social_engineering": "Multi-turn",
    "indirect_tool_injection": "Tool injection",
}


def heat_color(rate: float | None) -> tuple[str, str]:
    if rate is None:
        return "oklch(0.96 0 0)", "oklch(0.6 0.01 60)"
    if rate < 0.05:
        return "oklch(0.99 0.005 28)", "inherit"
    if rate < 0.12:
        return "oklch(0.97 0.015 28)", "inherit"
    if rate < 0.22:
        return "oklch(0.93 0.05 28)", "inherit"
    if rate < 0.4:
        return "oklch(0.85 0.09 28)", "inherit"
    if rate < 0.65:
        return "oklch(0.71 0.15 28)", "oklch(0.99 0 0)"
    return "oklch(0.57 0.19 28)", "oklch(0.99 0 0)"


def pick_highlights(traces: list[dict]) -> list[dict]:
    def outcome(trace: dict) -> str:
        if trace["verdict"]["leaked_secret"]:
            return "leaked"
        if trace["verdict"]["broke_character"]:
            return "broke"
        return "blocked"

    wanted = ["blocked", "broke", "leaked"]
    highlights = []
    for label in wanted:
        match = next((t for t in traces if outcome(t) == label), None)
        if match:
            first_attack = next((turn["message"] for turn in match["turns"] if turn["speaker"] == "attacker"), "")
            highlights.append(
                {
                    "outcome": label,
                    "attack_category": match["attack_category"],
                    "turns": len([t for t in match["turns"] if t["speaker"] == "attacker"]),
                    "excerpt": first_attack[:170] + ("…" if len(first_attack) > 170 else ""),
                }
            )
    return highlights


def build_context() -> dict:
    summary = summarize()
    traces = load_all_traces()
    ranked = sorted(summary["by_defense"].items(), key=lambda item: item[1], reverse=True)
    defense_cards = [
        {
            "name": name,
            "rate": rate,
            "blurb": DEFENSE_BLURBS.get(name, ""),
            "palette": BENTO_PALETTE[index % len(BENTO_PALETTE)],
            "strongest": index == len(ranked) - 1,
        }
        for index, (name, rate) in enumerate(ranked)
    ]
    worker_base = os.environ.get("WORKER_BASE_URL", "")
    return {
        "api_url": worker_base,
        "scan_api_url": f"{worker_base}/scan" if worker_base else "",
        "summary": summary,
        "highlights": pick_highlights(traces),
        "defense_cards": defense_cards,
        "category_labels": CATEGORY_LABELS,
        "heat_color": heat_color,
        "personas": ALL_PERSONAS,
        "defense_names": list(DEFENSES),
        "attack_categories": list(ATTACK_STRATEGIES),
    }


@app.route("/")
def index():
    return render_template("index.html", active_page="index", **build_context())


@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard", **build_context())


@app.route("/method/")
def method():
    return render_template("method.html", active_page="method", **build_context())


@app.route("/scan/")
def scan():
    return render_template("scan.html", active_page="scan", **build_context())


if __name__ == "__main__":
    app.run(debug=True, port=5001)

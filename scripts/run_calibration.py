import argparse
import json
import random

from agentredteamer.calibration import JUDGE_PANEL, CalibrationRow, pairwise_kappa, run_panel
from agentredteamer.trace_store import load_all_traces

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=25, help="number of traces to sample")
args = parser.parse_args()

traces = load_all_traces()

# Oversample the interesting cases: any trace with disagreement potential (a leak or
# character break per the original judge) plus the harder indirect-injection class,
# rather than a pure random sample that would be mostly uneventful "blocked" traces.
interesting = [t for t in traces if t["verdict"]["leaked_secret"] or t["verdict"]["broke_character"]]
tool_traces = [t for t in traces if t["attack_category"] == "indirect_tool_injection"]
rest = [t for t in traces if t not in interesting and t not in tool_traces]

rng = random.Random(11)
pool = {t["trace_id"]: t for t in interesting + tool_traces}
rng.shuffle(rest)
for t in rest:
    if len(pool) >= args.n:
        break
    pool[t["trace_id"]] = t

sample = list(pool.values())[: args.n]
print(f"running {len(JUDGE_PANEL)}-judge panel on {len(sample)} traces "
      f"({len(interesting)} eventful, {len(tool_traces)} tool-injection)\n")

rows: list[CalibrationRow] = []
for i, trace in enumerate(sample, start=1):
    print(f"[{i}/{len(sample)}] {trace['persona_name']} | {trace['defense_name']} | {trace['attack_category']}")
    try:
        row = run_panel(trace)
    except Exception as e:
        print(f"  skipped: {e}")
        continue
    rows.append(row)
    verdicts = {c.model.split("/")[-1]: (c.leaked_secret, c.broke_character) for c in row.calls}
    agree = "AGREE" if row.leaked_agreement and row.broke_agreement else "DISAGREE"
    print(f"  {agree}  {verdicts}")

leaked_total_agree = sum(1 for r in rows if r.leaked_agreement)
broke_total_agree = sum(1 for r in rows if r.broke_agreement)

print(f"\n=== agreement across all {len(JUDGE_PANEL)} judges ===")
print(f"leaked_secret unanimous:   {leaked_total_agree}/{len(rows)} ({leaked_total_agree/len(rows):.0%})")
print(f"broke_character unanimous: {broke_total_agree}/{len(rows)} ({broke_total_agree/len(rows):.0%})")

print("\n=== pairwise Cohen's kappa (leaked_secret) ===")
pair_kappas = {}
for i, m1 in enumerate(JUDGE_PANEL):
    for m2 in JUDGE_PANEL[i + 1 :]:
        k = pairwise_kappa(rows, "leaked_secret", m1, m2)
        pair_kappas[f"{m1.split('/')[-1]} vs {m2.split('/')[-1]}"] = k
        print(f"  {m1.split('/')[-1]:25s} vs {m2.split('/')[-1]:20s}  kappa={k:.3f}")

print("\n=== disagreements (worth reading by hand) ===")
disagreements = [r for r in rows if not (r.leaked_agreement and r.broke_agreement)]
for row in disagreements:
    print(f"\n--- {row.trace_id} | {row.persona_name} | {row.defense_name} | {row.attack_category} ---")
    for call in row.calls:
        print(f"  {call.model.split('/')[-1]:25s} leaked={call.leaked_secret!s:5s} broke={call.broke_character!s:5s}  {call.reasoning[:140]}")

output = {
    "n_traces": len(rows),
    "judges": JUDGE_PANEL,
    "leaked_secret_unanimous_rate": leaked_total_agree / len(rows) if rows else None,
    "broke_character_unanimous_rate": broke_total_agree / len(rows) if rows else None,
    "pairwise_kappa_leaked_secret": pair_kappas,
    "n_disagreements": len(disagreements),
    "disagreements": [
        {
            "trace_id": r.trace_id,
            "persona_name": r.persona_name,
            "defense_name": r.defense_name,
            "attack_category": r.attack_category,
            "calls": [
                {"model": c.model, "leaked_secret": c.leaked_secret, "broke_character": c.broke_character, "reasoning": c.reasoning}
                for c in r.calls
            ],
        }
        for r in disagreements
    ],
}
with open("web/static/data/calibration_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("\nsaved -> web/static/data/calibration_results.json")

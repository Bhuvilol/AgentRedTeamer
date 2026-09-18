import argparse
import itertools
from collections import Counter

from agentredteamer.attack_strategies import ATTACK_STRATEGIES
from agentredteamer.conversation import run_episode
from agentredteamer.defenses import DEFENSES
from agentredteamer.judge import judge_episode
from agentredteamer.personas import ALL_PERSONAS
from agentredteamer.retry import DailyQuotaExceeded
from agentredteamer.trace_store import load_all_traces, save_trace

MAX_TURNS_BY_CATEGORY = {"multi_turn_social_engineering": 5}
DEFAULT_MAX_TURNS = 1
TRIALS_PER_COMBINATION = 3

parser = argparse.ArgumentParser(description="Run the adversarial testing grid. Resumable: existing traces are skipped.")
parser.add_argument("--sample", action="store_true", help="run a tiny subset to sanity-check the pipeline")
parser.add_argument("--trials", type=int, default=TRIALS_PER_COMBINATION, help="trials per combination")
parser.add_argument("--limit", type=int, help="stop after this many new episodes (to stay inside a daily quota)")
args = parser.parse_args()

personas = ALL_PERSONAS[:1] if args.sample else ALL_PERSONAS
defense_names = list(DEFENSES)[:2] if args.sample else list(DEFENSES)
categories = list(ATTACK_STRATEGIES)[:2] if args.sample else list(ATTACK_STRATEGIES)
trials = 1 if args.sample else args.trials

done = Counter(
    (trace["persona_name"], trace["defense_name"], trace["attack_category"]) for trace in load_all_traces()
)

todo = []
for persona, defense_name, category in itertools.product(personas, defense_names, categories):
    already = done[(persona.name, defense_name, category)]
    for _ in range(max(0, trials - already)):
        todo.append((persona, defense_name, category))

if args.limit:
    todo = todo[: args.limit]

print(f"{sum(done.values())} traces already on disk. Running {len(todo)} more.\n")

failures: list[tuple] = []
completed = 0

for index, (persona, defense_name, category) in enumerate(todo, start=1):
    max_turns = MAX_TURNS_BY_CATEGORY.get(category, DEFAULT_MAX_TURNS)
    print(f"[{index}/{len(todo)}] {persona.name} | {defense_name} | {category}")

    try:
        episode = run_episode(persona=persona, defense_name=defense_name, attack_category=category, max_turns=max_turns)
        verdict = judge_episode(persona, episode)
        path = save_trace(episode, verdict)
    except DailyQuotaExceeded:
        print(f"\nDaily quota reached. Stopping cleanly after {completed} new traces.")
        print("Re-run this script (or scripts/watch_and_resume.sh) once quota resets; "
              "finished combinations are skipped automatically.")
        break
    except Exception as e:
        failures.append((persona.name, defense_name, category, str(e)))
        print(f"  -> FAILED: {e}")
        continue

    completed += 1
    outcome = "LEAKED" if verdict.leaked_secret else ("BROKE CHARACTER" if verdict.broke_character else "blocked")
    print(f"  -> {outcome}  ({path.name})")

print(f"\nDone. {completed} new traces, {len(failures)} failed.")
for failure in failures:
    print(f"  FAILED {failure[:3]}")

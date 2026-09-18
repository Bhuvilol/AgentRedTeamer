import argparse
import itertools

from agentredteamer.attack_strategies import ATTACK_STRATEGIES
from agentredteamer.conversation import run_episode
from agentredteamer.defenses import DEFENSES
from agentredteamer.judge import judge_episode
from agentredteamer.personas import ALL_PERSONAS
from agentredteamer.trace_store import save_trace

MAX_TURNS_BY_CATEGORY = {
    "multi_turn_social_engineering": 5,
}
DEFAULT_MAX_TURNS = 1

TRIALS_PER_COMBINATION = 3

parser = argparse.ArgumentParser()
parser.add_argument("--sample", action="store_true", help="run a tiny subset to sanity-check the pipeline")
args = parser.parse_args()

personas = ALL_PERSONAS[:1] if args.sample else ALL_PERSONAS
defense_names = list(DEFENSES)[:2] if args.sample else list(DEFENSES)
categories = list(ATTACK_STRATEGIES)[:2] if args.sample else list(ATTACK_STRATEGIES)
trials = 1 if args.sample else TRIALS_PER_COMBINATION

combinations = list(itertools.product(personas, defense_names, categories, range(trials)))
print(f"Running {len(combinations)} episodes...\n")

for i, (persona, defense_name, category, trial) in enumerate(combinations, start=1):
    max_turns = MAX_TURNS_BY_CATEGORY.get(category, DEFAULT_MAX_TURNS)
    print(f"[{i}/{len(combinations)}] {persona.name} | {defense_name} | {category} | trial {trial + 1}")

    episode = run_episode(persona=persona, defense_name=defense_name, attack_category=category, max_turns=max_turns)
    verdict = judge_episode(persona, episode)
    path = save_trace(episode, verdict)

    outcome = "LEAKED" if verdict.leaked_secret else ("BROKE CHARACTER" if verdict.broke_character else "blocked")
    print(f"  -> {outcome}  ({path.name})")

print("\nDone.")

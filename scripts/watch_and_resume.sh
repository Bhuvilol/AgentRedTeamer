#!/bin/bash
# Keep the experiment grid moving without a human needing to notice it stalled.
# run_experiment.py is resumable and exits cleanly when Groq's daily quota is
# genuinely exhausted (not just rate-limited) — this loop waits and restarts it.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX_ROUNDS=30
WAIT_SECONDS=1200  # 20 minutes between attempts once quota is truly exhausted

for round in $(seq 1 "$MAX_ROUNDS"); do
    echo "=== round $round/$MAX_ROUNDS — $(date) ==="
    python -u scripts/run_experiment.py
    remaining=$(python -c "
import itertools
from collections import Counter
from agentredteamer.attack_strategies import ATTACK_STRATEGIES
from agentredteamer.defenses import DEFENSES
from agentredteamer.personas import ALL_PERSONAS
from agentredteamer.trace_store import load_all_traces
done = Counter((t['persona_name'], t['defense_name'], t['attack_category']) for t in load_all_traces())
todo = 0
for p, d, c in itertools.product(ALL_PERSONAS, DEFENSES, ATTACK_STRATEGIES):
    todo += max(0, 3 - done[(p.name, d, c)])
print(todo)
")
    echo "remaining combinations: $remaining"
    if [ "$remaining" -eq 0 ]; then
        echo "grid complete."
        break
    fi
    echo "waiting ${WAIT_SECONDS}s before retrying..."
    sleep "$WAIT_SECONDS"
done

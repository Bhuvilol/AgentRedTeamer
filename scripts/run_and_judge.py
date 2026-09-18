from agentredteamer.conversation import run_episode
from agentredteamer.judge import judge_episode
from agentredteamer.personas import NOVABANK_SUPPORT

episode = run_episode(
    persona=NOVABANK_SUPPORT,
    defense_name="plain_instruction",
    attack_category="role_play_override",
    max_turns=1,
)

for turn in episode.turns:
    print(f"[{turn.speaker}] {turn.message}\n")

verdict = judge_episode(NOVABANK_SUPPORT, episode)
print("--- verdict ---")
print(verdict)

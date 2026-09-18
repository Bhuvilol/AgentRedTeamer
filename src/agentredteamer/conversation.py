from dataclasses import dataclass, field

from agentredteamer.attacker_agent import AttackerAgent
from agentredteamer.personas import Persona
from agentredteamer.target_agent import TargetAgent
from agentredteamer.tool_target import ToolTargetAgent

INDIRECT_CATEGORY = "indirect_tool_injection"


@dataclass
class Turn:
    speaker: str
    message: str


@dataclass
class Episode:
    persona_name: str
    defense_name: str
    attack_category: str
    turns: list[Turn] = field(default_factory=list)
    tool_was_called: bool | None = None

    def transcript_text(self) -> str:
        speaker_labels = {"attacker": "Attacker", "target": "Target", "tool": "Tool result (data the agent retrieved)"}
        return "\n\n".join(f"{speaker_labels[t.speaker]}: {t.message}" for t in self.turns)


def run_tool_injection_episode(persona: Persona, defense_name: str) -> Episode:
    attacker = AttackerAgent(persona=persona, category=INDIRECT_CATEGORY, max_turns=1)
    target = ToolTargetAgent(persona=persona, defense_name=defense_name)
    episode = Episode(persona_name=persona.name, defense_name=defense_name, attack_category=INDIRECT_CATEGORY)

    payload = attacker.next_message(None)
    reply, called_tool = target.run(persona.tool_trigger, payload)

    episode.turns.append(Turn(speaker="attacker", message=persona.tool_trigger))
    episode.turns.append(Turn(speaker="tool", message=f"{persona.benign_record}\n{payload}"))
    episode.turns.append(Turn(speaker="target", message=reply))
    episode.tool_was_called = called_tool
    return episode


def run_episode(persona: Persona, defense_name: str, attack_category: str, max_turns: int) -> Episode:
    if attack_category == INDIRECT_CATEGORY:
        return run_tool_injection_episode(persona, defense_name)

    target = TargetAgent(persona=persona, defense_name=defense_name)
    attacker = AttackerAgent(persona=persona, category=attack_category, max_turns=max_turns)
    episode = Episode(persona_name=persona.name, defense_name=defense_name, attack_category=attack_category)

    target_reply = None
    for _ in range(max_turns):
        attacker_message = attacker.next_message(target_reply)
        episode.turns.append(Turn(speaker="attacker", message=attacker_message))

        target_reply = target.respond(attacker_message)
        episode.turns.append(Turn(speaker="target", message=target_reply))

    return episode

from dataclasses import dataclass, field

from agentredteamer.attacker_agent import AttackerAgent
from agentredteamer.personas import Persona
from agentredteamer.target_agent import TargetAgent


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

    def transcript_text(self) -> str:
        speaker_labels = {"attacker": "Attacker", "target": "Target"}
        return "\n\n".join(f"{speaker_labels[t.speaker]}: {t.message}" for t in self.turns)


def run_episode(persona: Persona, defense_name: str, attack_category: str, max_turns: int) -> Episode:
    target = TargetAgent(persona=persona, defense_name=defense_name)
    attacker = AttackerAgent(persona=persona, category=attack_category)
    episode = Episode(persona_name=persona.name, defense_name=defense_name, attack_category=attack_category)

    target_reply = None
    for _ in range(max_turns):
        attacker_message = attacker.next_message(target_reply)
        episode.turns.append(Turn(speaker="attacker", message=attacker_message))

        target_reply = target.respond(attacker_message)
        episode.turns.append(Turn(speaker="target", message=target_reply))

    return episode

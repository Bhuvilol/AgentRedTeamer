from agentredteamer.defenses import DEFENSES
from agentredteamer.llm_client import get_chat_model
from agentredteamer.personas import Persona


class TargetAgent:
    def __init__(self, persona: Persona, defense_name: str):
        self.persona = persona
        self.defense_name = defense_name
        self.system_prompt = DEFENSES[defense_name](persona)
        self.model = get_chat_model(temperature=0.3)
        self.history: list[tuple[str, str]] = []

    def respond(self, user_message: str) -> str:
        self.history.append(("human", user_message))
        messages = [("system", self.system_prompt), *self.history]
        response = self.model.invoke(messages)
        self.history.append(("ai", response.content))
        return response.content

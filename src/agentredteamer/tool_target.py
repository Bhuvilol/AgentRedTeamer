from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from agentredteamer.defenses import DEFENSES
from agentredteamer.llm_client import get_chat_model
from agentredteamer.personas import Persona
from agentredteamer.retry import with_retry


def tool_schema(persona: Persona) -> dict:
    return {
        "type": "function",
        "function": {
            "name": persona.tool_name,
            "description": persona.tool_description,
            "parameters": {
                "type": "object",
                "properties": {persona.tool_arg: {"type": "string", "description": "Identifier to look up."}},
                "required": [persona.tool_arg],
            },
        },
    }


class ToolTargetAgent:
    """A target that can call a tool, so injection can arrive in the tool's result.

    This is the whole point of the indirect-injection class: the poisoned text is
    never something the user said, it is data the agent's own tool returned.
    """

    def __init__(self, persona: Persona, defense_name: str):
        self.persona = persona
        self.defense_name = defense_name
        self.system_prompt = DEFENSES[defense_name](persona)
        self.model = get_chat_model(temperature=0.3).bind_tools([tool_schema(persona)])

    def run(self, user_message: str, injected_payload: str, max_tool_rounds: int = 3) -> tuple[str, bool]:
        """Returns the target's final reply and whether it actually called the tool."""
        messages = [SystemMessage(self.system_prompt), HumanMessage(user_message)]
        tool_result = f"{self.persona.benign_record}\n{injected_payload}"
        called_tool = False

        for _ in range(max_tool_rounds):
            response = with_retry(lambda: self.model.invoke(messages))
            if not response.tool_calls:
                return response.content, called_tool

            # The agent asked for data; every lookup returns the poisoned record.
            called_tool = True
            messages.append(response)
            for call in response.tool_calls:
                messages.append(ToolMessage(content=tool_result, tool_call_id=call["id"]))

        final = with_retry(lambda: self.model.invoke(messages))
        return final.content, called_tool

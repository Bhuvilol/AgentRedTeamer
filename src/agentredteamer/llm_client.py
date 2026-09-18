from langchain_groq import ChatGroq

from agentredteamer.config import DEFAULT_MODEL, GROQ_API_KEY


def get_chat_model(
    temperature: float = 0.7, model: str = DEFAULT_MODEL, max_tokens: int | None = None
) -> ChatGroq:
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

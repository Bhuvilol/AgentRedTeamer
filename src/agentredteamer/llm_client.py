from langchain_groq import ChatGroq

from agentredteamer.config import DEFAULT_MODEL, GROQ_API_KEY

# gpt-oss models spend a large, invisible chunk of their token budget on chain-of-
# thought reasoning tokens even for short answers (measured: ~74 of 194 total
# tokens on a one-line refusal at default effort, vs. 13 of 133 at "low", same
# answer quality). None of our roles need deep reasoning, and this is the single
# biggest lever on how many episodes fit in a day's free-tier quota.
REASONING_EFFORT_MODELS = "openai/gpt-oss"


def get_chat_model(
    temperature: float = 0.7, model: str = DEFAULT_MODEL, max_tokens: int | None = None
) -> ChatGroq:
    kwargs = {}
    if model.startswith(REASONING_EFFORT_MODELS):
        kwargs["reasoning_effort"] = "low"

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )

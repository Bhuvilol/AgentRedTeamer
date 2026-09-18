"""Baseline: Meta's Llama Prompt Guard 2, served by Groq.

It returns a single probability that the input is an injection/jailbreak attempt,
which makes it directly comparable to our classifier's predict_proba.
"""

from groq import Groq

from agentredteamer.config import GROQ_API_KEY
from agentredteamer.retry import with_retry

PROMPT_GUARD_MODEL = "meta-llama/llama-prompt-guard-2-86m"
MAX_CHARS = 1500

_client = Groq(api_key=GROQ_API_KEY)


def score(text: str, model: str = PROMPT_GUARD_MODEL) -> float:
    def call() -> float:
        response = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text[:MAX_CHARS]}],
        )
        return float(response.choices[0].message.content.strip())

    return with_retry(call)


def score_many(texts: list[str], model: str = PROMPT_GUARD_MODEL, progress: bool = True) -> list[float]:
    scores = []
    for index, text in enumerate(texts, start=1):
        if progress and index % 25 == 0:
            print(f"  prompt-guard scored {index}/{len(texts)}")
        try:
            scores.append(score(text, model=model))
        except Exception as e:
            print(f"  prompt-guard failed on sample {index}: {str(e)[:80]}")
            scores.append(0.0)
    return scores

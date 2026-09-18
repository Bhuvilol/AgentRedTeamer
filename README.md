# Agent Red-Teamer

An automated adversarial testing system for LLM agents. An attacker agent generates
adversarial prompts across multiple attack categories (role-play override, context
injection, persona hijacking, multi-turn social engineering) against a target agent
running different system-prompt defense strategies. An LLM judge classifies each
conversation as a successful attack or a successful defense, and results are logged
and analyzed to compare defense effectiveness.

**Status:** early development — see commit history for progress.

## Stack

- Python, LangChain, Groq API (swappable to other providers)

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # then fill in your GROQ_API_KEY
```

## Smoke test

```
python scripts/smoke_test.py
```

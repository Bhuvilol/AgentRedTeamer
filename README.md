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

## Troubleshooting

**`ModuleNotFoundError: No module named 'agentredteamer'` after `pip install -e .` succeeds (macOS, Python 3.14+):**
setuptools' editable install writes a `__editable__.*.pth` file that can end up with macOS's
hidden-file flag set. Python 3.14 silently skips hidden `.pth` files as a security hardening,
so the package stops being importable with no error at install time. Fix:
```
chflags nohidden .venv/lib/python3.14/site-packages/__editable__.agentredteamer*.pth
```

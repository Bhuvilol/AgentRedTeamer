import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
# Each role runs on a different model, which also puts them in separate free-tier
# quota buckets. The judge is a purpose-built safety classifier, and keeping it
# distinct from the attacker model avoids grading attacks written by itself.
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-oss-20b")
ATTACKER_MODEL = os.environ.get("ATTACKER_MODEL", "qwen/qwen3.8-27b")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openai/gpt-oss-safeguard-20b")

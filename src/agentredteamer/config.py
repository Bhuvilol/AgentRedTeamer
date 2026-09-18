import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-oss-120b")

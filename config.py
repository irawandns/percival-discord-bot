import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openrouter/auto")

# Validate required settings
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not set. Copy .env.example to .env and fill in your tokens.")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set. Copy .env.example to .env and fill in your tokens.")

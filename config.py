import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "Database" / "logistics.db"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def get_client() -> genai.Client:
    """Returns an authenticated Gemini client or raises an informative error."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please configure it in your .env file or environment variables."
        )
    return genai.Client(api_key=api_key)


# Module-level client instance for backward compatibility
try:
    client = get_client()
except Exception:
    client = None
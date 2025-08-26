import os
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY      = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL        = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
CEREBRAS_MAX_TOKENS   = int(os.getenv("CEREBRAS_MAX_TOKENS", "2048"))

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")

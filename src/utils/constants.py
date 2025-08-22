import os

CEREBRAS_API_KEY      = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL        = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
CEREBRAS_MAX_TOKENS   = int(os.getenv("CEREBRAS_MAX_TOKENS", "2048"))

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

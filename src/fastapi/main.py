import os
import json
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from dotenv import load_dotenv
from github_client import verify_github_signature
from utils.constants import CEREBRAS_MODEL, GITHUB_WEBHOOK_SECRET
from letta.pr_reviewer import EVENT_HANDLERS

load_dotenv()  # Load variables from .env if present

app = FastAPI(title="PR Review Bot", version="1.1.0")

# Configuration


@app.post("/app-webhook", tags=["GitHub App"])
async def github_app_webhook_handler(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event")
):
    """Handle GitHub App webhook events"""

    payload_body = await request.body()

    # Verify signature
    if not verify_github_signature(payload_body, x_hub_signature_256 or "", GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Invalid signature for App webhook")

    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    print(f"Received App event: {x_github_event}, action: {payload.get('action', 'unknown')}")

    if x_github_event == "ping":
        print("Received ping event from GitHub App")
        return {"message": "Pong! App webhook is working"}

    if x_github_event == None:
        print("Received event with no event type")
        return {"message": "App webhook received"}

    handler = EVENT_HANDLERS.get(x_github_event, "")
    if handler:
        print(f"Calling handler for event: {x_github_event}")
        await handler(payload)
    else:
        print(f"Received unhandled App event: {x_github_event} (no handler registered)")
    return {"message": "App webhook received"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "PR Review Bot is running"}

@app.get("/status", tags=["Health"])
async def status():
    """Status endpoint with more details"""
    return {
        "status": "running",
        "webhook_secret_configured": bool(GITHUB_WEBHOOK_SECRET),
        "model_provider": "cerebras",
        "model": CEREBRAS_MODEL,
        "endpoints": {
            "legacy_webhook": "/webhook",
            "app_webhook": "/app-webhook",
            "health": "/",
            "status": "/status"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
import json
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="PR Review Bot Webhook", version="1.0.0")

# Configuration
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

def verify_github_signature(payload_body: bytes, signature: str) -> bool:
    """Verify the GitHub webhook signature"""
    if not GITHUB_WEBHOOK_SECRET:
        print("WARNING: No webhook secret set, skipping verification")
        return True
    
    if not signature or not signature.startswith('sha256='):
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@app.post("/webhook")
async def github_webhook_handler(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event")
):
    """Handle GitHub webhook events"""
    
    # Get the raw payload
    payload_body = await request.body()
    
    # Verify signature if secret is set
    if GITHUB_WEBHOOK_SECRET and not verify_github_signature(payload_body, x_hub_signature_256 or ""):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Handle PR events
    if x_github_event == "pull_request":
        action = payload.get("action", "")
        
        if action in ["opened", "synchronize", "reopened"]:
            await handle_pr_event(payload)
        else:
            print(f"Ignored PR action: {action}")
    
    elif x_github_event == "ping":
        print("Received ping event from GitHub")
        return {"message": "Pong! Webhook is working"}
    
    else:
        print(f"Received unhandled event: {x_github_event}")
    
    return {"message": "Webhook received"}

async def handle_pr_event(payload):
    """Handle PR opened/updated events"""
    pr = payload["pull_request"]
    repo = payload["repository"]
    action = payload["action"]
    
    print(f"\n🔄 PR Event Received:")
    print(f"   Action: {action}")
    print(f"   Repository: {repo['full_name']}")
    print(f"   PR #: {pr['number']}")
    print(f"   Title: {pr['title']}")
    print(f"   Author: {pr['user']['login']}")
    print(f"   Branch: {pr['head']['ref']} -> {pr['base']['ref']}")
    
    # TODO: Add your PR analysis logic here
    print("   Status: Ready for analysis (analysis logic not implemented yet)")

@app.get("/")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "PR Review Bot Webhook is running"}

@app.get("/status")
async def status():
    """Status endpoint with more details"""
    return {
        "status": "running",
        "webhook_secret_configured": bool(GITHUB_WEBHOOK_SECRET),
        "endpoints": {
            "webhook": "/webhook",
            "health": "/",
            "status": "/status"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
import json
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if present

app = FastAPI(title="PR Review Bot Webhook", version="1.0.0")

# Configuration
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


# Cerebras configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")
CEREBRAS_MAX_TOKENS = int(os.getenv("CEREBRAS_MAX_TOKENS", "2048"))

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
    
    # Fetch changed files and patches
    owner, repo_name = repo['full_name'].split('/')
    pr_number = pr['number']
    files = fetch_pr_changed_files(owner, repo_name, pr_number)

    if not files:
        print("   No changed files found or GitHub API access not configured")
        return

    # Build prompt for the LLM
    prompt = build_review_prompt(
        repository_full_name=repo['full_name'],
        pr_title=pr['title'],
        pr_author=pr['user']['login'],
        head_branch=pr['head']['ref'],
        base_branch=pr['base']['ref'],
        changed_files=files,
    )

    # Call Cerebras to get review text
    review_text = call_cerebras_for_review(prompt)

    if not review_text:
        print("   LLM review skipped (missing credentials or request failed)")
        return

    # Post the review as a PR comment
    posted = post_pr_comment(owner, repo_name, pr_number, review_text)
    if posted:
        print("   ✅ Posted PR review comment via GitHub API")
    else:
        print("   ⚠️ Could not post PR comment (missing GITHUB_TOKEN or API error). Review output:")
        print(review_text)

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
        "model_provider": "cerebras",
        "model": CEREBRAS_MODEL,
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


# --------- Helper functions for PR analysis and LLM integration ---------

def fetch_pr_changed_files(owner: str, repo_name: str, pr_number: int, max_files: int = 15) -> List[dict]:
    """Fetch changed files for a PR including patches. Requires GITHUB_TOKEN.

    Returns a list of dicts with keys: filename, status, additions, deletions, changes, patch (optional)
    """
    if not GITHUB_TOKEN:
        return []

    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pr-review-bot",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"   ⚠️ GitHub API error: {response.status_code} {response.text[:200]}")
            return []
        files = response.json()
        # Keep it small for prompting
        return files[:max_files]
    except requests.RequestException as exc:
        print(f"   ⚠️ Failed to fetch PR files: {exc}")
        return []


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n[...truncated...]\n"


def build_review_prompt(
    repository_full_name: str,
    pr_title: str,
    pr_author: str,
    head_branch: str,
    base_branch: str,
    changed_files: List[dict],
    max_total_patch_chars: int = 30_000,
) -> str:
    """Construct a concise prompt with limited diffs for the LLM."""
    header = (
        f"Repository: {repository_full_name}\n"
        f"PR Title: {pr_title}\n"
        f"Author: {pr_author}\n"
        f"Branches: {head_branch} -> {base_branch}\n"
        f"Files changed: {len(changed_files)}\n\n"
    )

    parts: List[str] = [header, "Diffs (unified patches, truncated):\n"]
    accumulated = 0
    for file_info in changed_files:
        filename = file_info.get("filename", "<unknown>")
        patch = file_info.get("patch", "")
        status = file_info.get("status", "modified")
        file_header = f"\n--- {filename} ({status}) ---\n"
        if not patch:
            parts.append(file_header + "(no patch available)\n")
            continue
        remaining = max_total_patch_chars - accumulated
        if remaining <= 0:
            parts.append("\n[Diff budget exhausted]\n")
            break
        patch_text = truncate_text(patch, min(remaining, 5_000))
        parts.append(file_header + patch_text)
        accumulated += len(patch_text)

    parts.append(
        "\nTask: Provide a thorough but concise code review.\n"
        "- Identify bugs, security issues, and performance concerns.\n"
        "- Flag missing tests, edge cases, and unclear naming.\n"
        "- Suggest concrete improvements with examples.\n"
        "- Use short sections with bullets.\n"
    )

    return "".join(parts)

def call_cerebras_for_review(prompt: str) -> str:
    """Call Cerebras chat completions and return combined text."""
    if not CEREBRAS_API_KEY:
        return ""
    try:
        from cerebras.cloud.sdk import Cerebras
    except Exception:
        return ""

    system_prompt = (
        "You are an expert software reviewer. Be precise, pragmatic, and actionable. "
        "Prefer specific code suggestions over generalities."
    )

    try:
        client = Cerebras(api_key=CEREBRAS_API_KEY)
        stream = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=CEREBRAS_MODEL,
            stream=True,
            max_completion_tokens=CEREBRAS_MAX_TOKENS,
            temperature=0.2,
            top_p=1,
        )
        pieces: list[str] = []
        for chunk in stream:
            try:
                delta = chunk.choices[0].delta
                piece = (
                    getattr(delta, "content", None)
                    or getattr(delta, "reasoning", None)
                    or ""
                )
            except Exception:
                piece = ""
            if piece:
                pieces.append(piece)
        return "".join(pieces).strip()
    except Exception as exc:
        print(f"   ⚠️ Failed to call Cerebras: {exc}")
        return ""

def post_pr_comment(owner: str, repo_name: str, pr_number: int, body: str) -> bool:
    """Post a comment to the PR using the Issues comments endpoint. Requires GITHUB_TOKEN."""
    if not GITHUB_TOKEN:
        return False
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pr-review-bot",
    }
    try:
        response = requests.post(url, headers=headers, json={"body": body}, timeout=30)
        if response.status_code in (200, 201):
            return True
        print(f"   ⚠️ GitHub API comment error: {response.status_code} {response.text[:200]}")
        return False
    except requests.RequestException as exc:
        print(f"   ⚠️ Failed to post PR comment: {exc}")
        return False

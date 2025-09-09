# A client for interacting
import os
import sys
import re
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from letta_client import Letta
import requests

from github_client import get_installation_access_token
from utils.constants import CEREBRAS_API_KEY, CEREBRAS_MODEL, CEREBRAS_MAX_TOKENS
from .prompts import build_review_prompt, build_pr_comment_prompt
from .memory_manager import MemoryManager

load_dotenv()
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
AGENT_ID = "agent-72b0ecc4-bd82-4776-880c-33a24b41f13e"


# Use default project instead of "Toph" to avoid project not found error
client = Letta(token=LETTA_API_KEY)
memory_manager = MemoryManager(client, AGENT_ID)

def get_user_memory_blocks(user_id: str):
    memory_blocks = []
    all_memory_blocks = client.blocks.list()
    for memory_block in all_memory_blocks:
        if memory_block.label.startswith(user_id):
            memory_blocks.append(memory_block)
    return memory_blocks

async def handle_pull_request_event(payload: dict):
    """Handles 'pull_request' events."""
    action = payload.get("action", "")
    if action in ["opened", "synchronize", "reopened"]:
        print(f"Handling pull_request.{action} event.")
        repo = payload.get("repository", {})
        pr_title = payload.get("pull_request", {}).get("title")
        pr_number = payload.get("pull_request", {}).get("number")
        installation_id = payload.get("installation", {}).get("id")
        app_token = get_installation_access_token(installation_id)
        pr_author = payload.get("pull_request", {}).get("user", {}).get("login")
        head_branch = payload.get("pull_request", {}).get("head", {}).get("ref")
        base_branch = payload.get("pull_request", {}).get("base", {}).get("ref")
        num_changed_files = payload.get("pull_request", {}).get("changed_files")
        owner, repo_name = repo['full_name'].split('/')


        # Use review prompt for full PR reviews (not comments)
        changed_files = fetch_pr_changed_files(owner, repo_name, pr_number, app_token)
        prompt = build_review_prompt(repo.get("full_name", ""), pr_title, pr_author, head_branch, base_branch, changed_files)
        response = await handle_pr_event(payload, prompt) # Your existing detailed handler
        if response:
            post_pr_comment(owner, repo_name, pr_number, response, app_token)
        else:
            post_pr_comment(owner, repo_name, pr_number, "⚠️ No response generated", app_token)
    else:
        print(f"Ignored PR action: {action}")

async def handle_pr_comment_event(payload: dict):
    """Handles 'issue_comment' events with command-based memory system."""
    print("PAYLOAD: ", payload)
    action = payload.get("action", "")
    comment_body = payload.get("comment", {}).get("body", "")
    commenter = payload.get("comment", {}).get("user", {}).get("login", "user")

    if action == "created":
        # Detect command in comment
        command = memory_manager.detect_command(comment_body)
        await command_router(payload, command)
        print(f"Handling mention in issue comment from {commenter}.")

async def handle_push_event(payload: dict):
    """Handles 'push' events."""
    ref = payload.get("ref", "")
    if ref == "refs/heads/main":
        print("Handling push to main branch.")
        # Add your logic here for what to do on a push to main.
        # For example, trigger a deployment, run tests, etc.
    else:
        print(f"Ignored push to ref: {ref}")

async def handle_pr_event(payload, prompt):
    """Handle PR opened/updated events from webhooks or the App"""
    pr = payload.get("pull_request")
    if not pr:
        print("⚠️ Missing pull_request data in payload")
        return

    repo = payload.get("repository")
    if not repo:
        print("⚠️ Missing repository data in payload")
        return

    action = payload.get("action", "unknown")
    user_query = payload.get("user_query", "")
    commenter = payload.get("commenter", "")

    installation_id = payload.get("installation", {}).get("id")
    try:
        # Generate a temporary token for this specific installation
        app_token = get_installation_access_token(installation_id)
    except Exception:
        print("⚠️ Could not get installation access token: {e}")
        return

    print("\n🔄 PR Event Received:")
    print(f"   Action: {action}")
    print(f"   Repository: {repo['full_name']}")
    print(f"   PR #: {pr['number']}")
    print(f"   Title: {pr['title']}")
    print(f"   Author: {pr['user']['login']}")
    print(f"   Branch: {pr['head']['ref']} -> {pr['base']['ref']}")
    if user_query:
        print(f"   User Query: {user_query}")
        print(f"   Commenter: {commenter}")

    # Fetch changed files and patches
    owner, repo_name = repo['full_name'].split('/')
    pr_number = pr['number']
    files = fetch_pr_changed_files(owner, repo_name, pr_number, app_token)

    if not files:
        print("   No changed files found or GitHub API access not configured")
        return

    # Call Cerebras to get review text
    review_text = call_cerebras_for_review(prompt, owner)

    if not review_text:
        print("   LLM review skipped (missing credentials or request failed)")
        return
    return review_text

def call_cerebras_for_review(prompt: str, user_id: str) -> str:
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
        user_memory_blocks = get_user_memory_blocks(user_id)
        for memory_block in user_memory_blocks:
            client.agents.blocks.attach(agent_id=AGENT_ID, block_id=memory_block.id)
        response = client.agents.messages.create(
            agent_id = AGENT_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        response_chunks = []
        for message in response.messages:
            if message.message_type == "assistant_message":
                response_chunks.append(message.content)
        return "".join(response_chunks).strip()
    except Exception as exc:
        print(f"   ⚠️ Failed to call Cerebras: {exc}")
        return ""

def post_pr_comment(owner: str, repo_name: str, pr_number: int, body: str, token: str) -> bool:
    """Post a comment to the PR using the Issues comments endpoint. Requires GITHUB_TOKEN."""
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
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

def fetch_pr_changed_files(owner: str, repo_name: str, pr_number: int, token: str, max_files: int = 15) -> List[dict]:
    """Fetch changed files for a PR including patches. Requires GITHUB_TOKEN.

    Returns a list of dicts with keys: filename, status, additions, deletions, changes, patch (optional)
    """

    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
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




async def handle_installation_event(payload):
    """Handle installation events for the GitHub App"""
    action = payload.get("action")
    installation = payload.get("installation", {})
    repos = payload.get("repositories", [])
    requester = payload.get("requester", {})

    print(f"App installation event:")
    print(f"  Action: {action}")
    print(f"  Installation ID: {installation.get('id')}")
    print(f"  App ID: {installation.get('app_id')}")
    print(f"  Target: {installation.get('target_type')} ({installation.get('target_id')})")
    print(f"  Account: {installation.get('account', {}).get('login')}")
    if requester:
        print(f"  Requested by: {requester.get('login')}")

    if action == "created":
        print(f"  ✅ App installed on {len(repos)} repositories:")
        for repo in repos:
            print(f"    - {repo['full_name']}")

    elif action == "deleted":
        print(f"  🗑️ App uninstalled")
    elif action == "suspend":
        print(f"  ⏸️ App suspended")
    elif action == "unsuspend":
        print(f"  ▶️ App unsuspended")

async def command_router(payload, command):
    installation_id = payload.get("installation", {}).get("id")
    app_token       = get_installation_access_token(installation_id)
    response        = await memory_manager.handle_init_command(payload)
    owner           = payload.get("repository", {}).get("owner", {}).get("login")
    repo_name       = payload.get("repository", {}).get("name")
    response        = None
    match command:
        case "init":
            response = await memory_manager.handle_init_command(payload)
        case "configure":
            response = await memory_manager.handle_configure_command(payload)
        case "interact":
            response = await memory_manager.handle_interaction_command(payload)
        case _:
            issue = payload.get("issue", {})
            repository = payload.get("repository", {})
            pr_title = payload.get("title", "")
            pr_author = payload.get("user", {}).get("login", "")
            head_branch = payload.get("head", {}).get("ref", "")
            base_branch = payload.get("base", {}).get("ref", "")
            pr_url = issue.get("pull_request", {}).get("url")
            comment_body = payload.get("comment", {}).get("body", "")
            if pr_url and comment_body.startswith("@toph-bot"):
                commenter = payload.get("comment", {}).get("user", {}).get("login", "user")
                user_query = comment_body.replace("@toph-bot", "").replace("@Toph", "").strip()
                if not user_query:
                    user_query = "Please provide information about this PR."

                # Fetch the full PR object so handle_pr_event has the 'pull_request' key it needs
                headers = {
                    "Authorization": f"Bearer {app_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "pr-review-bot",
                }
                try:
                    pr_resp = requests.get(pr_url, headers=headers, timeout=30)
                    if pr_resp.status_code != 200:
                        print(f"   ⚠️ Failed to fetch PR data: {pr_resp.status_code} {pr_resp.text[:200]}")
                        return
                    pr_data = pr_resp.json()
                except requests.RequestException as exc:
                    print(f"   ⚠️ Exception fetching PR data: {exc}")
                    return

                # Create a payload structure similar to a pull_request event
                pr_payload = {
                    "action": "commented",
                    "pull_request": pr_data,
                    "repository": repository,
                    "installation": payload.get("installation"),
                    "user_query": user_query,
                    "commenter": commenter
                }

                # Fetch changed files first
                owner = repository.get("owner", {}).get("login", "")
                repo_name = repository.get("name", "")
                pr_number = issue.get("number")
                installation_id = payload.get("installation", {}).get("id")
                app_token = get_installation_access_token(installation_id)
                changed_files = fetch_pr_changed_files(owner, repo_name, pr_number, app_token)

                repo_full_name = repository.get("full_name", "")
                prompt = build_pr_comment_prompt(repo_full_name, pr_title, pr_author, head_branch, base_branch, changed_files, user_query)
                response = await handle_pr_event(pr_payload, prompt)

    issue_number = payload.get("issue", {}).get("number")
    if issue_number and response is not None:
        posted = post_pr_comment(owner, repo_name, issue_number, response, app_token)
        if posted:
            print("✅ Posted initialization response")
        else:
            print("⚠️ Failed to post initialization response")
    return


EVENT_HANDLERS = {
    "pull_request": handle_pull_request_event,
    # "pull_request_review_comment": handle_pr_comment_event,
    "issue_comment": handle_pr_comment_event,
    "push": handle_push_event,
    "installation": handle_installation_event,
}

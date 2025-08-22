# A client for interacting
import os
from typing import List
from dotenv import load_dotenv
from letta_client import Letta
import requests
from ..github_client import get_installation_access_token
from utils.constants import CEREBRAS_API_KEY, CEREBRAS_MODEL, CEREBRAS_MAX_TOKENS

load_dotenv()
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
AGENT_ID = "agent-0042f472-b5a4-452f-8be1-d69f0cb91d22"


client = Letta(token=LETTA_API_KEY, project="Toph")

def get_letta_agent(user_id: str):
    agent = client.agents.retrieve(agent_id=AGENT_ID)
    all_memory_blocks = client.blocks.list()
    for memory_block in all_memory_blocks:
        if memory_block.label.startswith(user_id):
            agent.blocks.attach(agent_id=AGENT_ID, block_id=memory_block.id)

    return agent

def create_memory_block(value: str, user_id: str):
    client.blocks.create(value=value, label=f"{user_id}_memory_block")

def cleanup_agent_memory_blocks(user_id: str):
    blocks = client.agents.blocks.list(agent_id=AGENT_ID)
    for block in blocks:
        if block.label.startswith(user_id):
            client.agents.block.detach(
                agent_id=AGENT_ID,
                block_id=block.id
            )

async def handle_pull_request_event(payload: dict):
    """Handles 'pull_request' events."""
    action = payload.get("action", "")
    if action in ["opened", "synchronize", "reopened"]:
        print(f"Handling pull_request.{action} event.")
        await handle_pr_event(payload) # Your existing detailed handler
    else:
        print(f"Ignored PR action: {action}")

async def handle_issue_comment_event(payload: dict):
    """Handles 'issue_comment' events."""
    action = payload.get("action", "")
    comment_body = payload.get("comment", {}).get("body", "")

    if action == "created" and "@toph" in comment_body.lower(): # Case-insensitive check
        print("Handling mention in issue comment.")
        # Add your logic here. For example, you could re-run a review.
        # issue = payload.get("issue", {})
        # owner = payload.get("repository", {}).get("owner", {}).get("login")
        # repo_name = payload.get("repository", {}).get("name")
        # if "pull_request" in issue:
        #     await handle_pr_event(payload) # Example: re-trigger review
    else:
        print(f"Ignored issue_comment action: {action}")

async def handle_push_event(payload: dict):
    """Handles 'push' events."""
    ref = payload.get("ref", "")
    if ref == "refs/heads/main":
        print("Handling push to main branch.")
        # Add your logic here for what to do on a push to main.
        # For example, trigger a deployment, run tests, etc.
    else:
        print(f"Ignored push to ref: {ref}")

async def handle_pr_event(payload):
    """Handle PR opened/updated events from webhooks or the App"""
    pr = payload["pull_request"]
    repo = payload["repository"]
    action = payload["action"]

    installation_id = payload.get("installation", {}).get("id")
    try:
        # Generate a temporary token for this specific installation
        app_token = get_installation_access_token(installation_id)
    except Exception as e:
        print(f"   ⚠️ Could not get installation access token: {e}")
        return

    print("\n🔄 PR Event Received:")
    print(f"   Action: {action}")
    print(f"   Repository: {repo['full_name']}")
    print(f"   PR #: {pr['number']}")
    print(f"   Title: {pr['title']}")
    print(f"   Author: {pr['user']['login']}")
    print(f"   Branch: {pr['head']['ref']} -> {pr['base']['ref']}")

    # Fetch changed files and patches
    owner, repo_name = repo['full_name'].split('/')
    pr_number = pr['number']
    files = fetch_pr_changed_files(owner, repo_name, pr_number, app_token)

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
    posted = post_pr_comment(owner, repo_name, pr_number, review_text, app_token)
    if posted:
        print("   ✅ Posted PR review comment via GitHub API")
    else:
        print("   ⚠️ Could not post PR comment (missing GITHUB_TOKEN or API error). Review output:")
        print(review_text)

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


def build_review_prompt(
    repository_full_name: str,
    pr_title: str,
    pr_author: str,
    head_branch: str,
    base_branch: str,
    changed_files: List[dict],
    max_total_patch_chars: int = 30_000,
) -> str:
    """Construct a detailed, educational, and actionable review prompt for the LLM."""
    header = (
        f"Repository: {repository_full_name}\n"
        f"PR Title: {pr_title}\n"
        f"Author: {pr_author}\n"
        f"Branches: {head_branch} -> {base_branch}\n"
        f"Files changed: {len(changed_files)}\n\n"
    )

    parts: List[str] = [header, "## Code Diff to Review\n"]
    accumulated = 0
    for file_info in changed_files:
        filename = file_info.get("filename", "<unknown>")
        patch = file_info.get("patch", "")
        if not patch:
            continue # Skip files with no diff content (e.g., binary files)

        file_header = f"### File: `{filename}`\n```diff\n{patch}\n```\n"

        # Truncate the patch if it's too long to avoid exhausting the budget on one file
        remaining = max_total_patch_chars - accumulated
        if remaining <= 0:
            parts.append("\n[Diff budget exhausted, subsequent files omitted.]\n")
            break

        if len(file_header) > remaining:
            # A simplified truncation for the oversized patch
            truncated_patch = patch[:remaining - 150] + "\n... (truncated)\n"
            file_header = f"### File: `{filename}`\n```diff\n{truncated_patch}\n```\n"

        parts.append(file_header)
        accumulated += len(file_header)

    # --- START OF THE IMPROVED PROMPT INSTRUCTIONS ---
    instructions = """
## Review Task

You are a senior software engineer performing a code review. Your tone should be helpful, respectful, and educational. You are reviewing a pull request from a junior engineer, so your main goal is to help them learn and improve.

### Your Directives:
1.  **Prioritize High-Impact Feedback:** Focus on logic errors, potential bugs, security vulnerabilities, performance issues, and architectural improvements.
2.  **Explain the "Why":** For each point of feedback, briefly explain *why* it's important. Link your suggestions to principles like readability, maintainability, or security. This is crucial for learning.
3.  **Provide Actionable Code Snippets:** When suggesting a change, provide a concise code example of how to implement it correctly.
4.  **Ignore Trivial Nitpicks:** Do **not** comment on minor stylistic issues like whitespace, import order, or missing commas that a linter or code formatter would catch automatically.
5.  **Acknowledge Good Work:** If you see something done well (e.g., good test coverage, a clever solution), mention it briefly. This encourages good habits.

### Required Output Format:
Provide your review in Markdown. Adhere strictly to this structure:

**### High-Level Summary**
(Provide a brief, one-paragraph summary of the pull request and your overall impression.)

**### Actionable Feedback**
(List your main points here. If there are no major issues, state "No major issues found.")
*   **File:** `path/to/file.py`
    *   **Concern:** (Briefly describe the potential issue.)
    *   **Suggestion:** (Provide a clear, corrected code snippet.)
    *   **Reasoning:** (Explain why the suggestion is an improvement.)

*   **File:** `path/to/another_file.js`
    *   **Concern:** ...

**### Positive Reinforcement**
(Mention one or two things that were done well. If none, omit this section.)
*   👍 I appreciate the clear variable naming in the `calculate_totals` function. It makes the logic easy to follow.
"""
    parts.append(instructions)
    # --- END OF THE IMPROVED PROMPT INSTRUCTIONS ---

    return "".join(parts)


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

EVENT_HANDLERS = {
    "pull_request": handle_pull_request_event,
    "issue_comment": handle_issue_comment_event,
    "push": handle_push_event,
    "installation": handle_installation_event,
}

# A client for interacting
import os
from typing import List
from dotenv import load_dotenv
from letta_client import Letta
import requests
from github_client import get_installation_access_token
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
        repo = payload.get("repository", {})
        pr_title = payload.get("pull_request", {}).get("title")
        pr_author = payload.get("pull_request", {}).get("user", {}).get("login")
        head_branch = payload.get("pull_request", {}).get("head", {}).get("ref")
        base_branch = payload.get("pull_request", {}).get("base", {}).get("ref")
        changed_files = payload.get("pull_request", {}).get("changed_files")

        prompt = build_pr_comment_prompt(repo, pr_title, pr_author, head_branch, base_branch, changed_files)
        await handle_pr_event(payload, prompt) # Your existing detailed handler
    else:
        print(f"Ignored PR action: {action}")

async def handle_pr_comment_event(payload: dict):
    """Handles 'issue_comment' events."""
    action = payload.get("action", "")
    comment_body = payload.get("comment", {}).get("body", "")
    commenter = payload.get("comment", {}).get("user", {}).get("login", "user")

    if action == "created" and "@toph-bot" in comment_body.lower(): # Case-insensitive check
        print(f"Handling mention in issue comment from {commenter}.")
        issue = payload.get("issue", {})
        owner = payload.get("repository", {}).get("owner", {}).get("login")
        repo_name = payload.get("repository", {}).get("name")

        # Extract the actual question/request by removing the @toph mention
        user_query = comment_body.replace("@toph-bot", "").replace("@Toph", "").strip()
        if not user_query:
            user_query = "Please provide information about this PR."

        if "pull_request" in issue:
            print(f"Processing conversation request from PR comment with @toph mention")
            # Fetch PR data before handling the event
            try:
                pr_url = issue.get("pull_request", {}).get("url")
                if pr_url:
                    installation_id = payload.get("installation", {}).get("id")
                    app_token = get_installation_access_token(installation_id)

                    headers = {
                        "Authorization": f"Bearer {app_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                        "User-Agent": "pr-review-bot",
                    }
                    response = requests.get(pr_url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        repository = payload.get("repository", "")
                        pr_title = payload.get("title", "")
                        pr_author = payload.get("author", "")
                        head_branch = payload.get("head", {}).get("ref")
                        base_branch = payload.get("base", {}).get("ref")
                        changed_files = payload.get("changed_files", [])
                        pr_data = response.json()
                        # Create a payload structure similar to a pull_request event
                        pr_payload = {
                            "action": "commented",
                            "pull_request": pr_data,
                            "repository": repository,
                            "installation": payload.get("installation"),
                            "user_query": user_query,
                            "commenter": commenter
                        }
                        prompt = build_pr_comment_prompt(repository, pr_title, pr_author, head_branch, base_branch, changed_files)
                        await handle_pr_event(pr_payload, prompt)
                    else:
                        print(f"Failed to fetch PR data: {response.status_code}")
                else:
                    print(f"No pull_request URL found in issue payload")
            except Exception as e:
                print(f"Error handling PR comment: {e}")
        else:
            print(f"@toph mentioned in a regular issue (not a PR)")
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

async def handle_pr_event(payload, prompt):
    """Handle PR opened/updated events from webhooks or the App"""
    pr = payload.get("pull_request")
    if not pr:
        print(f"   ⚠️ Missing pull_request data in payload")
        return

    repo = payload.get("repository")
    if not repo:
        print(f"   ⚠️ Missing repository data in payload")
        return

    action = payload.get("action", "unknown")
    user_query = payload.get("user_query", "")
    commenter = payload.get("commenter", "")

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
    """Construct a context-rich prompt for the conversational assistant to answer questions about the PR."""
    header = (
        f"Repository: {repository_full_name}\n"
        f"PR Title: {pr_title}\n"
        f"Author: {pr_author}\n"
        f"Branches: {head_branch} -> {base_branch}\n"
        f"Files changed: {len(changed_files)}\n\n"
    )

    parts: List[str] = [header, "## Code Changes Context\n"]
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
            parts.append("\n[Context budget exhausted, subsequent files omitted.]\n")
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

def build_pr_comment_prompt(
    repository_full_name: str,
    pr_title: str,
    pr_author: str,
    head_branch: str,
    base_branch: str,
    changed_files: List[dict],
    max_total_patch_chars: int = 30_000,
):
    header = (
        f"Repository: {repository_full_name}\n"
        f"PR Title: {pr_title}\n"
        f"Author: {pr_author}\n"
        f"Branches: {head_branch} -> {base_branch}\n"
        f"Files changed: {len(changed_files)}\n\n"
    )

    parts: List[str] = [header, "## Code Diff Context\n"]
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

    # --- START OF THE CONVERSATIONAL BOT INSTRUCTIONS ---
    instructions = """
## Conversational Assistant Role

You are a helpful assistant with knowledge of this pull request. Your purpose is to answer questions and provide information about the PR in a conversational, helpful manner. Use the PR context and code diffs above to inform your responses.

### Guidelines:
1. **Be conversational and friendly** in your responses while maintaining technical accuracy.
2. **Refer to specific code** from the diffs when answering questions about implementation details.
3. **Provide context-aware answers** based on the PR's content, purpose, and changes.
4. **Explain technical concepts** clearly when they're relevant to understanding the PR.
5. **If you don't know something** or if the information isn't in the provided context, acknowledge this honestly.
6. **Answer questions about**:
   - What the PR is trying to accomplish
   - How specific code changes work
   - The purpose of new functions or modifications
   - Potential implications of the changes
   - Technical concepts related to the code

The user will ask you questions about this pull request, and your job is to provide helpful, informative responses using the context provided above.
"""
    parts.append(instructions)
    # --- END OF THE CONVERSATIONAL BOT INSTRUCTIONS ---

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
    "pull_request_review_comment": handle_pr_comment_event,
    "issue_comment": handle_pr_comment_event,
    "push": handle_push_event,
    "installation": handle_installation_event,
}

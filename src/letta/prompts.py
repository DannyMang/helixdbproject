from typing import List

# Review prompt instructions
REVIEW_INSTRUCTIONS = """
## Review Task

You are a senior software engineer performing a code review. Your tone should be helpful, respectful, and educational. You are reviewing a pull request from a junior engineer, so your main goal is to help them learn and improve.
Feel free to nitpick things like syntax, naming, structure, and best practices. Be thorough and constructive. The goal is to improve the code being written.

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

# Conversational comment instructions (much shorter responses)
COMMENT_INSTRUCTIONS = """
## Conversational Assistant Role

You are a helpful assistant with knowledge of this pull request.

### IMPORTANT: Response Rules
1. **First, determine if the user's question is relevant to this PR or code review**
2. **If IRRELEVANT** (like "hello", "what's the weather", "tell me a joke", random chit-chat):
   - Respond with EXACTLY ONE funny, short sentence (10-15 words max)
   - Include an emoji
   - Gently redirect to PR topics
   - Examples: "🤖 I review code, not weather reports - got PR questions?"

3. **If RELEVANT** to the PR/code:
   - Give SHORT, CONCISE responses - maximum 2-3 sentences
   - Be brief and friendly
   - Answer the specific question without unnecessary detail
   - Reference specific code only when directly relevant

### Guidelines:
- **Be brief and friendly** - aim for 1-2 sentences when possible
- **If you don't know**, say so in one sentence
- Keep responses SHORT and to the point

The user will ask you questions about this pull request.
"""

# Funny responses for irrelevant comments
IRRELEVANT_RESPONSES = [
    "🤔 I'm a code reviewer, not a mind reader - try asking about the actual PR!",
    "🎯 That's about as relevant to this PR as a chocolate teapot!",
    "🤖 ERROR 404: Relevance not found. Try asking about the code?",
    "📝 I review code, not... whatever that was. Got any PR questions?",
    "🎪 Nice try, but I'm here for the code circus, not this sideshow!",
    "🔍 I can analyze code, but I can't make sense of that. PR questions only!",
    "🎲 Rolling for comprehension... critical fail! Ask about the code instead?",
    "🚀 Houston, we have a problem - that question is lost in space. Try PR-related queries!"
]

def get_random_irrelevant_response() -> str:
    """Get a random funny response for irrelevant comments"""
    import random
    return random.choice(IRRELEVANT_RESPONSES)

def build_review_prompt(
    repository_full_name: str,
    pr_title: str,
    pr_author: str,
    head_branch: str,
    base_branch: str,
    changed_files: List[dict],
    max_total_patch_chars: int = 30_000,
) -> str:
    """Construct a context-rich prompt for PR review."""
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

    parts.append(REVIEW_INSTRUCTIONS)
    return "".join(parts)

def build_pr_comment_prompt(
    repository_full_name: str,
    pr_title: str,
    pr_author: str,
    head_branch: str,
    base_branch: str,
    changed_files: List[dict],
    user_query: str = "",
    max_total_patch_chars: int = 15_000,  # Smaller for comments
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

    parts.append(COMMENT_INSTRUCTIONS)

    # Add the user's specific question
    if user_query:
        parts.append(f"\n## User Question:\n{user_query}\n")

    return "".join(parts)

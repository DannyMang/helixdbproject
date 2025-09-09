"""
Memory Manager for Toph Bot - Handles user preferences per codebase
"""

import logging
from typing import Optional, Dict, Any
from letta_client import Letta
from .preference_extractor import PreferenceExtractor, UserPreferences

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages user preference memory blocks for Toph Bot"""

    def __init__(self, letta_client: Letta, agent_id: str):
        self.client = letta_client
        self.agent_id = agent_id
        self.extractor = PreferenceExtractor()

    # =============================================================================
    # LABEL MANAGEMENT
    # =============================================================================

    def _sanitize_label(self, text: str) -> str:
        """Sanitize text for use in memory block labels"""
        return text.replace("/", "_").replace(":", "_").replace(" ", "_").lower()

    def _create_preference_label(self, user_id: str, repo_full_name: str) -> str:
        """Create a standardized label for user preference blocks"""
        sanitized_repo = self._sanitize_label(repo_full_name)
        return f"{user_id}_{sanitized_repo}_preferences"

    def _create_codebase_label(self, repo_full_name: str) -> str:
        """Create a standardized label for codebase context blocks"""
        sanitized_repo = self._sanitize_label(repo_full_name)
        return f"{sanitized_repo}_codebase_context"

    # =============================================================================
    # COMMAND HANDLING
    # =============================================================================

    def detect_command(self, comment_body: str) -> Optional[str]:
        """Detect bot commands in comment body"""
        comment_lower = comment_body.lower()

        if "@toph-bot/init" in comment_lower:
            return "init"
        elif "@toph-bot/configure" in comment_lower:
            return "configure"
        elif "@toph-bot" in comment_lower:
            return "interact"

        return None

    async def handle_init_command(self, payload: dict) -> str:
        """Handle initialization command"""
        commenter = payload.get("comment", {}).get("user", {}).get("login")
        repo_full_name = payload.get("repository", {}).get("full_name")
        comment_body = payload.get("comment", {}).get("body", "")

        # Check if user already has preferences
        existing_block = await self.find_existing_preference_block(commenter, repo_full_name)
        if existing_block:
            return f"""🔧 **Preferences Already Exist**

You already have preferences set up for `{repo_full_name}`.
Use `@toph-bot/configure` to update them, or let me know if you'd like to reset them completely.

**Current preferences:**
{self._format_preference_summary(existing_block)}
"""

        # Check if preferences are provided in the same comment
        preference_content = self.extractor.extract_preference_content_from_comment(comment_body)

        if preference_content:
            # Process the preferences immediately
            block = await self.update_preference_block(commenter, repo_full_name, preference_content)
            if block:
                summary = self.extractor.extract_preferences_summary(block)
                return f"""✅ **Preferences Initialized Successfully!**

I've created your personalized settings for `{repo_full_name}`.

**What I remember about you:**
{self._format_preference_summary_from_dict(summary)}

You can update these anytime with `@toph-bot/configure` + new preferences!
"""
            else:
                return "❌ Failed to initialize preferences. Please try again."
        else:
            # Prompt user for preferences
            return f"""👋 **Welcome to toph-bot!**

I'd love to learn your preferences for reviewing code in `{repo_full_name}`.
Please reply with your preferences in any of these formats:

**📋 Markdown Format:**
```markdown
## Code Review Preferences
- Review style: thorough|moderate|light
- Focus areas: security, performance, readability
- Communication tone: friendly|professional|direct

## Programming Preferences
- Code style: prefer explicit over implicit
- Testing: require unit tests for business logic
```

**📄 YAML Format:**
```yaml
review_style: thorough
focus_areas: [security, performance, readability]
communication_tone: friendly
code_style:
  explicitness: "prefer explicit over implicit"
  testing: "require unit tests"
```

**📝 Plain Text:**
Just describe your preferences naturally - I'll understand!

*Example: "Please be thorough in reviews, focus on security and performance, and use a friendly tone."*
"""

    async def handle_configure_command(self, payload: dict) -> str:
        """Handle configuration update command"""
        commenter = payload.get("comment", {}).get("user", {}).get("login")
        repo_full_name = payload.get("repository", {}).get("full_name")
        comment_body = payload.get("comment", {}).get("body", "")

        # Extract preference content
        preference_content = self.extractor.extract_preference_content_from_comment(comment_body)

        if not preference_content:
            return f"""🔧 **Configure Your Preferences**

Please provide your updated preferences in the same comment.
I support Markdown, plain text formats.

**Current preferences for `{repo_full_name}`:**
{await self._get_current_preferences_summary(commenter, repo_full_name)}

*Reply with your new preferences to update them.*
"""

        # Get current preferences for comparison
        old_summary = await self._get_current_preferences_summary(commenter, repo_full_name)

        # Update preferences
        block = await self.update_preference_block(commenter, repo_full_name, preference_content)

        if block:
            new_summary = self.extractor.extract_preferences_summary(block)
            changes = self._detect_preference_changes(old_summary, new_summary)

            return f"""✅ **Preferences Updated Successfully!**

**Changes made:**
{changes}

**Updated preferences for `{repo_full_name}`:**
{self._format_preference_summary_from_dict(new_summary)}
"""
        else:
            return "❌ Failed to update preferences. Please check your format and try again."

    async def handle_interaction_command(self, payload: dict) -> Optional[str]:
        """Handle regular bot interaction, check if initialization is needed"""
        commenter = payload.get("comment", {}).get("user", {}).get("login")
        repo_full_name = payload.get("repository", {}).get("full_name")

        # Check if user has preferences
        existing_block = await self.find_existing_preference_block(commenter, repo_full_name)

        if not existing_block:
            return f"""👋 **Hi there!**

I notice this is our first interaction in `{repo_full_name}`.
To provide you with personalized reviews, I need to learn your preferences first.

Please run `@toph-bot/init` to set up your preferences, then I'll be able to help you!

*This only takes a minute and makes our interactions much more valuable.* 🚀
"""

        # User has preferences, continue with normal interaction
        return None

    # =============================================================================
    # MEMORY BLOCK OPERATIONS
    # =============================================================================

    async def find_or_create_preference_block(self, user_id: str, repo_full_name: str):
        """Find existing preference block or create a default one"""

        preference_label = self._create_preference_label(user_id, repo_full_name)
        logger.info(f"Looking for preference block with label: {preference_label}")

        try:
            # Try to find existing block
            existing_blocks = self.client.blocks.list(label=preference_label)
            logger.info(f"Found {len(existing_blocks)} blocks with label {preference_label}")
            if existing_blocks:
                logger.info(f"Returning existing block with ID: {getattr(existing_blocks[0], 'id', 'unknown_id')}")
                return existing_blocks[0]
        except Exception as e:
            logger.error(f"Error searching for existing block: {str(e)}", exc_info=True)

        # Create default block if none exists
        logger.info(f"No existing block found, generating default preferences")
        default_preferences = self._generate_default_preferences(user_id, repo_full_name)

        try:
            logger.info(f"Creating new block with label: {preference_label}")
            new_block = self.client.blocks.create(
                label=preference_label,
                value=default_preferences,
                description=f"User preferences for {user_id} in {repo_full_name}"
            )
            logger.info(f"Successfully created new block with ID: {getattr(new_block, 'id', 'unknown_id')}")
            return new_block
        except Exception as e:
            logger.error(f"Error creating preference block: {str(e)}", exc_info=True)
            return None

    async def update_preference_block(self, user_id: str, repo_full_name: str, new_preferences: str):
        """Update user preferences from uploaded content"""

        logger.info(f"Starting update_preference_block for user '{user_id}' in repo '{repo_full_name}'")

        logger.info(f"Attempting to find or create preference block")
        block = await self.find_or_create_preference_block(user_id, repo_full_name)
        if not block:
            logger.error("Failed to find or create preference block")
            return None

        logger.info(f"Found/created block: {getattr(block, 'id', 'unknown_id')}")

        # Parse and structure the preferences
        try:
            logger.info(f"Parsing preference content")
            structured_preferences = self.parse_preference_content(new_preferences)
            logger.info(f"Parsed preferences: {structured_preferences}")

            logger.info(f"Formatting preferences for storage")
            formatted_preferences = self._format_preferences_for_storage(
                structured_preferences, user_id, repo_full_name
            )

            # Update block value using modify (not update)
            # updated_block = self.client.blocks.modify(
            #     agent_id=,
            #     value=formatted_preferences
            # )
            logger.info(f"Listing all blocks to find the right one to update")
            blocks = self.client.blocks.list()
            logger.info(f"Found {len(blocks)} total blocks")

            block_found = False
            for block in blocks:
                block_name = block.name or ""
                logger.info(f"Checking block: {block_name} (ID: {getattr(block, 'id', 'unknown')})")

                if block_name.startswith(f"{user_id}_{repo_full_name}"):
                    block_id = block.id or ""
                    logger.info(f"Found matching block with ID: {block_id}")
                    block_found = True

                    logger.info(f"Modifying existing block with ID: {block_id}")
                    updated_block = self.client.blocks.modify(
                        block_id=block_id,
                        value=formatted_preferences
                    )
                    logger.info(f"Block successfully modified: {getattr(updated_block, 'id', 'unknown_id')}")
                    return updated_block

            # make new block if not found
            if not block_found:
                logger.info(f"No matching block found, creating new block with name: {user_id}_{repo_full_name}_preferences")
                new_block = self.client.blocks.create(
                    value=formatted_preferences,
                    name=f"{user_id}_{repo_full_name}_preferences",
                    label="pr_preferences"
                )
                logger.info(f"New block created with ID: {getattr(new_block, 'id', 'unknown_id')}")
                return new_block

        except Exception as e:
            logger.error(f"Error updating preference block: {str(e)}", exc_info=True)
            return None

    def parse_preference_content(self, content: str) -> UserPreferences:
        """Parse user's preference content into structured format using the extractor"""
        return self.extractor.parse_preference_content(content)

    def _format_preferences_for_storage(self, prefs: UserPreferences, user_id: str, repo_full_name: str) -> str:
        """Format preferences into a readable memory block format"""

        return f"""# User Preferences for {user_id} in {repo_full_name}

## Code Review Style
- Review depth: {prefs.review_style}
- Focus areas: {', '.join(prefs.focus_areas)}
- Communication tone: {prefs.communication_tone}
- Detail level: {prefs.detail_level}
- Feedback format: {prefs.feedback_format}

## Programming Preferences
{self._format_dict_section(prefs.code_style_preferences, "Code Style")}

## Testing Preferences
{self._format_dict_section(prefs.testing_preferences, "Testing")}

## Codebase-Specific Context
{self._format_dict_section(prefs.codebase_specific, "Codebase")}

---
Last updated: {self._get_current_timestamp()}
"""

    def _format_dict_section(self, data: Dict[str, Any], section_name: str) -> str:
        """Format a dictionary section for readable storage"""
        if not data:
            return f"- No specific {section_name.lower()} preferences set"

        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"- {key}: {', '.join(map(str, value))}")
            else:
                lines.append(f"- {key}: {value}")

        return "\\n".join(lines)

    def _generate_default_preferences(self, user_id: str, repo_full_name: str) -> str:
        """Generate default preferences for a new user"""
        default_prefs = UserPreferences()
        return self._format_preferences_for_storage(default_prefs, user_id, repo_full_name)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for tracking updates"""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    async def find_or_create_codebase_block(self, repo_full_name: str):
        """Find or create a codebase context block"""

        codebase_label = self._create_codebase_label(repo_full_name)

        try:
            existing_blocks = self.client.blocks.list(label=codebase_label)
            if existing_blocks:
                return existing_blocks[0]
        except Exception as e:
            print(f"Error searching for codebase block: {e}")

        # Create default codebase block
        default_context = f"""# Codebase Context for {repo_full_name}

## Architecture Notes
- Architecture style: (to be learned from interactions)
- Key patterns: (to be identified)
- Technology stack: (to be documented)

## Code Standards
- Coding conventions: (to be learned)
- Testing approach: (to be documented)
- Review process: (to be established)

## Important Files/Directories
- (to be identified through usage)

---
This context block will be automatically updated as I learn more about this codebase.
"""

        try:
            return self.client.blocks.create(
                label=codebase_label,
                value=default_context,
                description=f"Codebase context and patterns for {repo_full_name}"
            )
        except Exception as e:
            print(f"Error creating codebase block: {e}")
            return None

    def extract_preferences_summary(self, preference_block) -> Dict[str, str]:
        """Extract key preferences from a block for confirmation messages"""
        if not preference_block or not preference_block.value:
            return {}

        content = preference_block.value
        summary = {}

        # Extract key information using simple text parsing
        lines = content.split('\\n')
        for line in lines:
            if 'Review depth:' in line:
                summary['review_style'] = line.split(':')[1].strip()
            elif 'Focus areas:' in line:
                summary['focus_areas'] = line.split(':')[1].strip()
            elif 'Communication tone:' in line:
                summary['communication_tone'] = line.split(':')[1].strip()

        return summary

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    async def find_existing_preference_block(self, user_id: str, repo_full_name: str):
        """Find existing preference block without creating a new one"""
        preference_label = self._create_preference_label(user_id, repo_full_name)

        try:
            existing_blocks = self.client.blocks.list(label=preference_label)
            return existing_blocks[0] if existing_blocks else None
        except Exception as e:
            print(f"Error searching for existing block: {e}")
            return None

    def _format_preference_summary(self, preference_block) -> str:
        """Format preference summary for display"""
        if not preference_block or not preference_block.value:
            return "- No preferences found"

        summary = self.extract_preferences_summary(preference_block)
        return self._format_preference_summary_from_dict(summary)

    def _format_preference_summary_from_dict(self, summary: Dict[str, str]) -> str:
        """Format preference summary dictionary for display"""
        if not summary:
            return "- No preferences available"

        lines = []
        for key, value in summary.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"- {formatted_key}: {value}")

        return "\n".join(lines)

    async def _get_current_preferences_summary(self, user_id: str, repo_full_name: str) -> str:
        """Get current preferences summary for a user-repo combination"""
        block = await self.find_existing_preference_block(user_id, repo_full_name)
        if block:
            return self._format_preference_summary(block)
        else:
            return "- No preferences set yet"

    def _detect_preference_changes(self, old_summary: str, new_summary: Dict[str, str]) -> str:
        """Detect and format changes between old and new preferences"""
        if not new_summary:
            return "- No changes detected"

        # Simple change detection - in a real implementation you'd want more sophisticated comparison
        changes = []
        for key, value in new_summary.items():
            formatted_key = key.replace('_', ' ').title()
            changes.append(f"- {formatted_key}: updated to '{value}'")

        return "\n".join(changes) if changes else "- No specific changes detected"

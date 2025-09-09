# bennyPRBot Memory-Based Preference System

## Overview

Design a system where bennyPRBot uses Letta memory blocks to store user preferences per codebase. Each user-codebase combination gets its own memory block that persists across PR interactions.

## Architecture

### 1. Memory Block Structure

```python
# Memory block naming convention: {user_id}_{repo_full_name}_{block_type}
# Example: "octocat_owner/repo_preferences"

class UserPreferenceBlock:
    label: str = f"{user_id}_{repo_full_name}_preferences"
    value: str = """
    # User Preferences for {repo_full_name}
    
    ## Code Review Style
    - Review depth: thorough|moderate|light
    - Focus areas: [security, performance, readability, testing]
    - Comment style: conversational|formal|technical
    
    ## Programming Preferences  
    - Preferred patterns: [patterns from preferences file]
    - Code style: [style preferences]
    - Testing approach: [testing preferences]
    
    ## Communication Style
    - Tone: friendly|professional|direct
    - Level of detail: high|medium|low
    - Feedback format: inline|summary|both
    """
```

### 2. Agent-as-Server Model

```python
# Single agent instance with dynamic memory attachment
class BennyPRBotAgent:
    agent_id: str = "benny-pr-bot-main"
    
    def get_agent_for_context(self, user_id: str, repo_full_name: str):
        """Attach relevant memory blocks for this user-repo context"""
        
        # 1. Load base agent
        agent = client.agents.retrieve(agent_id=self.agent_id)
        
        # 2. Find and attach user-specific memory blocks
        preference_label = f"{user_id}_{repo_full_name}_preferences"
        preference_block = self.find_or_create_preference_block(
            user_id, repo_full_name, preference_label
        )
        
        # 3. Attach codebase-specific context if available
        codebase_label = f"{repo_full_name}_context"
        codebase_block = self.find_codebase_block(codebase_label)
        
        # 4. Return configured agent
        return agent
```

## Implementation

### 1. Preference File Processing

```python
async def handle_preference_file_upload(payload: dict):
    """Handle when user uploads a preferences file via PR comment"""
    
    comment_body = payload.get("comment", {}).get("body", "")
    commenter = payload.get("comment", {}).get("user", {}).get("login")
    repo_full_name = payload.get("repository", {}).get("full_name")
    
    # Check if comment contains preference file
    if "@bennyPRBot setup" in comment_body or has_preference_file_attachment(comment_body):
        
        # 1. Extract preference content from file/comment
        preference_content = extract_preference_content(comment_body, payload)
        
        # 2. Create memory block
        preference_block = await create_user_preference_block(
            user_id=commenter,
            repo_full_name=repo_full_name, 
            preferences=preference_content
        )
        
        # 3. Confirm setup
        setup_message = f"""
        ✅ **Preferences Set Successfully!**
        
        I've created a personalized memory block for you in `{repo_full_name}`.
        Your preferences will now be applied to all PR reviews and interactions.
        
        **What I remember about you:**
        - Review style: {extract_review_style(preference_content)}
        - Focus areas: {extract_focus_areas(preference_content)}
        - Communication tone: {extract_tone(preference_content)}
        
        You can update these anytime by mentioning me with new preferences!
        """
        
        await post_pr_comment(payload, setup_message)
```

### 2. Enhanced Memory Management

```python
class MemoryManager:
    
    async def find_or_create_preference_block(self, user_id: str, repo_full_name: str):
        """Find existing preference block or create default one"""
        
        preference_label = f"{user_id}_{repo_full_name}_preferences"
        
        # Try to find existing block
        existing_blocks = client.blocks.list(label=preference_label)
        if existing_blocks:
            return existing_blocks[0]
        
        # Create default block if none exists
        default_preferences = self.generate_default_preferences(user_id, repo_full_name)
        return client.blocks.create(
            label=preference_label,
            value=default_preferences,
            description=f"User preferences for {user_id} in {repo_full_name}"
        )
    
    async def update_preference_block(self, user_id: str, repo_full_name: str, new_preferences: str):
        """Update user preferences from uploaded file"""
        
        preference_label = f"{user_id}_{repo_full_name}_preferences"
        block = await self.find_or_create_preference_block(user_id, repo_full_name)
        
        # Parse and structure the preferences
        structured_preferences = self.parse_preference_file(new_preferences)
        
        # Update block value
        client.blocks.update(
            block_id=block.id,
            value=structured_preferences
        )
        
        return block
    
    def parse_preference_file(self, content: str) -> str:
        """Parse user's preference file into structured format"""
        
        # Example parsing logic for different file formats
        if content.startswith("```yaml") or content.endswith(".yml"):
            return self.parse_yaml_preferences(content)
        elif content.startswith("```json") or content.endswith(".json"):
            return self.parse_json_preferences(content)
        else:
            return self.parse_text_preferences(content)
```

### 3. Context-Aware Agent Loading

```python
async def get_configured_agent(user_id: str, repo_full_name: str, installation_id: int):
    """Load agent with user-specific and codebase-specific memory blocks"""
    
    memory_manager = MemoryManager()
    
    # 1. Get base agent
    agent = client.agents.retrieve(agent_id=AGENT_ID)
    
    # 2. Load user preferences for this codebase
    preference_block = await memory_manager.find_or_create_preference_block(
        user_id, repo_full_name
    )
    
    # 3. Load codebase-specific context (architecture, patterns, etc.)
    codebase_block = await memory_manager.find_or_create_codebase_block(repo_full_name)
    
    # 4. Attach memory blocks to agent
    client.agents.blocks.attach(agent_id=AGENT_ID, block_id=preference_block.id)
    client.agents.blocks.attach(agent_id=AGENT_ID, block_id=codebase_block.id)
    
    return agent, [preference_block.id, codebase_block.id]

async def cleanup_agent_memory(attached_block_ids: List[str]):
    """Clean up memory blocks after processing"""
    for block_id in attached_block_ids:
        client.agents.blocks.detach(agent_id=AGENT_ID, block_id=block_id)
```

### 4. Updated Event Handlers

```python
async def handle_pr_comment_event(payload: dict):
    """Enhanced comment handler with preference management"""
    
    action = payload.get("action", "")
    comment_body = payload.get("comment", {}).get("body", "")
    commenter = payload.get("comment", {}).get("user", {}).get("login", "user")
    repo_full_name = payload.get("repository", {}).get("full_name")
    
    if action == "created":
        
        # Handle preference setup
        if "@bennyPRBot setup" in comment_body.lower():
            await handle_preference_file_upload(payload)
            return
            
        # Handle normal PR interaction with preferences
        elif "@bennyPRBot" in comment_body.lower():
            
            # Get configured agent with user preferences
            agent, attached_blocks = await get_configured_agent(
                user_id=commenter,
                repo_full_name=repo_full_name,
                installation_id=payload.get("installation", {}).get("id")
            )
            
            try:
                # Process with personalized context
                user_query = comment_body.replace("@bennyPRBot", "").strip()
                response = await process_pr_interaction_with_preferences(
                    payload, user_query, agent
                )
                await post_pr_comment(payload, response)
                
            finally:
                # Always clean up memory
                await cleanup_agent_memory(attached_blocks)

async def process_pr_interaction_with_preferences(payload: dict, user_query: str, agent):
    """Process PR interaction using personalized agent with memory"""
    
    # The agent now has access to user preferences in its memory blocks
    # Letta will automatically use this context when generating responses
    
    pr_data = await fetch_pr_data(payload)
    changed_files = await fetch_pr_changed_files(payload)
    
    # Build prompt that references memory blocks
    prompt = build_personalized_pr_prompt(
        repo_full_name=payload.get("repository", {}).get("full_name"),
        pr_data=pr_data,
        changed_files=changed_files,
        user_query=user_query,
        # Memory blocks will be automatically included by Letta
    )
    
    # Use Letta agent instead of direct Cerebras call
    response = client.agents.send_message(
        agent_id=agent.id,
        message=prompt
    )
    
    return response.messages[-1].content
```

### 5. Preference File Examples

```markdown
# User Preference File Example (preferences.md)

## Code Review Preferences

**Review Style:** thorough
**Focus Areas:** 
- Security vulnerabilities
- Performance optimizations  
- Code readability
- Test coverage

**Communication Style:**
- Tone: friendly but professional
- Detail level: high for complex issues, moderate for simple ones
- Format: inline comments with summary

## Programming Preferences

**Code Style:**
- Prefer explicit over implicit
- Favor composition over inheritance
- Use descriptive variable names
- Maximum function length: 50 lines

**Testing Philosophy:**
- Unit tests required for all business logic
- Integration tests for API endpoints
- Mock external dependencies
- Minimum 80% coverage

## Specific to this Codebase

**Architecture Notes:**
- This is a microservices architecture
- We use Domain-Driven Design patterns
- Database changes require migration scripts
- All APIs must be backward compatible

**Deployment Process:**
- Feature flags for gradual rollouts
- Blue-green deployment strategy
- Monitoring alerts required for new endpoints
```

## Benefits

1. **Personalization**: Each user gets tailored reviews based on their preferences
2. **Context Awareness**: Agent remembers user preferences across all interactions
3. **Scalability**: Single agent serves all users with dynamic memory loading
4. **Persistence**: Preferences survive across sessions and deployments
5. **Flexibility**: Users can update preferences anytime
6. **Codebase-Specific**: Different preferences per repository

## Command System

### Initialization Commands

**`@toph-bot/init`** - Initialize user preferences for the first time
- Prompts user to provide preferences if none exist
- Creates new memory block for user-codebase combination
- Supports multiple input formats (YAML, JSON, Markdown, plain text)

**`@toph-bot/configure`** - Update existing user preferences
- Modifies existing memory block
- Can be used for incremental updates
- Supports same input formats as init

### Auto-Initialization
- If user interacts with bot without preferences, bot automatically prompts for initialization
- Provides helpful examples and format suggestions
- Guides user through preference setup process

## Usage Flow

1. **First Time Setup**:
   ```
   User: "@toph-bot/init"
   Bot: "Please provide your preferences in the following formats..."
   User: [uploads preferences file or pastes content]
   Bot: "✅ Preferences initialized! Here's what I remember about you..."
   ```

2. **Auto-Prompted Setup**:
   ```
   User: "@toph-bot review this PR"
   Bot: "👋 Hi! I notice this is our first interaction. Please run `@toph-bot/init` to set up your preferences..."
   ```

3. **Normal PR Review** (after setup):
   ```
   User: "@toph-bot review this PR"
   Bot: [Loads user preferences] → [Reviews with personal style] → [Posts personalized response]
   ```

4. **Preference Updates**:
   ```
   User: "@toph-bot/configure" + new preferences
   Bot: "✅ Preferences updated! Changes: review style: moderate → thorough"
   ```

5. **Quick Updates**:
   ```
   User: "@toph-bot please be more concise in your reviews"
   Bot: [Updates preferences] → "✅ I'll be more concise in future reviews"
   ```

This design gives you a sophisticated, personalized PR bot that remembers user preferences while maintaining efficiency through the agent-as-server pattern.

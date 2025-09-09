# toph-bot Preference Examples

This file shows different ways to configure your preferences for toph-bot.

## Example 1: Markdown Format

```markdown
## Code Review Preferences
- Review style: thorough
- Focus areas: security, performance, readability, testing
- Communication tone: friendly
- Detail level: high
- Feedback format: both

## Programming Preferences
- Code style: prefer explicit over implicit
- Naming: use descriptive variable names
- Functions: maximum 50 lines per function
- Architecture: favor composition over inheritance

## Testing Philosophy
- Unit tests: required for all business logic
- Integration tests: required for API endpoints
- Test coverage: minimum 80%
- Mocking: mock external dependencies

## Communication Preferences
- Be encouraging and constructive
- Provide specific examples when possible
- Include links to documentation when relevant
- Explain the "why" behind suggestions
```

## Example 2: YAML Format

```yaml
review_style: moderate
focus_areas: 
  - security
  - performance 
  - readability
communication_tone: professional
detail_level: medium
feedback_format: inline

code_style:
  explicitness: "prefer explicit over implicit"
  naming: "use descriptive names"
  functions: "keep functions focused and small"

testing:
  unit_tests: "required for business logic"
  coverage: "aim for 80% minimum"
  approach: "test-driven development preferred"

codebase_specific:
  architecture: "microservices with DDD patterns"
  deployment: "blue-green with feature flags"
  monitoring: "comprehensive logging and metrics"
```

## Example 3: JSON Format

```json
{
  "review_style": "thorough",
  "focus_areas": ["security", "performance", "architecture"],
  "communication_tone": "direct",
  "detail_level": "high",
  "feedback_format": "summary",
  "code_style": {
    "naming_convention": "descriptive and consistent",
    "function_length": "prefer smaller functions",
    "error_handling": "explicit error handling required"
  },
  "testing": {
    "approach": "comprehensive unit and integration tests",
    "coverage": "90% minimum",
    "mocking": "mock external services"
  },
  "codebase_specific": {
    "patterns": "follow established patterns in codebase",
    "documentation": "update docs for public APIs",
    "backwards_compatibility": "maintain API compatibility"
  }
}
```

## Example 4: Plain Text (Natural Language)

```
Please be thorough in your reviews and focus on security vulnerabilities and performance issues. 

I prefer a friendly but professional tone. Give me detailed explanations for complex issues but keep simple fixes concise.

For code style, I like explicit code over implicit, descriptive variable names, and small focused functions.

For testing, I want unit tests for all business logic and integration tests for APIs. Please suggest mocking external dependencies.

This codebase uses microservices architecture with domain-driven design patterns. We deploy using blue-green strategy with feature flags.
```

## Quick Setup Commands

### Initialize Preferences
```
@toph-bot/init
[paste your preferences in any format above]
```

### Update Preferences  
```
@toph-bot/configure
review_style: light
communication_tone: direct
```

### Quick Natural Language Update
```
@toph-bot please be more concise in your reviews and focus mainly on security issues
```

## Tips

1. **Mix and Match**: You can combine different preference types in one configuration
2. **Incremental Updates**: Use `/configure` to update just specific preferences
3. **Natural Language**: toph-bot understands natural language descriptions
4. **Per-Repository**: Each repository can have different preferences
5. **Evolving Preferences**: Update anytime as your needs change

## Preference Categories

### Review Style Options
- `thorough`: Detailed analysis with comprehensive feedback
- `moderate`: Balanced approach with key issues highlighted
- `light`: Focus on critical issues only

### Focus Areas
- `security`: Security vulnerabilities and best practices
- `performance`: Performance optimizations and bottlenecks
- `readability`: Code clarity and maintainability
- `testing`: Test coverage and quality
- `architecture`: System design and patterns
- `documentation`: Code documentation and comments

### Communication Tones
- `friendly`: Warm, encouraging, and supportive
- `professional`: Clear, direct, and business-focused
- `direct`: Straight to the point, minimal fluff

### Detail Levels
- `high`: Comprehensive explanations and context
- `medium`: Balanced detail with key points
- `low`: Concise summaries and bullet points

### Feedback Formats
- `inline`: Comments directly on code lines
- `summary`: Overall review summary
- `both`: Combination of inline and summary

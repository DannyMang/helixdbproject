"""
Preference Extractor for bennyPRBot - Handles parsing user preferences from various formats
"""

import json
import yaml
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class UserPreferences:
    """Structured user preferences"""
    review_style: str = "moderate"  # thorough, moderate, light
    focus_areas: List[str] = None
    communication_tone: str = "professional"  # friendly, professional, direct
    detail_level: str = "medium"  # high, medium, low
    feedback_format: str = "both"  # inline, summary, both
    code_style_preferences: Dict[str, Any] = None
    testing_preferences: Dict[str, Any] = None
    codebase_specific: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["readability", "performance", "security"]
        if self.code_style_preferences is None:
            self.code_style_preferences = {}
        if self.testing_preferences is None:
            self.testing_preferences = {}
        if self.codebase_specific is None:
            self.codebase_specific = {}


class PreferenceExtractor:
    """Handles extraction and parsing of user preferences from various formats"""
    
    def parse_preference_content(self, content: str) -> UserPreferences:
        """Parse user's preference content into structured format"""
        
        # Try different parsing strategies based on content format
        if self._is_yaml_format(content):
            return self._parse_yaml_preferences(content)
        elif self._is_json_format(content):
            return self._parse_json_preferences(content)
        elif self._is_markdown_format(content):
            return self._parse_markdown_preferences(content)
        else:
            return self._parse_text_preferences(content)
    
    def _is_yaml_format(self, content: str) -> bool:
        """Check if content appears to be in YAML format"""
        return ("```yaml" in content or 
                content.strip().startswith("---") or
                content.strip().startswith("review_style:"))
    
    def _is_json_format(self, content: str) -> bool:
        """Check if content appears to be in JSON format"""
        return ("```json" in content or 
                (content.strip().startswith("{") and content.strip().endswith("}")))
    
    def _is_markdown_format(self, content: str) -> bool:
        """Check if content appears to be in Markdown format"""
        return ("##" in content or "**" in content or "- " in content)
    
    def _parse_yaml_preferences(self, content: str) -> UserPreferences:
        """Parse YAML preference format"""
        try:
            # Extract YAML from code blocks if present
            yaml_content = self._extract_code_block(content, "yaml")
            if not yaml_content:
                yaml_content = content.strip()
            
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                raise ValueError("YAML content is not a dictionary")
                
            return self._create_preferences_from_dict(data)
            
        except Exception as e:
            print(f"Error parsing YAML preferences: {e}")
            return self._parse_text_preferences(content)
    
    def _parse_json_preferences(self, content: str) -> UserPreferences:
        """Parse JSON preference format"""
        try:
            # Extract JSON from code blocks if present
            json_content = self._extract_code_block(content, "json")
            if not json_content:
                json_content = content.strip()
            
            data = json.loads(json_content)
            return self._create_preferences_from_dict(data)
            
        except Exception as e:
            print(f"Error parsing JSON preferences: {e}")
            return self._parse_text_preferences(content)
    
    def _parse_markdown_preferences(self, content: str) -> UserPreferences:
        """Parse Markdown-formatted preferences"""
        prefs = UserPreferences()
        content_lower = content.lower()
        lines = content.split('\\n')
        
        current_section = None
        section_content = {}
        
        for line in lines:
            line = line.strip()
            
            # Detect sections
            if line.startswith('##'):
                current_section = line.replace('##', '').strip().lower()
                section_content[current_section] = []
            elif line.startswith('**') and line.endswith('**'):
                # Bold text - likely a key
                key = line.replace('**', '').replace(':', '').strip().lower()
                if current_section:
                    section_content[current_section].append(('key', key))
            elif line.startswith('- '):
                # List item
                item = line.replace('- ', '').strip()
                if current_section:
                    section_content[current_section].append(('item', item))
        
        # Extract preferences from parsed sections
        prefs = self._extract_from_markdown_sections(section_content)
        
        # Fall back to text parsing for any missed items
        text_prefs = self._parse_text_preferences(content)
        prefs = self._merge_preferences(prefs, text_prefs)
        
        return prefs
    
    def _parse_text_preferences(self, content: str) -> UserPreferences:
        """Parse free-form text preferences using keyword detection"""
        prefs = UserPreferences()
        content_lower = content.lower()
        
        # Extract review style
        style_keywords = {
            "thorough": ["thorough", "detailed", "comprehensive", "in-depth"],
            "light": ["light", "brief", "quick", "simple", "minimal"],
            "moderate": ["moderate", "balanced", "standard"]
        }
        
        for style, keywords in style_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                prefs.review_style = style
                break
        
        # Extract communication tone
        tone_keywords = {
            "friendly": ["friendly", "casual", "warm", "conversational"],
            "direct": ["direct", "straight", "blunt", "concise"],
            "professional": ["professional", "formal", "business"]
        }
        
        for tone, keywords in tone_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                prefs.communication_tone = tone
                break
        
        # Extract detail level
        detail_keywords = {
            "high": ["detailed", "verbose", "comprehensive", "thorough"],
            "low": ["brief", "summary", "minimal", "short"],
            "medium": ["moderate", "balanced", "standard"]
        }
        
        for level, keywords in detail_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                prefs.detail_level = level
                break
        
        # Extract focus areas from common keywords
        focus_keywords = {
            "security": ["security", "vulnerability", "secure", "safety", "auth"],
            "performance": ["performance", "speed", "optimization", "efficient", "fast"],
            "readability": ["readability", "readable", "clean", "clear", "maintainable"],
            "testing": ["testing", "test", "coverage", "unit test", "qa"],
            "documentation": ["documentation", "docs", "comments", "readme"],
            "architecture": ["architecture", "design", "patterns", "structure"]
        }
        
        detected_areas = []
        for area, keywords in focus_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_areas.append(area)
        
        if detected_areas:
            prefs.focus_areas = detected_areas
        
        # Extract code style preferences
        code_style_hints = {}
        if "explicit" in content_lower:
            code_style_hints["explicitness"] = "prefer explicit over implicit"
        if "composition" in content_lower:
            code_style_hints["inheritance"] = "favor composition over inheritance"
        if "descriptive" in content_lower:
            code_style_hints["naming"] = "use descriptive names"
        
        if code_style_hints:
            prefs.code_style_preferences = code_style_hints
        
        return prefs
    
    def _extract_code_block(self, content: str, language: str) -> str:
        """Extract code block content for a specific language"""
        marker = f"```{language}"
        start_idx = content.find(marker)
        if start_idx == -1:
            return ""
        
        start_idx += len(marker)
        end_idx = content.find("```", start_idx)
        if end_idx == -1:
            return ""
        
        return content[start_idx:end_idx].strip()
    
    def _create_preferences_from_dict(self, data: Dict[str, Any]) -> UserPreferences:
        """Create UserPreferences object from dictionary data"""
        return UserPreferences(
            review_style=data.get("review_style", "moderate"),
            focus_areas=data.get("focus_areas", ["readability", "performance"]),
            communication_tone=data.get("communication_tone", "professional"),
            detail_level=data.get("detail_level", "medium"),
            feedback_format=data.get("feedback_format", "both"),
            code_style_preferences=data.get("code_style", {}),
            testing_preferences=data.get("testing", {}),
            codebase_specific=data.get("codebase_specific", {})
        )
    
    def _extract_from_markdown_sections(self, sections: Dict[str, List]) -> UserPreferences:
        """Extract preferences from parsed markdown sections"""
        prefs = UserPreferences()
        
        # Process each section
        for section_name, content in sections.items():
            if "review" in section_name or "code review" in section_name:
                prefs = self._process_review_section(content, prefs)
            elif "programming" in section_name or "code" in section_name:
                prefs = self._process_programming_section(content, prefs)
            elif "testing" in section_name:
                prefs = self._process_testing_section(content, prefs)
            elif "communication" in section_name:
                prefs = self._process_communication_section(content, prefs)
        
        return prefs
    
    def _process_review_section(self, content: List, prefs: UserPreferences) -> UserPreferences:
        """Process review preferences section"""
        for item_type, item_value in content:
            if item_type == "item":
                item_lower = item_value.lower()
                if "security" in item_lower:
                    if "security" not in prefs.focus_areas:
                        prefs.focus_areas.append("security")
                elif "performance" in item_lower:
                    if "performance" not in prefs.focus_areas:
                        prefs.focus_areas.append("performance")
                elif "readability" in item_lower:
                    if "readability" not in prefs.focus_areas:
                        prefs.focus_areas.append("readability")
        return prefs
    
    def _process_programming_section(self, content: List, prefs: UserPreferences) -> UserPreferences:
        """Process programming preferences section"""
        for item_type, item_value in content:
            if item_type == "item":
                key_value = item_value.split(":", 1)
                if len(key_value) == 2:
                    key, value = key_value
                    prefs.code_style_preferences[key.strip()] = value.strip()
        return prefs
    
    def _process_testing_section(self, content: List, prefs: UserPreferences) -> UserPreferences:
        """Process testing preferences section"""
        for item_type, item_value in content:
            if item_type == "item":
                key_value = item_value.split(":", 1)
                if len(key_value) == 2:
                    key, value = key_value
                    prefs.testing_preferences[key.strip()] = value.strip()
        return prefs
    
    def _process_communication_section(self, content: List, prefs: UserPreferences) -> UserPreferences:
        """Process communication preferences section"""
        for item_type, item_value in content:
            if item_type == "item":
                item_lower = item_value.lower()
                if "friendly" in item_lower:
                    prefs.communication_tone = "friendly"
                elif "direct" in item_lower:
                    prefs.communication_tone = "direct"
                elif "professional" in item_lower:
                    prefs.communication_tone = "professional"
        return prefs
    
    def _merge_preferences(self, primary: UserPreferences, fallback: UserPreferences) -> UserPreferences:
        """Merge two preference objects, with primary taking precedence"""
        return UserPreferences(
            review_style=primary.review_style if primary.review_style != "moderate" else fallback.review_style,
            focus_areas=primary.focus_areas if primary.focus_areas != ["readability", "performance", "security"] else fallback.focus_areas,
            communication_tone=primary.communication_tone if primary.communication_tone != "professional" else fallback.communication_tone,
            detail_level=primary.detail_level if primary.detail_level != "medium" else fallback.detail_level,
            feedback_format=primary.feedback_format if primary.feedback_format != "both" else fallback.feedback_format,
            code_style_preferences={**fallback.code_style_preferences, **primary.code_style_preferences},
            testing_preferences={**fallback.testing_preferences, **primary.testing_preferences},
            codebase_specific={**fallback.codebase_specific, **primary.codebase_specific}
        )
    
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
    
    def detect_preference_file_in_comment(self, comment_body: str) -> bool:
        """Detect if a comment contains preference file content"""
        indicators = [
            "```yaml", "```json", "```markdown",
            "review_style:", "focus_areas:", "communication_tone:",
            "## Code Review", "## Programming Preferences",
            "@bennyPRBot setup", "@bennyprbot setup"
        ]
        
        comment_lower = comment_body.lower()
        return any(indicator.lower() in comment_lower for indicator in indicators)
    
    def extract_preference_content_from_comment(self, comment_body: str) -> str:
        """Extract preference content from a GitHub comment"""
        # If it's a code block, extract the content
        for lang in ["yaml", "json", "markdown", "md", "txt"]:
            marker = f"```{lang}"
            if marker in comment_body.lower():
                return self._extract_code_block(comment_body, lang)
        
        # If no code block, check for setup command and return everything after it
        setup_patterns = ["@bennyPRBot setup", "@bennyprbot setup"]
        for pattern in setup_patterns:
            if pattern.lower() in comment_body.lower():
                start_idx = comment_body.lower().find(pattern.lower()) + len(pattern)
                return comment_body[start_idx:].strip()
        
        # Return the whole comment if it looks like preferences
        if self.detect_preference_file_in_comment(comment_body):
            return comment_body.strip()
        
        return ""
